import os
import get_speech_metrics
import llm
import prompts
import speech_recognition as sr
import logging
# import pyaudio
import json
import threading
import time


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler('KidsAcademy.log')
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


# def start_recording():
#     os.makedirs("AudioFiles", exist_ok=True)
#     audio_path = "AudioFiles\\output.wav"

#     r = sr.Recognizer()
#     with sr.Microphone() as source:
#         audio = r.listen(source)
#     with open(audio_path, "wb") as f:
#         f.write(audio.get_wav_data())

#     return "Completed"


# record_and_analyze.py


audio_frames = []  # Global variable to store audio frames
recording_flag = False  # Control flag for recording


recognizer = sr.Recognizer()
microphone = sr.Microphone()
audio_data = None
stop_event = threading.Event()
start_time = None

def record_audio():
    global audio_data, start_time, audio_frames  # <-- ADD audio_frames here
    print("Recording thread started.")
    with microphone as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        print("Adjusted for ambient noise.")
        audio_frames = []
        start_time = time.time()
        while not stop_event.is_set():
            remaining = 15 - (time.time() - start_time)
            if remaining <= 0:
                print("Time limit reached.")
                break
            print(f"Recording... remaining: {remaining:.2f}s")
            try:
                audio = recognizer.record(source, duration=1)
                audio_frames.append(audio)
            except Exception as e:
                print(f"Error during recording: {e}")

        if audio_frames:
            print(f"Recorded {len(audio_frames)} frames.")
            combined_data = sr.AudioData(
                b''.join([a.get_raw_data() for a in audio_frames]),
                sample_rate=audio_frames[0].sample_rate,
                sample_width=audio_frames[0].sample_width
            )
            audio_data = combined_data  # <-- Store final data here
        else:
            print("No audio frames captured.")
            audio_data = None

    stop_event.set()
    print("Recording thread finished.")



def start_recording():
    global stop_event, audio_data
    stop_event.clear()
    audio_data = None
    os.makedirs("AudioFiles", exist_ok=True)

    threading.Thread(target=record_audio, daemon=True).start()
    return "Recording started"

def stop_recording():
    global audio_data
    stop_event.set()
    time.sleep(1)  # Allow time for thread to join and complete

    if audio_data:
        os.makedirs("AudioFiles", exist_ok=True)
        with open("AudioFiles/output.wav", "wb") as f:
            f.write(audio_data.get_wav_data())
        print("Recording saved.")
        return "Completed"
    else:
        print("No recording to save.")
        return "Failed"




import json


#working fine
# def analyze_recording(text, model="sent.eval.promax"):
#     audio_path = "AudioFiles\\output.wav"
#     metrics = get_speech_metrics.start_processing(audio_path, text, model)
#     print(f"Metrics: {metrics}")

#     feedback = llm.get_response_from_ai(prompts.analyze_metrics(), metrics)
#     top_level_metrics = llm.get_response_from_ai(prompts.top_level_metrics(), metrics)

#     # Ensure top_level_metrics is parsed from string to dict
#     try:
#         parsed_metrics = json.loads(top_level_metrics)
#     except json.JSONDecodeError as e:
#         print(f"Failed to decode JSON: {e}")
#         return "Error: Could not parse top-level metrics response"

#     # Save as proper JSON
#     output_file_path = "top_level_metrics.json"
#     with open(output_file_path, "w") as json_file:
#         json.dump(parsed_metrics, json_file, indent=4)

#     print(f"Metrics stored in {output_file_path}")
#     logger.info(f"Feedback: {feedback}")

#     return feedback

def analyze_recording(text, model="sent.eval.promax"):
    audio_path = "AudioFiles\\output.wav"
    metrics = get_speech_metrics.start_processing(audio_path, text, model)
    print(f"Metrics: {metrics}")

    feedback = llm.get_response_from_ai(prompts.analyze_metrics(), metrics)
    
    top_level_metrics = llm.get_response_from_ai(prompts.top_level_metrics(), metrics)
    grammar = llm.get_response_from_ai(prompts.get_grammar_feedback(), feedback)

    try:
        # Parse both JSON strings
        parsed_metrics = json.loads(top_level_metrics)
        parsed_grammar = json.loads(grammar)
        
        # Combine the metrics
        combined_metrics = {**parsed_metrics, **parsed_grammar}
        
        logger.info(f"Combined Metrics: {combined_metrics}")
        logger.info(f"Feedback: {feedback}")
        
        return combined_metrics, feedback
        
    except json.JSONDecodeError as e:
        print(f"Failed to decode JSON: {e}")
        return None, None

# In record_and_analyze.py
def save_user_metrics(username, metrics):
    try:
        # Try to load existing data
        try:
            with open("user_metrics.json", "r") as f:
                data = json.load(f)
        except:
            data = {}
            
        # Update with new metrics
        data[username] = metrics
        
        # Save back to file
        with open("user_metrics.json", "w") as f:
            json.dump(data, f, indent=2)
            
    except Exception as e:
        print(f"Error saving metrics: {e}")
        # raise

