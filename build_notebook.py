"""Construye TP1_AirbnbBaires_MachineLearning.ipynb usando nbformat."""
import nbformat as nbf

nb = nbf.v4.new_notebook()
cells = []

def md(text):
    cells.append(nbf.v4.new_markdown_cell(text))

def code(text):
    cells.append(nbf.v4.new_code_cell(text))

# =========================================================================
md("""# Optimización de Precios y Ocupación en el Mercado de Alquileres Temporarios
## Análisis de Airbnb en la Ciudad Autónoma de Buenos Aires

**Data Science II — Machine Learning para la Ciencia de Datos**
**Primera Entrega — Obtención de insights a partir de visualizaciones**
""")

# =========================================================================
md("""## Abstracto: motivación y audiencia

**Motivación.** El alquiler temporario (Airbnb y plataformas similares) es hoy una de las
formas más dinámicas de explotación inmobiliaria en las grandes ciudades. A diferencia del
alquiler tradicional, el precio "correcto" de una propiedad de alquiler temporario depende de
variables muy específicas del negocio turístico: ubicación relativa a puntos de interés,
comodidades ofrecidas, reputación acumulada (reviews) y estacionalidad. Fijar un precio por
debajo o por encima del punto óptimo tiene un costo directo: precios muy altos generan baja
ocupación, precios muy bajos resignan rentabilidad.

Este proyecto analiza más de 29.000 publicaciones activas de Airbnb en la Ciudad Autónoma de
Buenos Aires (CABA), enriquecidas con datos de OpenStreetMap sobre la oferta gastronómica y de
transporte público de cada barrio, para entender **qué factores explican el precio y la
ocupación** de una propiedad.

**Audiencia.** El análisis está dirigido a **inversores inmobiliarios y gestores de
propiedades de alquiler temporario** que evalúan en qué barrio comprar/alquilar una unidad,
cómo equiparla y cómo fijar precio, sin necesidad de conocimientos técnicos de estadística o
programación.
""")

# =========================================================================
md("""## Preguntas / Hipótesis a responder

1. **¿Cómo impacta la densidad de puntos de interés (restaurantes/bares y transporte) en el
   precio base de la propiedad?** Hipótesis: los barrios con mayor densidad de oferta
   gastronómica y transporte público concentran precios promedio más altos.

2. **¿Existe una correlación directa entre las valoraciones (reviews) y la tarifa promedio
   diaria?** Hipótesis: a mayor puntaje de reviews, mayor es el precio que el mercado
   convalida (el host puede "cobrar" su reputación).

3. **¿Qué comodidades (amenities) generan un premium real en el precio de alquiler?**
   Hipótesis: comodidades de alto valor percibido (pileta, aire acondicionado, cochera) generan
   un incremento de precio significativo frente a propiedades que no las ofrecen.
""")

# =========================================================================
md("""## 1. Obtención de datos

Se combinan dos fuentes públicas:

- **Inside Airbnb** (https://insideairbnb.com): dataset detallado de publicaciones activas de
  Airbnb en CABA (scrape del 29/06/2026), descargado directamente vía HTTP en formato CSV.
- **OpenStreetMap / Overpass API** (https://overpass-api.de): API pública y gratuita que permite
  consultar puntos de interés geográficos. Se utiliza para calcular, por barrio, la cantidad de
  locales gastronómicos y de paradas/estaciones de transporte público cercanas al centroide de
  las publicaciones de ese barrio.

Los bloques de descarga guardan los datos crudos en archivos locales (`data/*.csv`) para que el
resto del notebook pueda ejecutarse sin volver a golpear las APIs.
""")

code("""import json
import time
import warnings

import numpy as np
import pandas as pd
import requests
import matplotlib.pyplot as plt
import seaborn as sns

warnings.filterwarnings("ignore")
sns.set_style("whitegrid")
pd.set_option("display.max_columns", 60)
""")

# --- 1.1 Airbnb ---------------------------------------------------------
md("""### 1.1 Dataset base: Inside Airbnb (CABA)

Se descarga el archivo detallado de publicaciones (90 columnas: precio, ubicación, huésped
máximo, amenities, puntajes de reviews, disponibilidad, etc.) directamente desde el servidor de
Inside Airbnb y se guarda una copia local.
""")

code("""AIRBNB_URL = (
    "https://data.insideairbnb.com/argentina/ciudad-aut%C3%B3noma-de-buenos-aires/"
    "buenos-aires/2026-06-29/data/listings.csv.gz"
)
LOCAL_RAW_PATH = "data/listings_raw_cache.csv.gz"

# Descarga desde la API pública. Se puede comentar esta celda luego de la primera
# ejecución y cargar directamente el archivo local guardado en LOCAL_RAW_PATH.
listings_raw = pd.read_csv(AIRBNB_URL, compression="gzip", low_memory=False)
listings_raw.to_csv(LOCAL_RAW_PATH, index=False, compression="gzip")

print(f"Publicaciones descargadas: {listings_raw.shape[0]:,}")
print(f"Columnas: {listings_raw.shape[1]}")
""")

# --- 1.2 Overpass --------------------------------------------------------
md("""### 1.2 Enriquecimiento con OpenStreetMap (Overpass API)

Para responder la Pregunta 1 (densidad de puntos de interés) se calcula, para cada uno de los
48 barrios de CABA, un centroide (promedio de latitud/longitud de las publicaciones de ese
barrio) y se consulta a la Overpass API cuántos locales gastronómicos (restaurantes, cafés,
bares, comida rápida) y puntos de transporte público (paradas de colectivo, estaciones de
subte/tren) hay en un radio de 900 metros.

Esta celda ya fue ejecutada y el resultado se guardó en `data/poi_density_by_barrio.csv`.
Como la API pública de Overpass es de uso gratuito y compartido (rate-limited), la celda de
descarga queda comentada por defecto; se puede reactivar cambiando `RUN_OVERPASS = True`.
""")

code("""RUN_OVERPASS = False  # cambiar a True para volver a consultar la API en vivo
POI_CACHE_PATH = "data/poi_density_by_barrio.csv"

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
HEADERS = {"User-Agent": "TP-DataScienceII-Airbnb-BsAs/1.0 (proyecto educativo)"}
RADIUS_M = 900


def poi_count(lat, lon, radius=RADIUS_M, max_retries=3):
    query_gastro = f\"\"\"
    [out:json][timeout:25];
    (
      node[amenity=restaurant](around:{radius},{lat},{lon});
      node[amenity=cafe](around:{radius},{lat},{lon});
      node[amenity=bar](around:{radius},{lat},{lon});
      node[amenity=fast_food](around:{radius},{lat},{lon});
    );
    out count;
    \"\"\"
    query_transporte = f\"\"\"
    [out:json][timeout:25];
    (
      node[highway=bus_stop](around:{radius},{lat},{lon});
      node[railway=station](around:{radius},{lat},{lon});
      node[station=subway](around:{radius},{lat},{lon});
    );
    out count;
    \"\"\"
    counts = {}
    for label, q in [("gastronomia", query_gastro), ("transporte", query_transporte)]:
        for attempt in range(max_retries):
            try:
                r = requests.get(OVERPASS_URL, params={"data": q}, headers=HEADERS, timeout=35)
                r.raise_for_status()
                counts[label] = int(r.json()["elements"][0]["tags"]["total"])
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    counts[label] = None
                else:
                    time.sleep(3)
        time.sleep(1.2)
    return counts


if RUN_OVERPASS:
    centroids = (
        listings_raw.groupby("neighbourhood_cleansed")[["latitude", "longitude"]]
        .mean()
        .reset_index()
        .rename(columns={"neighbourhood_cleansed": "barrio"})
    )
    rows = []
    for _, row in centroids.iterrows():
        counts = poi_count(row["latitude"], row["longitude"])
        rows.append({
            "barrio": row["barrio"],
            "poi_gastronomia_900m": counts["gastronomia"],
            "poi_transporte_900m": counts["transporte"],
        })
    poi_density = pd.DataFrame(rows)
    poi_density["poi_total_900m"] = (
        poi_density["poi_gastronomia_900m"] + poi_density["poi_transporte_900m"]
    )
    poi_density.to_csv(POI_CACHE_PATH, index=False)
else:
    poi_density = pd.read_csv(POI_CACHE_PATH)

poi_density.sort_values("poi_total_900m", ascending=False).head(10)
""")

nb["cells"] = cells
with open("TP1_AirbnbBaires_MachineLearning.ipynb", "w", encoding="utf-8") as f:
    nbf.write(nb, f)

print(f"Notebook creado con {len(cells)} celdas (parte 1/3)")
