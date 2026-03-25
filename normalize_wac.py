import wave
import audioop
import math

def normalize_wav(input_path, output_path, target_dBFS=-20.0):
    with wave.open(input_path, 'rb') as wf:
        params = wf.getparams()
        frames = wf.readframes(wf.getnframes())

    sample_width = params.sampwidth
    rms = audioop.rms(frames, sample_width)  # Calculate RMS (Root Mean Square)

    if rms == 0:
        print("The audio file is empty.")
        return

    # Calculate current dBFS (dB relative to full scale)
    current_dBFS = 20 * math.log10(rms / (2 ** (8 * sample_width - 1)))

    # Calculate the difference between target and current dBFS
    difference = target_dBFS - current_dBFS
    factor = 10 ** (difference / 20)

    # Normalize the audio by multiplying by the factor
    normalized_frames = audioop.mul(frames, sample_width, factor)

    with wave.open(output_path, 'wb') as wf:
        wf.setparams(params)
        wf.writeframes(normalized_frames)

    print(f"Normalized file saved as: {output_path}")


# Example usage
input_file = r"AudioFiles\output.wav"
output_file = r"AudioFiles\normalized_output.wav"
normalize_wav(input_file, output_file)
