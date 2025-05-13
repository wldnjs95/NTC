# image_utils.py
import os, cv2, numpy
from config import conversion_widths
from utils import format_number

def convert_images_to_jpg(directory, quality):
    os.chdir(directory)
    count = 1

    for photo in os.listdir(directory):
        if not photo.lower().endswith('.jpg'):
            img = cv2.imdecode(numpy.fromfile(photo, dtype=numpy.uint8), cv2.IMREAD_COLOR)
            cv2.imwrite(f"{format_number(count)}.jpg", img, [cv2.IMWRITE_JPEG_QUALITY, quality])
            os.remove(photo)
            count += 1

    print(f'{count - 1} converted to jpg')
