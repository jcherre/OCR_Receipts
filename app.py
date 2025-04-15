import os

from pathlib import Path
from datetime import datetime
from module.utils import allowed_file
from flask import Flask, request, jsonify, render_template
from module.ocr.ocr_invoice import OcrInvoice


UPLOAD_FOLDER = 'tmp'
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Route to serve the main page (frontend)
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/v1/ocr-receipt', methods=['POST'])
def ocr_factura():
    ruc_receiving_company = request.form.get('ruc_receiving_company')
    #file = request.files.get('file')
    file = request.files.getlist('files')
    qr_code = request.form.get('qr_code')

    if not ruc_receiving_company:
        return jsonify(
            {
                'error': 'El campo ruc_receiving_company es obligatorio.',
                'code': 'REQUIRED_FIELD_MISSING'
            }
        ), 400

    if not file:
        return jsonify(
            {
                'error': 'Debe adjuntar un archivo PDF (pdf_file) o una imagen (image_file).',
                'code': 'MISSING_REQUIRED_FILE'
            }), 400
    print(file)
    if len(file) > 1:
        return jsonify({
            'error': 'Solo puede adjuntar un archivo PDF (pdf_file) o una imagen (image_file), no ambos.',
            'code': 'MUTUALLY_EXCLUSIVE_FIELDS'
        }), 400
    file = file[0]
    if file.filename.lower().endswith('.pdf'):
        try:
            print(Path(__file__).parent.absolute())
            tmp_directory = os.path.join(Path(__file__).parent.absolute(), 'tmp')
            pdf_path = os.path.join(tmp_directory, file.filename)
            file.save(pdf_path)

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
            print(response)
            return jsonify(response), 200

        except Exception as e:
            return jsonify({'error': f'Error: {str(e)}'}), 500
    else:
        return jsonify({'error': 'Invalid file type. Please upload a PDF file.'})


if __name__ == '__main__':
    app.run(debug=True)
