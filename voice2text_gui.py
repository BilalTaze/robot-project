import threading
import tkinter as tk
from tkinter import ttk, scrolledtext
import time

from voice2text import Voice2text


class Voice2TextApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Voice2Text")
        self.resizable(False, False)
        self.configure(bg="#F5F4F0")

        self.v2t = Voice2text()
        self.is_recording = False
        self.record_thread = None
        self._after_id = None

        self._build_ui()
        self._populate_microphones()

    # ── UI Construction ──────────────────────────────────────────────────────

    def _build_ui(self):
        pad = dict(padx=16, pady=8)

        # ── Top bar ──
        top = tk.Frame(self, bg="#F5F4F0")
        top.pack(fill="x", **pad)

        tk.Label(top, text="Voice2Text", font=("Helvetica", 16, "bold"),
                 bg="#F5F4F0", fg="#1A1A1A").pack(side="left")

        # ── Settings row ──
        settings = tk.Frame(self, bg="#F5F4F0")
        settings.pack(fill="x", padx=16, pady=(0, 4))

        tk.Label(settings, text="Microphone", font=("Helvetica", 11),
                 bg="#F5F4F0", fg="#555").grid(row=0, column=0, sticky="w")
        self.mic_var = tk.StringVar()
        self.mic_combo = ttk.Combobox(settings, textvariable=self.mic_var,
                                      state="readonly", width=34)
        self.mic_combo.grid(row=0, column=1, padx=(8, 24), pady=4)

        tk.Label(settings, text="API", font=("Helvetica", 11),
                 bg="#F5F4F0", fg="#555").grid(row=0, column=2, sticky="w")
        self.api_var = tk.StringVar(value="google")
        apis = ["google", "google_cloud", "sphinx", "bing", "houndify", "wit", "ibm"]
        self.api_combo = ttk.Combobox(settings, textvariable=self.api_var,
                                      values=apis, state="readonly", width=14)
        self.api_combo.grid(row=0, column=3, padx=(8, 0), pady=4)

        # ── Record button ──
        self.record_btn = tk.Button(
            self, text="⏺  Start Recording",
            font=("Helvetica", 13, "bold"),
            bg="#E24B4A", fg="white", activebackground="#C03B3A",
            activeforeground="white", relief="flat",
            padx=20, pady=10, cursor="hand2",
            command=self.toggle_recording
        )
        self.record_btn.pack(fill="x", padx=16, pady=(4, 0))

        # ── Status label ──
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = tk.Label(self, textvariable=self.status_var,
                                     font=("Helvetica", 10, "italic"),
                                     bg="#F5F4F0", fg="#888")
        self.status_label.pack(pady=(4, 8))

        # ── Result area ──
        result_frame = tk.LabelFrame(self, text="Transcription",
                                     font=("Helvetica", 11),
                                     bg="#F5F4F0", fg="#333",
                                     bd=1, relief="solid")
        result_frame.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        self.result_text = scrolledtext.ScrolledText(
            result_frame, wrap=tk.WORD, height=6,
            font=("Helvetica", 12), bg="white", fg="#1A1A1A",
            relief="flat", padx=8, pady=8
        )
        self.result_text.pack(fill="both", expand=True, padx=4, pady=4)
        self.result_text.insert("1.0", "Waiting for recording…")
        self.result_text.config(state="disabled")

        # ── Copy button ──
        self.copy_btn = tk.Button(
            self, text="Copy text",
            font=("Helvetica", 10),
            bg="#F5F4F0", fg="#555",
            relief="flat", cursor="hand2",
            command=self.copy_result
        )
        self.copy_btn.pack(anchor="e", padx=16, pady=(0, 4))

        # ── History ──
        hist_frame = tk.LabelFrame(self, text="History",
                                   font=("Helvetica", 11),
                                   bg="#F5F4F0", fg="#333",
                                   bd=1, relief="solid")
        hist_frame.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        self.history_list = tk.Listbox(
            hist_frame, font=("Helvetica", 10),
            bg="white", fg="#444",
            selectbackground="#E6F1FB", selectforeground="#042C53",
            relief="flat", height=4, bd=0
        )
        self.history_list.pack(fill="both", expand=True, padx=4, pady=4)
        self.history_list.bind("<<ListboxSelect>>", self._on_history_select)

        self.geometry("560x540")

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _populate_microphones(self):
        mics = self.v2t.list_microphones()
        names = [f"{i}: {name}" for i, name in enumerate(mics)]
        self.mic_combo["values"] = names if names else ["0: Default"]
        self.mic_combo.current(0)

    def _set_status(self, text: str, color: str = "#888"):
        self.status_var.set(text)
        self.status_label.config(fg=color)

    def _set_result(self, text: str):
        self.result_text.config(state="normal")
        self.result_text.delete("1.0", "end")
        self.result_text.insert("1.0", text)
        self.result_text.config(state="disabled")

    def _add_to_history(self, text: str):
        if text.startswith("Could not"):
            return
        ts = time.strftime("%H:%M:%S")
        self.history_list.insert(0, f"[{ts}]  {text}")
        if self.history_list.size() > 20:
            self.history_list.delete("end")

    def _on_history_select(self, _event):
        sel = self.history_list.curselection()
        if not sel:
            return
        raw = self.history_list.get(sel[0])
        text = raw.split("]  ", 1)[-1] if "]  " in raw else raw
        self._set_result(text)

    # ── Recording logic ───────────────────────────────────────────────────────

    def toggle_recording(self):
        if not self.is_recording:
            self._start_recording()

    def _get_mic_index(self) -> int:
        val = self.mic_var.get()
        try:
            return int(val.split(":")[0])
        except (ValueError, IndexError):
            return 0

    def _start_recording(self):
        self.is_recording = True
        self.record_btn.config(text="⏺  Recording…", state="disabled",
                               bg="#888", activebackground="#666")
        self._set_status("Recording…  Speak now.", "#C03B3A")
        self._set_result("")

        mic_index = self._get_mic_index()
        api = self.api_var.get()
        self.record_thread = threading.Thread(
            target=self._record_worker, args=(mic_index, api), daemon=True
        )
        self.record_thread.start()

    def _record_worker(self, mic_index: int, api: str):
        try:
            audio = self.v2t.record_voice(mic_index)
            self.after(0, lambda: self._set_status("Transcribing…", "#185FA5"))
            text = "I don't hear, sorry"
        except Exception as e:
            text = "I don't hear, sorry"
        self.after(0, lambda: self._on_result(text))

    def _on_result(self, text: str):
        self.is_recording = False
        self.record_btn.config(text="⏺  Start Recording", state="normal",
                               bg="#E24B4A", activebackground="#C03B3A")
        self._set_result(text)
        self._add_to_history(text)
        self._set_status("Done.", "#3B6D11")

    # ── Copy ─────────────────────────────────────────────────────────────────

    def copy_result(self):
        text = self.result_text.get("1.0", "end").strip()
        if not text or text == "Waiting for recording…":
            return
        self.clipboard_clear()
        self.clipboard_append(text)
        self.copy_btn.config(text="Copied ✓", fg="#3B6D11")
        if self._after_id:
            self.after_cancel(self._after_id)
        self._after_id = self.after(2000, lambda: self.copy_btn.config(
            text="Copy text", fg="#555"))


if __name__ == "__main__":
    app = Voice2TextApp()
    app.mainloop()
