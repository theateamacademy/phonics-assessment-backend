import sounddevice as sd
import numpy as np
import soundfile as sf
import os
import re
import get_speech_metrics
import llm
import prompts
import logging
import json
import librosa


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler('KidsAcademy.log', encoding='utf-8')
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.propagate = False


def _extract_json_object(text, log_label: str):
    """
    Parse JSON from LLM output. Handles empty replies, markdown fences, and leading/trailing prose.
    Empty input causes json.loads to raise: Expecting value: line 1 column 1 (char 0).
    """
    if text is None:
        logger.warning("LLM returned None for %s", log_label)
        return None
    s = str(text).strip()
    if not s:
        logger.warning("LLM returned empty string for %s", log_label)
        return None
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", s, re.IGNORECASE)
    if fence:
        s = fence.group(1).strip()
    start = s.find("{")
    end = s.rfind("}")
    if start != -1 and end != -1 and end > start:
        s = s[start : end + 1]
    try:
        return json.loads(s)
    except json.JSONDecodeError as e:
        logger.warning("JSON decode failed for %s: %s — snippet: %r", log_label, e, s[:200])
        return None


_DEFAULT_TOP_LEVEL = {
    "overall": 0,
    "rhythm": 0,
    "pause_count": 0,
    "pronunciation": 0,
    "fluency": 0,
    "integrity": 0,
    "speed": 0,
    "grammar": 0,
}

_DEFAULT_GRAMMAR = {
    "word_error": 0,
    "word_error_list": [],
    "verb_error": 0,
    "verb_error_list": [],
    "article_error": 0,
    "article_error_list": [],
    "phoneme_scores": [],
}

_DEFAULT_SKILLS = {
    "Skill 1 (Vowel sounds)": 0,
    "Skill 2 (Fricatives and Affricates)": 0,
    "Skill 3 (Consonant clusters)": 0,
    "Skill 4 (Intrusion and Elision)": 0,
    "Skill 5 (Diphthongs)": 0,
}


def start_recording():
    duration = 13  # seconds
    rate = 44100
    channels = 1
    output_folder = "AudioFiles"
    filename = os.path.join(output_folder, "output.wav")

    os.makedirs(output_folder, exist_ok=True)

    print("🎙️ Recording for 15 seconds...")

    try:
        # Record float32 audio between -1.0 and 1.0
        recording = sd.rec(int(duration * rate), samplerate=rate, channels=channels, dtype='float32')
        sd.wait()
        print("✅ Done recording.")
    except Exception as e:
        print(f"❌ Recording failed: {e}")
        return

    # Normalize and boost
    audio = recording.flatten()
    peak = np.max(np.abs(audio))

    if peak == 0:
        print("⚠️ Silence detected. Skipping normalization.")
        boosted_audio = audio
    else:
        normalized_audio = audio / peak
        boosted_audio = normalized_audio * 2.0  # Boost volume (try 1.5 - 2.5)
        boosted_audio = np.clip(boosted_audio, -1.0, 1.0)  # Prevent distortion

    # Save to WAV
    sf.write(filename, boosted_audio, rate, subtype='PCM_16')
    print(f"💾 Boosted audio saved to: {filename}")


def analyze_recording(text, child_name, model="sent.eval.promax"):
    logger.info("inside analyse recording")
    audio_path = "AudioFiles/output.wav"
    metrics = get_speech_metrics.start_processing(audio_path, text, model)
    logger.info(f"Metrics received, length: {len(metrics) if metrics else 0}")
    # metrics = get_speech_metrics.start_processing(audio_path, text, model)
    # print(f"DEBUG: Metrics type: {type(metrics)}, Content: {metrics}")

    # Validate audio
    try:
        y, sr = librosa.load(audio_path)
        duration = librosa.get_duration(y=y, sr=sr)
        max_amplitude = np.max(np.abs(y))
        logger.info(
            f"Audio stats: duration={duration:.2f}s, sample_rate={sr}, max_amplitude={max_amplitude:.4f}"
        )
        if duration < 0.5 or max_amplitude < 0.001:
            logger.warning("Audio too short or silent")
            pitch_score = volume_score = 0
        else:
            # Trim silence
            y_trimmed, _ = librosa.effects.trim(y, top_db=20)
            trimmed_duration = librosa.get_duration(y=y_trimmed, sr=sr)
            logger.info(f"Trimmed duration: {trimmed_duration:.2f}s")

            # Calculate Pitch (unchanged, since 100% is correct)
            try:
                pitches, magnitudes = librosa.piptrack(y=y_trimmed, sr=sr)
                pitch_values = pitches[magnitudes > np.percentile(
                    magnitudes, 50)]
                if len(pitch_values) > 0:
                    avg_pitch = np.mean(pitch_values)
                    pitch_score = np.clip(
                        (avg_pitch - 150) / (450 - 150) * 100, 0, 100)
                    logger.info(
                        f"Pitch: count={len(pitch_values)}, avg={avg_pitch:.2f}Hz, score={pitch_score:.2f}%"
                    )
                else:
                    logger.warning("No valid pitch values detected")
                    pitch_score = 0
            except Exception as e:
                logger.error(f"Error calculating pitch: {e}")
                pitch_score = 0

            # Calculate Volume
            try:
                rms = librosa.feature.rms(y=y_trimmed)[0]
                if len(rms) > 0:
                    avg_rms = np.mean(rms)
                    volume_score = np.clip(avg_rms / 0.05 * 100, 0, 100)
                    logger.info(
                        f"Volume: rms_count={len(rms)}, avg_rms={avg_rms:.4f}, score={volume_score:.2f}%"
                    )
                else:
                    logger.warning("No RMS values detected")
                    volume_score = 0
            except Exception as e:
                logger.error(f"Error calculating volume: {e}")
                volume_score = 0
    except Exception as e:
        logger.error(f"Error loading audio: {e}")
        pitch_score = volume_score = 0

    feedback = llm.get_response_from_ai(prompts.analyze_metrics(child_name), metrics)
    skill_cluster = llm.get_response_from_ai(prompts.skill_cluster(), metrics)
    top_level_metrics = llm.get_response_from_ai(prompts.top_level_metrics(), metrics)
    grammar = llm.get_response_from_ai(prompts.get_grammar_feedback(), metrics)
    logger.info("Grammar LLM call finished")

    if not feedback or not str(feedback).strip():
        feedback = (
            f"We couldn't generate detailed feedback for {child_name} this time. "
            "Try recording again with a clear voice, or check your OpenAI API key and quota."
        )

    parsed_metrics = _extract_json_object(top_level_metrics, "top_level_metrics")
    parsed_grammar = _extract_json_object(grammar, "grammar")
    parsed_cluster = _extract_json_object(skill_cluster, "skill_cluster")

    if parsed_metrics is None:
        parsed_metrics = dict(_DEFAULT_TOP_LEVEL)
        logger.warning("Using default top_level_metrics after LLM JSON parse failure")
    if parsed_grammar is None:
        parsed_grammar = dict(_DEFAULT_GRAMMAR)
        logger.warning("Using default grammar structure after LLM JSON parse failure")
    if parsed_cluster is None:
        parsed_cluster = dict(_DEFAULT_SKILLS)
        logger.warning("Using default skill_cluster after LLM JSON parse failure")

    combined_metrics = {
        **parsed_metrics,
        **parsed_grammar,
        "pitch": float(pitch_score),
        "volume": float(volume_score),
        **parsed_cluster,
    }
    try:
        logger.info("Combined metrics assembled (keys: %s)", list(combined_metrics.keys()))
    except Exception:
        logger.info("Combined metrics assembled")
    logger.info("Feedback length: %s chars", len(feedback) if feedback else 0)
    return combined_metrics, feedback


def save_user_metrics(username, metrics):
    try:
        try:
            with open("user_metrics.json", "r") as f:
                data = json.load(f)
        except:
            data = {}
        data[username] = metrics
        with open("user_metrics.json", "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving metrics: {e}")
        # raise

