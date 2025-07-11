import customtkinter as ctk
import asyncio
import subprocess
import tempfile
import os
import g4f
import edge_tts
import pygame
import requests
from PIL import Image, ImageTk
from io import BytesIO
from tkinter import filedialog
import pytesseract

client = g4f.Client()
pygame.mixer.init()
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

VOICES = [
    ("Sonia (en-GB-SoniaNeural)", "en-GB-SoniaNeural"),
    ("Jenny (en-US-JennyNeural)", "en-US-JennyNeural"),
    ("Guy (en-US-GuyNeural)", "en-US-GuyNeural"),
    ("Ryan (en-GB-RyanNeural)", "en-GB-RyanNeural"),
    ("Salma (ar-EG-SalmaNeural)", "ar-EG-SalmaNeural"),
]

class AITools(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("AI Tools")
        self.geometry("1000x700")

        # sidebar
        self.sidebar = ctk.CTkFrame(self, width=200)
        self.sidebar.pack(side="left", fill="y")

        ctk.CTkLabel(self.sidebar, text="AI Tools", font=("Arial", 20)).pack(pady=20)
        ctk.CTkButton(self.sidebar, text="Image Generator", command=self.show_image_gen).pack(pady=10)
        ctk.CTkButton(self.sidebar, text="Text To Speech", command=self.show_tts).pack(pady=10)
        ctk.CTkButton(self.sidebar, text="AI PowerShell", command=self.show_ai_shell).pack(pady=10)
        ctk.CTkButton(self.sidebar, text="OCR Image To Text", command=self.show_ocr).pack(pady=10)

        # sidebar footer
        ctk.CTkLabel(self.sidebar, text="v0.8 | by thomasvatk\n for personal use",
                     font=("Arial", 10), justify="center").pack(side="bottom", pady=20)

        # main area
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(side="left", fill="both", expand=True)

        self.show_image_gen()

    def show_image_gen(self):
        self.clear_main()
        ctk.CTkLabel(self.main_frame, text="Image Generator", font=("Arial", 18)).pack(pady=10)
        self.prompt_entry = ctk.CTkTextbox(self.main_frame, width=600, height=100)
        self.prompt_entry.insert("1.0", "Ultra-realistic cyberpunk cityscape")
        self.prompt_entry.pack(pady=10)
        ctk.CTkButton(self.main_frame, text="Generate", command=self.generate_image).pack(pady=10)
        self.img_label = ctk.CTkLabel(self.main_frame, text="")
        self.img_label.pack(pady=20)

    def generate_image(self):
        prompt = self.prompt_entry.get("1.0", "end").strip()
        if not prompt:
            self.img_label.configure(text="Prompt empty")
            return
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        img_url = loop.run_until_complete(self._generate_image_async(prompt))
        loop.close()
        if img_url:
            response = requests.get(img_url)
            img = Image.open(BytesIO(response.content)).resize((512, 512))
            img_tk = ImageTk.PhotoImage(img)
            self.img_label.configure(image=img_tk)
            self.img_label.image = img_tk
        else:
            self.img_label.configure(text="Failed")

    async def _generate_image_async(self, prompt):
        try:
            response = await asyncio.to_thread(
                client.images.generate,
                model="ImageLabs",
                prompt=prompt,
                response_format="url"
            )
            return response.data[0].url
        except Exception:
            return None

    def show_tts(self):
        self.clear_main()
        ctk.CTkLabel(self.main_frame, text="Text To Speech", font=("Arial", 18)).pack(pady=10)
        self.tts_entry = ctk.CTkTextbox(self.main_frame, width=600, height=100)
        self.tts_entry.insert("1.0", "Hello world from AI Tools")
        self.tts_entry.pack(pady=10)
        self.voice_dropdown = ctk.CTkOptionMenu(self.main_frame, values=[v[0] for v in VOICES])
        self.voice_dropdown.set(VOICES[0][0])
        self.voice_dropdown.pack(pady=10)
        ctk.CTkButton(self.main_frame, text="Play Speech", command=self.play_tts).pack(pady=10)

    def play_tts(self):
        text = self.tts_entry.get("1.0", "end").strip()
        voice_id = next(v[1] for v in VOICES if v[0] == self.voice_dropdown.get())
        if not text:
            return
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        temp_audio = loop.run_until_complete(self._generate_tts_async(text, voice_id))
        loop.close()
        if temp_audio:
            pygame.mixer.music.load(temp_audio)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
            os.remove(temp_audio)

    async def _generate_tts_async(self, text, voice):
        try:
            temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
            communicate = edge_tts.Communicate(text=text, voice=voice)
            await communicate.save(temp_audio.name)
            return temp_audio.name
        except Exception:
            return None

    def show_ai_shell(self):
        self.clear_main()
        ctk.CTkLabel(self.main_frame, text="AI PowerShell", font=("Arial", 18)).pack(pady=10)
        self.shell_entry = ctk.CTkTextbox(self.main_frame, width=700, height=100)
        self.shell_entry.insert("1.0", "Example: Create a folder named test")
        self.shell_entry.pack(pady=10)
        ctk.CTkButton(self.main_frame, text="Run", command=self.run_ai_command).pack(pady=10)
        self.shell_output = ctk.CTkTextbox(self.main_frame, width=700, height=300)
        self.shell_output.pack(pady=20)

    def run_ai_command(self):
        user_input = self.shell_entry.get("1.0", "end").strip()
        if not user_input:
            return
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        command = loop.run_until_complete(self.generate_ps_command(user_input))
        loop.close()
        self.shell_output.insert("end", f"PowerShell: {command}\n")
        try:
            result = subprocess.check_output(["powershell", "-Command", command], stderr=subprocess.STDOUT, text=True)
            self.shell_output.insert("end", f"{result}\n")
        except subprocess.CalledProcessError as e:
            self.shell_output.insert("end", f"Error:\n{e.output}\n")

    async def generate_ps_command(self, user_prompt):
        response = await asyncio.to_thread(
            client.chat.completions.create,
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a PowerShell command generator. Only output the final command."},
                {"role": "user", "content": f"{user_prompt}"}
            ]
        )
        return response.choices[0].message.content.strip()

    def show_ocr(self):
        self.clear_main()
        ctk.CTkLabel(self.main_frame, text="OCR Image To Text", font=("Arial", 18)).pack(pady=10)
        ctk.CTkButton(self.main_frame, text="Select Image", command=self.load_image_for_ocr).pack(pady=10)
        self.ocr_output = ctk.CTkTextbox(self.main_frame, width=700, height=400)
        self.ocr_output.pack(pady=20)

    def load_image_for_ocr(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.bmp")])
        if not file_path:
            return
        img = Image.open(file_path)
        text = pytesseract.image_to_string(img)
        self.ocr_output.insert("end", f"Recognized Text:\n{text}\n")

    def clear_main(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

if __name__ == "__main__":
    app = AITools()
    app.mainloop()

# by thomasvatk
