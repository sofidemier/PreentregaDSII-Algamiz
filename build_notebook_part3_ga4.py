"""Agrega el anexo de conexion con Google Analytics 4 (requisito de catedra,
mencionado en clase, no escrito en la consigna) al notebook ya generado."""
import nbformat as nbf

nb = nbf.read("TP1_AirbnbBaires_MachineLearning.ipynb", as_version=4)
cells = nb["cells"]

def md(text):
    cells.append(nbf.v4.new_markdown_cell(text))

def code(text):
    cells.append(nbf.v4.new_code_cell(text))

md("""## Anexo: Conexión con Google Analytics 4 (requisito de cátedra)

Este bloque no forma parte del análisis de Airbnb (que usa Inside Airbnb + OpenStreetMap, ver
Sección 1). Se incluye para acreditar el requisito, mencionado en clase, de establecer una
conexión funcional con **Google Analytics 4** desde el notebook.

Como este proyecto no cuenta con un sitio o app propia instrumentada con GA4, la conexión se
realiza contra la **exportación pública de GA4 a BigQuery** que Google publica para fines
educativos (`bigquery-public-data.ga4_obfuscated_sample_ecommerce`): son eventos reales de GA4
(page_view, session_start, add_to_cart, purchase, etc.) de una tienda de e-commerce, con la
misma estructura que exporta cualquier propiedad de Google Analytics 4 real.

**Para ejecutar esta celda:**
1. Se necesita un proyecto de Google Cloud (gratuito, sin tarjeta) con la API de BigQuery
   habilitada — ya está creado: `tp-ds2-ga4-airbnb`.
2. Al correr la celda en Google Colab, `auth.authenticate_user()` abre un login interactivo
   con tu cuenta de Google. Fuera de Colab (por ejemplo, Jupyter local) la celda detecta el
   entorno y no intenta autenticar.
""")

code("""try:
    from google.colab import auth
    IN_COLAB = True
except ImportError:
    IN_COLAB = False

GA4_PROJECT_ID = "tp-ds2-ga4-airbnb"  # proyecto de Google Cloud (Zona de pruebas, sin facturacion)

if IN_COLAB:
    auth.authenticate_user()
    from google.cloud import bigquery

    client = bigquery.Client(project=GA4_PROJECT_ID)

    query_ga4 = \"\"\"
    SELECT
      event_date,
      event_name,
      COUNT(*) AS eventos
    FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_20210131`
    GROUP BY event_date, event_name
    ORDER BY eventos DESC
    LIMIT 10
    \"\"\"
    ga4_eventos = client.query(query_ga4).to_dataframe()
    print("Conexion con Google Analytics 4 (BigQuery) establecida correctamente.")
    display(ga4_eventos)
else:
    print(
        "Esta celda se conecta a Google Analytics 4 via BigQuery y requiere un entorno "
        "de Google Colab (usa google.colab.auth para el login interactivo). "
        "Ejecutar este notebook en Colab para ver la conexion en accion."
    )
""")

md("""**Lectura:** la tabla muestra los 10 tipos de evento de GA4 más frecuentes en un día de
la tienda de referencia (page_view, user_engagement, scroll, session_start, etc.), confirmando
que la conexión con la API/exportación de Google Analytics 4 está establecida y devuelve datos
reales.
""")

nb["cells"] = cells
with open("TP1_AirbnbBaires_MachineLearning.ipynb", "w", encoding="utf-8") as f:
    nbf.write(nb, f)

print(f"Notebook actualizado con anexo GA4. Total de celdas: {len(cells)}")
