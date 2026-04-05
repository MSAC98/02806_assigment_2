"""
ISTRUZIONI:
1. Copia questo file nella stessa cartella dove hai il tuo CSV
2. Cambia CSV_PATH con il percorso esatto del tuo file CSV
3. Esegui: python generate_heatmap.py
   oppure incolla tutto in una cella Jupyter e lancia con Shift+Enter

Il file heatmap_hour_day.html verrà creato nella cartella plots/
Poi caricalo nel tuo repo GitHub nella cartella plots/ come hai fatto
con gli altri grafici interattivi.
"""

import pandas as pd
import plotly.graph_objects as go
import numpy as np
import os

# ── CAMBIA QUESTO con il percorso del tuo CSV ─────────────────────────────────
CSV_PATH = "sfcrime.csv"
# ─────────────────────────────────────────────────────────────────────────────

# Crea la cartella plots/ se non esiste
os.makedirs("plots", exist_ok=True)

# ── Carica il CSV ─────────────────────────────────────────────────────────────
print("Carico il CSV...")
df = pd.read_csv(CSV_PATH, quotechar='"', on_bad_lines="skip")
df.columns = df.columns.str.strip().str.lower()
print(f"Righe caricate: {len(df)}")
print(f"Categorie trovate: {sorted(df['category'].unique())}")

# ── Estrai l'ora dal campo time ───────────────────────────────────────────────
df["hour"] = pd.to_datetime(df["time"], format="%H:%M", errors="coerce").dt.hour

# ── Ordine giorni ─────────────────────────────────────────────────────────────
DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
df["day_of_week"] = pd.Categorical(df["day_of_week"], categories=DAY_ORDER, ordered=True)

# ── Tipi di crimine da visualizzare ──────────────────────────────────────────
# Se i nomi nel tuo CSV sono diversi, cambiali qui
CRIMES = {
    "Assault":  "ASSAULT",
    "Burglary": "BURGLARY",
    "Theft":    "THEFT",
}

# ── Funzione che costruisce la tabella pivot ora x giorno ─────────────────────
def make_pivot(crime_label):
    sub = df[df["category"] == crime_label].dropna(subset=["hour", "day_of_week"])
    if len(sub) == 0:
        print(f"ATTENZIONE: nessuna riga trovata per '{crime_label}'")
        print(f"Le categorie disponibili sono: {sorted(df['category'].unique())}")
    pivot = (
        sub.groupby(["day_of_week", "hour"])
           .size()
           .reset_index(name="count")
    )
    table = pivot.pivot(index="day_of_week", columns="hour", values="count").fillna(0)
    table = table.reindex(columns=range(24), fill_value=0)
    table = table.reindex(DAY_ORDER, fill_value=0)
    return table

print("\nCostruisco le pivot tables...")
pivots = {name: make_pivot(label) for name, label in CRIMES.items()}

# ── Costruisce il grafico Plotly ──────────────────────────────────────────────
print("Genero il grafico...")

PALETTE = {
    "Assault":  "Reds",
    "Burglary": "Blues",
    "Theft":    "Oranges",
}

SUBTITLES = {
    "Assault":  "Assault shifts sharply toward Friday and Saturday nights.",
    "Burglary": "Burglary peaks during daytime hours across all days.",
    "Theft":    "Theft follows a broad daytime pattern with little weekend shift.",
}

x_labs = [f"{h:02d}:00" for h in range(24)]
fig = go.Figure()

for i, (name, pivot) in enumerate(pivots.items()):
    z = pivot.values.astype(float)

    # Normalizza per riga: ogni cella = % degli incidenti di quel giorno
    # in quell'ora. Così il colore mostra il ritmo, non il volume assoluto.
    row_sums = z.sum(axis=1, keepdims=True)
    row_sums = np.where(row_sums == 0, 1, row_sums)
    z_pct = z / row_sums * 100

    # Testo che appare al passaggio del mouse
    hover = np.array([[
        f"<b>{DAY_ORDER[r]}, {x_labs[c]}</b><br>"
        f"Share of day: {z_pct[r, c]:.1f}%<br>"
        f"Incident count: {int(z[r, c])}"
        for c in range(24)] for r in range(7)])

    fig.add_trace(go.Heatmap(
        z=z_pct,
        x=x_labs,
        y=DAY_ORDER,
        colorscale=PALETTE[name],
        zmin=0,
        zmax=float(np.ceil(z_pct.max())),
        hovertemplate="%{customdata}<extra></extra>",
        customdata=hover,
        colorbar=dict(
            title=dict(text="% of day", side="right"),
            ticksuffix="%",
            len=0.8,
            thickness=14,
        ),
        visible=(i == 0),  # solo il primo visibile all'inizio
        name=name,
    ))

# ── Dropdown per cambiare crimine ─────────────────────────────────────────────
buttons = []
for i, name in enumerate(pivots):
    buttons.append(dict(
        label=name,
        method="update",
        args=[
            {"visible": [j == i for j in range(len(pivots))]},
            {"title": {
                "text": (
                    f"<b>Hour × Day of Week — {name}</b><br>"
                    f"<sup>{SUBTITLES[name]}</sup>"
                ),
                "font": {"size": 16, "family": "Arial, sans-serif"},
                "x": 0.02,
            }},
        ],
    ))

fig.update_layout(
    title=dict(
        text=(
            "<b>Hour × Day of Week — Assault</b><br>"
            f"<sup>{SUBTITLES['Assault']}</sup>"
        ),
        font=dict(size=16, family="Arial, sans-serif"),
        x=0.02,
    ),
    updatemenus=[dict(
        type="dropdown",
        direction="down",
        x=0.0,
        xanchor="left",
        y=1.22,
        yanchor="top",
        buttons=buttons,
        bgcolor="#f5f5f5",
        bordercolor="#cccccc",
        font=dict(size=13, family="Arial, sans-serif"),
        active=0,
        showactive=True,
    )],
    annotations=[dict(
        text="Select crime:",
        x=0.0, xanchor="left",
        y=1.28, yanchor="top",
        xref="paper", yref="paper",
        showarrow=False,
        font=dict(size=12, family="Arial, sans-serif", color="#555"),
    )],
    xaxis=dict(
        title="Hour of day",
        tickangle=0,
        tickfont=dict(size=10),
        showgrid=False,
        dtick=2,
    ),
    yaxis=dict(
        title="",
        autorange="reversed",
        tickfont=dict(size=12),
        showgrid=False,
    ),
    plot_bgcolor="white",
    paper_bgcolor="white",
    font=dict(family="Georgia, serif", color="#222"),
    margin=dict(l=100, r=70, t=120, b=60),
    height=420,
)

# ── Salva il file HTML ────────────────────────────────────────────────────────
out = "plots/heatmap_hour_day.html"
fig.write_html(
    out,
    include_plotlyjs="cdn",
    full_html=True,
    config={"displayModeBar": False},
)
print(f"\nFatto! File salvato in: {out}")
print("Carica questo file nella cartella plots/ del tuo repo GitHub.")
