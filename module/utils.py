import io
import fitz
import numpy as np

from PIL import Image

def allowed_file(filename: str, allowed_extensions:list) -> bool:
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
    set_prices['IGV'] = price if 'IGV' in text_upper else set_prices['IGV']
    set_prices['total_descuentos'] = price if 'DESCUENTO' in text_upper else set_prices['total_descuentos']
    set_prices['OP.Gratuita'] = price if 'GRATUITA' in text_upper else set_prices['OP.Gratuita']
    set_prices['OP.Exoneradas'] = price if 'EXONERADA' in text_upper else set_prices['OP.Exoneradas']
    set_prices['OP.Inafectas'] = price if 'INAFECTA' in text_upper else set_prices['OP.Inafectas']
    set_prices['OP.Gravadas'] = price if 'GRAVADA' in text_upper else set_prices['OP.Gravadas']
    set_prices['ICBPER'] = price if 'ICBPER' in text_upper else set_prices['ICBPER']
    set_prices['importe_total'] = price if 'TOTAL' in text_upper else set_prices['importe_total']
    return set_prices


def process_pdf(pdf_path: np.array) -> np.ndarray:
    """
    Converts the first page of a PDF file to a NumPy array of an image.
    :param pdf_path: The path to the PDF file.
    :type pdf_path: np.ndarray.
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