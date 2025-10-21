import time
import mss
import numpy as np
import cv2

OUTPUT = "output.avi"
FPS = 15
DURATION = 10
frame_period = 1.0 / FPS

with mss.mss() as sct:
    monitor = sct.monitors[1]  # primary
    width = monitor['width']
    height = monitor['height']

    
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(OUTPUT, fourcc, FPS, (width, height))

    start = time.perf_counter()
    frames = 0
    while time.perf_counter() - start < DURATION:
        t0 = time.perf_counter()
        img = sct.grab(monitor)
        arr = np.array(img)
        rgb = arr[..., :3][:, :, ::-1]  # BGRA -> RGB -> BGR for cv2
        # OpenCV expects BGR ordering, and uint8
        out.write(rgb)  # rgb is actually BGR after the slice order above
        frames += 1
        elapsed = time.perf_counter() - t0
        to_sleep = frame_period - elapsed
        if to_sleep > 0:
            time.sleep(to_sleep)

    out.release()
    print("Recorded", frames, "frames")