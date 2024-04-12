import os
import threading
import time
import tkinter
from tkinter import messagebox
from tkinter import *
from tkinter import filedialog
from tkinter import ttk
from ttkthemes import themed_tk as tk
from pygame import mixer
import sounddevice as sd
from scipy.io.wavfile import write
import numpy as np
import requests
import json
import base64
import hmac
import hashlib
import pyaudio
import struct
import matplotlib.pyplot as plt
from mutagen.mp3 import MP3
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import TclError

root = tk.ThemedTk()
root.get_themes()
root.configure(bg='#784B84')
root.set_theme("equilux")


statusbar = ttk.Label(root, text="Musico , play as you search", relief=SUNKEN, anchor=W, font='Times 10 italic')
statusbar.pack(side=BOTTOM, fill=X)

# Create the menubar
menubar = Menu(root)
root.config(menu=menubar)


subMenu = Menu(menubar, tearoff=0)
def about_us():
    tkinter.messagebox.showinfo('About MUSICO', 'Muisco was developed by ProjAY')

playlist = []

def browse_file():
    global filename_path
    filename_path = filedialog.askopenfilename()
    add_to_playlist(filename_path)

    mixer.music.queue(filename_path)


def add_to_playlist(filename):
    filename = os.path.basename(filename)
    index = 0
    playlistbox.insert(index, filename)
    playlist.insert(index, filename_path)
    index += 1


menubar.add_cascade(label="File", menu=subMenu)
subMenu.add_command(label="Open", command=browse_file)
subMenu.add_command(label="Exit", command=root.destroy)


subMenu = Menu(menubar, tearoff=0)
menubar.add_cascade(label="Help", menu=subMenu)
subMenu.add_command(label="About Us", command=about_us)

mixer.init()  

root.title("Musico")
root.iconbitmap(r'images/iconmm.ico')

# Root Window - StatusBar, LeftFrame, RightFrame
# LeftFrame - The listbox (playlist)
# RightFrame - TopFrame,MiddleFrame and the BottomFrame

leftframe = Frame(root , bg='#784B84')
leftframe.pack(side=LEFT, padx=30, pady=30)

playlistbox = Listbox(leftframe)
playlistbox.pack()

addBtn = ttk.Button(leftframe, text="+ Add", command=browse_file)
addBtn.pack(side=LEFT , pady=10)
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
    global filename
    filename = "output.wav"
    record_audio(filename=filename, duration=5)
    result = recognize_song(filename)
    try:
        title = result['metadata']['music'][0]['title']
        artist = result['metadata']['music'][0]['artists'][0]['name']
        genre = result['metadata']['music'][0]['genres'][0]['name'] if 'genres' in result['metadata']['music'][0] else "Unknown"
        messagebox.showinfo("Song Info", f"Title: {title}\nArtist: {artist}\nGenre: {genre}")
    except KeyError:
        messagebox.showinfo("Error", "Song could not be recognized.")

def del_song():
    selected_song = playlistbox.curselection()
    selected_song = int(selected_song[0])
    playlistbox.delete(selected_song)
    playlist.pop(selected_song)


delBtn = ttk.Button(leftframe, text="- Del", command=del_song)
delBtn.pack(side=LEFT , pady=10)

rightframe = Frame(root , bg='#784B84')
rightframe.pack(pady=30)

topframe = Frame(rightframe , background='#784B84')
topframe.pack()

lengthlabel = ttk.Label(topframe, text='Total Length  : --:--' , relief=GROOVE)
lengthlabel.pack()

currenttimelabel = ttk.Label(topframe, text='Current Time : --:--', relief=GROOVE)
currenttimelabel.pack(pady=5)

now_playing_label = ttk.Label(topframe, text='Now Playing: None' , relief=GROOVE)
now_playing_label.pack()

def show_details(play_song):
    file_data = os.path.splitext(play_song)

    if file_data[1] == '.mp3':
        audio = MP3(play_song)
        total_length = audio.info.length
    else:
        a = mixer.Sound(play_song)
        total_length = a.get_length()

    # div - total_length/60, mod - total_length % 60
    mins, secs = divmod(total_length, 60)
    mins = round(mins)
    secs = round(secs)
    timeformat = '{:02d}:{:02d}'.format(mins, secs)
    lengthlabel['text'] = "Total Length" + ' - ' + timeformat
    now_playing_label['text'] = f'Now Playing: {os.path.basename(play_song)}'

    t1 = threading.Thread(target=start_count, args=(total_length,))
    t1.start()
def start_count(t):
    global paused
    current_time = 0
    while current_time <= t and mixer.music.get_busy():
        if paused:
            continue
        else:
            mins, secs = divmod(current_time, 60)
            mins = round(mins)
            secs = round(secs)
            timeformat = '{:02d}:{:02d}'.format(mins, secs)
            currenttimelabel['text'] = "Current Time" + ' - ' + timeformat
            time.sleep(1)
            current_time += 1


def play_music():
    global paused

    if paused:
        mixer.music.unpause()
        statusbar['text'] = "Music Resumed"
        paused = FALSE
    else:
        try:
            stop_music()
            time.sleep(1)
            selected_song = playlistbox.curselection()
            selected_song = int(selected_song[0])
            play_it = playlist[selected_song]
            mixer.music.load(play_it)
            mixer.music.play()
            statusbar['text'] = "Playing music" + ' - ' + os.path.basename(play_it)
            show_details(play_it)
        except:
            tkinter.messagebox.showerror('File not found', 'Musico could not find the file. Please check again.')


def stop_music():
    mixer.music.stop()
    statusbar['text'] = "Music Stopped"


paused = FALSE

def next_song():
    global playlistbox
    current_song = playlistbox.curselection()
    current_song = current_song[0] + 1
    if current_song >= len(playlist):  # Loop back to beginning
        current_song = 0
    next_one = playlist[current_song]
    playlistbox.select_clear(0, END)
    playlistbox.activate(current_song)
    playlistbox.select_set(current_song)

    mixer.music.load(next_one)
    mixer.music.play()
    statusbar['text'] = "Playing music" + ' - ' + os.path.basename(next_one)
    show_details(next_one)

def prev_song():
    global playlistbox
    current_song = playlistbox.curselection()
    current_song = current_song[0] - 1
    if current_song < 0:  # Loop to end of list
        current_song = len(playlist) - 1
    prev_one = playlist[current_song]
    playlistbox.select_clear(0, END)
    playlistbox.activate(current_song)
    playlistbox.select_set(current_song)

    mixer.music.load(prev_one)
    mixer.music.play()
    statusbar['text'] = "Playing music" + ' - ' + os.path.basename(prev_one)
    show_details(prev_one)


def pause_music():
    global paused
    paused = TRUE
    mixer.music.pause()
    statusbar['text'] = "Music Paused"


def rewind_music():
    play_music()
    statusbar['text'] = "Music Rewinded"


def set_vol(val):
    volume = float(val) / 100
    mixer.music.set_volume(volume)
    


muted = FALSE


def mute_music():
    global muted
    if muted: 
        mixer.music.set_volume(0.7)
        volumeBtn.configure(image=volumePhoto)
        scale.set(70)
        muted = FALSE
    else:  
        mixer.music.set_volume(0)
        volumeBtn.configure(image=mutePhoto)
        scale.set(0)
        muted = TRUE


middleframe = Frame(rightframe , background='#784B84')
middleframe.pack(pady=30, padx=30)

prevPhoto = PhotoImage(file='images/prev.png')
prevBtn = ttk.Button(middleframe, image=prevPhoto, command=prev_song)
prevBtn.grid(row=0, column=0 , padx=10)

playPhoto = PhotoImage(file='images/play.png')
playBtn = ttk.Button(middleframe, image=playPhoto, command=play_music)
playBtn.grid(row=0, column=2, padx=10)

stopPhoto = PhotoImage(file='images/stop.png')
stopBtn = ttk.Button(middleframe, image=stopPhoto, command=stop_music)
stopBtn.grid(row=0, column=1, padx=10)

pausePhoto = PhotoImage(file='images/pause.png')
pauseBtn = ttk.Button(middleframe, image=pausePhoto, command=pause_music)
pauseBtn.grid(row=0, column=3, padx=10)

nextPhoto = PhotoImage(file='images/next.png')
nextBtn = ttk.Button(middleframe, image=nextPhoto, command=next_song)
nextBtn.grid(row=0, column=4 , padx=10)

bottomframe = Frame(rightframe , background='#784B84')
bottomframe.pack()

rewindPhoto = PhotoImage(file='images/rewind.png')
rewindBtn = ttk.Button(bottomframe, image=rewindPhoto, command=rewind_music)
rewindBtn.grid(row=0, column=0)

mutePhoto = PhotoImage(file='images/mute.png')
volumePhoto = PhotoImage(file='images/volume.png')
volumeBtn = ttk.Button(bottomframe, image=volumePhoto, command=mute_music)
volumeBtn.grid(row=0, column=1)

recognize_button = ttk.Button(middleframe, text="Recognize", command=on_recognize_clicked)
recognize_button.grid(row=1, column=1, columnspan=3, pady=10)

scale = ttk.Scale(bottomframe, from_=0, to=100, orient=HORIZONTAL, command=set_vol)
scale.set(70)  
mixer.music.set_volume(0.7)
scale.grid(row=0, column=2, pady=15, padx=30)


def on_closing():
    stop_music()
    root.destroy()


root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()
