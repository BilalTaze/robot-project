"""
Main application for UR3 voice control using Whisper for speech recognition.
This script sets up a Tkinter GUI with a button to start recording and a text area to display the recognized speech. It uses the SpeechRecognition library to capture audio from the microphone and the Whisper model to transcribe it into text. The application runs in a separate thread to ensure the UI remains responsive during recording and processing.
"""

import speech_recognition as sr
import whisper
import numpy as np
import torch
import tkinter as tk
import threading
import time


class RobotVoiceApp:
    """Class for handling voice recording with Whisper support."""

    def __init__(self, model_name="base"):
        """
        Initialize:
            - the recognizer and Whisper model.
                Model options: "tiny", "base", "small", "medium", "large"
                "base" is a good option for speed/precision balance for an UR3.
            - the Tkinter interface with a button to start recording and a text area for output.
            - variables to manage the state of the application (recognized text, command confirmation, etc.).
        """
    # Initialize the voice recognition engine
        self.recognizer = sr.Recognizer()
        print(f"Loading Whisper model '{model_name}'...")
        self.model = whisper.load_model(model_name)
    
    # Initialisation of variables
        self.mic = None
        self.text = None
        self.command = None
        self.stop_robot = False

    # Initialize the Tkinter GUI
        background_color = "grey"
        text_area_color = "darkgrey"
        self.root = tk.Tk()
        self.root.title("UR3 Voice Control - Whisper")
        self.root.geometry("450x600")
        self.root.configure(bg=background_color)

    # Instructions for user
        self.label_instruction = tk.Label(self.root, text='Press "Record" and wait that the button displays "Listening"... to speak the command for the UR3 robot. The recognized command will appear below.\n\nIf you want to stop and quit the interface, say "exit"\n\nIf you want to stop the movment during the execution, use the stop button', font=("Arial", 12), wraplength=400, justify="left", bg=background_color)
        self.label_instruction.pack(pady=20)

    # Button to trigger voice recording
        self.btn_listen = tk.Button(self.root, text="Record", command=self.buton_activation, bg="green", fg="white", font=("Arial", 14, "bold"), width=15, height=2)
        self.btn_listen.pack(pady=10)

    # Stop button
        self.btn_stop = tk.Button(self.root, text="Stop Robot", command=self.stop_button_activation, bg="red", fg="white", font=("Arial", 12, "bold"), width=15, height=2)
        self.btn_stop.pack(pady=10) 

    # Text area to display recognized speech
        self.text_output = tk.Text(self.root, height=20, width=60, font=("Arial", 10), bg=text_area_color)
        self.text_output.pack(pady=20)

        

    def buton_activation(self):
        """Starts voice recognition in a separate thread to prevent UI freezing."""
    # Clear previous output
        self.text_output.delete("1.0", tk.END)
    # Launch voice processing in a background thread
        thread = threading.Thread(target=self.process_voice)
        thread.start()


    def stop_button_activation(self):
        """Handles the stop button activation."""
        self.stop_robot = True
        self.display_information("Stop command received")


    def process_voice(self):
        """Handles voice recording and recognition in a separate thread."""
        try:
        # Update UI to indicate recording has started
            self.root.after(1500, lambda: self.btn_listen.config(text="Listening...", state="disabled"))

        # Record audio from microphone
            audio = self.record_voice()

        # Update UI to indicate processing
            self.root.after(0, lambda: self.btn_listen.config(text="Processing...", state="disabled"))

        # Recognize speech using Whisper with English as the default language
            self.text = self.recognize_voice(audio, api="whisper", language='en')

            self.root.quit()

        except Exception as e:
        # Display error message if something goes wrong
            self.display_information(f"Error: {e}")
            self.enable_record_button()


    def record_voice(self, mic_index: int=0, timeout: int=10, phrase_time_limit: int=30) -> sr.AudioData:
        """Records voice input from the specified microphone.
        Parameters:
            mic_index: Index of the microphone to use (default is 0).
            timeout: Maximum time to wait for audio input (default is 10 seconds).
            phrase_time_limit: Maximum time for a phrase to be recorded (default is 30 seconds).
        Returns:
            sr.AudioData: The recorded audio data.
        """
    # Initialize microphone with the given index
        self.mic = sr.Microphone(device_index=mic_index)
        with self.mic as source:
        # Adjust for ambient noise in a separate thread
            threading.Thread(target=self.recognizer.adjust_for_ambient_noise, args=(source, 1)).start()
        # Wait 1 second for the noise adjustment to take effect
            time.sleep(1)
        # Listen for audio input with timeout and phrase limit
            return self.recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)


    def recognize_voice(self, audio, api: str = "whisper", language: str= 'en') -> str|list[str]:
        """Recognizes speech from audio input using the specified API."""
        try:
            match api:
                case "whisper":
                # Convert audio data to a format compatible with Whisper
                    wav_data = audio.get_wav_data(convert_rate=16000)
                # Convert bytes to float32 numpy array
                    audio_np = np.frombuffer(wav_data, np.int16).flatten().astype(np.float32) / 32768.0

                # Transcribe audio using Whisper with the specified language
                    result = self.model.transcribe(audio_np, fp16=torch.cuda.is_available())
                    return result.get("text", "")

                case "google":
                # Use Google's speech recognition API
                    return self.recognizer.recognize_google(audio)

                case _:
                    raise ValueError("Unsupported API")

        except sr.UnknownValueError:
            return "Error: Could not understand audio"
        except Exception as e:
            return f"Error during recognition: {e}"


    def display_information(self, information: str = "", delete_previous: bool=False):
        """
        Display information on the text area.
        Parameters:
            information: The text to display in the text area.
            delete_previous: If True, clears the text area before displaying new information.
        """
    # Reset text output if delete_previous is True
        if delete_previous: self.text_output.delete("1.0", tk.END)
    # Information is displayed
        self.text_output.insert(tk.END, f'{information}\n')


    def enable_record_button(self):
        """Enable the record button for the next command."""
        self.btn_listen.config(state="normal", text="Record")


    def reset(self):
        """Reset variables for the next command and re-enable the record button."""
        self.enable_record_button()
        self.text = None
        self.command = None



if __name__ == "__main__":
# Launch the application
    app = RobotVoiceApp()
    while True:
        app.root.mainloop()
        if app.text is not None:
            app.display_information(f"Recognized command: {app.text}")
            app.enable_record_button()

