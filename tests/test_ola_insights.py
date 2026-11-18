from __future__ import annotations

import unittest

import pandas as pd

from src.ola_insights import clean_bookings, create_database, load_sql_queries


class CleanBookingsTests(unittest.TestCase):
    def test_normalizes_nulls_types_and_duplicate_bookings(self) -> None:
        raw = pd.DataFrame(
            {
                "Booking ID": ["B1", "B1", "B2"],
                "Booking Status": ["Success", "Success", "Canceled by Customer"],
                "Date": ["2024-07-01", "2024-07-01", "2024-07-02"],
                "Time": ["09:30:00", "09:30:00", "10:00:00"],
                "Booking Value": ["125", "125", "200"],
                "Ride Distance": ["12", "12", "0"],
                "Driver Ratings": ["4.5", "4.5", "null"],
                "Customer Rating": ["5", "5", "null"],
                "Payment Method": ["UPI", "UPI", "null"],
                "Vehicle Images": ["image.png", "image.png", "image.png"],
            }
        )

        cleaned = clean_bookings(raw)

        self.assertEqual(len(cleaned), 2)
        self.assertNotIn("vehicle_images", cleaned.columns)
        self.assertEqual(cleaned.loc[0, "booking_value"], 125)
        self.assertTrue(pd.isna(cleaned.loc[1, "payment_method"]))
        self.assertEqual(cleaned.loc[0, "booking_hour"], 9)

    def test_all_catalog_queries_execute_on_cleaned_table(self) -> None:
        rows = pd.DataFrame(
            {
                "booking_id": ["B1", "B2"],
                "customer_id": ["C1", "C2"],
                "booking_status": ["Success", "Canceled by Driver"],
                "vehicle_type": ["Prime Sedan", "Bike"],
                "booking_value": [100, 50],
                "ride_distance": [10, 0],
                "driver_ratings": [4.5, None],
                "customer_rating": [5.0, None],
                "payment_method": ["UPI", None],
                "canceled_rides_by_customer": [None, None],
                "canceled_rides_by_driver": [None, "Personal & Car related issue"],
                "incomplete_rides": [None, None],
                "incomplete_rides_reason": [None, None],
            }
        )
        queries = load_sql_queries()
        connection = create_database(rows)
        try:
            for name, query in queries.items():
                with self.subTest(query=name):
                    pd.read_sql_query(query, connection)
        finally:
            connection.close()


if __name__ == "__main__":
    unittest.main()
