from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from typing import Any

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_PATH = PROJECT_ROOT / "data" / "cleaned_bookings.csv"
DEFAULT_RAW_DATA_PATH = PROJECT_ROOT / "data" / "OLA_DataSet.xlsx"
SQL_PATH = PROJECT_ROOT / "sql" / "queries.sql"

NUMERIC_COLUMNS = (
    "v_tat",
    "c_tat",
    "booking_value",
    "ride_distance",
    "driver_ratings",
    "customer_rating",
)


def _clean_cell(value: Any) -> Any:
    if isinstance(value, str):
        value = value.strip()
        if value.casefold() in {"", "null", "none", "nan", "n/a"}:
            return pd.NA
    return value


def clean_bookings(raw: pd.DataFrame) -> pd.DataFrame:
    """Normalize workbook fields and derive consistent ride date/time features."""
    df = raw.copy()
    df.columns = [
        re.sub(r"_+", "_", re.sub(r"[^a-z0-9]+", "_", str(column).strip().lower())).strip("_")
        for column in df.columns
    ]
    df = df.loc[:, ~df.columns.duplicated()]

    for column in df.select_dtypes(include=["object", "string"]).columns:
        df[column] = df[column].map(_clean_cell)

    df = df.drop(columns=["vehicle_images"], errors="ignore")

    for column in NUMERIC_COLUMNS:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")
            df.loc[df[column] < 0, column] = pd.NA

    for column in ("driver_ratings", "customer_rating"):
        if column in df.columns:
            df.loc[~df[column].between(1, 5), column] = pd.NA

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.normalize()
    if "time" in df.columns:
        df["time"] = df["time"].astype("string").str.strip()

    if {"date", "time"}.issubset(df.columns):
        df["booking_datetime"] = pd.to_datetime(
            df["date"].dt.strftime("%Y-%m-%d") + " " + df["time"].astype("string"),
            errors="coerce",
        )
    elif "date" in df.columns:
        df["booking_datetime"] = df["date"]

    if "booking_datetime" in df.columns:
        df["booking_hour"] = df["booking_datetime"].dt.hour.astype("Int64")
        df["booking_day"] = df["booking_datetime"].dt.day_name()
        df["is_weekend"] = df["booking_datetime"].dt.dayofweek >= 5

    if "booking_id" in df.columns:
        df = df.drop_duplicates(subset=["booking_id"], keep="first")
    if "customer_id" in df.columns:
        df["customer_id"] = df["customer_id"].astype("string")

    return df.reset_index(drop=True)


def load_bookings(path: str | Path = DEFAULT_DATA_PATH) -> pd.DataFrame:
    """Load and clean the July worksheet from the provided Excel workbook."""
    data_path = Path(path)
    if not data_path.is_file():
        raise FileNotFoundError(f"Dataset not found: {data_path}")
    if data_path.suffix.casefold() == ".csv":
        raw = pd.read_csv(data_path)
    else:
        raw = pd.read_excel(data_path, sheet_name="July", engine="openpyxl")
    if raw.empty:
        raise ValueError(f"The July worksheet in {data_path} contains no booking rows.")
    return clean_bookings(raw)


def quality_report(bookings: pd.DataFrame) -> pd.DataFrame:
    """Return one row per field with missing-value and distinct-value counts."""
    return pd.DataFrame(
        {
            "column": bookings.columns,
            "missing_values": [int(bookings[column].isna().sum()) for column in bookings],
            "missing_percent": [
                round(float(bookings[column].isna().mean() * 100), 2)
                for column in bookings
            ],
            "distinct_values": [
                int(bookings[column].nunique(dropna=True)) for column in bookings
            ],
        }
    )


def create_database(bookings: pd.DataFrame) -> sqlite3.Connection:
    """Create an in-memory SQLite database containing the cleaned bookings."""
    connection = sqlite3.connect(":memory:")
    bookings.to_sql("bookings", connection, index=False, if_exists="replace")
    return connection


def load_sql_queries(path: str | Path = SQL_PATH) -> dict[str, str]:
    """Read named SQL statements from the project's query catalog."""
    content = Path(path).read_text(encoding="utf-8")
    sections = re.split(r"(?m)^--\s*name:\s*(.+?)\s*$", content)
    if len(sections) < 3:
        raise ValueError(f"No named SQL queries were found in {path}.")
    queries = {
        sections[index].strip(): sections[index + 1].strip()
        for index in range(1, len(sections), 2)
        if sections[index].strip() and sections[index + 1].strip()
    }
    if not queries:
        raise ValueError(f"No runnable SQL statements were found in {path}.")
    return queries
