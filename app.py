from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/api/v1/hello', methods=['GET'])
def hello():
    response = {'message': 'Hello, World!'}
    return jsonify(response)

@app.route('/api/v1/ocr-factura', methods=['POST'])
def ocr_factura():
    pass


if __name__ == '__main__':
    app.run(debug=True)
