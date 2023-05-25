import numpy as np
from PIL import Image
from pydub import AudioSegment
from pydub.effects import low_pass_filter
from tqdm import tqdm
import os
import sys
from flask import Flask, request, send_file

app = Flask(__name__)

def karplus_strong(frequency, duration, sample_rate=44100, blend=0.5):
    N = int(sample_rate / frequency)
    buffer = np.random.uniform(-1, 1, size=N)
    output = np.zeros(int(sample_rate * duration))

    for i in range(output.shape[0]):
        output[i] = buffer[i % N]
        buffer[i % N] = blend * (buffer[i % N] + buffer[(i - 1) % N])

    return output

def pixel_to_audio_sample(pixel, sample_rate=44100):
    red, green, blue = pixel / 3
    base_frequency = 82.41 + (((red + green + blue) / 765) * (987.77 - 82.41))

    red_frequency = base_frequency
    green_frequency = base_frequency * (2**(6/12))  # Phrygian fifth
    blue_frequency = base_frequency * (2**(1/12))  # Phrygian second

    duration = 0.15

    audio_sample_red = karplus_strong(red_frequency, duration, sample_rate)
    audio_sample_green = karplus_strong(green_frequency, duration, sample_rate)
    audio_sample_blue = karplus_strong(blue_frequency, duration, sample_rate)

    sample_width = audio_sample_red.dtype.itemsize
    channels = 1
    remainder_red = len(audio_sample_red) % (sample_width * channels)
    remainder_green = len(audio_sample_green) % (sample_width * channels)
    remainder_blue = len(audio_sample_blue) % (sample_width * channels)

    if remainder_red != 0:
        audio_sample_red = audio_sample_red[:-remainder_red]
    if remainder_green != 0:
        audio_sample_green = audio_sample_green[:-remainder_green]
    if remainder_blue != 0:
        audio_sample_blue = audio_sample_blue[:-remainder_blue]

    audio_sample = (audio_sample_red + audio_sample_green + audio_sample_blue) / 3

    return audio_sample

def image_to_audio(image, size=(10, 10), sample_rate=44100):
    image = image.resize(size)

    pixel_data = np.array(image)

    audio_segments = []
    for row in tqdm(pixel_data, desc="Processing audio segments"):
        for pixel in row:
            audio_sample = pixel_to_audio_sample(pixel, sample_rate)
            audio_sample = audio_sample / np.max(np.abs(audio_sample)) * 0.5  # Scale the audio to increase volume

            audio_segment = AudioSegment(
                audio_sample.tobytes(),
                frame_rate=sample_rate,
                sample_width=4,
                channels=1,
            )
            audio_segments.append(audio_segment)

    combined_audio = sum(audio_segments)
    combined_audio = low_pass_filter(combined_audio, 5000)
    return combined_audio

def convertImg(path):
    image = Image.open(path).convert("RGB")
    audio = image_to_audio(image)
    output_filename = f"{path.split('/')[-1].split('.')[0]}.wav"
    audio.export("./output/" + output_filename, format="wav")
    print("Processing completed successfully file stored in output/" + output_filename)
    return output_filename

@app.route('/convert', methods=['POST'])
def convert_image():
    file = request.files['file']
    file.save(file.filename)
    output_filename = convertImg(file.filename)
    os.remove(file.filename)
    return send_file("./output/" + output_filename)

if __name__ == "__main__":
    if not os.path.exists("./output/"):
        os.makedirs("./output/")
    app.run(host='0.0.0.0')
