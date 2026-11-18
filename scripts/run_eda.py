from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from src.ola_insights import DEFAULT_RAW_DATA_PATH, DEFAULT_DATA_PATH, load_bookings, quality_report


def main() -> None:
    parser = argparse.ArgumentParser(description="Clean the Ola workbook and create EDA exports.")
    parser.add_argument("--input", type=Path, default=DEFAULT_RAW_DATA_PATH, help="Path to OLA_DataSet.xlsx")
    parser.add_argument("--output", type=Path, default=Path("reports"), help="Directory for CSV outputs")
    args = parser.parse_args()

    bookings = load_bookings(args.input)
    args.output.mkdir(parents=True, exist_ok=True)
    quality_report(bookings).to_csv(args.output / "data_quality.csv", index=False)
    bookings.to_csv(args.output / "cleaned_bookings.csv", index=False)
    DEFAULT_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    bookings.to_csv(DEFAULT_DATA_PATH, index=False)

    successful = bookings.loc[bookings["booking_status"].eq("Success")]
    summaries = {
        "total_bookings": len(bookings),
        "successful_bookings": len(successful),
        "success_rate_percent": round(len(successful) / len(bookings) * 100, 2),
        "successful_booking_value_inr": int(successful["booking_value"].fillna(0).sum()),
        "customer_cancelled_bookings": int(bookings["booking_status"].eq("Canceled by Customer").sum()),
        "driver_cancelled_bookings": int(bookings["booking_status"].eq("Canceled by Driver").sum()),
    }
    pd.DataFrame([summaries]).to_csv(args.output / "eda_summary.csv", index=False)
    print(
        f"Cleaned {len(bookings):,} bookings; EDA exports written to "
        f"{args.output.resolve()} and {DEFAULT_DATA_PATH}."
    )


if __name__ == "__main__":
    main()
