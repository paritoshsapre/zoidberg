import cv2
import numpy
from time import time, sleep
from threading import Thread, Event

from flask import Flask, render_template, Response, request

from camera import Grabber

class FrameThread(Thread):
    def __init__(self, width=640, height=480, capture_rate=50, key=0):
        Thread.__init__(self)
        self.width, self.height, self.capture_rate = width, height, capture_rate
        self.daemon = True        
        self.frame = None       
        self.start()
        self.fps, self.center, self.radius= 0, None, None
    
    def run(self):
        grabber = Grabber(self.width, self.height, self.capture_rate)
        c = 0
        while True:
            start = time()
            uv = grabber.read()            
            
            blurred_uv = uv        
            blurred_uv = cv2.blur(uv, (4,4))  # kills perf but smooths the picture
            mask = cv2.inRange(blurred_uv, (60, 160), (90, 255))  ## FILTER THE COLORS!!
           
            mask = cv2.dilate(mask, None, iterations=2)
            cnts = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2] 

            if cnts:
                contour = max(cnts, key=cv2.contourArea)
                self.center, self.radius = cv2.minEnclosingCircle(contour)
                self.radius = round(self.radius)

            self.fps = round(1 / (time()-start)), round(time()-start,4 )
            c = (c+1)%20
            if not c:
                #print("fps: {} center: {} radious: {}".format(self.fps,self.center, self.radius))
                frame = grabber.image
                self.frame = cv2.bitwise_and(frame,frame, mask=mask)
                 
            
            
camera = FrameThread()
# camera = FrameThread(width=320,height=240,capture_rate=200)


app = Flask(__name__)
SLEEP_TIME = 0.08

@app.route('/')
def both():
    print('arse')
    def generator():
        while True:
            frame = camera.frame
            try:
                ret, jpeg = cv2.imencode('.jpg', frame, (cv2.IMWRITE_JPEG_QUALITY, 80))
                yield b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + jpeg.tostring() + b'\r\n\r\n'
                print('+web fps',camera.fps)
            except:
                pass
            sleep(SLEEP_TIME)
    return Response(generator(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, use_reloader=False, threaded=True)
