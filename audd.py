def on_recognize_clicked():
    recognize_button.config(text="Recording...", state="disabled")
    app.update()
    
    filename = "output.wav"
    record_audio(filename=filename, duration=5)  # Adjust duration as needed
    
    # Try recognizing with ACRCloud first
    result_acr = recognize_song(filename)
    if result_acr and result_acr['status']['msg'] == 'Success':
        # ACRCloud found a match
        show_song_info(result_acr)
    else:
        # If ACRCloud doesn't find a match, try AudD
        result_audd = recognize_song_with_audd(filename, api_token="Your_AudD_Token")
        if result_audd and result_audd['status'] == 'success':
            # AudD found a match
            show_song_info_audd(result_audd)
        else:
            messagebox.showinfo("Error", "Song could not be recognized by either service.")
    
    recognize_button.config(text="Recognize", state="normal")
    app.update()
