from flask import Flask, render_template, request, jsonify, send_from_directory
import os
from spleeter.separator import Separator
from pydub import AudioSegment
import numpy as np
from scipy.io import wavfile
import uuid
import logging

ALLOWED_EXTENSIONS = {'mp3', 'wav'}

# Made "public" folder to serve static files
app = Flask(__name__, template_folder='../frontend/templates', static_url_path='',static_folder='../public')


def mp3_to_wav(mp3_path):
    wav_path = mp3_path.replace(".mp3", ".wav")
    audio = AudioSegment.from_mp3(mp3_path)
    audio.export(wav_path, format="wav")
    return wav_path


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/split-audio', methods=['POST'])
def split_audio():

    # Generate a new session ID for this request
    session_id = uuid.uuid4().hex

    # Define the upload and split audio directories for this request
    upload_folder = os.path.join(os.getcwd(), os.pardir, 'uploads', session_id)
    split_audio_dir = os.path.join(os.getcwd(), os.pardir, 'public/tracks', session_id)


    # get uploaded audio file
    audio_file = request.files['audioFile']

    # Make sure user uploaded an allowed file type
    if audio_file and allowed_file(audio_file.filename):

        # Save to a temp location
        os.makedirs(app.config['upload_folder'], exist_ok=True)
        temp_file = os.path.join(upload_folder, 'uploaded_audio.mp3')
        audio_file.save(temp_file)

        # Transcode MP3 to WAV
        wav_path = mp3_to_wav(temp_file)

        # Load with scipy ting
        rate, audio = wavfile.read(wav_path)

        # Convert the audio to float32 for Spleeter
        audio = audio.astype(np.float32) / 32767.0

        # mono to stereo
        if audio.ndim == 1:
            audio = np.repeat(audio[:, np.newaxis], 2, axis=1)

        # letting spleeter do the damn ting
        separator = Separator('spleeter:4stems')
        prediction = separator.separate(audio)

        # magical place to hold our precious split audio files
        os.makedirs(split_audio_dir, exist_ok=True)

        # Export stemies to WAV files
        split_audio_files = {}
        for instrument, data in prediction.items():
            # Rescaling?
            rescaled_data = np.int16(data * 32767)

            # Setting split audio length to original audio length
            target_length = len(audio)
            padded_data = np.pad(rescaled_data, ((0, target_length - len(rescaled_data)), (0, 0)), mode='constant')
            truncated_data = padded_data[:target_length]

            # Export split audio file as WAV
            track_file = os.path.join(split_audio_dir, f'output_{instrument}.wav')
            wavfile.write(track_file, rate, truncated_data)
            split_audio_files[instrument] = f'/tracks/{session_id}/output_{instrument}.wav'

        # Return the actual done split audio
        return jsonify(split_audio_files)
    else:
        return "Invalid file type", 400


# [Brian NOTE] This is useless.
# API metadata stuff that I had to look up
# @app.route('/metadata')
# def get_metadata():
#     metadata = {
#         'sample_rate': 44100,
#         'channels': 2
#     }
#     return jsonify(metadata)

# [Brian NOTE] Shouldn't need this anymore bc public directory is serving static files...
# @app.route('/public/tracks/<filename>')
# def serve_audio(filename):
#     try:
#         return send_from_directory(split_audio_dir, filename)
#     except FileNotFoundError:
#         return "Audio file not found.", 404



# prevent cached responses
if app.config["DEBUG"]:
    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = " no-store, max-age=0"
        return response

logging.basicConfig(level=logging.DEBUG, handlers=[logging.StreamHandler()])

if __name__ == '__main__':
    app.run()
