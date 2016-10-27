import time
import picamera

def take_picture(pic_name='image.jpg', delay=0):
    #pic_location = '/home/pi/workshop/camera/'
    pic_location = 'pictures/'
    pic_location = pic_location + pic_name
    with picamera.PiCamera() as camera:
        camera.start_preview()
        time.sleep(delay)
        camera.capture(pic_location)
        camera.stop_preview()

#pic_location = '/home/pi/workshop/camera/image.jpg'
#take_picture()
