import os
import json

from pathlib import Path
from module.ocr.ocr_incoice import OcrInvoice

def comparar_json(ruta_json_test, ruta_json_correcto):
    try:
        with open(ruta_json_test, 'r') as archivo_test, open(ruta_json_correcto, 'r') as archivo_correcto:
            datos_test = json.load(archivo_test)
            datos_correcto = json.load(archivo_correcto)

        return datos_test, datos_correcto
    except FileNotFoundError:
        print("Error: Uno o ambos archivos JSON no fueron encontrados.")
        return
    except json.JSONDecodeError:
        print("Error: Uno o ambos archivos no son JSON válidos.")
        return

if __name__ == '__main__':
    recipients = os.path.join(Path(__file__).parents[1], 'Receipts')
    ocr_invoice = OcrInvoice()

    list_documents = os.listdir(recipients)
    final_response = {}
    for document in list_documents:
        pdf_path = os.path.join(recipients, document)
        ruc_issuer = document.split('-')[0]
        response = ocr_invoice.extract_information(pdf_path, ruc_issuer, 'pdf')
        final_response[document] = response

    with open('./ocr_response.json', 'w') as archivo_json:
        json.dump(final_response, archivo_json, indent=4)


    datos_test, datos_correctos = comparar_json('./ocr_response.json', './correct_response.json')

    compare_testing_files = {}
    for key, value in datos_test.items():
        count = 0
        missmatch = []
        for category in datos_test[key]:
            if category == 'invoice_details':
                for invoice_key, invoice_value in datos_test[key]['invoice_details'].items():
                    if datos_correctos[key]['invoice_details'][invoice_key] != invoice_value:
                        missmatch.append('invoice_details.' + invoice_key)

            else:
                if datos_correctos[key][category] != datos_test[key][category]:
                    missmatch.append(category)

        if len(missmatch) == 0:
            compare_testing_files[key] = {
                "test": "PASS"
            }
        else:
            compare_testing_files[key] = {
                "test": "FAIL",
                "mismatch": missmatch
            }


    with open('test_result.json', 'w') as archivo_json:
        json.dump(compare_testing_files, archivo_json, indent=4)

    # Métricas
    total_documents = len(compare_testing_files.keys())
    total_pass = len([value for value in compare_testing_files.values() if value['test'] == 'PASS'])
    print(f"La eficiencia de extracción es de: {total_pass*100/total_documents}")