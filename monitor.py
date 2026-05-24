import os
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv

import db

load_dotenv()

ORIGIN = "SJO"
DESTINATION = "CUN"
DATE_WINDOWS = [
    ("2027-02-13", "2027-02-20"),
    ("2027-02-20", "2027-02-27"),
]

SERPAPI_URL = "https://serpapi.com/search" #revisar quota https://serpapi.com/plan


def search_flights(departure_date: str, return_date: str) -> dict:
    params = {
        "engine": "google_flights",
        "departure_id": ORIGIN,
        "arrival_id": DESTINATION,
        "outbound_date": departure_date,
        "return_date": return_date,
        "currency": "USD",
        "hl": "en",
        "type": "1",
        "api_key": os.environ["SERPAPI_KEY"],
    }
    resp = requests.get(SERPAPI_URL, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()



def parse_offers(data: dict, departure_date: str, return_date: str) -> list[dict]:
    results = []
    for category in ("best_flights", "other_flights"):
        for it in data.get(category, []):
            try:
                price = float(it["price"])
                first_segment = it["flights"][0]
                actual_origin = first_segment["departure_airport"]["id"]
                if actual_origin != ORIGIN:
                    print(f"  [skip] sale de {actual_origin}, no de {ORIGIN}")
                    continue
                airline = first_segment["airline"]
                stops = len(it.get("layovers", []))
                duration_min = int(it.get("total_duration", 0))
                results.append({
                    "departure_date": departure_date,
                    "return_date": return_date,
                    "airline": airline,
                    "price_usd": price,
                    "stops": stops,
                    "duration_min": duration_min,
                })
            except (KeyError, IndexError, ValueError, TypeError):
                continue
    return results


def main() -> None:
    conn = db.get_connection()
    db.init_db(conn)

    queried_at = datetime.now(timezone.utc).isoformat()
    total_inserted = 0

    for departure_date, return_date in DATE_WINDOWS:
        print(f"Buscando vuelos {departure_date} -> {return_date} ...")
        try:
            data = search_flights(departure_date, return_date)
        except requests.RequestException as exc:
            print(f"  Error en la API: {exc}")
            continue

        flights = parse_offers(data, departure_date, return_date)
        print(f"  {len(flights)} oferta(s) encontrada(s)")

        for flight in flights:
            if db.insert_flight(conn, queried_at=queried_at, **flight):
                total_inserted += 1

    print(f"\nListo. {total_inserted} registro(s) nuevo(s) guardado(s) en {db.DB_PATH}")
    conn.close()


if __name__ == "__main__":
    main()
