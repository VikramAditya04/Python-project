import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
import cv2
import threading
from PIL import Image, ImageTk
import time
import pygame

class VideoPlayer:
    def __init__(self, root):
        self.root = root
        self.root.title("Video Player")

        self.video_frame = tk.Frame(self.root)
        self.video_frame.pack(fill=tk.BOTH, expand=1)

        self.canvas = tk.Canvas(self.video_frame, bg='black')
        self.canvas.pack(fill=tk.BOTH, expand=1)

        self.btn_frame = tk.Frame(self.root)
        self.btn_frame.pack()

        self.load_btn = tk.Button(self.btn_frame, text="Browse", command=self.load_video)
        self.load_btn.pack(side=tk.LEFT)

        self.play_btn = tk.Button(self.btn_frame, text="Play", command=self.play_video, state=tk.DISABLED)
        self.play_btn.pack(side=tk.LEFT)

        self.pause_btn = tk.Button(self.btn_frame, text="Pause", command=self.pause_video, state=tk.DISABLED)
        self.pause_btn.pack(side=tk.LEFT)

        self.stop_btn = tk.Button(self.btn_frame, text="Stop", command=self.stop_video, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT)

        self.mute_btn = tk.Button(self.btn_frame, text="Mute", command=self.toggle_mute, state=tk.DISABLED)
        self.mute_btn.pack(side=tk.LEFT)

        self.fullscreen_btn = tk.Button(self.btn_frame, text="Fullscreen", command=self.toggle_fullscreen, state=tk.DISABLED)
        self.fullscreen_btn.pack(side=tk.LEFT)

        self.time_label = tk.Label(self.btn_frame, text="00:00 / 00:00")
        self.time_label.pack(side=tk.LEFT)

        self.slider = ttk.Scale(self.btn_frame, from_=0, to=100, orient=tk.HORIZONTAL, command=self.on_slider_change, state=tk.DISABLED)
        self.slider.pack(fill=tk.X, expand=1)

        self.video_path = ""
        self.cap = None
        self.playing = False
        self.paused = False
        self.muted = False
        self.fullscreen = False
        self.update_thread = None
        self.lock = threading.Lock()
        pygame.mixer.init()

    def load_video(self):
        self.video_path = filedialog.askopenfilename()
        if self.video_path:
            self.cap = cv2.VideoCapture(self.video_path)
            self.slider.config(to=self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            self.update_time_label()
            self.play_btn.config(state=tk.NORMAL)
            self.pause_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.DISABLED)
            self.mute_btn.config(state=tk.NORMAL)
            self.fullscreen_btn.config(state=tk.NORMAL)
            self.slider.config(state=tk.NORMAL)

    def play_video(self):
        if self.video_path and not self.playing:
            self.playing = True
            self.paused = False
            self.play_btn.config(state=tk.DISABLED)
            self.pause_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.NORMAL)
            self.update_thread = threading.Thread(target=self.update_frame)
            self.update_thread.start()

    def pause_video(self):
        if self.playing:
            self.paused = not self.paused
            if self.paused:
                self.pause_btn.config(text="Resume")
            else:
                self.pause_btn.config(text="Pause")

    def stop_video(self):
        self.playing = False
        self.paused = False
        if self.cap:
            self.cap.release()
            self.cap = None
        self.play_btn.config(state=tk.NORMAL)
        self.pause_btn.config(state=tk.DISABLED, text="Pause")
        self.stop_btn.config(state=tk.DISABLED)
        self.slider.set(0)

    def toggle_mute(self):
        self.muted = not self.muted

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        self.root.attributes("-fullscreen", self.fullscreen)
        self.resize_frame()

    def resize_frame(self):
        if self.cap and self.fullscreen:
            ret, frame = self.cap.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = self.resize_frame(frame)
                image = Image.fromarray(frame)
                photo = ImageTk.PhotoImage(image)
                self.canvas.config(width=self.root.winfo_screenwidth(), height=self.root.winfo_screenheight())
                self.canvas.create_image(0, 0, anchor=tk.NW, image=photo)
                self.canvas.image = photo

    def resize_frame(self, frame):
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        height, width, _ = frame.shape
        scale = min(canvas_width / width, canvas_height / height)
        new_width = int(width * scale)
        new_height = int(height * scale)
        return cv2.resize(frame, (new_width, new_height))

    def update_frame(self):
        while self.playing:
            if not self.paused:
                if self.cap:
                    ret, frame = self.cap.read()
                    if ret:
                        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        frame = self.resize_frame(frame)
                        image = Image.fromarray(frame)
                        photo = ImageTk.PhotoImage(image)
                        self.canvas.create_image(0, 0, anchor=tk.NW, image=photo)
                        self.canvas.image = photo
                        self.slider.set(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
                        self.update_time_label()
                    else:
                        self.stop_video()
                        break
            time.sleep(0.03)

    def update_time_label(self):
        if self.cap:
            pos_frames = self.cap.get(cv2.CAP_PROP_POS_FRAMES)
            total_frames = self.cap.get(cv2.CAP_PROP_FRAME_COUNT)
            fps = self.cap.get(cv2.CAP_PROP_FPS)
            current_time = pos_frames / fps
            total_time = total_frames / fps
            self.time_label.config(text=f"{self.format_time(current_time)} / {self.format_time(total_time)}")

    def format_time(self, seconds):
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02}:{seconds:02}"

    def on_slider_change(self, value):
        if self.cap:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, int(float(value)))
            self.update_time_label()

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("800x600")
    player = VideoPlayer(root)
    root.mainloop()
