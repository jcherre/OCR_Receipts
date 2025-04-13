import io
import re
import fitz
import numpy as np
import module.utils as ut


from paddleocr import PaddleOCR



class OcrInvoice:
    """
    Class for performing optical character recognition (OCR) on invoices,specifically for extracting
    relevant information such as tax identification number (RUC), issue date, series, serial number,
    and sales total.
    """

    def __init__(self, lang:str ='es'):
        """
        Initializes the OcrInvoice class.
        :param lang: The language for OCR. The default is 'es' (Spanish).
        :type lang: str, optional
        """
        self.ocr = PaddleOCR(use_angle_cls=True, lang=lang)
        self.extracted_word = list()
        self.word_and_locations = list()
        self.words_joined = ""

    def extract_text(self, image_to_analyze:np.ndarray):
        """
        Performs OCR on the provided image and extracts the text.
        :param image_to_analyze: The invoice image to be analyzed as a NumPy array.
        :type image_to_analyze: np.ndarray
        """
        result = self.ocr.ocr(image_to_analyze, cls=True)
        self.word_and_locations = [[line[1][0], line[0]] for line in result[0] if line[1][0] not in ('s/', 'S/.', 'S/', '$/', '$/.')]
        self.extracted_word = [line[1][0] for line in result[0] if line[1][0] not in ('s/', 'S/.', 'S/', '$/', '$/.')]

    def extract_ruc(self) -> list:
        """
        Extract the RUC from the invoice for the extracted text.
        :return list: A list of the RUCs found in the text.
        """
        ruc_pattern = r"\b(?:10|20)\d{9}"
        found_rucs = re.findall(ruc_pattern, self.words_joined)
        return found_rucs

    def extract_issue_date(self) -> list:
        """
        Extract the invoice issue date from the extracted text.
        :return list: A list of the issue dates found in the text.
        """
        date_pattern = r"\d{1,2}[-/]\d{2}[-/]\d{2,4}"
        found_dates = re.findall(date_pattern, self.words_joined)
        return found_dates

    def extract_series_and_correlative(self) -> list:
        """
        Extracts the series and the correlative (folio) of the invoice from the extracted text.
        :return list: A list of tuples, where each tuple contains (series, correlative).
        """
        folio_pattern = r"([A-Z0-9]+)-(\d+)"
        found_series_correlative = re.findall(folio_pattern, self.words_joined)
        found_series_correlative = [element for element in found_series_correlative if len(element[0]) == 4]
        if len(found_series_correlative) == 0:
            correlative_and_serie = ['', '']
            for found_word in self.extracted_word:
                if 'SERIE' in found_word.upper():
                    pattern_serie = "([A-Z0-9]+)"
                    founded_series = re.findall(pattern_serie, found_word)
                    founded_series = [serie for serie in founded_series if len(serie) == 4]
                    correlative_and_serie[0] = founded_series[0]
                if 'CORRELATIVO' in found_word.upper():
                    pattern_correlative = "(\d+)"
                    correlatives = re.findall(pattern_correlative, found_word)
                    correlatives = [correlative for correlative in correlatives if len(correlative) > 3]
                    correlative_and_serie[1] = correlatives[0]
            found_series_correlative.append(correlative_and_serie)
        return found_series_correlative

    def extract_prices(self) -> dict:
        """
        Extract all prices and their corresponding charge type.
        :return dict: Dictionary with the charges found
        """
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
        currency_pattern = r"\d{1,3}(?:,\d{3})*\.\d{2,}"
        currency_found = re.findall(currency_pattern, self.words_joined)

        if not currency_found:
            return set_prices

        found_indices = set()
        for element_to_search in currency_found:
            for index, element in enumerate(self.extracted_word):
                if element_to_search in element:
                    found_indices.add(index)
        found_indices = sorted(list(found_indices))

        rows_prices = []
        height_tolerance = 20.0

        for index in found_indices:
            price = self.extracted_word[index]
            if not ut.is_number(price):
                continue

            row = [price]
            y_coord = self.word_and_locations[index][1][3][1]

            for i in [index + 1, index - 1]:
                if 0 <= i < len(self.word_and_locations) and abs(
                        self.word_and_locations[i][1][3][1] - y_coord) < height_tolerance:
                    row.append(self.word_and_locations[i][0])
                    break

            if len(row) == 2:
                rows_prices.append(row)

        if rows_prices:
            for price, label_candidate in rows_prices:
                set_prices = ut.assign_price(price, label_candidate, set_prices)
        else:
            for word in self.extracted_word:
                prices = re.findall(currency_pattern, word)
                if prices:
                    price = prices[0]
                    set_prices = ut.assign_price(price, word, set_prices)

        return set_prices

    def extract_information(self, image_content: str) -> dict:
        """
        Process the invoice image to extract key information such as RUC, issue date,
        series, serial number, and total price.

        :param image_content:The path to the invoice PDF file.
        :type image_content: str
        :return dict: A dictionary containing the information extracted from the invoice,
                      empty dictionary if there is an error.
        """
        numpy_image = ut.process_pdf(image_content)
        if numpy_image is None:
            return {}
        self.extract_text(numpy_image)
        self.words_joined = " ".join(self.extracted_word).replace(
            " - ", "-"
        )
        set_prices = self.extract_prices()
        found_rucs = self.extract_ruc()
        found_dates = self.extract_issue_date()
        found_series_and_correlative = self.extract_series_and_correlative()
        response = {
            "ruc_emisor": found_rucs[0] if found_rucs else None,
            "fecha_emision": found_dates[0] if found_dates else None,
            "serie": found_series_and_correlative[0][0] if found_series_and_correlative else None,
            "correlativo": found_series_and_correlative[0][1] if found_series_and_correlative else None,
            "cargos_encontrados": set_prices
        }
        return response