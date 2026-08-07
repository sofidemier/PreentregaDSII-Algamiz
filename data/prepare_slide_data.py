"""Calcula todos los numeros/series que usa la presentacion ejecutiva y los
vuelca a slide_data.json, para que el generador de PPTX (Node/pptxgenjs) no
tenga que repetir logica de pandas."""
import json

import pandas as pd

df = pd.read_csv("airbnb_baires_analitico.csv")
poi = pd.read_csv("poi_density_by_barrio.csv")

data = {}

# --- metadata general ---
data["n_filas"] = int(len(df))
data["n_cols"] = int(df.shape[1])
data["n_barrios"] = int(df["barrio"].nunique())
data["n_filas_crudo"] = 29685
data["n_cols_crudo"] = 90

room_type_pct = (df["room_type"].value_counts(normalize=True) * 100).round(1)
data["room_type_pct"] = room_type_pct.to_dict()

data["precio_medio"] = round(float(df["price_clean"].mean()))
data["precio_mediana"] = round(float(df["price_clean"].median()))
data["ocupacion_media_pct"] = round(float(df["ocupacion_pct_365d"].mean()), 1)
data["n_amenities_media"] = round(float(df["n_amenities"].mean()), 1)
data["pct_missing_reviews"] = round(float(df["review_scores_rating"].isna().mean() * 100), 1)

# --- Pregunta 1: POI density vs precio (a nivel barrio) ---
precio_barrio = (
    df.groupby("barrio")
    .agg(precio_promedio=("price_clean", "mean"), publicaciones=("price_clean", "size"))
    .reset_index()
)
merged = precio_barrio.merge(poi, on="barrio", how="inner").dropna(subset=["poi_total_900m"])
data["n_barrios_con_poi"] = int(len(merged))
data["corr_poi_precio"] = round(float(merged["poi_total_900m"].corr(merged["precio_promedio"])), 2)
data["scatter_poi_precio"] = [
    {"barrio": r["barrio"], "x": float(r["poi_total_900m"]), "y": float(r["precio_promedio"])}
    for _, r in merged.iterrows()
]

# --- Pregunta 2: reviews vs precio ---
con = df[df["review_scores_rating"].notna()].copy()
data["corr_reviews_precio"] = round(float(con["review_scores_rating"].corr(con["price_clean"])), 2)
data["corr_ubicacion_precio"] = round(
    float(con["review_scores_location"].corr(con["price_clean"])), 2
)
bins = [0, 4.5, 4.8, 4.95, 5.01]
labels = ["< 4.5", "4.5 - 4.8", "4.8 - 4.95", "4.95 - 5.0"]
con["bin"] = pd.cut(con["review_scores_rating"], bins=bins, labels=labels, right=False)
bin_stats = con.groupby("bin", observed=True)["price_clean"].mean().round(0)
data["reviews_bins"] = {str(k): float(v) for k, v in bin_stats.items()}

# --- Pregunta 3: premium por amenities ---
amenities_cols = {
    "tiene_wifi": "Wifi",
    "tiene_pileta": "Pileta",
    "tiene_aire_acondicionado": "Aire acondicionado",
    "tiene_cochera": "Cochera",
    "tiene_cocina": "Cocina",
    "tiene_ascensor": "Ascensor",
    "tiene_gimnasio": "Gimnasio",
    "acepta_mascotas": "Acepta mascotas",
}
premium = []
for col, label in amenities_cols.items():
    con_p = df.loc[df[col], "price_clean"].mean()
    sin_p = df.loc[~df[col], "price_clean"].mean()
    premium.append({
        "amenity": label,
        "premium_pct": round(float((con_p / sin_p - 1) * 100), 1),
        "penetracion_pct": round(float(df[col].mean() * 100), 1),
    })
premium.sort(key=lambda d: d["premium_pct"], reverse=True)
data["amenities_premium"] = premium

# --- contexto: top barrios por publicaciones ---
top_barrios = (
    df.groupby("barrio")["price_clean"]
    .agg(["mean", "count"])
    .sort_values("count", ascending=False)
    .head(8)
    .reset_index()
)
data["top_barrios"] = [
    {"barrio": r["barrio"], "precio_promedio": round(float(r["mean"])), "n": int(r["count"])}
    for _, r in top_barrios.iterrows()
]

with open("slide_data.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("slide_data.json generado")
print(json.dumps({k: v for k, v in data.items() if not isinstance(v, list)}, indent=2, ensure_ascii=False))
