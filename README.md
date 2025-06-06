# OCR_Receipts

El repo consiste en una implementación de PaddleOCRv5 para extraer información de comprobantes de pago en formatos de una imagen o un fichero PDF. El PDF es convertido a imagen y, una vez leído por el modelo, se extraen los siguientes campos utilizando expresiones regulares y lógica de similitud Fuzzy con la librería `rapidfuzz`:
* RUC del emisor
* Tipo de documento
* Serie y correlativo
* Fecha de emisión
* Operaciones Gravadas
* Operaciones Inafectas
* Operaciones Gratuitas
* Total descuentos
* IGV
* ICBPER
* Otros cargos
* Importe total

## Despliegue

Se utiliza un archivo docker-compose para construir y desplegar la imagen mediante el siguiente comando:

```
docker-compose up --build
```

Se deben declarar las siguientes variables de entorno previamente:

```
PORT_OCR: Puerto que se utilizará para exponer la API
UPLOAD_FOLDER: Folder de destino en el que se guardarán los archivos localmente
HEIGHT_TOLERANCE_COR: Toleracian en píxeles para considerar dos rectángulos de detección como una misma línea para la lectura de la serie y correlativo (default 20.0)
HEIGHT_TOLERANCE: Toleracian en píxeles para considerar dos rectángulos de detección como una misma línea para la lectura de los importes(default 25.0)
WIDTH_TOLERANCE: Toleracian en píxeles para considerar dos rectángulos de detección como una misma columna para la lectura de los importes (default 20.0)
NEW_LINE_TOLERANCE: Toleracian en píxeles para considerar una nueva línea en la lectura de los importes (default 80.0)
MAX_STRING_LENGTH: Máximo largo de la cadena a incluir en la lectura de los importes (default 40)
SCORE_CUTOFF_ROWS: Puntuación mínima de la lógica de similitud fuzzy para considerar un match al analizar filas (default 65.0)
SCORE_CUTOFF_COLS: Puntuación mínima de la lógica de similitud fuzzy para considerar un match al analizar columnas (default 70.0)
```

Para evitar compartir la fuente se pueden utilizar los siguientes comandos para publicar la imagen en un repositorio y desplegarla remotamente:
```
# En el servidor de desarrollo
docker tag mi_imagen mi_usuario/mi_imagen:latest
docker push mi_usuario/mi_imagen:latest
# En el servidor remoto
docker pull mi_usuario/mi_imagen:latest
```
