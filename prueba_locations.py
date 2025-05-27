import re
import datetime
import numpy as np
import module.ocr.utils as ut
import json

# Path to your JSON file
file_path = "output/1748306268_5509_res.json"

# Read and parse it
with open(file_path, "r", encoding="utf-8") as f:
    result_json = json.load(f)

word_and_locations = [[line, box] for box, line in zip(result_json.get('rec_boxes'), result_json.get('rec_texts')) if line not in ('s/', 'S/.', 'S/', '$/', '$/.')]
extracted_word = [line for line in result_json.get('rec_texts') if line not in ('s/', 'S/.', 'S/', '$/', '$/.')]
words_joined = " ".join(extracted_word).replace(
            " - ", "-"
        )
print(words_joined)

set_prices = {
    "IGV": [None, 0.00],
    "total_descuentos": [None, 0.00],
    "OP.Exoneradas": [None, 0.00],
    "OP.Inafectas": [None, 0.00],
    "OP.Gravadas": [None, 0.00],
    "OP.Gratuita": [None, 0.00],
    "ICBPER": [None, 0.00],
    "otros_cargos": [None, 0.00],
    "importe_total": [None, 0.00]
}
currency_pattern = r"\d{1,3}(?:,\d{3})*\.\d{2,}"
currency_found = re.findall(currency_pattern, words_joined)

if not currency_found:
    print("Return Not Found")
    exit()

found_indices = set()
for element_to_search in currency_found:
    for index, element in enumerate(extracted_word):
        if element_to_search in element:
            found_indices.add(index)
found_indices = sorted(list(found_indices))

rows_prices = []
cols_prices = []
height_tolerance = 25.0
width_tolerance = 20.0
new_line_tolerance = 60.0

for index in found_indices:
    #Version 1
    """price = (extracted_word[index]
                .replace('S', '')
                .replace('$', '')
                .replace('/.', '')
                .replace('/', '')
                .replace('[', '')
                .replace(']', '')
                .replace(',', '').strip())"""
    #Version 2
    check_pattern = r"(?<!\d)[^\w\d]?(\d+(?:[\.,]\d+)?)"
    matches = re.findall(check_pattern, extracted_word[index])
    if len(matches) > 0:
        price = matches[-1].strip()
    
    if ut.is_number(price): #or re.search(r'\d+(?:\.\d+)?%', extracted_word[index].strip()):
        match = re.search(r'\d+(?:\.\d+)?%', extracted_word[index].strip())
        if match:
            # Look at the rest of the string after the match
            rest = extracted_word[index].strip()[match.end():]
            # Check if there are any other numbers after it
            if not re.search(r'\d', rest):
                continue
    else:
        continue

    row = [price]
    y1_coord = word_and_locations[index][1][1]
    row_candidates = []

    for i in range(len(word_and_locations)):
        if ((i != index or (i == index and word_and_locations[i][0].replace('S', '')
                        .replace('$', '')
                        .replace('/.', '')
                        .replace('/', '')
                        .replace('[', '')
                        .replace(']', '')
                        .replace(',', '').strip() != price))
            and abs(word_and_locations[i][1][1] - y1_coord) < height_tolerance
            and len(word_and_locations[i][0].strip()) < 40):
            row_candidates.append((abs(word_and_locations[i][1][1] - y1_coord), word_and_locations[i][0]))
            #break
    if len(row_candidates) > 0:
        sorted_list = sorted(row_candidates, key=lambda x: x[0], reverse=True)
        row.append([item[1] for item in sorted_list])

    if len(row) > 1:
        rows_prices.append(row)

    col = [price]
    y1_coord = word_and_locations[index][1][1]
    x2_coord = word_and_locations[index][1][2]
    col_candidates = []

    for i in range(len(word_and_locations)):
        if (i != index
            and abs(word_and_locations[i][1][2] - x2_coord) < width_tolerance
            and len(word_and_locations[i][0].strip()) < 40
            and 0 <= (y1_coord - word_and_locations[i][1][1]) < new_line_tolerance):
            col_candidates.append((abs(word_and_locations[i][1][2] - x2_coord), word_and_locations[i][0]))
            #break 
    if len(col_candidates) > 0:
        sorted_list = sorted(col_candidates, key=lambda x: x[0], reverse=True)
        col.append([item[1] for item in sorted_list])

    if len(col) > 1:
        cols_prices.append(col)

if rows_prices or cols_prices:
    for price, label_candidates in rows_prices:
        if price == '51.00':
            print('aca')
        set_prices = ut.assign_price_v2(price, label_candidates, set_prices)
    
    for price, label_candidates in cols_prices:
        set_prices = ut.assign_price_v2(price, label_candidates, set_prices)
    
    if set_prices['importe_total'][0] is None:
        set_prices['importe_total'] = [str(max([float(currency_arr) for currency_arr in currency_found])), 0.00]
        if set_prices['IGV'][0] is None:
            set_prices['IGV'] = [str(min([float(currency_arr) for currency_arr in currency_found if float(currency_arr) > 0.0])), 0.00]

else:
    for word in extracted_word:
        prices = re.findall(currency_pattern, word.replace('18.00%', ''))
        if prices:
            price = prices[0]
            set_prices = ut.assign_price(price, word, set_prices)

if set_prices['otros_cargos'][0] is None:
    for index_word in range(len(extracted_word)):
        if 'CARGO' in extracted_word[index_word].upper():
            price_currently = re.findall(currency_pattern, extracted_word[index_word + 1])
            if price_currently:
                set_prices['otros_cargos'] = [price_currently[0], 0.00]
            else:
                set_prices['otros_cargos'] = ['0.00', 0.00]