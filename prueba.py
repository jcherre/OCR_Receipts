from module.ocr_facturas import OcrFactura


ocr_factura = OcrFactura()

response = ocr_factura.extract_information('./Receipts/20510069251_CasaIdeas_F009-17902.pdf')
print(response)