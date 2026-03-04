import speech_recognition as sr
import time

from test_voice_recognition import VoiceRecognition

class VoiceRecording:
    """Class for handling voice recording."""

    def __init__(self):
        """Initialize the recognizer."""
        self.recognizer = sr.Recognizer()
        self.mic = None

    def record_voice(self, mic_index=0):
        """Record voice from the microphone."""
        # list available microphones
        availableMicrophones = sr.Microphone.list_microphone_names()
        # choose one from the list as 
        self.mic = sr.Microphone(device_index=mic_index)

        wait_time = 1  # seconds
        time.sleep(wait_time)  # wait for the microphone to initialize
        
        print("Recording... Please speak into the microphone.")
        with self.mic as source:
            self.recognizer.adjust_for_ambient_noise(source)
            audio = self.recognizer.listen(source)
            print("Recording complete.")
        
        return audio
    
    def recognize_recorded_voice(self, audio):
        """Recognize the recorded voice."""
        try:
            return self.recognizer.recognize_google(audio)
        except sr.UnknownValueError:
            return "Could not understand audio"
        except sr.RequestError as e:
            return f"Could not request results; {e}"


if __name__ == "__main__":
    # Example usage
    voice_recording = VoiceRecording()
    audio = voice_recording.record_voice()
    text = voice_recording.recognize_recorded_voice(audio)
    print(f"Recognized text: {text}")

