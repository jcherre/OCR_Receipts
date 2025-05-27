import os
import shutil
import module.utils as ut

from pathlib import Path
from flask import Flask, request, jsonify, render_template
from module.ocr.ocr_invoice import OcrInvoice

TEMP_FOLDER = os.path.join(Path(__file__).parent, 'tmp')
IMAGE_FOLDER = os.path.join(Path(__file__).parent, 'img')
SAVED_FOLDER = os.path.join(Path(__file__).parent, 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = TEMP_FOLDER
app.config['IMAGE_FOLDER'] = IMAGE_FOLDER
app.config['SAVED_FOLDER'] = SAVED_FOLDER

ocr_extractor = OcrInvoice()

@app.route('/api/v1/ocr-receipt', methods=['POST'])
def ocr_factura():
    seller_ruc = request.form.get('seller_ruc')
    files = request.files.getlist('files')
    qr_code = request.form.get('qr_code')

    if not seller_ruc:
        return ut.build_api_response_format(
            status='error',
            message='El campo seller_ruc es obligatorio.',
            body='REQUIRED_FIELD_MISSING'
        )

    #if not pdf_file and not image_file:
    if not files:
        return ut.build_api_response_format(
            status='error',
            message='Debe adjuntar un archivo PDF (pdf_file) o una imagen (image_file).',
            body='MISSING_REQUIRED_FILE'
        )
    print(files)
    if len(files) > 1:
    #if pdf_file and image_file:
        return ut.build_api_response_format(
            status='error',
            message='Solo puede adjuntar un archivo PDF (pdf_file) o una imagen (image_file), no ambos.',
            body='MUTUALLY_EXCLUSIVE_FIELDS'
        )
    file = files[0]
    print(file)

    if file.filename.lower().endswith('.pdf'):
        try:
            pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            saved_path = os.path.join(app.config['SAVED_FOLDER'], file.filename)
            file.save(pdf_path)
            extracted_information = ocr_extractor.extract_information(
                image_content=pdf_path,
                seller_ruc=seller_ruc,
                type_document='pdf'
            )

            if 'error' in extracted_information.keys():
                return ut.build_api_response_format(
                    status="error",
                    message=extracted_information['error'],
                    body=extracted_information['code']
                )
            else:
                shutil.copy(pdf_path, saved_path)
                return ut.build_api_response_format(
                    status="success",
                    message="Datos de la factura obtenidos exitosamente",
                    body=extracted_information
                )

        except Exception as e:
            return jsonify({'error': f'Error: {str(e)}'}), 500
        finally:
            os.remove(pdf_path)
    elif ut.allowed_file(filename=file.filename, allowed_extensions=ALLOWED_EXTENSIONS):
        try:
            image_path = os.path.join(app.config['IMAGE_FOLDER'], file.filename)
            saved_path = os.path.join(app.config['SAVED_FOLDER'], file.filename)
            file.save(image_path)
            if ut.evaluate_sharpness(image_path):
                extracted_information = ocr_extractor.extract_information(
                    image_content=image_path,
                    seller_ruc=seller_ruc,
                    type_document='image'
                )
                if 'error' in extracted_information.keys():
                    return ut.build_api_response_format(
                        status="error",
                        message=extracted_information['error'],
                        body=extracted_information['code']
                    )
                else:
                    shutil.copy(image_path, saved_path)
                    return ut.build_api_response_format(
                        status="success",
                        message="Datos de la factura obtenidos exitosamente",
                        body=extracted_information
                    )
            else:
                return ut.build_api_response_format(
                    status='error',
                    message='La imagen cargada no cumple con los estándares de nitidez establecidos',
                    body='IMAGE_QUALITY_LOW'
                )
        except Exception as e:
            return jsonify({'error': f'Error: {str(e)}'}), 500
        finally:
            os.remove(image_path)
    else:
        return ut.build_api_response_format(
            status='error',
            message='El tipo de archivo es inválido. Por favor suba un archivo PDF, PNG o JPG',
            body='INVALID_FILE_TYPE'
        )

@app.route('/')
def index():
#    return "API running successfully!"
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=1100, debug=True)
