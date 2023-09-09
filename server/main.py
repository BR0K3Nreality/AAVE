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

# Function to handle dynamic audio parameters
def handle_dynamic_params(request):
    tempo = request.json.get('tempo', 120)
    instrument = request.json.get('instrument', 'Piano')
    return tempo, instrument

# API Endpoint for dynamic audio parameters
@app.route('/generate_audio', methods=['POST'])
def generate_audio():
    tempo, instrument = handle_dynamic_params(request)
    # Integrate code here for actual audio generation
    return jsonify({"message": f"Generated audio with tempo: {tempo}, instrument: {instrument}"}), 200

# Function to handle audio effects
def handle_audio_effects(request):
    reverb = request.json.get('reverb', False)
    echo = request.json.get('echo', False)
    return reverb, echo

# API Endpoint for audio effects
@app.route('/apply_effects', methods=['POST'])
def apply_effects():
    reverb, echo = handle_audio_effects(request)
    # Integrate code here for actual audio effects
    return jsonify({"message": f"Applied effects - Reverb: {reverb}, Echo: {echo}"}), 200

# Function to handle user authentication
def handle_authentication(request):
    token = request.json.get('token', None)
    if token == "valid_token":  # Replace with actual authentication logic
        return True
    else:
        return False

# API Endpoint for user authentication
@app.route('/authenticate', methods=['POST'])
def authenticate():
    if handle_authentication(request):
        return jsonify({"message": "Authenticated successfully"}), 200
    else:
        return jsonify({"message": "Invalid token"}), 401

# API Endpoint for file management (e.g., retrieval)
@app.route('/get_audio', methods=['GET'])
def get_audio():
    # Integrate code here for actual file retrieval
    file_path = "path/to/audio/file"
    return jsonify({"file_path": file_path}), 200

# Add API documentation endpoint if needed
# ...
