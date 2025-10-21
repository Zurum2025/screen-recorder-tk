print("Running screc.py...")

import threading
import time
import queue
import tkinter as tk
from tkinter import filedialog, messagebox
import mss
import numpy as np
import cv2
from PIL import Image, ImageTk
import os

class ScreenRec:
    def __init__(self, root):
        self.root = root
        root.title("Screen Recorder")
        frame = tk.Frame(root, padx=10)
        frame.grid(row=0, column=0, sticky="nsew")

        # Output file path
        tk.Label(frame, text="Output file:").grid(row=0, column=0, sticky="w")
        self.filename_var = tk.StringVar(value="output.mp4")
        self.filename_entry = tk.Entry(frame, textvariable=self.filename_var, width=30)
        self.filename_entry.grid(row=0, column=1, sticky="w")
        tk.Button(frame, text="Browse", command=self.browse).grid(row=0, column=2, padx=5)

        # FPS input
        tk.Label(frame, text="FPS:").grid(row=1, column=0, sticky="w")
        self.fps_var = tk.IntVar(value=15)
        tk.Spinbox(frame, from_=1, to=60, textvariable=self.fps_var, width=5).grid(row=1, column=1, sticky="w")

        # Buttons
        self.start_btn = tk.Button(frame, text="Start Recording", command=self.start_recording)
        self.start_btn.grid(row=2, column=0, pady=8)
        self.stop_btn = tk.Button(frame, text="Stop Recording", command=self.stop_recording, state="disabled")
        self.stop_btn.grid(row=2, column=1, pady=8)

        # Preview canvas
        self.preview_label = tk.Label(frame, text="Preview (updates while recording)")
        self.preview_label.grid(row=3, column=0, columnspan=3)
        self.canvas = tk.Canvas(frame, width=480, height=270, bg="black")
        self.canvas.grid(row=4, column=0, columnspan=3, pady=5)
        self.canvas_image = self.canvas.create_image(0, 0, anchor='nw') 

        # Internal state
        self.recording = False
        self.thread = None
        self.frame_queue = queue.Queue(maxsize=10)

        # Schedule periodic preview updates
        self.root.after(100, self.update_preview)

    def browse(self):
        f = filedialog.asksaveasfilename(
            defaultextension=".mp4",
            filetypes=[("MP4 files", "*.mp4"), ("AVI files", "*.avi"), ("All files", "*.*")]
        )
        if f:
            self.filename_var.set(f)

    def start_recording(self):
        out_path = self.filename_var.get().strip()
        if not out_path:
            messagebox.showerror("Error", "Please provide output file path.")
            return

        fps = self.fps_var.get()
        try:
            fps = int(fps)
            if fps <= 0 or fps > 120:
                raise ValueError
        except Exception:
            messagebox.showerror("Error", "FPS must be a positive integer <= 120")
            return

        # Disable/enable buttons
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")

        # Start background recording thread
        self.recording = True
        self.thread = threading.Thread(target=self.record_loop, args=(out_path, fps), daemon=True)
        self.thread.start()

    def stop_recording(self):
        self.recording = False
        if self.thread:
            self.thread.join(timeout=3)
        self.stop_btn.configure(state="disabled")
        self.start_btn.configure(state="normal")
        print("Recording stopped manually.")

    def record_loop(self, out_path, fps):
        print("Starting recording loop...")
        try:
            with mss.mss() as sct:
                monitor = sct.monitors[1]  
                width, height = monitor['width'], monitor['height']

                # Choose codec based on extension
                _, ext = os.path.splitext(out_path)
                ext = ext.lower()
                if ext == ".mp4":
                    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                else:
                    fourcc = cv2.VideoWriter_fourcc(*'XVID')

                out = cv2.VideoWriter(out_path, fourcc, fps, (width, height))
                if not out.isOpened():
                    print("VideoWriter failed, trying fallback...")
                    out = cv2.VideoWriter(out_path, cv2.VideoWriter_fourcc(*'XVID'), fps, (width, height))

                frame_period = 1.0 / fps

                while self.recording:
                    t0 = time.perf_counter()
                    try:
                        img = sct.grab(monitor)
                    except Exception as e:
                        print(f"Screen capture failed: {e}")
                        break

                    # Convert image and write frame
                    frame = np.array(img)
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                    out.write(frame)

                    # Update preview
                    preview = cv2.resize(frame, (480, 270))
                    preview_rgb = preview[..., ::-1]
                    try:
                        self.frame_queue.put_nowait(preview_rgb)
                    except queue.Full:
                        pass

                    elapsed = time.perf_counter() - t0
                    to_sleep = frame_period - elapsed
                    if to_sleep > 0:
                        time.sleep(to_sleep)

        finally:
            out.release()
            print("Recording stopped; file saved to", out_path)

    def update_preview(self):
        try:
            frame = self.frame_queue.get_nowait()
            img = Image.fromarray(frame)
            self.tkimg = ImageTk.PhotoImage(img)
            self.canvas.itemconfig(self.canvas_image, image=self.tkimg)
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.update_preview)


if __name__ == "__main__":
    print("main block is running...")
    root = tk.Tk()
    app = ScreenRec(root)
    root.mainloop()
