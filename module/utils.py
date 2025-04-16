import cv2
import numpy as np

from flask import jsonify
from datetime import datetime


def allowed_file(filename: str, allowed_extensions:set) -> bool:
    """
    Checks if a file name has an allowed extension.
    This function takes a file name and a set of allowed extensions and determines whether the file extension (if any)
    falls within the set of allowed extensions. The extension comparison is performed case-insensitively.

    :param filename:  The name of the file to be verified.
    :type filename: str
    :param allowed_extensions: A set of strings representing the allowed file extensions (e.g., {'pdf', 'png', 'jpg'}).
                               It is recommended to use a set for more efficient searches.
    :type allowed_extensions: list
    :return bool: True if the file has an allowed extension, False otherwise. Returns False if the file name does not
                  contain a period ('.') or if the extracted extension is not in the set of `allowed_extensions`.
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


def evaluate_sharpness(image_path):
    try:
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        laplacian = cv2.Laplacian(img, cv2.CV_64F)
        variance = np.var(laplacian)

        blurred_threshold = 100
        sharp_threshold = 300

        if variance < blurred_threshold:
            return False
        elif variance > sharp_threshold:
            return True
        else:
            return False

    except Exception as e:
        print(f"Error al procesar la imagen: {e}")


def build_api_response_format(status: str, message: str, body):
    if status == 'success':
        return jsonify({
            "status": status,
            "message": message,
            "data": body,
            "metadata": {
                "version": "1.0.0",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        }), 200
    elif status == 'error':
        return jsonify({
            'error': message,
            'code': body
        }), 400