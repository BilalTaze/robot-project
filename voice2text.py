import speech_recognition as sr
import time

class Voice2text:
    """Class for handling voice recording."""

    def __init__(self):
        """Initialize the recognizer."""
        self.recognizer = sr.Recognizer()
        self.mic = None

    def list_microphones(self) -> list:
        """List available microphones."""
        mic_list = sr.Microphone.list_microphone_names()
        for index, name in enumerate(mic_list):
            print(f"{index}: {name}")
        return mic_list
    
    def voice_to_text(self, mic_index: int=0, api: str = "google") -> str|list[str]:
        """
        Record voice from the microphone and recognize it.
        
        ### Parameters:
            mic_index: The index of the microphone to use. Default is 0.
            api: The API to use for recognition. Default is "google".

        ### Returns:
            The recognized text from the audio.
        """
        audio = self.record_voice(mic_index)
        return self.recognize_recorded_voice(audio, api)

    def record_voice(self, mic_index: int=0, timeout: int=2, phrase_time_limit: int=20) -> sr.AudioData:
        """
        Record voice from the microphone.
        
        ### Parameters:
            mic_index: The index of the microphone to use. Default is 0.
            timeout: Seconds to wait for speech to start before giving up. Default is 20.
            phrase_time_limit: Max seconds of recording once speech starts. Default is 20.

        ### Returns:
            audio: The recorded audio.

        ### Raises:
            sr.WaitTimeoutError: If no speech is detected within `timeout` seconds.
        """
        self.mic = sr.Microphone(device_index=mic_index)

        time.sleep(1)  # wait 1 second for the microphone to initialize
        
        print("Recording... Please speak into the microphone.")
        with self.mic as source:
            self.recognizer.adjust_for_ambient_noise(source)
            audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
            print("Recording complete.")
        
        return audio
    
    def recognize_recorded_voice(self, audio, api: str = "google") -> str|list[str]:
        """
        Recognize the recorded voice.
        ### Parameters:
            audio: The recorded audio to recognize. Use the output from the record_voice method.
            api: The API to use for recognition. Default is "google".
        ### Returns:
            The recognized text from the audio.
        """
        try:
            match api:
                case "google": return self.recognizer.recognize_google(audio)
                case "google_cloud": return self.recognizer.recognize_google_cloud(audio)
                case "sphinx": return self.recognizer.recognize_sphinx(audio)
                case "bing": return self.recognizer.recognize_bing(audio)
                case "houndify": return self.recognizer.recognize_houndify(audio)
                case "wit": return self.recognizer.recognize_wit(audio)
                case "ibm": return self.recognizer.recognize_ibm(audio)
                case "all": return [self.recognizer.recognize_google(audio), self.recognizer.recognize_google_cloud(audio), self.recognizer.recognize_sphinx(audio), self.recognizer.recognize_bing(audio), self.recognizer.recognize_houndify(audio), self.recognizer.recognize_wit(audio), self.recognizer.recognize_ibm(audio)]
                case _:
                    raise ValueError("Unsupported API")
        except sr.UnknownValueError:
            return "Could not understand audio"
        except sr.RequestError as e:
            return f"Could not request results; {e}"


if __name__ == "__main__":
    # Utilisation simple : uniquement l'API Google (pas besoin de clé API)
    voice_recording = Voice2text()
    text = voice_recording.voice_to_text(api="google")
    print(f"Recognized text: {text}")
