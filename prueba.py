from module.ocr_facturas import OcrFactura


ocr_factura = OcrFactura()

response = ocr_factura.extract_information('./Receipts/10436083128_SanguchezLocos_F001-448.pdf')
print(response)