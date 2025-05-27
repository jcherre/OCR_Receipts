import re
import datetime
import numpy as np
import module.ocr.utils as ut
import json

# Path to your JSON file
file_path = "output/1748295527_5509_res.json"

# Read and parse it
with open(file_path, "r", encoding="utf-8") as f:
    result_json = json.load(f)

word_and_locations = [[line, box] for box, line in zip(result_json.get('rec_boxes'), result_json.get('rec_texts')) if line not in ('s/', 'S/.', 'S/', '$/', '$/.')]
extracted_word = [line for line in result_json.get('rec_texts') if line not in ('s/', 'S/.', 'S/', '$/', '$/.')]
words_joined = " ".join(extracted_word).replace(
            " - ", "-"
        )
print(words_joined)

folio_pattern = r"([A-Z0-9]+)-\s*(\d+)"
found_series_correlative = re.findall(folio_pattern, words_joined)
found_series_correlative = [element for element in found_series_correlative if len(element[0]) == 4]
if len(found_series_correlative) == 0:
    correlative_and_serie = ['', '']
    for found_word in extracted_word:
        if 'SERIE' in found_word.upper():
            pattern_serie = "([A-Z0-9]+)"
            founded_series = re.findall(pattern_serie, found_word)
            founded_series = [serie for serie in founded_series if len(serie) == 4]
            correlative_and_serie[0] = founded_series[0]
        if 'CORRELATIVO' in found_word.upper():
            pattern_correlative = "(\d+)"
            correlatives = re.findall(pattern_correlative, found_word)
            correlatives = [correlative for correlative in correlatives if len(correlative) > 3]
            correlative_and_serie[1] = correlatives[0]
    
    if correlative_and_serie == ['', '']:
        height_tolerance = 20.0
        escape = False
        for found_word in word_and_locations:
            if escape:
                break
            row = [(found_word[1][0], found_word[0])]
            y1_coord = found_word[1][1]
            for i in range(len(word_and_locations)):
                if (word_and_locations[i][0] != found_word[0]) and (abs(word_and_locations[i][1][1] - y1_coord) < height_tolerance):
                    row.append((abs(word_and_locations[i][1][0] - y1_coord), word_and_locations[i][0].strip()))
            sorted_list = sorted(row, key=lambda x: x[0], reverse=False)
            result = "".join(map(lambda x: x[1], sorted_list))
            found_series_correlative_line = re.findall(folio_pattern, result)
            if len(found_series_correlative_line) > 0:
                for element in found_series_correlative_line:
                    if len(element[0]) >= 4:
                        correlative_and_serie = [element[0][:4], element[1]]
                        escape = True
                        break

    found_series_correlative.append(correlative_and_serie)

print(found_series_correlative)