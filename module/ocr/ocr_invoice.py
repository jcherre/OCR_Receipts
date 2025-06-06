import re
import datetime
import numpy as np
import module.ocr.utils as ut
import copy
import os

from paddleocr import PaddleOCR

_HEIGHT_TOLERANCE_COR = float(os.getenv("HEIGHT_TOLERANCE_COR", 20.0))
_HEIGHT_TOLERANCE = float(os.getenv("HEIGHT_TOLERANCE", 25.0))
_WIDTH_TOLERANCE = float(os.getenv("WIDTH_TOLERANCE", 20.0))
_NEW_LINE_TOLERANCE = float(os.getenv("NEW_LINE_TOLERANCE", 80.0))
_MAX_STRING_LENGTH = int(os.getenv("MAX_STRING_LENGTH", 40))
_SCORE_CUTOFF_ROWS = float(os.getenv("SCORE_CUTOFF_ROWS", 65.0))
_SCORE_CUTOFF_COLS = float(os.getenv("SCORE_CUTOFF_COLS", 65.0))

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
        self.ocr = PaddleOCR(use_doc_orientation_classify=False, # Disables document orientation classification model via this parameter
                            use_doc_unwarping=False, # Disables text image rectification model via this parameter
                            use_textline_orientation=False, # Disables text line orientation classification model via this parameter
                            lang=lang)
        self.extracted_word = list()
        self.word_and_locations = list()
        self.words_joined = ""

    def extract_text(self, image_to_analyze:np.ndarray):
        """
        Performs OCR on the provided image and extracts the text.
        :param image_to_analyze: The invoice image to be analyzed as a NumPy array.
        :type image_to_analyze: np.ndarray
        """
        result = self.ocr.predict(image_to_analyze)
        #for res in result:
        #    res.save_to_img("output")  
        #    res.save_to_json("output")
        self.result_json = result[0].json.get('res')
        self.word_and_locations = [[line, box] for box, line in zip(self.result_json.get('rec_boxes'), self.result_json.get('rec_texts')) if line not in ('s/', 'S/.', 'S/', '$/', '$/.')]
        self.extracted_word = [line for line in self.result_json.get('rec_texts') if line not in ('s/', 'S/.', 'S/', '$/', '$/.')]

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
        for date in found_dates:
            if '/' not in date[-4:] or '-' not in date[-4:]:
                try:
                    if int(date[-4:]) > datetime.datetime.now().year:
                        found_dates.remove(date)
                        found_dates.append(date[:-2])
                except Exception as e:
                    pass

        return found_dates

    def extract_series_and_correlative(self) -> list:
        """
        Extracts the series and the correlative (folio) of the invoice from the extracted text.
        :return list: A list of tuples, where each tuple contains (series, correlative).
        """
        folio_pattern = r"([A-Z0-9]+)-\s*(\d+)"
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

            if correlative_and_serie == ['', '']:
                height_tolerance = _HEIGHT_TOLERANCE_COR
                escape = False
                for found_word in self.word_and_locations:
                    if escape:
                        break
                    row = [(found_word[1][0], found_word[0])]
                    y1_coord = found_word[1][1]
                    for i in range(len(self.word_and_locations)):
                        if (self.word_and_locations[i][0] != found_word[0]) and (abs(self.word_and_locations[i][1][1] - y1_coord) < height_tolerance):
                            row.append((abs(self.word_and_locations[i][1][0] - y1_coord), self.word_and_locations[i][0].strip()))
                    sorted_list = sorted(row, key=lambda x: x[0], reverse=False)
                    result = "".join(map(lambda x: x[1], sorted_list))
                    found_series_correlative_line = re.findall(folio_pattern, result)
                    if len(found_series_correlative_line) > 0:
                        for element in found_series_correlative_line:
                            if len(element[0]) >= 4:
                                correlative_and_serie = [element[0][:4], element[1]]
                                escape = True
                                break
            
            found_series_correlative.append(correlative_and_serie)
        return found_series_correlative

    def extract_prices(self) -> dict:
        """
        Extract all prices and their corresponding charge type.
        :return dict: Dictionary with the charges found
        """
        set_prices = {
            "IGV": [None, 0.00],
            "total_descuentos": [None, 0.00],
            "OP.Exoneradas": [None, 0.00],
            "OP.Inafectas": [None, 0.00],
            "OP.Gravadas": [None, 0.00],
            "OP.Gratuita": [None, 0.00],
            "ICBPER": [None, 0.00],
            "otros_cargos": [None, 0.00],
            "importe_total": [None, 0.00]
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
        cols_prices = []
        height_tolerance = _HEIGHT_TOLERANCE
        width_tolerance = _WIDTH_TOLERANCE
        new_line_tolerance = _NEW_LINE_TOLERANCE
        max_string_length = _MAX_STRING_LENGTH

        for index in found_indices:
            check_pattern = r"(?<!\d)[^\w\d]?(\d+(?:[\.,]\d+)?)"
            matches = re.findall(check_pattern, self.extracted_word[index])
            if len(matches) > 0:
                price = matches[-1].strip()
            else:
                price = (self.extracted_word[index]
                        .replace('S', '')
                        .replace('$', '')
                        .replace('/.', '')
                        .replace('/', '')
                        .replace('[', '')
                        .replace(']', '')
                        .replace(',', '').strip())
            if ut.is_number(price): #or re.search(r'\d+(?:\.\d+)?%', self.extracted_word[index].strip()):
                match = re.search(r'\d+(?:\.\d+)?%', self.extracted_word[index].strip())
                if match:
                    # Look at the rest of the string after the match
                    rest = self.extracted_word[index].strip()[match.end():]
                    # Check if there are any other numbers after it
                    if not re.search(r'\d', rest):
                        continue
            else:
                continue

            row = [price]
            y1_coord = self.word_and_locations[index][1][1]
            row_candidates = []

            for i in range(len(self.word_and_locations)):
                if ((i != index or (i == index and self.word_and_locations[i][0].replace('S', '')
                        .replace('$', '')
                        .replace('/.', '')
                        .replace('/', '')
                        .replace('[', '')
                        .replace(']', '')
                        .replace(',', '').strip() != price)) and
                    abs(self.word_and_locations[i][1][1] - y1_coord) < height_tolerance and
                    len(self.word_and_locations[i][0].strip()) < max_string_length):
                    row_candidates.append((abs(self.word_and_locations[i][1][1] - y1_coord), self.word_and_locations[i][0].strip()))
                    #break
            if len(row_candidates) > 0:
                sorted_list = sorted(row_candidates, key=lambda x: x[0], reverse=True)
                row.append([item[1] for item in sorted_list])

            if len(row) > 1:
                rows_prices.append(row)

            col = [price]
            y1_coord = self.word_and_locations[index][1][1]
            x2_coord = self.word_and_locations[index][1][2]
            col_candidates = []

            for i in range(len(self.word_and_locations)):
                if (i != index and
                    abs(self.word_and_locations[i][1][2] - x2_coord) < width_tolerance and
                    len(self.word_and_locations[i][0].strip()) < max_string_length and
                    0 <= (y1_coord - self.word_and_locations[i][1][1]) < new_line_tolerance):
                    col_candidates.append((abs(self.word_and_locations[i][1][2] - x2_coord), self.word_and_locations[i][0].strip()))
                    #break 
            if len(col_candidates) > 0:
                sorted_list = sorted(col_candidates, key=lambda x: x[0], reverse=True)
                col.append([item[1] for item in sorted_list])

            if len(col) > 1:
                cols_prices.append(col)


        if rows_prices or cols_prices:
            score_cutoff_rows = _SCORE_CUTOFF_ROWS
            set_prices_rows = copy.deepcopy(set_prices)
            for price, label_candidates in rows_prices:
                set_prices_rows = ut.assign_price_v2(price, label_candidates, set_prices_rows, score_cutoff_rows)
            
            score_cutoff_cols = _SCORE_CUTOFF_COLS
            set_prices_cols = copy.deepcopy(set_prices)
            for price, label_candidates in cols_prices:
                set_prices_cols = ut.assign_price_v2(price, label_candidates, set_prices_cols, score_cutoff_cols)

            set_prices = {k: set_prices_rows[k] if set_prices_cols[k][0] is None or (set_prices_rows[k][0] is not None and set_prices_cols[k][0] is not None and set_prices_rows[k][1] >= set_prices_cols[k][1]) else set_prices_cols[k] for k in set_prices}
            #This should be handled further
            """if set_prices['IGV'][0] is None and not(set_prices['importe_total'][0] is None) and not(set_prices['OP.Gravadas'][0] is None):
                set_prices['IGV'] = [f"{(float(set_prices['importe_total'][0]) - float(set_prices['OP.Gravadas'][0])):.2f}", 0.00]
            if set_prices['OP.Gravadas'][0] is None and not(set_prices['importe_total'][0] is None) and not(set_prices['IGV'][0] is None):
                set_prices['OP.Gravadas'] = [f"{(float(set_prices['importe_total'][0]) - float(set_prices['IGV'][0])):.2f}", 0.00]
            if set_prices['importe_total'][0] is None:
                set_prices['importe_total'] = [f"{(max([float(currency_arr) for currency_arr in currency_found])):.2f}", 0.00]"""
        else:
            for word in self.extracted_word:
                prices = re.findall(currency_pattern, word.replace('18.00%', ''))
                if prices:
                    price = prices[0]
                    set_prices = ut.assign_price(price, word, set_prices)
        
        return set_prices

    def extract_information(self, image_content: str, seller_ruc: str, type_document: str) -> dict:
        """
        Process the invoice image to extract key information such as RUC, issue date,
        series, serial number, and total price.

        :param image_content:The path to the invoice PDF file.
        :type image_content: str
        :param seller_ruc: The ruc of the recipient company.
        :type seller_ruc: str
        :param type_document: Type of document that we upload.
        :type type_document: str
        :return dict: A dictionary containing the information extracted from the invoice,
                      empty dictionary if there is an error.
        """
        if type_document == 'pdf':
            numpy_image = ut.process_pdf(image_content)
        elif type_document == 'image':
            numpy_image = ut.proces_image(image_content)
        else:
            numpy_image = None

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
                "issuer_ruc": found_rucs[0] if found_rucs else None,
                "emission_date": found_dates[0] if found_dates else None,
                "doc_type": 'Factura' if 'F' in found_series_and_correlative[0][0] else 'Boleta',
                "series": found_series_and_correlative[0][0] if found_series_and_correlative else None,
                "sequential_number": found_series_and_correlative[0][1] if found_series_and_correlative else None,
                "invoice_details": set_prices
        }
        return response