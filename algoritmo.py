from itertools import combinations

def encontrar_sumas_igual_maximo(arr, maximo):
    try:
        numeros = [float(x) for x in arr]
    except ValueError:
        return None, "Error: El array contiene elementos no numéricos."

    if not numeros:
        return None, "Error: El array está vacío."

    n = len(numeros)
    combinaciones_suma_maximo = []

    for r in range(1, n):
        for combo_indices in combinations(range(n), r):
            subconjunto = [arr[i] for i in combo_indices]
            suma_subconjunto = sum(numeros[i] for i in combo_indices)

            if abs(suma_subconjunto - maximo) < 0.1:
                combinaciones_suma_maximo.append(subconjunto)

    return maximo, combinaciones_suma_maximo


maximo = 49.0
mi_array = [4.46, 23.0, 26.0, 44.55]
max_valor, combinaciones = encontrar_sumas_igual_maximo(mi_array, maximo)

