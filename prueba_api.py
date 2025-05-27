import requests
#from paddleocr import PaddleOCR

# Initialize PaddleOCR instance
#ocr = PaddleOCR()

def test_ocr_receipt():
    url = "http://localhost:8000/api/v1/ocr-receipt"
    
    # Path to the file you want to test with (PDF or image)
    file_path = "Receipts/10436083128_SanguchezLocos_F001-448.pdf"
    
    # Make sure the file exists
    with open(file_path, "rb") as f:
        files = {"files": f}
        data = {
            "seller_ruc": "20611901748"  # Replace with a realistic RUC if needed
        }
        response = requests.post(url, files=files, data=data)

    # Print and check the response
    print("Status Code:", response.status_code)
    print("Response JSON:", response.json())

    assert response.status_code == 200
    assert "data" in response.json()  # Replace "result" with expected key in your response

test_ocr_receipt()