import pyaudio
import wave
import numpy as np

# Parameters
chunk = 1024
format = pyaudio.paInt16
channels = 1  # mono is often more consistent for speech
rate = 44100
duration = 5
filename = "output_loud.wav"

# Initialize PyAudio
p = pyaudio.PyAudio()
stream = p.open(format=format, channels=channels, rate=rate,
                input=True, frames_per_buffer=chunk)

print("🎙️ Recording...")
frames = []

for _ in range(0, int(rate / chunk * duration)):
    data = stream.read(chunk)
    frames.append(data)

print("✅ Done recording.")

stream.stop_stream()
stream.close()
p.terminate()

# Convert byte data to numpy array
audio_data = b''.join(frames)
audio_array = np.frombuffer(audio_data, dtype=np.int16)

# Normalize audio to maximum volume
max_val = np.max(np.abs(audio_array))
if max_val == 0:
    print("⚠️ Silence detected. No normalization applied.")
else:
    normalized_audio = (audio_array / max_val) * 32767  # max for int16
    normalized_audio = normalized_audio.astype(np.int16)

# Save to WAV file
wf = wave.open(filename, 'wb')
wf.setnchannels(channels)
wf.setsampwidth(p.get_sample_size(format))
wf.setframerate(rate)
wf.writeframes(normalized_audio.tobytes())
wf.close()

print(f"💾 Saved with volume boosted: {filename}")
