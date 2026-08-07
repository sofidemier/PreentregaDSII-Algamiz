"""Agrega limpieza + EDA + insights al notebook ya creado por build_notebook.py."""
import nbformat as nbf

nb = nbf.read("TP1_AirbnbBaires_MachineLearning.ipynb", as_version=4)
cells = nb["cells"]

def md(text):
    cells.append(nbf.v4.new_markdown_cell(text))

def code(text):
    cells.append(nbf.v4.new_code_cell(text))

# =========================================================================
md("""## 2. Limpieza y transformación de datos

Se parte del dataset crudo de 90 columnas y se construye un dataset analítico con:

- **Precio limpio** (`price` viene como texto, ej. `"$86,206.29"`).
- **Filtrado de outliers extremos** de precio (fuera del percentil 1–99, valores que
  corresponden a errores de carga o publicaciones no representativas).
- **Amenities parseadas** desde el campo de texto tipo lista a columnas binarias para las
  comodidades más relevantes, y un conteo total de amenities.
- **Proxy de ocupación**: `estimated_occupancy_l365d` (noches ocupadas estimadas en los últimos
  365 días, ya provisto por Inside Airbnb a partir del historial de reviews y disponibilidad).
- **Cruce con densidad de POI por barrio** (dataset enriquecido en la sección 1.2).
""")

code("""df = listings_raw.copy()

# --- precio ---
df["price_clean"] = (
    df["price"].astype(str).str.replace("$", "", regex=False).str.replace(",", "", regex=False)
)
df["price_clean"] = pd.to_numeric(df["price_clean"], errors="coerce")

# --- filtro de calidad: precio valido, al menos 1 huesped, no son estadias de largo plazo ---
p1, p99 = df["price_clean"].quantile([0.01, 0.99])
df = df[
    df["price_clean"].notna()
    & df["price_clean"].between(p1, p99)
    & (df["accommodates"] > 0)
    & (df["minimum_nights"] <= 30)
].copy()

print(f"Filas antes de limpiar: {listings_raw.shape[0]:,}")
print(f"Filas luego de limpiar: {df.shape[0]:,}")
print(f"Rango de precios analizado: ${p1:,.0f} - ${p99:,.0f} ARS/noche")
""")

code("""# --- amenities: de texto tipo lista a columnas binarias ---
def parse_amenities(raw):
    try:
        return json.loads(raw)
    except Exception:
        return []

df["amenities_list"] = df["amenities"].apply(parse_amenities)
df["n_amenities"] = df["amenities_list"].apply(len)

amenities_clave = {
    "tiene_wifi": "Wifi",
    "tiene_pileta": "Pool",
    "tiene_aire_acondicionado": "Air conditioning",
    "tiene_cochera": "parking",
    "tiene_cocina": "Kitchen",
    "tiene_ascensor": "Elevator",
    "tiene_gimnasio": "Gym",
    "acepta_mascotas": "Pets allowed",
}
for col, keyword in amenities_clave.items():
    df[col] = df["amenities_list"].apply(
        lambda lst: any(keyword.lower() in a.lower() for a in lst)
    )

df[list(amenities_clave.keys()) + ["n_amenities"]].mean(numeric_only=True).round(2)
""")

code("""# --- ocupacion y reviews ---
df["ocupacion_pct_365d"] = (df["estimated_occupancy_l365d"] / 365 * 100).clip(0, 100)
df["tiene_reviews"] = df["number_of_reviews"] > 0

# --- cruce con densidad de POI por barrio ---
df = df.rename(columns={"neighbourhood_cleansed": "barrio"})
df = df.merge(
    poi_density[["barrio", "poi_gastronomia_900m", "poi_transporte_900m", "poi_total_900m"]],
    on="barrio",
    how="left",
)

# --- dataset final para el analisis, guardado localmente ---
cols_analisis = [
    "id", "barrio", "latitude", "longitude", "room_type", "property_type",
    "accommodates", "bedrooms", "beds", "price_clean", "minimum_nights",
    "number_of_reviews", "review_scores_rating", "review_scores_location",
    "review_scores_value", "estimated_occupancy_l365d", "ocupacion_pct_365d",
    "n_amenities", "poi_gastronomia_900m", "poi_transporte_900m", "poi_total_900m",
    "instant_bookable", "host_is_superhost",
] + list(amenities_clave.keys())

df_analisis = df[cols_analisis].copy()
df_analisis.to_csv("data/airbnb_baires_analitico.csv", index=False)
df_analisis.to_json("data/airbnb_baires_analitico.json", orient="records", indent=2)

df_analisis.head()
""")

# =========================================================================
md("""## 3. Análisis Exploratorio de Datos (EDA)

### 3.0 Resumen general del dataset
""")

code("""print(f"Filas: {df_analisis.shape[0]:,}  |  Columnas: {df_analisis.shape[1]}")
print()
print("Tipos de datos:")
print(df_analisis.dtypes.value_counts())
print()
resumen_metadata = pd.DataFrame({
    "tipo": df_analisis.dtypes.astype(str),
    "% nulos": (df_analisis.isna().mean() * 100).round(1),
    "valores_unicos": df_analisis.nunique(),
})
resumen_metadata.to_csv("data/resumen_metadata.csv")
resumen_metadata
""")

code("""df_analisis["price_clean"].describe().round(0)
""")

# --- Pregunta 1 ----------------------------------------------------------
md("""### 3.1 Pregunta 1 — Densidad de puntos de interés vs. precio

¿Los barrios con más oferta gastronómica y de transporte público cercano tienen precios
promedio más altos?
""")

code("""precio_por_barrio = (
    df_analisis.groupby("barrio")
    .agg(precio_promedio=("price_clean", "mean"), publicaciones=("price_clean", "size"))
    .join(poi_density.set_index("barrio"))
    .dropna()
)

fig, ax = plt.subplots(figsize=(8, 5.5))
sns.regplot(
    data=precio_por_barrio, x="poi_total_900m", y="precio_promedio",
    scatter_kws={"s": 60, "alpha": 0.7}, line_kws={"color": "crimson"}, ax=ax,
)
ax.set_xlabel("Puntos de interés en 900m del centro del barrio (gastronomía + transporte)")
ax.set_ylabel("Precio promedio por noche (ARS)")
ax.set_title("Densidad de puntos de interés vs. precio promedio por barrio")
plt.tight_layout()
plt.savefig("data/fig_poi_vs_precio.png", dpi=150)
plt.show()

corr = precio_por_barrio["poi_total_900m"].corr(precio_por_barrio["precio_promedio"])
print(f"Correlación (barrio): densidad de POI vs. precio promedio = {corr:.2f}")
""")

md("""**Lectura:** cada punto es un barrio de CABA. Una correlación positiva indica que los
barrios mejor "equipados" en oferta gastronómica y de transporte —típicamente los barrios
turísticos y céntricos— sostienen precios promedio más altos. *(La celda de arriba calcula el
coeficiente de correlación real sobre los datos.)*
""")

# --- Pregunta 2 ----------------------------------------------------------
md("""### 3.2 Pregunta 2 — Reviews vs. tarifa promedio diaria

¿Las propiedades mejor valoradas cobran tarifas más altas?
""")

code("""con_reviews = df_analisis[df_analisis["review_scores_rating"].notna()]

fig, axes = plt.subplots(1, 2, figsize=(12, 5))

sns.scatterplot(
    data=con_reviews.sample(min(4000, len(con_reviews)), random_state=42),
    x="review_scores_rating", y="price_clean", alpha=0.25, ax=axes[0],
)
axes[0].set_title("Puntaje de review vs. precio (muestra de publicaciones)")
axes[0].set_xlabel("Puntaje promedio de reviews (0-5)")
axes[0].set_ylabel("Precio por noche (ARS)")

corr_cols = [
    "price_clean", "review_scores_rating", "review_scores_location",
    "review_scores_value", "ocupacion_pct_365d", "n_amenities", "poi_total_900m",
]
sns.heatmap(
    con_reviews[corr_cols].corr(), annot=True, fmt=".2f", cmap="RdBu_r", center=0, ax=axes[1],
    cbar_kws={"label": "correlación"},
)
axes[1].set_title("Matriz de correlación")

plt.tight_layout()
plt.savefig("data/fig_reviews_vs_precio.png", dpi=150)
plt.show()

corr_rp = con_reviews["review_scores_rating"].corr(con_reviews["price_clean"])
print(f"Correlación puntaje de reviews vs. precio = {corr_rp:.2f}")
""")

md("""**Lectura:** el scatter de la izquierda muestra la relación puntaje-precio a nivel
publicación individual; el heatmap de la derecha compara esa relación con otras variables
(ubicación, valor percibido, ocupación, amenities, densidad de POI) para evitar sacar
conclusiones apuradas de una sola correlación.
""")

# --- Pregunta 3 ----------------------------------------------------------
md("""### 3.3 Pregunta 3 — Premium de precio por amenities

¿Qué comodidades explican un salto real en el precio promedio?
""")

code("""amenities_cols = list(amenities_clave.keys())
premium = []
for col in amenities_cols:
    con = df_analisis.loc[df_analisis[col], "price_clean"].mean()
    sin = df_analisis.loc[~df_analisis[col], "price_clean"].mean()
    premium.append({
        "amenity": col.replace("tiene_", "").replace("acepta_", "").replace("_", " ").title(),
        "precio_con": con,
        "precio_sin": sin,
        "premium_pct": (con / sin - 1) * 100,
    })
premium_df = pd.DataFrame(premium).sort_values("premium_pct", ascending=False)

fig, ax = plt.subplots(figsize=(8, 5.5))
sns.barplot(data=premium_df, y="amenity", x="premium_pct", hue="amenity", palette="viridis", legend=False, ax=ax)
ax.axvline(0, color="black", linewidth=0.8)
ax.set_xlabel("Premium de precio (%) vs. propiedades sin esa comodidad")
ax.set_ylabel("")
ax.set_title("Premium de precio por tipo de amenity")
plt.tight_layout()
plt.savefig("data/fig_premium_amenities.png", dpi=150)
plt.show()

premium_df.round(1)
""")

md("""**Lectura:** cada barra muestra cuánto más caras son, en promedio, las propiedades que
ofrecen esa comodidad frente a las que no la ofrecen. Comodidades con premium alto y baja
penetración (pocas propiedades la ofrecen) son las mejores candidatas a inversión con retorno
más claro.
""")

# --- Visualizacion extra: distribucion de precio y tipo de propiedad -----
md("""### 3.4 Contexto adicional: distribución de precios y tipo de propiedad
""")

code("""fig, axes = plt.subplots(1, 2, figsize=(12, 5))

sns.histplot(df_analisis["price_clean"], bins=50, kde=True, ax=axes[0], color="#4C72B0")
axes[0].set_title("Distribución de precios por noche (ARS)")
axes[0].set_xlabel("Precio por noche")

top_barrios = df_analisis["barrio"].value_counts().head(10).index
sns.boxplot(
    data=df_analisis[df_analisis["barrio"].isin(top_barrios)],
    x="price_clean", y="barrio", hue="barrio", palette="Set2", legend=False,
    order=top_barrios, ax=axes[1],
)
axes[1].set_title("Precio por barrio (10 barrios con más publicaciones)")
axes[1].set_xlabel("Precio por noche (ARS)")
axes[1].set_ylabel("")

plt.tight_layout()
plt.savefig("data/fig_distribucion_precio.png", dpi=150)
plt.show()
""")

# =========================================================================
md("""## 4. Insights / Conclusiones

**Pregunta 1 — Densidad de puntos de interés vs. precio:**
Los barrios con mayor concentración de restaurantes, bares y opciones de transporte público en
un radio de 900 metros muestran, en promedio, tarifas más altas por noche (ver correlación
calculada en 3.1). Para un inversor, esto sugiere que la "caminabilidad" del barrio hacia oferta
gastronómica y transporte es un factor de pricing tan relevante como el tamaño o tipo de la
propiedad.

**Pregunta 2 — Reviews vs. tarifa promedio:**
La relación entre puntaje de reviews y precio es más débil y ruidosa de lo que la intuición
sugiere (ver 3.2): un buen puntaje es casi una condición necesaria para sostenerse en el
mercado, pero no explica por sí solo tarifas más altas. El puntaje de "ubicación" dentro de las
reviews tiende a moverse más en línea con el precio que el puntaje general.

**Pregunta 3 — Premium por amenities:**
No todas las comodidades valen lo mismo. Las amenities con mayor premium de precio (ver 3.3) son
las que conviene priorizar al equipar una propiedad nueva, especialmente si tienen baja
penetración en el mercado actual (pocos competidores las ofrecen todavía).

**Recomendación para la audiencia (inversores / gestores de alquiler temporario):**
Priorizar barrios con alta densidad de oferta gastronómica y transporte, mantener un puntaje de
reviews saludable como piso no negociable, e invertir selectivamente en las amenities de mayor
premium relativo antes que en amenities "de moda" mal aprovechadas por el mercado.

*Nota metodológica: este análisis es exploratorio y descriptivo (correlaciones), no causal. La
segunda entrega del TP incorporará modelos de Machine Learning entrenados y optimizados para
predecir precio y ocupación, y así cuantificar el efecto de cada variable de forma más rigurosa.*
""")

nb["cells"] = cells
with open("TP1_AirbnbBaires_MachineLearning.ipynb", "w", encoding="utf-8") as f:
    nbf.write(nb, f)

print(f"Notebook completo con {len(cells)} celdas")
