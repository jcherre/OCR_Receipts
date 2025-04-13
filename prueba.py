from module.ocr.ocr_incoice import OcrInvoice


ocr_factura = OcrInvoice()

response = ocr_factura.extract_information('./Receipts/20510069251_CasaIdeas_F009-17902.pdf')
print(response)