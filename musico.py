import tkinter as tk
from tkinter import messagebox
import sounddevice as sd
from scipy.io.wavfile import write
import numpy as np
import requests
import base64
import hashlib
import hmac
import time
import json

def record_audio(filename='output.wav', duration=5, fs=44100):
    print("Recording...")
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=2, dtype='float64')
    sd.wait()  # Wait until recording is finished
    write(filename, fs, np.int16(recording * 32767))  # Convert to 16-bit data
    print("Recording stopped.")

def recognize_song(file_path):
    http_url = "http://identify-ap-southeast-1.acrcloud.com/v1/identify"
    access_key = "47a728c7e0fef35868bfb691cc65dd23"
    access_secret = "3IoQsH2E5J6N7Eon9iuB02DNbw9SJtKqOGs0pcPg".encode('utf-8')
    http_method = "POST"
    http_uri = "/v1/identify"
    data_type = "audio"
    signature_version = "1"
    timestamp = str(int(time.time()))

    string_to_sign = http_method + "\n" + http_uri + "\n" + access_key + "\n" + data_type + "\n" + signature_version + "\n" + timestamp
    sign = base64.b64encode(hmac.new(access_secret, string_to_sign.encode('utf-8'), digestmod=hashlib.sha1).digest())

    files = {'sample': open(file_path, 'rb')}
    data = {'access_key': access_key,
            'sample_bytes': str(files['sample'].tell()),
            'timestamp': timestamp,
            'signature': sign.decode('utf-8'),  # Ensure this is decoded for the request
            'data_type': data_type,
            'signature_version': signature_version}

    response = requests.post(http_url, files=files, data=data)
    files['sample'].close()  # Close the file after sending it
    return json.loads(response.text)

def on_recognize_clicked():
    filename = "output.wav"
    record_audio(filename=filename, duration=5)  # Adjust duration as needed
    result = recognize_song(filename)
    try:
        title = result['metadata']['music'][0]['title']
        artist = result['metadata']['music'][0]['artists'][0]['name']
        genre = result['metadata']['music'][0]['genres'][0]['name'] if 'genres' in result['metadata']['music'][0] else "Unknown"
        messagebox.showinfo("Song Info", f"Title: {title}\nArtist: {artist}\nGenre: {genre}")
    except KeyError:
        messagebox.showinfo("Error", "Song could not be recognized.")

# Setting up the GUI
app = tk.Tk()
app.title("Song Recognizer")

recognize_button = tk.Button(app, text="Recognize", command=on_recognize_clicked)
recognize_button.pack(pady=20)

app.mainloop()
