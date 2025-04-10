from flask import Flask, render_template, request, jsonify
from paddleocr import PaddleOCR
import fitz  # PyMuPDF
from PIL import Image
import io
import os
import re

ocr = PaddleOCR(use_angle_cls=True, lang='en')
app = Flask(__name__)

# Route to serve the main page (frontend)
@app.route('/')
def index():
    return render_template('index.html')

def extract_text_from_image(image_path):
    result = ocr.ocr(image_path, det=True, cls=False)
    # result contains the detected text
    # You can refine this to focus on key fields, e.g., total amount, invoice number, etc.
    extracted_text = ''
    for line in result[0]:
        extracted_text += line[1][0] + '\n'
    
    return extracted_text


def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    extracted_text = ''
    
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        pix = page.get_pixmap()  # Get a pixmap (image) of the page
        img = Image.open(io.BytesIO(pix.tobytes("png")))  # Convert to PIL image
        img_path = f'page_{page_num}.png'
        img.save(img_path)
        
        # Extract text using PaddleOCR
        extracted_text += extract_text_from_image(img_path)
    
    return extracted_text


def parse_invoice_data(extracted_text):
    # This is a simple mock parser. You can customize it based on your OCR output.
    # Extract the first R.U.C. number (11 digits after 'R.U.C.')
    ruc = re.findall(r'RUC(\d{11})', extracted_text.replace('.','').replace(':','').replace('\n',''))
    ruc_number = ruc[0] #ruc.group(1) if ruc else None

    # Extract the date (format: d/m/yyyy)
    date = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', extracted_text)
    invoice_date = date.group(1) if date else None

    # Extract the invoice number (example: F609-00010527)
    invoice_number = re.search(r'F\d{3}-\d{8}', extracted_text)
    invoice_number = invoice_number.group(0) if invoice_number else None

    # Extract the total amount (next to 'IMPORTE TOTAL')
    total_amount = re.search(r'IMPORTE TOTAL\s*(\d+\.\d{2})', extracted_text)
    total = total_amount.group(1) if total_amount else None

    return {
        'ruc_number': ruc_number,
        'date': invoice_date,
        'invoice_number': invoice_number,
        'total_amount': total
    }

# Route to handle file upload and OCR processing
@app.route('/process_receipt', methods=['POST'])
def process_receipt():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files['file']

    # Handle the file type (JPG or PDF)
    if file.filename.endswith('.jpg') or file.filename.endswith('.jpeg'):
        # Save the image
        img_path = 'temp_image.jpg'
        file.save(img_path)
        extracted_text = extract_text_from_image(img_path)
    elif file.filename.endswith('.pdf'):
        # Save the PDF
        pdf_path = 'temp_receipt.pdf'
        file.save(pdf_path)
        extracted_text = extract_text_from_pdf(pdf_path)
    else:
        return jsonify({"error": "Unsupported file format"}), 400
    print(extracted_text, flush=True)
    # Process extracted text and structure it in JSON
    invoice_data = parse_invoice_data(extracted_text)
    
    return jsonify(invoice_data)

if __name__ == '__main__':
    app.run(debug=True)
