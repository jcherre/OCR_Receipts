import re

text = """REPSOL
REPSOL COMERCIAL S.A.C.
Av. V. A. Belaunde 147, Vie Real 185, Edif. R. 12
Sanisidro-Lims
Tiki Too
AV.JOSE GALVEZ BARRENECHEA 211
Sen isidro-Lima
R.U.C.20503840121
FACTURA ELECTRONICAE
3/03/2025
13:12
F609-00010527
SENOR[ES):
HELPOESK ALL SERVICES S.A.C.
RUC:
20611901748
PLACA:
CANT.U.M. DESCRIP
P.UNIT. IMPORTE
1.000 UN NESTLE TORTA DE C
8.900
6.90
TARJETAS MASTERCARO
6.90
TOTAL DESCUENTOS
0.00
OP.EXONERAOAS
0.00
OP.INAFECTAS
0.00
OP.GRAVADAS
5.85
IGV 18%
1.05
IMPORTE TOTAL
6.90
REDONDEO
0.00
IMPORTE TOTAL A COBRAR
6.90
EFECTIVO SOLES
0.00
SON: SEIS CON 90/1OD SDLES
TIPO OE CAMBIO S/ 3.60
Cobrado pOr: MENOOZA RIOS FATIMA KATERINA
Representscion impresa de la factura electronice
Podra ser consultada en: www.repsol.pe
Autorizado mediente la R.i. Nro.0180050o01138 /
SUNAT
MUCHAS GRACIAS POR SU COMPRA"""

def extract_invoice_data(text):
    # Extract the first R.U.C. number (11 digits after 'R.U.C.')
    ruc = re.findall(r'RUC(\d{11})', text.replace('.','').replace(':','').replace('\n',''))
    ruc_number = ruc[0] #ruc.group(1) if ruc else None

    # Extract the date (format: d/m/yyyy)
    date = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', text)
    invoice_date = date.group(1) if date else None

    # Extract the invoice number (example: F609-00010527)
    invoice_number = re.search(r'F\d{3}-\d{8}', text)
    invoice_number = invoice_number.group(0) if invoice_number else None

    # Extract the total amount (next to 'IMPORTE TOTAL')
    total_amount = re.search(r'IMPORTE TOTAL\s*(\d+\.\d{2})', text)
    total = total_amount.group(1) if total_amount else None

    return {
        'ruc_number': ruc_number,
        'date': invoice_date,
        'invoice_number': invoice_number,
        'total_amount': total
    }

samay = extract_invoice_data(text)
print(samay)