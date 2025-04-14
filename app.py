import os

from pathlib import Path
from typing import Optional

from flask import Flask, request, jsonify
from module.ocr.ocr_incoice import OcrInvoice

app = Flask(__name__)

@app.route('/api/v1/ocr-factura', methods=['POST'])
def ocr_factura():
    request_key = [
        {
            'key': 'ruc_receiving_company',
            'required': True
        },
        {
            'key': 'pdf_file',
            'required': True
        },
        {
            'key': 'image_file',
            'required': False
        },
        {
            'key': 'qr_code',
            'required': False
        }
    ]

    data = request.form

    ruc_receiving_company = request.files['ruc_receiving_company']


    if 'pdf_file' not in request.files:
        return jsonify({'error': 'No PDF file provided'}), 400

    pdf_file = request.files['pdf_file']
    if pdf_file.filename.lower().endswith('.pdf'):
        try:
            tmp_directory = os.path.join(Path(__file__).parent.absolute(), 'tmp')
            pdf_path = os.path.join(tmp_directory, pdf_file.filename)
            pdf_file.save(pdf_path)

            # I-process ang PDF
            ocr_extractor = OcrInvoice()
            response = ocr_extractor.extract_information(pdf_path)

            # Tanggalin ang temporary file
            os.remove(pdf_path)
            return jsonify(response)

        except Exception as e:
            return jsonify({'error': f'Error: {str(e)}'}), 500
    else:
        return jsonify({'error': 'Invalid file type. Please upload a PDF file.'})


if __name__ == '__main__':
    app.run(debug=True)
