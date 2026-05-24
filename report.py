from datetime import datetime, timezone

import pandas as pd
from jinja2 import Template

import db

DATE_WINDOWS = [
    ("2027-02-13", "2027-02-20", "13-20 de febrero 2027"),
    ("2027-02-20", "2027-02-27", "20-27 de febrero 2027"),
]

_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>Monitor de Vuelos SJO-CUN</title>
  <style>
    body  { font-family: Arial, sans-serif; max-width: 1100px; margin: 40px auto; color: #333; }
    h1    { color: #1a73e8; }
    h2    { color: #444; border-bottom: 2px solid #1a73e8; padding-bottom: 4px; margin-top: 36px; }
    table { border-collapse: collapse; width: 100%; margin-top: 12px; margin-bottom: 8px; }
    th    { background: #1a73e8; color: #fff; padding: 10px 14px; text-align: left; }
    td    { padding: 9px 14px; border-bottom: 1px solid #e0e0e0; }
    tr:hover td { background: #f5f9ff; }
    .min-price td { background: #d4edda !important; font-weight: bold; }
    .empty { color: #888; font-style: italic; }
    a.buscar { color: #1a73e8; text-decoration: none; font-size: 13px; }
    a.buscar:hover { text-decoration: underline; }
    footer { color: #aaa; font-size: 12px; margin-top: 32px; }
  </style>
</head>
<body>
  <h1>Monitor de Vuelos SJO -> CUN</h1>
  <p>Ultima actualizacion: <strong>{{ generated_at }}</strong></p>

  {% for section in sections %}
  <h2>{{ section.title }}</h2>
  {% if section.rows %}
  <table>
    <thead>
      <tr>
        <th>Salida</th>
        <th>Regreso</th>
        <th>Aerolinea</th>
        <th>Precio USD</th>
        <th>Escalas</th>
        <th>Duracion total</th>
        <th>Buscar</th>
      </tr>
    </thead>
    <tbody>
      {% for row in section.rows %}
      <tr class="{{ 'min-price' if row.is_min else '' }}">
        <td>{{ row.departure_date }}</td>
        <td>{{ row.return_date }}</td>
        <td>{{ row.airline }}</td>
        <td>${{ "%.2f" | format(row.price_usd) }}</td>
        <td>{{ row.stops }}</td>
        <td>{{ row.duration_fmt }}</td>
        <td><a class="buscar" href="{{ row.search_url }}" target="_blank">Ver en Kayak</a></td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
  <p>Precio minimo: <strong>${{ "%.2f" | format(section.min_price) }}</strong> — fila resaltada en verde.</p>
  {% else %}
  <p class="empty">Sin datos para esta ventana de fechas. Ejecuta monitor.py primero.</p>
  {% endif %}
  {% endfor %}

  <footer>Generado automaticamente - monitor-vuelos</footer>
</body>
</html>"""


def _fmt_duration(minutes: int) -> str:
    if not minutes:
        return "N/D"
    return f"{minutes // 60}h {minutes % 60}m"


def _kayak_url(departure_date: str, return_date: str) -> str:
    return f"https://www.kayak.com/flights/SJO-CUN/{departure_date}/{return_date}"


def _build_section(conn, departure_date: str, return_date: str, title: str) -> dict:
    df = pd.read_sql_query(
        """SELECT queried_at, departure_date, return_date, airline, price_usd, stops, duration_min
           FROM flight_prices
           WHERE departure_date = ? AND return_date = ?
           ORDER BY price_usd ASC, queried_at DESC""",
        conn,
        params=(departure_date, return_date),
    )

    if df.empty:
        return {"title": title, "rows": [], "min_price": 0.0}

    min_price = float(df["price_usd"].min())
    rows = df.to_dict("records")
    for row in rows:
        row["is_min"] = row["price_usd"] == min_price
        row["duration_fmt"] = _fmt_duration(row["duration_min"])
        row["search_url"] = _kayak_url(row["departure_date"], row["return_date"])

    return {"title": title, "rows": rows, "min_price": min_price}


def generate_report(output_path: str = "index.html") -> None:
    conn = db.get_connection()
    sections = [
        _build_section(conn, dep, ret, title)
        for dep, ret, title in DATE_WINDOWS
    ]
    conn.close()

    html = Template(_HTML_TEMPLATE).render(
        sections=sections,
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    )

    with open(output_path, "w", encoding="utf-8") as fh:
        fh.write(html)

    print(f"Reporte generado: {output_path}")


if __name__ == "__main__":
    generate_report()
