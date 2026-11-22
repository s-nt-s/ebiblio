# ebiblio-client

Cliente Python sin dependencias externas para realizar búsquedas en catálogos
con el formulario web de eBiblio y convertir los resultados HTML en objetos
Python.

## Uso

```python
from ebiblio import EbiblioClient, SearchQuery

catalog = EbiblioClient("https://madrid.ebiblio.es/")

# Los nombres de filtros coinciden con los campos del formulario de búsqueda.
query = SearchQuery(
    keywords="Mabuse",
    author="Norbert Jacques",
    language="spa",
    nature="ebook",
    availability="available",
)
page = catalog.search(query)

for book in page.items:
    print(book.title, book.authors, book.url)
    for medium in book.media:
        print(medium.format, medium.availability, medium.borrow_url)

print("Página siguiente:", page.next_page_url)

# Recupera todas las páginas (máximo 100 por defecto).
all_results = catalog.search_all(query, max_pages=10)
```

`search()` devuelve `SearchResults`, que incluye `items`, `current_page`, los
números de página visibles y `next_page_url`. Cada `SearchResult` incluye título,
tipo, URL, identificador, portada, descripción, colaboradores y formatos
disponibles. Los nombres de los colaboradores se agrupan por etiqueta del sitio
(por ejemplo, `autor`, `director` o `actores principales`).
Los modelos son `NamedTuple` y sus colecciones se exponen como tuplas. Cada
colaborador es un `Contributor` con `role` y `names`, para evitar modificaciones
accidentales de los resultados devueltos.

Los filtros admitidos son `isbn`, `author`, `narrator`, `director`, `actor`,
`publisher`, `collection_title`, `issued_on_range`, `language`, `audience`,
`category`, `nature`, `medium` y `availability`. También se pueden usar
`sort_by`. Se pasan como campos de `SearchQuery`; `keywords` contiene las
palabras clave y `q` es su alias. Para limitar a títulos disponibles, usa
`availability="available"`.

## Línea de comandos

Tras instalar el paquete, se puede invocar `ebiblio` con la URL del catálogo y
las palabras clave. Los filtros corresponden al formulario web:

```sh
ebiblio https://madrid.ebiblio.es/ Mabuse --author "Norbert Jacques" --language spa
ebiblio https://madrid.ebiblio.es/ --category fiction --available --json
ebiblio https://madrid.ebiblio.es/ homes --all --max-pages 5
```

`--page` selecciona una página; `--all` recorre las páginas siguientes hasta
`--max-pages`. `--json` emite los resultados estructurados. Consulta todas las
opciones con `ebiblio --help`.

## Servicio HTTP JSON

Se incluye un servidor basado únicamente en la biblioteca estándar. Recibe una
petición `GET /search` cuyos parámetros coinciden con los campos de
`SearchQuery` y devuelve un array JSON plano con los resultados de todos los
catálogos configurados. Define `EBIBLIO_URL` como una lista de URLs separadas
por espacios:

```sh
export EBIBLIO_URL="https://madrid.ebiblio.es/ https://castillayleon.ebiblio.es/ https://murcia.ebiblio.es/"
python -m ebiblio.server
```

Por defecto escucha solo en `127.0.0.1:8000`, consulta hasta 10 páginas por
catálogo y acepta, por ejemplo:

```sh
curl --get 'http://127.0.0.1:8000/search' \
    --data-urlencode 'keywords=Fun Home' \
    --data-urlencode 'language=spa'
```

Se pueden ajustar `EBIBLIO_HOST`, `EBIBLIO_PORT` y `EBIBLIO_MAX_PAGES` (máximo
100). No se acepta una URL de catálogo desde la petición: solo se consultan las
URLs configuradas en `EBIBLIO_URL`. Mantén el servidor en localhost o protégelo
con autenticación y límites de tráfico antes de exponerlo a una red pública.

## Instalación local

Requiere Python 3.10 o posterior. Desde este directorio:

```sh
python -m pip install .
```

La implementación solo usa la biblioteca estándar de Python. La consulta sí
requiere acceso de red al sitio elegido y respeta los códigos HTTP y límites
del propio catálogo; no realiza préstamos ni inicia sesión.

## Pruebas

```sh
PYTHONPATH=src python -m unittest discover -s tests -v
```

## Construir y publicar

El script `publish.sh` ejecuta las pruebas, construye y valida los
paquetes. Por defecto sube a TestPyPI; `--pypi` selecciona la publicación real
y solicita confirmación. Usa `--dry-run` para validar todo sin subir nada:

```sh
bash publish.sh --dry-run
bash publish.sh --testpypi
bash publish.sh --pypi
```

Twine solicita las credenciales de forma interactiva. Para PyPI, utiliza
`__token__` como usuario y escribe el token en la solicitud de contraseña; no
lo añadas al repositorio ni a la línea de comandos.