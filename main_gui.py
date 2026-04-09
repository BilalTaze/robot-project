import tkinter as tk
import threading
import time
from voice_processing import Voice2text  # Import de votre classe modifiée

class RobotVoiceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Contrôle Vocal UR3 - Whisper")
        self.root.geometry("400x300")
        
        # Initialisation de l'IA (On le fait au début pour éviter d'attendre après)
        self.voice_engine = Voice2text(model_name="base")
        
        # --- Interface Graphique ---
        self.label_status = tk.Label(root, text="Ready for UR3", font=("Arial", 12))
        self.label_status.pack(pady=20)

        self.btn_listen = tk.Button(root, text="🎙 SPEAK", command=self.start_listening_thread, bg="red", fg="white", font=("Arial", 14, "bold"), width=15, height=2)
        self.btn_listen.pack(pady=10)

        self.text_output = tk.Text(root, height=5, width=40, font=("Arial", 10))
        self.text_output.pack(pady=20)
        
    def start_listening_thread(self):
        """Lance la reconnaissance dans un thread séparé pour ne pas figer l'interface."""
        thread = threading.Thread(target=self.process_voice)
        thread.start()

        time.sleep(1.8)  # wait a bit to ensure the thread has started before updating the UI
        self.btn_listen.config(state="disabled", text="Recording...")
        self.text_output.delete("1.0", tk.END)
        
    def process_voice(self):
        # Appel de votre méthode Whisper
        audio = self.voice_engine.record_voice(mic_index=0)

        self.btn_listen.config(state="disabled", text="Listenning...")
        self.text_output.delete("1.0", tk.END)

        result = self.voice_engine.recognize_recorded_voice(audio, api="whisper")

        # Mise à jour de l'interface (doit être fait via la file principale)
        self.root.after(0, self.update_ui, result)

    def update_ui(self, result):
        self.btn_listen.config(state="normal", text="🎙 SPEAK")
        
        # Gestion des erreurs de compréhension
        error_messages = ["Could not understand audio", "Error", "n'entends pas"]
        
        if any(err in str(result) for err in error_messages) or result == "":
            self.text_output.insert(tk.END, "Sorry, I didn't understand or hear anything.")
            self.label_status.config(text="Reception failed", fg="orange")
        else:
            self.text_output.insert(tk.END, f"Understood : {result}")
            self.label_status.config(text="Command received!", fg="green")
            
            # C'est ici que vous pourriez ajouter :
            # self.robot.send_command(result) 

if __name__ == "__main__":
    root = tk.Tk()
    app = RobotVoiceApp(root)
    root.mainloop()
