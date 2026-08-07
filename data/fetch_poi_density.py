"""
Enriquecimiento con OpenStreetMap (Overpass API):
cuenta puntos de interes (gastronomia + transporte) en un radio de 900m
alrededor del centroide de cada barrio de CABA, usando las coordenadas
promedio de las publicaciones de Airbnb en ese barrio.

Guarda progreso incremental en poi_density_by_barrio.csv por si se corta.
"""
import csv
import os
import sys
import time

import pandas as pd
import requests

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
HEADERS = {"User-Agent": "TP-DataScienceII-Airbnb-BsAs/1.0 (proyecto educativo)"}
RADIUS_M = 900
OUT_PATH = "poi_density_by_barrio.csv"
CONNECT_TIMEOUT = 8
READ_TIMEOUT = 20
MAX_RETRIES = 2


GASTRO_AMENITIES = {"restaurant", "cafe", "bar", "fast_food"}


def poi_counts(lat, lon, radius=RADIUS_M):
    """Un solo request por barrio; clasifica por tags en el cliente."""
    query = f"""
    [out:json][timeout:20];
    (
      node[amenity=restaurant](around:{radius},{lat},{lon});
      node[amenity=cafe](around:{radius},{lat},{lon});
      node[amenity=bar](around:{radius},{lat},{lon});
      node[amenity=fast_food](around:{radius},{lat},{lon});
      node[highway=bus_stop](around:{radius},{lat},{lon});
      node[railway=station](around:{radius},{lat},{lon});
      node[station=subway](around:{radius},{lat},{lon});
    );
    out tags;
    """
    for attempt in range(MAX_RETRIES):
        try:
            r = requests.get(
                OVERPASS_URL,
                params={"data": query},
                headers=HEADERS,
                timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
            )
            r.raise_for_status()
            elements = r.json()["elements"]
            gastro = sum(1 for e in elements if e.get("tags", {}).get("amenity") in GASTRO_AMENITIES)
            transporte = len(elements) - gastro
            return gastro, transporte
        except Exception as e:
            print(f"    intento {attempt+1} fallo: {e}", flush=True)
            time.sleep(4)
    return None, None


def main():
    listings = pd.read_csv("listings_raw_cache.csv.gz", compression="gzip", low_memory=False)
    centroids = (
        listings.groupby("neighbourhood_cleansed")[["latitude", "longitude"]]
        .mean()
        .reset_index()
        .rename(columns={"neighbourhood_cleansed": "barrio"})
    )

    done = set()
    if os.path.exists(OUT_PATH):
        prev = pd.read_csv(OUT_PATH)
        done = set(prev["barrio"])
        print(f"Reanudando: {len(done)} barrios ya resueltos", flush=True)

    is_new_file = not os.path.exists(OUT_PATH)
    with open(OUT_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if is_new_file:
            writer.writerow([
                "barrio", "lat_centroide", "lon_centroide",
                "poi_gastronomia_900m", "poi_transporte_900m", "poi_total_900m",
            ])

        for i, row in centroids.iterrows():
            if row["barrio"] in done:
                continue
            print(f"[{i+1}/{len(centroids)}] {row['barrio']}", flush=True)
            gastro, transporte = poi_counts(row["latitude"], row["longitude"])
            total = None if gastro is None else gastro + transporte
            writer.writerow([row["barrio"], row["latitude"], row["longitude"], gastro, transporte, total])
            f.flush()
            time.sleep(1.5)

    print("Listo.", flush=True)


if __name__ == "__main__":
    main()
