import hashlib
import sqlite3
from pathlib import Path

DB_PATH = Path("flights.db")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS flight_prices (
            flight_id      TEXT    PRIMARY KEY,
            queried_at     TEXT    NOT NULL,
            query_date     TEXT    NOT NULL,
            departure_date TEXT    NOT NULL,
            return_date    TEXT    NOT NULL,
            airline        TEXT    NOT NULL,
            price_usd      REAL    NOT NULL,
            stops          INTEGER NOT NULL,
            duration_min   INTEGER NOT NULL
        )
    """)
    conn.commit()


def make_flight_id(departure_date: str, return_date: str, airline: str,
                   price_usd: float, stops: int, query_date: str) -> str:
    raw = f"{departure_date}|{return_date}|{airline}|{price_usd}|{stops}|{query_date}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def insert_flight(
    conn: sqlite3.Connection,
    queried_at: str,
    departure_date: str,
    return_date: str,
    airline: str,
    price_usd: float,
    stops: int,
    duration_min: int,
) -> bool:
    query_date = queried_at[:10]
    flight_id = make_flight_id(departure_date, return_date, airline, price_usd, stops, query_date)
    cursor = conn.execute(
        """INSERT OR IGNORE INTO flight_prices
               (flight_id, queried_at, query_date, departure_date, return_date,
                airline, price_usd, stops, duration_min)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (flight_id, queried_at, query_date, departure_date, return_date,
         airline, price_usd, stops, duration_min),
    )
    conn.commit()
    return cursor.rowcount > 0
