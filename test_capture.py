import numpy as np
import mss #multiple screenshots library 
from PIL import Image

with mss.mss() as sct: #create an mss screen-capture context and assign it to variable
    monitor = sct.monitors[1] #primary monitor
    img = sct.grab(monitor)
    arr = np.array(img)
    rgb = arr[..., :3][:,:,::-1]
    im = Image.fromarray(rgb) #convert a numpy array to an image object(so it can be saved to disk)
    im.save("scrsht.png")
    print("saved", rgb.shape)