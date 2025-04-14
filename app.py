import os

from pathlib import Path
from datetime import datetime
from module.utils import allowed_file
from flask import Flask, request, jsonify
from module.ocr.ocr_incoice import OcrInvoice


UPLOAD_FOLDER = 'tmp'
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/api/v1/ocr-factura', methods=['POST'])
def ocr_factura():
    ruc_receiving_company = request.form.get('ruc_receiving_company')
    pdf_file = request.files.get('pdf_file')
    image_file = request.files.get('image_file')
    qr_code = request.form.get('qr_code')

    if not ruc_receiving_company:
        return jsonify(
            {
                'error': 'El campo ruc_receiving_company es obligatorio.',
                'code': 'REQUIRED_FIELD_MISSING'
            }
        ), 400

    if not pdf_file and not image_file:
        return jsonify(
            {
                'error': 'Debe adjuntar un archivo PDF (pdf_file) o una imagen (image_file).',
                'code': 'MISSING_REQUIRED_FILE'
            }), 400

    if pdf_file and image_file:
        return jsonify({
            'error': 'Solo puede adjuntar un archivo PDF (pdf_file) o una imagen (image_file), no ambos.',
            'code': 'MUTUALLY_EXCLUSIVE_FIELDS'
        }), 400

    if pdf_file.filename.lower().endswith('.pdf'):
        try:
            tmp_directory = os.path.join(Path(__file__).parent.absolute(), 'tmp')
            pdf_path = os.path.join(tmp_directory, pdf_file.filename)
            pdf_file.save(pdf_path)

            ocr_extractor = OcrInvoice()
            extracted_information = ocr_extractor.extract_information(pdf_path)
            os.remove(pdf_path)

            response = {
                "status": "success",
                "message": "Datos de la factura obtenidos exitosamente",
                "data": extracted_information,
                "metadata": {
                    "version": "1.0",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            }

            return jsonify(response), 200

        except Exception as e:
            return jsonify({'error': f'Error: {str(e)}'}), 500
    else:
        return jsonify({'error': 'Invalid file type. Please upload a PDF file.'})


if __name__ == '__main__':
    app.run(debug=True)
