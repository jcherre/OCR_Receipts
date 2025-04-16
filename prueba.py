# from module.ocr.ocr_incoice import OcrInvoice
#
#
# ocr_factura = OcrInvoice()
#
# response = ocr_factura.extract_information('./Receipts/20510069251_CasaIdeas_F009-17902.pdf')
# print(response)
#
# from flask import Flask, request, jsonify
# from werkzeug.utils import secure_filename
# import os
#
# app = Flask(__name__)
#
# # Configuración para la subida de archivos (opcional, pero recomendado)
# UPLOAD_FOLDER = 'uploads'
# ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
# app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
#
# def allowed_file(filename, allowed_extensions):
#     return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions
#
# @app.route('/api/process_data', methods=['POST'])
# def process_data():
#     """
#     Endpoint para procesar datos incluyendo el RUC de la empresa receptora,
#     un archivo PDF o una imagen (uno de los dos es obligatorio), y un código QR opcional.
#     """
#     # Procesamiento de archivos (si se adjuntan)
#     pdf_filename = None
#     if pdf_file and allowed_file(pdf_file.filename):
#         filename = secure_filename(pdf_file.filename)
#         # Guardar el archivo de forma segura (esto es solo un ejemplo, considera la seguridad)
#         os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
#         pdf_filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
#         pdf_file.save(pdf_filepath)
#         pdf_filename = filename
#         print(f"Archivo PDF guardado en: {pdf_filepath}")
#
#     image_filename = None
#     if image_file and allowed_file(image_file.filename):
#         filename = secure_filename(image_file.filename)
#         # Guardar el archivo de forma segura (esto es solo un ejemplo, considera la seguridad)
#         os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
#         image_filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
#         image_file.save(image_filepath)
#         image_filename = filename
#         print(f"Archivo de imagen guardado en: {image_filepath}")
#
#     # Procesamiento del código QR (opcional)
#     if qr_code:
#         print(f"Código QR recibido: {qr_code}")
#
#     # Aquí iría la lógica principal de tu API con los datos recibidos
#     response_data = {
#         'message': 'Datos recibidos y procesados exitosamente.',
#         'ruc_receiving_company': ruc_receiving_company,
#         'pdf_file': pdf_filename,
#         'image_file': image_filename,
#         'qr_code': qr_code
#     }
#
#     return jsonify(response_data), 200
#
# if __name__ == '__main__':
#     app.run(debug=True)

import module.ocr.utils as ut

image = './img/20503840121_Repsol_F609-10527.png'

ut.evaluate_sharpness(image)

























