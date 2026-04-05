# ── CELLA DA AGGIUNGERE IN FONDO AL TUO NOTEBOOK ─────────────────────────────
# Copia tutto questo blocco in una nuova cella e premi Shift+Enter
# Genera il file plots/heatmap_hour_day.html
# Poi carica quel file su GitHub nella cartella plots/
# ─────────────────────────────────────────────────────────────────────────────

import plotly.graph_objects as go
import numpy as np
import os

os.makedirs("plots", exist_ok=True)

# I tuoi dati già caricati nel notebook: df con colonne crime, dayofweek, hour
# dayofweek: 0=Monday ... 6=Sunday

DAY_ORDER = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
CRIMES    = ["Assault", "Burglary", "Theft"]
PALETTE   = {"Assault": "Reds", "Burglary": "Blues", "Theft": "Oranges"}
SUBTITLES = {
    "Assault":  "Assault shifts sharply toward Friday and Saturday nights.",
    "Burglary": "Burglary peaks during daytime hours across all days.",
    "Theft":    "Theft follows a broad daytime pattern with little weekend shift.",
}

# Mappa numero giorno → nome
day_map = {0:"Monday",1:"Tuesday",2:"Wednesday",3:"Thursday",
           4:"Friday",5:"Saturday",6:"Sunday"}

fig = go.Figure()
x_labs = [f"{h:02d}:00" for h in range(24)]

for i, crime in enumerate(CRIMES):
    sub = df[df["crime"] == crime].copy()
    sub["day_name"] = sub["dayofweek"].map(day_map)

    pivot = (
        sub.groupby(["day_name","hour"])
           .size()
           .reset_index(name="count")
    )
    table = pivot.pivot(index="day_name", columns="hour", values="count").fillna(0)
    table = table.reindex(columns=range(24), fill_value=0)
    table = table.reindex(DAY_ORDER, fill_value=0)

    z = table.values.astype(float)

    # Normalizza per riga: % degli incidenti di quel giorno concentrati in quell'ora
    row_sums = z.sum(axis=1, keepdims=True)
    row_sums = np.where(row_sums == 0, 1, row_sums)
    z_pct = z / row_sums * 100

    hover = np.array([[
        f"<b>{DAY_ORDER[r]}, {x_labs[c]}</b><br>"
        f"Share of day: {z_pct[r,c]:.1f}%<br>"
        f"Incident count: {int(z[r,c])}"
        for c in range(24)] for r in range(7)])

    fig.add_trace(go.Heatmap(
        z=z_pct,
        x=x_labs,
        y=DAY_ORDER,
        colorscale=PALETTE[crime],
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
        visible=(i == 0),
        name=crime,
    ))

# Dropdown
buttons = []
for i, crime in enumerate(CRIMES):
    buttons.append(dict(
        label=crime,
        method="update",
        args=[
            {"visible": [j == i for j in range(len(CRIMES))]},
            {"title": {
                "text": f"<b>Hour × Day of Week — {crime}</b><br><sup>{SUBTITLES[crime]}</sup>",
                "font": {"size": 16, "family": "Arial, sans-serif"},
                "x": 0.02,
            }},
        ],
    ))

fig.update_layout(
    title=dict(
        text=f"<b>Hour × Day of Week — Assault</b><br><sup>{SUBTITLES['Assault']}</sup>",
        font=dict(size=16, family="Arial, sans-serif"),
        x=0.02,
    ),
    updatemenus=[dict(
        type="dropdown",
        direction="down",
        x=0.0, xanchor="left",
        y=1.22, yanchor="top",
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
        tickfont=dict(size=10),
        showgrid=False,
        dtick=2,
    ),
    yaxis=dict(
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

out = "plots/heatmap_hour_day.html"
fig.write_html(out, include_plotlyjs="cdn", full_html=True,
               config={"displayModeBar": False})
print(f"✓ Salvato in: {out}")
fig.show()
