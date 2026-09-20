"""Genera Presentacion_Ejecutiva_Airbnb_CABA.pptx con python-pptx a partir de
data/slide_data.json. Paleta 'Midnight Executive'. Maximo 12 slides."""
import json

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.chart.data import CategoryChartData, XyChartData
from pptx.enum.chart import XL_CHART_TYPE, XL_TICK_LABEL_POSITION, XL_MARKER_STYLE
from pptx.oxml.ns import qn

with open("data/slide_data.json", "r", encoding="utf-8") as f:
    DATA = json.load(f)

# ---- paleta "Midnight Executive" ----
NAVY = RGBColor(0x1E, 0x27, 0x61)
NAVY_DARK = RGBColor(0x14, 0x1B, 0x4D)
ICE = RGBColor(0xCA, 0xDC, 0xFC)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
GOLD = RGBColor(0xC9, 0xA2, 0x27)
INK = RGBColor(0x1B, 0x1F, 0x3B)
MUTED = RGBColor(0x6B, 0x72, 0x80)
CARD_BG = RGBColor(0xF4, 0xF6, 0xFC)
GRID = RGBColor(0xE5, 0xE7, 0xEB)

FONT_HEAD = "Cambria"
FONT_BODY = "Calibri"

PAGE_W, PAGE_H = 13.333, 7.5

prs = Presentation()
prs.slide_width = Inches(PAGE_W)
prs.slide_height = Inches(PAGE_H)
BLANK = prs.slide_layouts[6]


def add_slide(bg=WHITE):
    slide = prs.slides.add_slide(BLANK)
    rect = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    rect.fill.solid()
    rect.fill.fore_color.rgb = bg
    rect.line.fill.background()
    rect.shadow.inherit = False
    return slide


def no_line(shape):
    shape.line.fill.background()
    shape.shadow.inherit = False


def add_shape(slide, shape_type, x, y, w, h, fill_color, radius=None):
    shp = slide.shapes.add_shape(shape_type, Inches(x), Inches(y), Inches(w), Inches(h))
    shp.fill.solid()
    shp.fill.fore_color.rgb = fill_color
    no_line(shp)
    if radius is not None and shape_type == MSO_SHAPE.ROUNDED_RECTANGLE:
        try:
            shp.adjustments[0] = radius
        except Exception:
            pass
    return shp


def add_text(slide, x, y, w, h, text, size=14, color=INK, bold=False, italic=False,
             font=FONT_BODY, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, line_spacing=1.0,
             char_spacing=None, wrap=True):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = wrap
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = anchor
    lines = text.split("\n")
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = line_spacing
        run = p.add_run()
        run.text = line
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.italic = italic
        run.font.name = font
        run.font.color.rgb = color
        if char_spacing is not None:
            rPr = run.font._rPr
            rPr.set("spc", str(int(char_spacing * 100)))
    return tb


def circle_badge(slide, x, y, d, text, bg=NAVY, fg=WHITE, size=16):
    sh = add_shape(slide, MSO_SHAPE.OVAL, x, y, d, d, bg)
    add_text(slide, x, y, d, d, text, size=size, color=fg, bold=True, font=FONT_BODY,
             align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    return sh


def section_tag(slide, x, y, text, color=NAVY):
    add_text(slide, x, y, 6, 0.3, text.upper(), size=12, color=color, bold=True,
              font=FONT_BODY, char_spacing=1.5)


def footer(slide, page_num, dark=False):
    fcolor = RGBColor(0x88, 0x91, 0xC4) if dark else MUTED
    add_text(slide, 0.5, PAGE_H - 0.42, 8, 0.3, "Airbnb CABA · Data Science II · TP1", size=9, color=fcolor)
    add_text(slide, PAGE_W - 1.1, PAGE_H - 0.42, 0.6, 0.3, str(page_num), size=9, color=fcolor, align=PP_ALIGN.RIGHT)


def style_category_chart(chart, color=NAVY, number_format='"$"#,##0', cat_title=None, val_title=None,
                          show_labels=True, label_size=10):
    chart.has_legend = False
    chart.has_title = False
    plot = chart.plots[0]
    plot.has_data_labels = show_labels
    if show_labels:
        dl = plot.data_labels
        dl.number_format = number_format
        dl.number_format_is_linked = False
        dl.font.size = Pt(label_size)
        dl.font.color.rgb = INK
        dl.font.name = FONT_BODY

    series = chart.series[0]
    series.format.fill.solid()
    series.format.fill.fore_color.rgb = color
    series.format.line.fill.background()

    cat_ax = chart.category_axis
    cat_ax.has_major_gridlines = False
    cat_ax.tick_labels.font.size = Pt(11)
    cat_ax.tick_labels.font.color.rgb = INK
    cat_ax.tick_labels.font.name = FONT_BODY
    cat_ax.format.line.color.rgb = GRID

    val_ax = chart.value_axis
    val_ax.has_major_gridlines = True
    val_ax.major_gridlines.format.line.color.rgb = GRID
    val_ax.tick_labels.font.size = Pt(9)
    val_ax.tick_labels.font.color.rgb = MUTED
    val_ax.tick_labels.font.name = FONT_BODY
    val_ax.format.line.fill.background()

    if cat_title:
        cat_ax.axis_title.text_frame.text = cat_title
        for p in cat_ax.axis_title.text_frame.paragraphs:
            for r in p.runs:
                r.font.size = Pt(11)
                r.font.color.rgb = MUTED
                r.font.name = FONT_BODY
    if val_title:
        val_ax.axis_title.text_frame.text = val_title
        for p in val_ax.axis_title.text_frame.paragraphs:
            for r in p.runs:
                r.font.size = Pt(11)
                r.font.color.rgb = MUTED
                r.font.name = FONT_BODY


def fmt(n):
    return f"{round(n):,}".replace(",", ".")


# =========================================================================
# Slide 1 — Titulo
# =========================================================================
s = add_slide(NAVY)
add_shape(s, MSO_SHAPE.OVAL, 9.7, -2.3, 6, 6, NAVY_DARK)
add_shape(s, MSO_SHAPE.OVAL, 11.3, 4.6, 3.6, 3.6, NAVY_DARK)
add_text(s, 0.9, 1.15, 10.5, 0.4, "DATA SCIENCE II · MACHINE LEARNING PARA LA CIENCIA DE DATOS",
          size=13, color=GOLD, bold=True, char_spacing=1.5)
add_text(s, 0.9, 1.6, 11.5, 2.6, "Optimización de Precios y Ocupación\nen Alquileres Temporarios",
          size=36, color=WHITE, bold=True, font=FONT_HEAD, line_spacing=1.08)
add_text(s, 0.9, 4.35, 8.8, 0.9,
          "Un análisis de Airbnb en la Ciudad Autónoma de Buenos Aires, enriquecido con datos "
          "abiertos de OpenStreetMap", size=16, color=ICE)
add_text(s, 0.9, 6.45, 9, 0.4, "Primera Entrega: Obtención de insights a partir de visualizaciones",
          size=13, color=RGBColor(0x9A, 0xA6, 0xDA), italic=True)
add_text(s, 0.9, 6.8, 9, 0.4, "Sofia Algamiz", size=13, color=ICE, bold=True)

# =========================================================================
# Slide 2 — Abstract
# =========================================================================
s = add_slide(WHITE)
section_tag(s, 0.7, 0.55, "Abstract")
add_text(s, 0.7, 0.9, 11.5, 0.7, "Por qué este análisis, y para quién", size=30, color=INK, bold=True, font=FONT_HEAD)
add_text(s, 0.7, 1.85, 6.6, 2.6,
          "El alquiler temporario es una de las formas más dinámicas de explotación inmobiliaria en "
          "las grandes ciudades. A diferencia del alquiler tradicional, el precio “correcto” de una "
          "propiedad depende de variables muy específicas del negocio turístico: ubicación relativa "
          "a bares y restaurantes, cercanía al transporte, comodidades ofrecidas y reputación acumulada.",
          size=15, color=INK, line_spacing=1.3)
add_text(s, 0.7, 4.35, 6.6, 1.8,
          "Este proyecto analiza publicaciones activas de Airbnb en CABA, enriquecidas con datos "
          "abiertos de OpenStreetMap sobre oferta gastronómica y transporte, para entender qué "
          "factores explican el precio y la ocupación de una propiedad.",
          size=15, color=INK, line_spacing=1.3)

add_shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, 7.75, 1.85, 4.85, 4.3, CARD_BG, radius=0.06)
circle_badge(s, 8.15, 2.2, 0.55, "A", bg=NAVY, size=18)
add_text(s, 8.85, 2.2, 3.5, 0.55, "Audiencia", size=18, color=INK, bold=True, font=FONT_HEAD, anchor=MSO_ANCHOR.MIDDLE)
add_text(s, 8.15, 3.0, 4.15, 1.6,
          "Inversores inmobiliarios y gestores de propiedades de alquiler temporario que evalúan en "
          "qué barrio comprar o alquilar una unidad, cómo equiparla y cómo fijar precio.",
          size=13.5, color=INK, line_spacing=1.3)
add_text(s, 8.15, 4.7, 4.15, 1.2, "Sin necesidad de conocimientos técnicos de estadística o programación.",
          size=13, color=MUTED, italic=True, line_spacing=1.3)
footer(s, 2)

# =========================================================================
# Slide 3 — Resumen de metadata
# =========================================================================
s = add_slide(WHITE)
section_tag(s, 0.7, 0.55, "Los datos")
add_text(s, 0.7, 0.9, 11.5, 0.7, "Resumen del dataset analizado", size=30, color=INK, bold=True, font=FONT_HEAD)
add_text(s, 0.7, 1.55, 11.8, 0.4,
          "Fuente: Inside Airbnb (scrape 29/06/2026) enriquecido con densidad de puntos de interés "
          "de OpenStreetMap (Overpass API).", size=13, color=MUTED)

tiles = [
    (fmt(DATA["n_filas"]), f"publicaciones activas\nanalizadas (de {fmt(DATA['n_filas_crudo'])} crudas)"),
    (str(DATA["n_cols_crudo"]), "variables originales por\npublicación (90 → 31 curadas)"),
    (str(DATA["n_barrios"]), "barrios de la Ciudad\nAutónoma de Buenos Aires"),
    (f"${fmt(DATA['precio_mediana'])}", "precio mediano\npor noche (ARS)"),
    (f"{DATA['ocupacion_media_pct']}%", "ocupación estimada\npromedio (últimos 365 días)"),
    (str(DATA["n_amenities_media"]), "comodidades (amenities)\npromedio por propiedad"),
]
gw, gh, gx, gy, gap = 3.85, 1.7, 0.7, 2.1, 0.2
for i, (n, l) in enumerate(tiles):
    cx = gx + (i % 3) * (gw + gap)
    cy = gy + (i // 3) * (gh + gap)
    add_shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, cx, cy, gw, gh, CARD_BG, radius=0.05)
    add_text(s, cx + 0.25, cy + 0.15, gw - 0.5, 0.75, n, size=30, color=NAVY, bold=True, font=FONT_HEAD)
    add_text(s, cx + 0.25, cy + 0.88, gw - 0.5, 0.75, l, size=12, color=MUTED, line_spacing=1.1)

# --- desglose de tipos de variable ---
ty = gy + 2 * gh + gap + 0.15
add_shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, 0.7, ty, 11.8, 0.85, NAVY, radius=0.08)
add_text(s, 1.0, ty + 0.14, 2.3, 0.57, "TIPOS DE\nVARIABLE", size=11, color=GOLD, bold=True, line_spacing=1.05, anchor=MSO_ANCHOR.MIDDLE)
tipos = [
    (str(DATA["n_vars_numericas"]), "numéricas\n(precio, ocupación, reviews…)"),
    (str(DATA["n_vars_categoricas"]), "categóricas\n(barrio, tipo de propiedad…)"),
    (str(DATA["n_vars_binarias"]), "binarias\n(amenities: sí / no)"),
]
tw = 2.9
for i, (n, l) in enumerate(tipos):
    tx = 3.55 + i * (tw + 0.15)
    add_text(s, tx, ty + 0.1, 0.75, 0.65, n, size=22, color=WHITE, bold=True, font=FONT_HEAD, anchor=MSO_ANCHOR.MIDDLE)
    add_text(s, tx + 0.75, ty + 0.1, tw - 0.75, 0.65, l, size=10.5, color=ICE, line_spacing=1.1, anchor=MSO_ANCHOR.MIDDLE)
footer(s, 3)

# =========================================================================
# Slide 4 — Preguntas / hipotesis
# =========================================================================
s = add_slide(WHITE)
section_tag(s, 0.7, 0.55, "El problema")
add_text(s, 0.7, 0.9, 11.8, 0.7, "Tres preguntas para optimizar precio y ocupación", size=28, color=INK, bold=True, font=FONT_HEAD)

qs = [
    ("1", "Densidad de puntos de interés", "¿Los barrios con más oferta gastronómica y transporte cercano tienen precios más altos?"),
    ("2", "Reviews y tarifa diaria", "¿Las propiedades mejor valoradas por sus huéspedes logran cobrar tarifas más altas?"),
    ("3", "Premium por comodidades", "¿Qué amenities (pileta, cochera, aire acondicionado…) generan un salto real de precio?"),
]
cw, ch, cx0, cy0, gap = 3.85, 4.35, 0.7, 1.9, 0.25
for i, (n, t, d) in enumerate(qs):
    cx = cx0 + i * (cw + gap)
    is_mid = i == 1
    add_shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, cx, cy0, cw, ch, NAVY if is_mid else CARD_BG, radius=0.05)
    circle_badge(s, cx + 0.3, cy0 + 0.35, 0.65, n, bg=GOLD if is_mid else NAVY, fg=INK if is_mid else WHITE, size=24)
    add_text(s, cx + 0.3, cy0 + 1.25, cw - 0.6, 1.0, t, size=18, color=WHITE if is_mid else INK, bold=True, font=FONT_HEAD, line_spacing=1.1)
    add_text(s, cx + 0.3, cy0 + 2.35, cw - 0.6, 1.8, d, size=13.5, color=ICE if is_mid else MUTED, line_spacing=1.3)
footer(s, 4)

# =========================================================================
# Slide 5 — Pregunta 1: POI vs precio (scatter)
# =========================================================================
s = add_slide(WHITE)
circle_badge(s, 0.7, 0.5, 0.5, "1", size=16)
add_text(s, 1.4, 0.5, 10, 0.6, "Densidad de puntos de interés vs. precio", size=26, color=INK, bold=True, font=FONT_HEAD, anchor=MSO_ANCHOR.MIDDLE)

chart_data = XyChartData()
series = chart_data.add_series("Barrios de CABA")
for d in DATA["scatter_poi_precio"]:
    series.add_data_point(d["x"], d["y"])
gframe = s.shapes.add_chart(XL_CHART_TYPE.XY_SCATTER, Inches(0.6), Inches(1.35), Inches(7.6), Inches(5.5), chart_data)
chart = gframe.chart
chart.has_legend = False
chart.has_title = False
ser = chart.series[0]
ser.marker.style = XL_MARKER_STYLE.CIRCLE
ser.marker.size = 7
ser.marker.format.fill.solid()
ser.marker.format.fill.fore_color.rgb = NAVY
ser.marker.format.line.fill.background()
ser.format.line.fill.background()
cat_ax = chart.category_axis
cat_ax.has_major_gridlines = False
cat_ax.axis_title.text_frame.text = "Puntos de interés en 900m (gastronomía + transporte)"
val_ax = chart.value_axis
val_ax.has_major_gridlines = True
val_ax.major_gridlines.format.line.color.rgb = GRID
val_ax.axis_title.text_frame.text = "Precio promedio por noche (ARS)"
for ax in (cat_ax, val_ax):
    ax.tick_labels.font.size = Pt(10)
    ax.tick_labels.font.color.rgb = MUTED
    ax.tick_labels.font.name = FONT_BODY
    for p in ax.axis_title.text_frame.paragraphs:
        for r in p.runs:
            r.font.size = Pt(11)
            r.font.color.rgb = MUTED
            r.font.name = FONT_BODY

add_shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, 8.45, 1.35, 4.2, 5.5, CARD_BG, radius=0.05)
add_text(s, 8.75, 1.6, 3.6, 0.6, "Cada punto es un barrio de CABA", size=13, color=INK, bold=True)
add_text(s, 8.75, 2.15, 3.6, 1.0, f"{DATA['corr_poi_precio']}", size=44, color=NAVY, bold=True, font=FONT_HEAD)
add_text(s, 8.75, 3.15, 3.6, 0.9, "correlación entre densidad de POI y precio promedio por barrio", size=12.5, color=MUTED, line_spacing=1.25)
add_text(s, 8.75, 4.2, 3.6, 2.5,
          "La caminabilidad hacia oferta gastronómica y transporte suma valor de ubicación "
          "medible, junto con el tamaño y tipo de propiedad.",
          size=12.5, color=INK, line_spacing=1.3)
footer(s, 5)

# =========================================================================
# Slide 6 — Pregunta 2: Reviews vs precio (columnas por bin)
# =========================================================================
s = add_slide(WHITE)
circle_badge(s, 0.7, 0.5, 0.5, "2", size=16)
add_text(s, 1.4, 0.5, 10, 0.6, "Reviews vs. tarifa promedio diaria", size=26, color=INK, bold=True, font=FONT_HEAD, anchor=MSO_ANCHOR.MIDDLE)

cd = CategoryChartData()
bin_labels = list(DATA["reviews_bins"].keys())
cd.categories = bin_labels
cd.add_series("Precio promedio", [DATA["reviews_bins"][k] for k in bin_labels])
gframe = s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(0.6), Inches(1.35), Inches(7.6), Inches(5.5), cd)
style_category_chart(gframe.chart, color=NAVY, cat_title="Puntaje promedio de reviews",
                      val_title="Precio promedio por noche (ARS)")

add_shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, 8.45, 1.35, 4.2, 5.5, CARD_BG, radius=0.05)
add_text(s, 8.75, 1.6, 3.6, 0.5, "Correlación puntaje ↔ precio", size=13, color=INK, bold=True)
add_text(s, 8.75, 2.1, 3.6, 1.0, f"{DATA['corr_reviews_precio']}", size=44, color=NAVY, bold=True, font=FONT_HEAD)
add_text(s, 8.75, 3.1, 3.6, 0.6, "(0 = sin relación lineal, 1 = relación perfecta)", size=11.5, color=MUTED, italic=True)
add_text(s, 8.75, 3.85, 3.6, 2.8,
          "La relación es más débil de lo que la intuición sugiere. Un buen puntaje sostiene al "
          "host en el mercado, pero no explica tarifas más altas por sí solo.",
          size=12.5, color=INK, line_spacing=1.3)
footer(s, 6)

# =========================================================================
# Slide 7 — Pregunta 3: Premium por amenities
# =========================================================================
s = add_slide(WHITE)
circle_badge(s, 0.7, 0.5, 0.5, "3", size=16)
add_text(s, 1.4, 0.5, 10, 0.6, "Qué comodidades generan un premium real", size=26, color=INK, bold=True, font=FONT_HEAD, anchor=MSO_ANCHOR.MIDDLE)

am = list(reversed(DATA["amenities_premium"]))
cd = CategoryChartData()
cd.categories = [a["amenity"] for a in am]
cd.add_series("Premium de precio", [a["premium_pct"] for a in am])
gframe = s.shapes.add_chart(XL_CHART_TYPE.BAR_CLUSTERED, Inches(0.5), Inches(1.3), Inches(8.6), Inches(5.6), cd)
style_category_chart(gframe.chart, color=GOLD, number_format='0"%"', val_title="Premium de precio (%) vs. sin esa comodidad")
gframe.chart.category_axis.tick_labels.font.size = Pt(12)
gframe.chart.category_axis.tick_labels.font.color.rgb = INK

top3 = DATA["amenities_premium"][:3]
add_shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, 9.35, 1.3, 3.3, 5.6, NAVY, radius=0.05)
add_text(s, 9.65, 1.55, 2.8, 0.4, "Top 3 oportunidades", size=13, color=GOLD, bold=True)
for i, a in enumerate(top3):
    yy = 2.15 + i * 1.6
    add_text(s, 9.65, yy, 2.8, 0.4, a["amenity"], size=14, color=WHITE, bold=True)
    add_text(s, 9.65, yy + 0.38, 1.6, 0.55, f"+{a['premium_pct']}%", size=24, color=GOLD, bold=True, font=FONT_HEAD)
    add_text(s, 9.65, yy + 0.95, 2.8, 0.6, f"{a['penetracion_pct']}% de las\npropiedades la ofrece", size=10.5, color=ICE, line_spacing=1.15)
footer(s, 7)

# =========================================================================
# Slide 8 — Panorama por barrio
# =========================================================================
s = add_slide(WHITE)
section_tag(s, 0.7, 0.55, "Contexto adicional")
add_text(s, 0.7, 0.9, 11.5, 0.6, "Panorama de precios en los barrios con más oferta", size=26, color=INK, bold=True, font=FONT_HEAD)
add_text(s, 0.7, 1.25, 10, 0.35, "8 barrios con mayor cantidad de publicaciones activas en Airbnb (CABA).", size=12, color=MUTED, italic=True)

tb = DATA["top_barrios"]
cd = CategoryChartData()
cd.categories = [b["barrio"] for b in tb]
cd.add_series("Precio promedio", [b["precio_promedio"] for b in tb])
gframe = s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(0.5), Inches(1.65), Inches(12.3), Inches(5.2), cd)
style_category_chart(gframe.chart, color=NAVY, val_title="Precio promedio por noche (ARS)", label_size=10)
gframe.chart.category_axis.tick_labels.font.size = Pt(12)
gframe.chart.category_axis.tick_labels.font.color.rgb = INK
footer(s, 8)

# =========================================================================
# Slide 9 — Insights clave (dark)
# =========================================================================
s = add_slide(NAVY)
add_shape(s, MSO_SHAPE.OVAL, -2.5, 4.2, 6, 6, NAVY_DARK)
section_tag(s, 0.7, 0.55, "Síntesis", color=GOLD)
add_text(s, 0.7, 0.9, 10, 0.7, "Insights clave", size=32, color=WHITE, bold=True, font=FONT_HEAD)

insights = [
    ("1", "Ubicación con densidad de servicios",
     f"Correlación de {DATA['corr_poi_precio']} entre densidad de POI y precio promedio por barrio: "
     "la cercanía a oferta gastronómica y transporte es un factor de pricing medible."),
    ("2", "Las reviews son un piso, no una palanca",
     f"Correlación de solo {DATA['corr_reviews_precio']} entre puntaje de reviews y precio: un buen "
     "puntaje sostiene al host en el mercado, pero no justifica tarifas premium por sí solo."),
    ("3", "No todas las amenities valen lo mismo",
     f"Gimnasio y pileta lideran el premium de precio (hasta +{DATA['amenities_premium'][0]['premium_pct']}%) "
     "y aún tienen baja penetración: son las mejores candidatas a inversión."),
]
cy0, ch, gap = 1.9, 1.55, 0.15
for i, (n, t, d) in enumerate(insights):
    cy = cy0 + i * (ch + gap)
    circle_badge(s, 0.7, cy + 0.1, 0.6, n, bg=GOLD, fg=INK, size=20)
    add_text(s, 1.65, cy, 4.6, ch, t, size=16, color=WHITE, bold=True, font=FONT_HEAD, anchor=MSO_ANCHOR.MIDDLE, line_spacing=1.15)
    add_text(s, 6.5, cy, 6.2, ch, d, size=13, color=ICE, anchor=MSO_ANCHOR.MIDDLE, line_spacing=1.25)
footer(s, 9, dark=True)

# =========================================================================
# Slide 10 — Recomendaciones
# =========================================================================
s = add_slide(WHITE)
section_tag(s, 0.7, 0.55, "Recomendaciones")
add_text(s, 0.7, 0.9, 11, 0.6, "Qué hacer con estos hallazgos", size=28, color=INK, bold=True, font=FONT_HEAD)

recs = [
    ("Priorizar ubicación caminable", "Al elegir barrio para invertir, ponderar la densidad de gastronomía y transporte cercano, no solo el precio del metro cuadrado."),
    ("Reviews: piso no negociable", "Mantener un puntaje alto de reviews como condición de permanencia en el mercado, sin esperar que por sí solo justifique subir tarifas."),
    ("Invertir en amenities de alto premium", "Priorizar gimnasio, pileta y cochera al equipar una propiedad: son las comodidades con mayor retorno relativo y todavía baja penetración."),
]
cw, ch, cx0, cy0, gap = 3.85, 3.9, 0.7, 1.9, 0.25
for i, (t, d) in enumerate(recs):
    cx = cx0 + i * (cw + gap)
    add_shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, cx, cy0, cw, ch, CARD_BG, radius=0.05)
    circle_badge(s, cx + 0.3, cy0 + 0.3, 0.55, str(i + 1), bg=NAVY, size=18)
    add_text(s, cx + 0.3, cy0 + 1.05, cw - 0.6, 0.9, t, size=16, color=INK, bold=True, font=FONT_HEAD, line_spacing=1.15)
    add_text(s, cx + 0.3, cy0 + 1.95, cw - 0.6, 1.8, d, size=12.5, color=MUTED, line_spacing=1.3)
footer(s, 10)

# =========================================================================
# Slide 11 — Cierre
# =========================================================================
s = add_slide(NAVY)
add_shape(s, MSO_SHAPE.OVAL, 9.7, -2.3, 6, 6, NAVY_DARK)
add_text(s, 0.9, 2.6, 10, 1.2, "Gracias", size=46, color=WHITE, bold=True, font=FONT_HEAD)
add_text(s, 0.9, 3.75, 9.5, 0.5, "Optimización de Precios y Ocupación en Alquileres Temporarios · Airbnb CABA", size=15, color=ICE)
add_text(s, 0.9, 4.35, 9.5, 0.4, "Fuentes: Inside Airbnb · OpenStreetMap (Overpass API) · Google Analytics 4 (BigQuery)", size=12.5, color=RGBColor(0x9A, 0xA6, 0xDA), italic=True)
footer(s, 11, dark=True)

prs.save("Presentacion_Ejecutiva_Airbnb_CABA.pptx")
print("PPTX generado:", len(prs.slides.__iter__().__length_hint__() if False else list(prs.slides)), "slides" if False else "")
print(f"Slides: {len(prs.slides._sldIdLst)}")
