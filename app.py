import os

from pathlib import Path
from flask import Flask, request, jsonify
from module.ocr_incoice import OcrInvoice

app = Flask(__name__)

@app.route('/api/v1/hello', methods=['GET'])
def hello():
    response = {'message': 'Hello, World!'}
    return jsonify(response)

@app.route('/api/v1/ocr-factura', methods=['POST'])
def ocr_factura():
    if 'pdf_file' not in request.files:
        return jsonify({'error': 'No PDF file provided'}), 400
    pdf_file = request.files['pdf_file']
    if pdf_file.filename.lower().endswith('.pdf'):
        try:
            # I-save ang file sa isang temporary location
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
