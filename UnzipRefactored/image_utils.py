# image_utils.py
import os, cv2, numpy
from utils import format_number
from logging_utils import log_user, log_debug, log_error
from state import global_state

def convert_images_to_jpg(directory, quality):
    os.chdir(directory)
    count = 1

    for photo in os.listdir(directory):
        if not photo.lower().endswith('.jpg'):
            img = cv2.imdecode(numpy.fromfile(photo, dtype=numpy.uint8), cv2.IMREAD_COLOR)
            cv2.imwrite(f"{format_number(count)}.jpg", img, [cv2.IMWRITE_JPEG_QUALITY, quality])
            os.remove(photo)
            count += 1

    log_user(f'{count - 1} converted to jpg')
