import os
import module.utils as ut

from pathlib import Path
from flask import Flask, request, jsonify
from module.ocr.ocr_incoice import OcrInvoice

TEMP_FOLDER = os.path.join(Path(__file__).parent, 'tmp')
IMAGE_FOLDER = os.path.join(Path(__file__).parent, 'img')
ALLOWED_EXTENSIONS = {'png', 'jpg'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = TEMP_FOLDER
app.config['IMAGE_FOLDER'] = IMAGE_FOLDER


@app.route('/api/v1/ocr-factura', methods=['POST'])
def ocr_factura():
    seller_ruc = request.form.get('seller_ruc')
    pdf_file = request.files.get('pdf_file')
    image_file = request.files.get('image_file')
    qr_code = request.form.get('qr_code')
    ocr_extractor = OcrInvoice()
    if not seller_ruc:
        return ut.build_api_response_format(
            status='error',
            message='El campo seller_ruc es obligatorio.',
            body='REQUIRED_FIELD_MISSING'
        )

    if not pdf_file and not image_file:
        return ut.build_api_response_format(
            status='error',
            message='Debe adjuntar un archivo PDF (pdf_file) o una imagen (image_file).',
            body='MISSING_REQUIRED_FILE'
        )

    if pdf_file and image_file:
        return ut.build_api_response_format(
            status='error',
            message='Solo puede adjuntar un archivo PDF (pdf_file) o una imagen (image_file), no ambos.',
            body='MUTUALLY_EXCLUSIVE_FIELDS'
        )

    if pdf_file:
        if pdf_file.filename.lower().endswith('.pdf'):
            try:
                pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_file.filename)
                pdf_file.save(pdf_path)
                extracted_information = ocr_extractor.extract_information(
                    image_content=pdf_path,
                    seller_ruc=seller_ruc,
                    type_document='pdf'
                )
                os.remove(pdf_path)

                if 'error' in extracted_information.keys():
                    return ut.build_api_response_format(
                        status="error",
                        message=extracted_information['error'],
                        body=extracted_information['code']
                    )
                else:
                    return ut.build_api_response_format(
                        status="success",
                        message="Datos de la factura obtenidos exitosamente",
                        body=extracted_information
                    )

            except Exception as e:
                return jsonify({'error': f'Error: {str(e)}'}), 500
        else:
            return jsonify({'error': 'Invalid file type. Please upload a PDF file.'})

    elif image_file:
        if ut.allowed_file(filename=image_file.filename, allowed_extensions=ALLOWED_EXTENSIONS):
            image_path = os.path.join(app.config['IMAGE_FOLDER'], image_file.filename)
            image_file.save(image_path)
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


if __name__ == '__main__':
    app.run(debug=True)
