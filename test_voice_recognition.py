"""Module for testing the voice recognition functionality."""

import speech_recognition as sr

class VoiceRecognition:
    """Class for handling voice recognition."""

    def __init__(self):
        """Initialize the recognizer."""
        self.recognizer = sr.Recognizer()

    def recognize_voice(self, audio_file):
        """Recognize voice from an audio file."""
        with sr.AudioFile(audio_file) as source:
            audio = self.recognizer.record(source)
            try:
                return self.recognizer.recognize_google(audio)
            except sr.UnknownValueError:
                return "Could not understand audio"
            except sr.RequestError as e:
                return f"Could not request results; {e}"


if __name__ == "__main__":
    # Example usage
    voice_recognition = VoiceRecognition()
    result = voice_recognition.recognize_voice("experiment_harvard.wav")
    print(result)