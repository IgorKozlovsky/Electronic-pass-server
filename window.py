import tkinter as tk
from PIL import Image, ImageTk
import tkinter.font as font
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class StudentInfoWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Інформація про студента")
        self.panel = tk.Label(self)
        self.panel.pack(side="top", padx=20, pady=10)
        self.labels = []
        for i in range(3):
            label = tk.Label(self)
            label.pack()
            self.labels.append(label)

    def update_info(self, student):
        image_path = os.path.join(BASE_DIR, f"assets/images/{student.photo}")
        img = Image.open(image_path)

        new_width = 300
        img = img.resize(
            (new_width, int(new_width * img.height / img.width)))

        img = ImageTk.PhotoImage(img)
        self.panel.config(image=img)
        self.panel.photo = img

        my_font = font.Font(size=24)
        self.labels[0].config(text=student.fullname, font=my_font)
        self.labels[1].config(text=student.faculty, font=my_font)
        self.labels[2].config(text=f'Кімната: {student.room}', font=my_font)
