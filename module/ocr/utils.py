import io
import fitz
import numpy as np
from rapidfuzz import process, fuzz

from PIL import Image


def is_number(string: str) -> bool:
    """
    Checks if a text string can be converted to a floating-point number.
    This function attempts to convert the input string to a `float` data type.
    If the conversion is successful, it means the string represents a valid number (either an integer or a number with
    decimal places). If the conversion fails, a `ValueError` exception is caught, indicating that the string is not in
    a recognizable numeric format.
    :param string: The text string you want to verify.
    :type string: str
    :return bool: True if the string can be converted to a floating-point number, False otherwise.
    """
    try:
        float(string)
        return True
    except ValueError:
        return False


def assign_price(price: str, text: str, set_prices: dict) -> dict:
    """
    Assigns a price value to different price categories (VAT, discounts, transactions, etc.) within a dictionary,
    based on the presence of specific keywords in the associated text.
    :param price:The value of the price to be assigned.
    :type price: str
    :param text: The text associated with the price, which will be used to determine the price category.
    :type text: str
    :param set_prices: The dictionary that stores the different types of invoice prices. The expected keys are:
                       'IGV', 'total_descuentos', 'OP.Gratuita', 'OP.Exoneradas', 'OP.Inafectas','OP.Gravadas',
                       'ICBPER', 'importe_total'.
    :return dict: The `set_prices` dictionary is updated with the value of the price assigned to the corresponding
                  category (if a matching keyword is found). If no matching keyword is found,  the dictionary is
                  returned unchanged for that price.
    """
    text_upper = text.upper().replace('.', '')
    set_prices['IGV'] = [price, 0.00] if 'IGV' in text_upper or 'GV' in text_upper else  set_prices['IGV']
    set_prices['total_descuentos'] = [price, 0.00] if 'DESCUENTO' in text_upper else set_prices['total_descuentos']
    set_prices['OP.Gratuita'] = [price, 0.00] if 'GRATUIT' in text_upper else set_prices['OP.Gratuita']
    set_prices['OP.Exoneradas'] = [price, 0.00] if 'EXONERAD' in text_upper else set_prices['OP.Exoneradas']
    set_prices['OP.Inafectas'] = [price, 0.00] if 'INAFECT' in text_upper else set_prices['OP.Inafectas']
    set_prices['OP.Gravadas'] = [price, 0.00] if 'GRAVAD' in text_upper or 'VALOR' in text_upper else set_prices['OP.Gravadas']
    set_prices['ICBPER'] = [price, 0.00] if 'ICBPER' in text_upper else set_prices['ICBPER']
    set_prices['otros_cargos'] = [price, 0.00] if 'CARGO' in text_upper else set_prices['otros_cargos']
    set_prices['importe_total'] = [price, 0.00] if 'TOTAL' in text_upper else set_prices['importe_total']
    return set_prices

def assign_price_v2(price: str, texts: list[str], set_prices: dict, score_cutoff: float=65.0) -> dict:
    """
    Assigns a price value to different price categories (VAT, discounts, transactions, etc.) within a dictionary,
    based on the presence of specific keywords in the associated text.
    :param price:The value of the price to be assigned.
    :type price: str
    :param texts: The labels associated with the price, which will be used to determine the price category.
    :type texts: list[str]
    :param set_prices: The dictionary that stores the different types of invoice prices. The expected keys are:
                       'IGV', 'total_descuentos', 'OP.Gratuita', 'OP.Exoneradas', 'OP.Inafectas','OP.Gravadas',
                       'ICBPER', 'importe_total'.
    :return dict: The `set_prices` dictionary is updated with the value of the price assigned to the corresponding
                  category (if a matching keyword is found). If no matching keyword is found,  the dictionary is
                  returned unchanged for that price.
    :param score_cutoff: The minimum score for the fuzzy search algorithm
    :type score_cutoff: float
    """
    dict_matches = {
        'IGV': ["IGV"],
        'total_descuentos': ["DESCUENTO"],
        'OP.Gratuita': ["GRATUIT"],
        'OP.Exoneradas': ["EXONERAD"],
        'OP.Inafectas': ["INAFECT"],
        'OP.Gravadas': ["GRAVAD","VALOR"],
        'ICBPER': ["ICBPER"],
        'otros_cargos': ["CARGO"],
        'importe_total': ["TOTAL"]
    }

    best_score = 0
    best_key = None

    for text in texts:
        for key, patterns in dict_matches.items():
            # Check against all patterns for the current key
            results = process.extract(text.upper(), patterns, scorer=fuzz.WRatio, score_cutoff=score_cutoff)
            if len(results) > 0:
                for result in results:
                    if result[1] >= best_score:
                        best_score = result[1]
                        best_key = key
    
    if best_key:
        if not(set_prices[best_key][0]) or (set_prices[best_key][0] and best_score >= set_prices[best_key][1]):
            set_prices[best_key] = [price, best_score]

    return set_prices


def process_pdf(pdf_path: str) -> np.ndarray:
    """
    Converts the first page of a PDF file to a NumPy array of an image.
    :param pdf_path: The path to the PDF file.
    :type pdf_path: str.
    :return np.ndarray: A NumPy array representing the image of the first page of the PDF, or None if there is an error.
    """
    pdf_document = fitz.open(pdf_path)
    invoice = pdf_document.load_page(0)
    matriz = fitz.Matrix(300 / 72, 300 / 72)
    pix = invoice.get_pixmap(matrix=matriz)
    pdf_document.close()
    image_bytes = pix.tobytes("png")
    image_pil = Image.open(io.BytesIO(image_bytes))
    image_numpy = np.array(image_pil)
    return image_numpy


def proces_image(image_path: str) -> np.ndarray:
    """
    Loads an image file and converts it to a NumPy array.

    :param image_path: The path to the image file.
    :type image_path: str
    :return: A NumPy array representing the image, or None if there is an error loading the image.
    :rtype: np.ndarray
    """
    image_pil = Image.open(image_path)
    image_numpy = np.array(image_pil)
    return image_numpy
