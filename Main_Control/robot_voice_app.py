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
        self.text_recognized = False
        self.command = None
        self.command_confirmed = False

    # Initialize the Tkinter GUI
        self.root = tk.Tk()
        self.root.title("UR3 Voice Control - Whisper")
        self.root.geometry("500x500")

    # Instructions for user
        self.label_instruction = tk.Label(self.root, text="Press 'Record' and wait that the button displays Listening... to speak the command for the UR3 robot. The recognized command will appear below.\nIf you want to stop the robot, say 'stop'.\nIf you want to quit the interface, say 'exit'", font=("Arial", 12))
        self.label_instruction.pack(pady=20)

    # Status label to show current state
        self.label_status = tk.Label(self.root, text="Ready for UR3", font=("Arial", 12))
        self.label_status.pack(pady=20)

    # Button to trigger voice recording
        self.btn_listen = tk.Button(self.root, text="Record", command=self.buton_activation, bg="red", fg="white", font=("Arial", 14, "bold"), width=15, height=2)
        self.btn_listen.pack(pady=10)

    # Text area to display recognized speech
        self.text_output = tk.Text(self.root, height=5, width=40, font=("Arial", 10))
        self.text_output.pack(pady=20)

    # Button to cancel the command (hide until we have a command to cancel)
        self.btn_cancel = tk.Button(self.root, text="Cancel", command=self.cancel_command, bg="red", fg="white", font=("Arial", 14, "bold"), width=10, height=1)
        self.btn_cancel.pack(pady=10)
        self.btn_cancel.pack_forget()

    # Frame to hold the confirm button (Canvas)
        self.confirm_frame = tk.Frame(self.root)
        self.btn_confirm_canvas = tk.Canvas(self.confirm_frame, width=150, height=40, bg="#90E000", highlightthickness=0)
        self.btn_confirm_canvas.pack()
        self.btn_confirm_canvas.bind("<Button-1>", lambda e: self.command_confirmation())
    # Draw the "Confirm" text (only once)
        self.btn_confirm_canvas.create_text(75, 20, text="Confirm", fill="white", font=("Arial", 12, "bold"), tags="confirm_text")
        self.confirm_frame.pack(pady=10)
        self.confirm_frame.pack_forget()
        

    def buton_activation(self):
        """Starts voice recognition in a separate thread to prevent UI freezing."""
    # Clear previous output
        self.text_output.delete("1.0", tk.END)
    # Launch voice processing in a background thread
        thread = threading.Thread(target=self.process_voice)
        thread.start()


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

            self.text_recognized = True
            self.root.quit()

        except Exception as e:
        # Display error message if something goes wrong
            self.root.after(0, self.update_ui, f"Error: {e}")


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


    def display_information(self, information: str = "", validationButton: bool = True):
        """
        Display information on the text area.
        Parameters:
            information: The text to display in the text area.
            validationButton: Whether to show the confirm/cancel buttons (default is True).
        """
    # Re-enable the record button
        self.btn_listen.config(state="normal", text="Record")

    # Reset text output
        self.text_output.delete("1.0", tk.END)
    # Information is displayed
        self.text_output.insert(tk.END, information)
    # Status is updated to indicate a command was received
        self.label_status.config(text="Command received!", fg="green")

        if validationButton:
        # Show the confirm and cancel buttons
            self.btn_cancel.pack()
            self.confirm_frame.pack()
        # Launch the confirm button animation
            self.animate_confirm_button(duration = 6000)
        # After 6 seconds, if the user hasn't canceled, the command is confirmed automatically
            self.confirm_timer = self.root.after(6000, self.command_confirmation)
        else:
            self.btn_cancel.pack_forget()
            self.confirm_frame.pack_forget()


    def cancel_command(self):
        """Button callback for canceling the recognized command."""
    # Hide the confirm and cancel buttons
        self.btn_cancel.pack_forget()
        self.confirm_frame.pack_forget()
    # reset status
        self.reset()
    # Display cancellation message
        self.display_information(information = "Command canceled", activateButton=False)
    # Clear message after 5 seconds
        self.root.after(5000, self.display_information, information="", activateButton=False)
    # Cancel the automatic confirmation timer if it's still running
        if hasattr(self, 'confirm_timer'):
            self.root.after_cancel(self.confirm_timer)


    def command_confirmation(self):
        """Button callback for confirming the recognized command and sending it to the robot."""
    # Hide the confirm and cancel buttons
        self.btn_cancel.pack_forget()
        self.confirm_frame.pack_forget()
    # Cancel the automatic confirmation timer if it's still running
        if hasattr(self, 'confirm_timer'):
            self.root.after_cancel(self.confirm_timer)
    # Set the command as confirmed to allow execution in the main loop
        self.command_confirmed = True


    def animate_confirm_button(self, duration: int = 6000, steps: int = 60):
        """
        Animates a progress bar under the "Confirm" text.
        The bar moves from left to right with a color gradient.
        Parameters:
            duration: Total duration of the animation in milliseconds (default is 6000ms).
            steps: Number of steps for the animation (default is 60).
        """
    # Define the dimensions of the canvas (button)
        width = 150
        height = 40

    # Define the start and end colors for the progress bar
        start_color = "#90E000"
        end_color = "#228B22"

    # Helper function to convert a hexadecimal color string to an RGB tuple and vice versa
        def hex_to_rgb(hex_color):
            hex_color = hex_color.lstrip('#')
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

        def rgb_to_hex(rgb):
            return '#{:02x}{:02x}{:02x}'.format(*rgb)

    # Convert start and end colors from hexadecimal to RGB for interpolation
        start_rgb = hex_to_rgb(start_color)
        end_rgb = hex_to_rgb(end_color)

        current_step = 0

    # Inner function to update the progress bar at each step
        def update_progress():
            # Allow modification of the current_step variable from the outer scope
            nonlocal current_step

            if current_step <= steps:
                bar_width = (current_step / steps) * width

            # Linearly interpolate between start and end colors for each RGB component
                r = int(start_rgb[0] + (end_rgb[0] - start_rgb[0]) * (current_step / steps))
                g = int(start_rgb[1] + (end_rgb[1] - start_rgb[1]) * (current_step / steps))
                b = int(start_rgb[2] + (end_rgb[2] - start_rgb[2]) * (current_step / steps))

            # Convert the interpolated RGB color back to hexadecimal format
                bar_color = rgb_to_hex((r, g, b))

            # Remove the previous progress bar (if any) to prepare for the new one
                self.btn_confirm_canvas.delete("progress_bar")

            # Draw the new progress bar at the bottom of the canvas
                self.btn_confirm_canvas.create_rectangle(0, height - 10, bar_width, height, fill=bar_color, tags="progress_bar", outline="")

                current_step += 1
                self.root.after(duration // steps, update_progress)

        update_progress()


    def reset(self):
        """Reset variables for the next command and hide validation buttons."""
        self.text = None
        self.text_recognized = False
        self.command = None
        self.command_confirmed = False
        self.btn_cancel.pack_forget()
        self.confirm_frame.pack_forget()





if __name__ == "__main__":
    # Launch the application
    app = RobotVoiceApp()
    app.root.mainloop()
    while True:
        command = app.main()  # Get the recognized command from the voice app
        if app.command_confirmed:
            print(f"Confirmed command: {command}")
