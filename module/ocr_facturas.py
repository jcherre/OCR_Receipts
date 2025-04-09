import io
import re
import fitz
import numpy as np

from PIL import Image
from paddleocr import PaddleOCR


class OcrFactura:
    """
    Clase para realizar el reconocimiento óptico de caracteres (OCR) en facturas,
    específicamente para extraer información relevante como RUC, fecha de emisión,
    serie, correlativo y total de venta.
    """

    def __init__(self, lang:str ='es'):
        """
        Inicializa la clase OcrFactura.
        :param lang: El idioma para el OCR. Por defecto es 'es' (español).
        :type lang: str, optional
        """
        self.ocr = PaddleOCR(lang=lang)
        self.extract_words = list()
        self.join_words = ""

    def extract_text(self, image_to_analyze:np.ndarray):
        """
        Realiza OCR en la imagen proporcionada y extrae el texto.
        :param image_to_analyze: La imagen de la factura a analizar como un array de NumPy.
        :type image_to_analyze: np.ndarray
        """
        result = self.ocr.ocr(image_to_analyze, cls=True)
        self.extract_words = [line[1][0] for line in result[0]]

    def process_pdf(self, pdf_path) -> np.ndarray:
        """
        Convierte la primera página de un archivo PDF en un array de NumPy de una imagen.
        :param pdf_path: La ruta al archivo PDF.
        :type pdf_path: np.ndarray.
        :return np.ndarray: Un array de NumPy que representa la imagen de la primera página del PDF o None si hay un error.
        """
        pdf_document = fitz.open(pdf_path)
        factura = pdf_document.load_page(0)
        matriz = fitz.Matrix(300 / 72, 300 / 72)
        pix = factura.get_pixmap(matrix=matriz)
        pdf_document.close()
        image_bytes = pix.tobytes("png")
        image_pil = Image.open(io.BytesIO(image_bytes))
        image_numpy = np.array(image_pil)
        return image_numpy

    def extract_ruc(self) -> list:
        """
        Extrae el RUC de la factura del texto extraído.
        :return list: Una lista de los RUC encontrados en el texto.
        """
        patron_ruc = r"\b(?:10|20)\d{9}"
        rucs_encontrados = re.findall(patron_ruc, self.join_words)
        return rucs_encontrados

    def extract_fecha_emision(self) -> list:
        """
        Extrae la fecha de emisión de la factura del texto extraído.
        :return list: Una lista de las fechas de emisión encontradas en el texto.
        """
        patron_fecha = r"\d{1,2}[-/]\d{2}[-/]\d{2,4}"
        fechas_encontradas = re.findall(patron_fecha, self.join_words)
        return fechas_encontradas

    def extract_patron_folio(self) -> list:
        """
        Extrae la serie y el correlativo (folio) de la factura del texto extraído.
        :return list: Una lista de tuplas, donde cada tupla contiene (serie, correlativo).
        """
        patron_folio = r"([A-Z0-9]+)-(\d+)"
        folio_encontrados = re.findall(patron_folio, self.join_words)
        folio_encontrados = [element for element in folio_encontrados if len(element[0]) > 2]
        return folio_encontrados

    def extract_total_venta(self) -> list:
        """
        Extrae el total de venta de la factura del texto extraído.
        :return list: Una lista de los totales de venta encontrados en el texto.
        """
        patron_precios = r"\d+\.\d+\d"
        precios_encontrados = re.findall(patron_precios, self.join_words)
        return precios_encontrados

    def extract_information(self, image_content: str) -> dict:
        """
        Procesa la imagen de la factura para extraer información clave como RUC,
        fecha de emisión, serie, correlativo y precio total.

        :param image_content:La ruta al archivo PDF de la factura.
        :type image_content: str
        :return dict: Un diccionario que contiene la información extraída de la factura,
                      o un diccionario vacío si hay un error.
        """
        numpy_image = self.process_pdf(image_content)  # Procesa el PDF y obtiene la imagen como NumPy array.
        if numpy_image is None:
            return {}  # Devuelve un diccionario vacío si no se pudo procesar el PDF
        self.extract_text(numpy_image)  # Extrae el texto de la imagen.
        self.join_words = " ".join(self.extract_words).replace(
            " - ", "-"
        )
        rucs_encontrados = self.extract_ruc()
        fechas_encontradas = self.extract_fecha_emision()
        folio_encontrados = self.extract_patron_folio()
        precios_encontrados = self.extract_total_venta()
        response = {
            "rucs_encontrados": rucs_encontrados,
            "fecha_emision": fechas_encontradas[0] if fechas_encontradas else None,
            "serie": folio_encontrados[0][0] if folio_encontrados else None,
            "correlativo": folio_encontrados[0][1] if folio_encontrados else None,
            "precio_total": max(precios_encontrados) if precios_encontrados else None,
        }
        return response