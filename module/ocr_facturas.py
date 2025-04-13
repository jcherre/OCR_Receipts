import io
import re
import fitz
import numpy as np

from PIL import Image
from paddleocr import PaddleOCR
from module.utils import is_number


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
        self.ocr = PaddleOCR(use_angle_cls=True, lang=lang)
        self.extract_words = list()
        self.word_and_locations = list()
        self.join_words = ""

    def extract_text(self, image_to_analyze:np.ndarray):
        """
        Realiza OCR en la imagen proporcionada y extrae el texto.
        :param image_to_analyze: La imagen de la factura a analizar como un array de NumPy.
        :type image_to_analyze: np.ndarray
        """
        result = self.ocr.ocr(image_to_analyze, cls=True)
        self.word_and_locations = [[line[1][0], line[0]] for line in result[0] if line[1][0] not in ('s/', 'S/.', 'S/', '$/', '$/.')]
        self.extract_words = [line[1][0] for line in result[0] if line[1][0] not in ('s/', 'S/.', 'S/', '$/', '$/.')]

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
        folio_encontrados = [element for element in folio_encontrados if len(element[0]) == 4]
        if len(folio_encontrados) == 0:
            folio_and_serie = ['', '']
            for element in self.extract_words:
                if 'SERIE' in element.upper():
                    pattern_serie = "([A-Z0-9]+)"
                    series = re.findall(pattern_serie, element)
                    series = [serie for serie in series if len(serie) == 4]
                    folio_and_serie[0] = series[0]
                if 'CORRELATIVO' in element.upper():
                    pattern_correlativo = "(\d+)"
                    correlativos = re.findall(pattern_correlativo, element)
                    correlativos = [correlativo for correlativo in correlativos if len(correlativo) > 3]
                    folio_and_serie[1] = correlativos[0]
            folio_encontrados.append(folio_and_serie)
        return folio_encontrados

    def extract_prices(self) -> dict:
        set_prices = {
            "IGV": None,
            "total_descuentos": None,
            "OP.Exoneradas": None,
            "OP.Inafectas": None,
            "OP.Gravadas": None,
            "OP.Gratuita": None,
            "ICBPER": None,
            "importe_total": None
        }
        currency_pattern = r"\d+\.\d+\d"
        currency_found = re.findall(currency_pattern, self.join_words)

        # Find index of currency
        found_index = set()
        for element_to_search in currency_found:
            for index, element in enumerate(self.extract_words):
                if element_to_search in element:
                    found_index.add(index)

        # Struct information to response
        found_index= sorted(list(found_index))

        rows_prices = []
        for index in found_index:
            same_row = [self.extract_words[index]]
            if abs(self.word_and_locations[index][1][3][1] - self.word_and_locations[index + 1][1][3][1]) < 20.0:
                same_row.append(self.word_and_locations[index + 1][0])
            elif abs(self.word_and_locations[index][1][3][1] - self.word_and_locations[index - 1][1][3][1]) < 20.0:
                same_row.append(self.word_and_locations[index - 1][0])
            rows_prices.append(same_row)

        rows_prices = [row for row in rows_prices if len(row) == 2 and is_number(row[0])]

        if len(rows_prices) == 0:
            for index in found_index:
                set_prices['IGV']  = re.findall(currency_pattern, self.extract_words[index].replace('18.00', ''))[0] \
                    if 'IGV' in self.extract_words[index] else set_prices['IGV']
                set_prices['total_descuentos'] = re.findall(currency_pattern, self.extract_words[index])[0] \
                    if 'DESCUENTO' in self.extract_words[index] else set_prices['total_descuentos']
                set_prices['OP.Gratuita'] = re.findall(currency_pattern, self.extract_words[index])[0] \
                    if 'GRATUITA' in self.extract_words[index] else set_prices['OP.Gratuita']
                set_prices['OP.Exoneradas'] = re.findall(currency_pattern, self.extract_words[index])[0] \
                    if 'EXONERADA' in self.extract_words[index] else set_prices['OP.Exoneradas']
                set_prices['OP.Inafectas'] = re.findall(currency_pattern, self.extract_words[index])[0] \
                    if 'INAFECTA' in self.extract_words[index] else set_prices['OP.Inafectas']
                set_prices['OP.Gravadas'] = re.findall(currency_pattern, self.extract_words[index])[0] \
                    if 'GRAVADA' in self.extract_words[index] else set_prices['OP.Gravadas']
                set_prices['ICBPER'] = re.findall(currency_pattern, self.extract_words[index])[0] \
                    if 'ICBPER' in self.extract_words[index] else set_prices['ICBPER']
                set_prices['importe_total'] =re.findall(currency_pattern, self.extract_words[index])[0]\
                    if 'TOTAL' in self.extract_words[index] else set_prices['importe_total']
        else:
            for new_row in rows_prices:
                set_prices['IGV'] = new_row[0] if 'IGV' in new_row[1].replace('.', '') else set_prices['IGV']
                set_prices['total_descuentos'] = new_row[0] if 'DESCUENTO' in new_row[1] else set_prices['total_descuentos']
                set_prices['OP.Gratuita'] = new_row[0] if 'GRATUITA' in new_row[1] else set_prices['OP.Gratuita']
                set_prices['OP.Exoneradas'] = new_row[0] if 'EXONERADA' in new_row[1] else set_prices['OP.Exoneradas']
                set_prices['OP.Inafectas'] = new_row[0] if 'INAFECTA' in new_row[1] else set_prices['OP.Inafectas']
                set_prices['OP.Gravadas'] = new_row[0] if 'GRAVADA' in new_row[1] else set_prices['OP.Gravadas']
                set_prices['ICBPER'] = new_row[0] if 'ICBPER' in new_row[1] else set_prices['ICBPER']
                set_prices['importe_total'] = new_row[0] if 'TOTAL' in new_row[1] else set_prices['importe_total']


        return set_prices

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
        set_prices = self.extract_prices()
        rucs_encontrados = self.extract_ruc()
        fechas_encontradas = self.extract_fecha_emision()
        folio_encontrados = self.extract_patron_folio()
        response = {
            "ruc_emisor": rucs_encontrados[0] if rucs_encontrados else None,
            "rucs_encontrados": rucs_encontrados,
            "fecha_emision": fechas_encontradas[0] if fechas_encontradas else None,
            "serie": folio_encontrados[0][0] if folio_encontrados else None,
            "correlativo": folio_encontrados[0][1] if folio_encontrados else None,
            "cargos_encontrados": set_prices
        }
        return response