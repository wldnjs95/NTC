import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from pillow_heif import register_heif_opener
from PIL import Image, UnidentifiedImageError
from src.utils.general_utils import format_number
from src.utils.logging_utils import log_user, log_debug, log_error
from src.utils.state import global_state

VALID_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.heic', '.heif')
register_heif_opener()

def convert_images_to_jpg(directory, quality=95):
    count = 1
    converted = 0
    errors = 0

    for photo in os.listdir(directory):
        photo_path = os.path.join(directory, photo)
        photo_lower = photo.lower()

        if not photo_lower.endswith(VALID_EXTENSIONS):
            log_user(f"Skipping {photo} (invalid extension)")
            continue

        output_path = os.path.join(directory, f"{format_number(count)}.jpg")
        try:
            img = Image.open(photo_path).convert("RGB")
            img.save(output_path, "JPEG", quality=quality)
            os.remove(photo_path)
            print(f"Converted: {photo} → {format_number(count)}.jpg")
            count += 1
            converted += 1
        except UnidentifiedImageError:
            log_error(f"Pillow cannot identify image file: {photo}")
            errors += 1
        except Exception as e:
            log_error(f"Pillow conversion failed for {photo}: {e}")
            errors += 1

    log_user(f"{converted} converted, {errors} errors.")
    return converted, errors

def main():
    sample_directory = 'src/utils/sample_image'
    directory = os.path.join(os.getcwd(), sample_directory)
    converted, errors = convert_images_to_jpg(directory, 95)
    if errors > 0:
        print(f"Conversion completed with {errors} error(s).")
    print("Done")

if __name__ == "__main__":
    main()
