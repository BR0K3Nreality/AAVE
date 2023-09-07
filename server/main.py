import numpy as np
from PIL import Image
from midiutil import MIDIFile
from flask import Flask, request, send_from_directory
from scipy.signal import butter, lfilter
from midi2audio import FluidSynth
import os
import sys
from flask_cors import CORS
import threading
import numpy as np
from PIL import Image
from pydub import AudioSegment
from pydub.effects import low_pass_filter
from tqdm import tqdm
import os
import sys
from flask import Flask, request, send_file
from flasgger import Swagger, swag_from


app = Flask(__name__)
CORS(app)
swagger = Swagger(app)

def butter_lowpass(cutoff, fs, order=5):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    return b, a

def butter_lowpass_filter(data, cutoff, fs, order=5):
    b, a = butter_lowpass(cutoff, fs, order=order)
    y = lfilter(b, a, data)
    return y

def pixel_to_midi(pixel, time, track, channel, velocity, duration, midi):
    red, green, blue = pixel
    midi.addNote(track, channel, red, time, duration, velocity)
    midi.addNote(track, channel, green, time + duration, duration, velocity)
    midi.addNote(track, channel, blue, time + 2 * duration, duration, velocity)

def image_to_midi(image, size=(10, 10), track=0, channel=0, velocity=100, duration=1):
    image = image.resize(size)
    pixel_data = np.array(image)

    midi = MIDIFile(1)
    midi.addTempo(track, 0, 120)  # Add tempo of 120 BPM to track 0 at time 0


    time = 0
    for row in pixel_data:
        for pixel in row:
            pixel_to_midi(pixel, time, track, channel, velocity, duration, midi)
            time += 3 * duration
    return midi

def delete_file(path):
    if os.path.exists(path):
        os.remove(path)
    else:
        print("The file does not exist")

def convertImg(path):
    image = Image.open(path).convert("RGB")
    midi = image_to_midi(image)
    output_filename = f"{path.split('/')[-1].split('.')[0]}.mid"
    output_filepath = os.path.join("./output/", output_filename)
    with open(output_filepath, "wb") as output_file:
        midi.writeFile(output_file)

    # Generate audio from MIDI
    output_audio_filename = f"{path.split('/')[-1].split('.')[0]}.wav"
    # FluidSynth().midi_to_audio(output_filepath, "./output/" + output_audio_filename) Convert midi to wav
    
    print("Processing completed successfully. File stored in output/" + output_audio_filename)
    return output_filename

@app.route('/convert', methods=['POST'])
@swag_from({
    'parameters': [
        {
            'name': 'file',
            'in': 'formData',
            'type': 'file',
            'required': 'true'
        }
    ],
    'responses': {
        200: {
            'description': 'Success',
            'schema': {
                'type': 'file',
                'description': 'The generated .mid file'
            }
        }
    },
    'consumes':['multipart/form-data'],
})
def convert_image():
    """Converts the uploaded image file to a .mid file
    ---
    post:
      parameters:
        - in: formData
          name: file
          type: file
          required: true
          description: The image file to convert
      responses:
        200:
          description: The generated .mid file
          schema:
            type: file
            description: The generated .mid file
    """
    file = request.files['file']
    filename = file.filename  # Get the uploaded file name
    file.save(filename)
    output_filename = convertImg(filename)
    os.remove(filename)

    # Set the content disposition header to force download with the original image name and .mid extension
    response = send_from_directory("./output/", output_filename, as_attachment=True)
    response.headers["Content-Disposition"] = f"attachment; filename={filename}.mid"
    
    # Delete the output file after 20 minutes
    timer = threading.Timer(1200, delete_file, ["./output/" + output_filename])
    timer.start()

    return response

if __name__ == "__main__":
    if not os.path.exists("./output/"):
        os.makedirs("./output/")
        
    # Default port will be 5000 if no argument is provided
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 1223
    app.run(host='0.0.0.0', port=port)
