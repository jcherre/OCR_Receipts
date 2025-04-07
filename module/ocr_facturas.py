from paddleocr import PaddleOCR


class OcrFactura:
    def __init__(self):
        self.ocr = PaddleOCR(lang='es')

    def extract_information(self, image_content):
        pass
