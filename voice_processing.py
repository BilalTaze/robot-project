import speech_recognition as sr
import whisper
import numpy as np
import torch

class Voice2text:
    """Class for handling voice recording with Whisper support."""

    def __init__(self, model_name="base"):
        """
        Initialize the recognizer and Whisper model.
        Model options: "tiny", "base", "small", "medium", "large"
        "base" est un bon compromis vitesse/précision pour un UR3.
        """
        self.recognizer = sr.Recognizer()
        print(f"Loading Whisper model '{model_name}'...")
        self.model = whisper.load_model(model_name)
        self.mic = None

    def list_microphones(self) -> list:
        mic_list = sr.Microphone.list_microphone_names()
        for index, name in enumerate(mic_list):
            print(f"{index}: {name}")
        return mic_list
    
    def voice_to_text(self, mic_index: int=0, api: str = "whisper") -> str|list[str]:
        try:
            audio = self.record_voice(mic_index)
            return self.recognize_recorded_voice(audio, api)
        except Exception as e:
            return f"Error: {e}"

    def record_voice(self, mic_index: int=0, timeout: int=5, phrase_time_limit: int=10) -> sr.AudioData:
        self.mic = sr.Microphone(device_index=mic_index)
        # Un peu de délai pour l'initialisation
        with self.mic as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            print("Recording... Speak now.")
            audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
            print("Recording complete.")
        return audio
    
    def recognize_recorded_voice(self, audio, api: str = "whisper") -> str|list[str]:
        try:
            match api:
                case "whisper":
                    # Conversion de l'audio SpeechRecognition en format compatible Whisper
                    # On récupère les données brutes (PCM)
                    wav_data = audio.get_wav_data(convert_rate=16000)
                    
                    # Whisper a besoin d'un fichier ou d'un array numpy
                    # Ici on transforme les bytes en float32
                    audio_np = np.frombuffer(wav_data, np.int16).flatten().astype(np.float32) / 32768.0
                    
                    # Transcription
                    result = self.model.transcribe(audio_np, fp16=torch.cuda.is_available())
                    return result["text"].strip()

                case "google": 
                    return self.recognizer.recognize_google(audio, language="fr-FR")
                
                case _:
                    raise ValueError("Unsupported API")
                    
        except sr.UnknownValueError:
            return "Could not understand audio"
        except Exception as e:
            return f"Error during recognition: {e}"

if __name__ == "__main__":
    # "base" est rapide, "small" est plus précis.
    voice_recording = Voice2text(model_name="base")
    
    # On teste avec Whisper en local
    text = voice_recording.voice_to_text(api="whisper")
    print(f"Recognized text: {text}")