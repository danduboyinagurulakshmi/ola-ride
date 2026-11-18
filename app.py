from __future__ import annotations

import os
import sqlite3
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from src.ola_insights import (
    DEFAULT_DATA_PATH,
    DEFAULT_RAW_DATA_PATH,
    create_database,
    load_bookings,
    load_sql_queries,
    quality_report,
)


st.set_page_config(page_title="Ola Ride Insights", page_icon="O", layout="wide")
st.title("Ola Ride Insights")
st.caption("Explore July 2024 booking activity, revenue, cancellations, and ratings.")


@st.cache_data(show_spinner="Loading and cleaning the ride dataset...")
def get_bookings(path: str) -> pd.DataFrame:
    return load_bookings(path)


@st.cache_data
def get_query_catalog() -> dict[str, str]:
    return load_sql_queries()


configured_path = Path(os.environ.get("OLA_DATA_PATH", DEFAULT_DATA_PATH))
if not configured_path.is_file():
    fallback_paths = (
        DEFAULT_RAW_DATA_PATH,
        Path(__file__).resolve().parent / "OLA_DataSet.xlsx",
    )
    configured_path = next((path for path in fallback_paths if path.is_file()), configured_path)

try:
    bookings = get_bookings(str(configured_path))
except (FileNotFoundError, ValueError, OSError) as exc:
    st.error(f"Could not load the ride dataset: {exc}")
    st.info("Set OLA_DATA_PATH to the cleaned CSV or source workbook.")
    st.stop()

if bookings.empty:
    st.warning("The workbook contains no usable booking rows.")
    st.stop()

st.sidebar.header("Filters")
date_values = bookings["booking_datetime"].dropna()
if date_values.empty:
    st.error("No valid booking dates were found in the dataset.")
    st.stop()

minimum_date = date_values.min().date()
maximum_date = date_values.max().date()
selected_dates = st.sidebar.date_input(
    "Booking date range",
    value=(minimum_date, maximum_date),
    min_value=minimum_date,
    max_value=maximum_date,
)
if isinstance(selected_dates, (list, tuple)) and len(selected_dates) == 2:
    start_date, end_date = selected_dates
else:
    start_date = end_date = selected_dates

def choices(column: str) -> list[str]:
    return sorted(bookings[column].dropna().astype(str).unique().tolist())


status_options = choices("booking_status")
vehicle_options = choices("vehicle_type")
payment_options = choices("payment_method")
selected_statuses = st.sidebar.multiselect("Booking status", status_options, default=status_options)
selected_vehicles = st.sidebar.multiselect("Vehicle type", vehicle_options, default=vehicle_options)
selected_payments = st.sidebar.multiselect("Payment method", payment_options, default=payment_options)

date_mask = bookings["booking_datetime"].dt.date.between(start_date, end_date)
filtered = bookings.loc[
    date_mask
    & bookings["booking_status"].isin(selected_statuses)
    & bookings["vehicle_type"].isin(selected_vehicles)
    & bookings["payment_method"].isin(selected_payments)
].copy()

successful = filtered.loc[filtered["booking_status"].eq("Success")]
revenue = float(successful["booking_value"].fillna(0).sum())
success_rate = (
    float(filtered["booking_status"].eq("Success").mean() * 100) if not filtered.empty else 0.0
)
average_rating = successful["customer_rating"].mean()

kpis = st.columns(4)
kpis[0].metric("Bookings", f"{len(filtered):,}")
kpis[1].metric("Successful rides", f"{len(successful):,}", f"{success_rate:.1f}% of filtered bookings")
kpis[2].metric("Successful booking value", f"₹{revenue:,.0f}")
kpis[3].metric("Average customer rating", f"{average_rating:.2f}" if pd.notna(average_rating) else "N/A")

overview, vehicle, revenue_tab, cancellation, ratings, sql_tab, data_tab = st.tabs(
    ["Overall", "Vehicle type", "Revenue", "Cancellation", "Ratings", "SQL explorer", "Data quality"]
)

with overview:
    left, right = st.columns(2)
    with left:
        daily = (
            filtered.groupby(filtered["booking_datetime"].dt.date, as_index=False)
            .size()
            .rename(columns={"booking_datetime": "date", "size": "bookings"})
        )
        st.plotly_chart(
            px.line(daily, x="date", y="bookings", markers=True, title="Ride volume over time"),
            width="stretch",
        )
    with right:
        statuses = filtered["booking_status"].value_counts().rename_axis("status").reset_index(name="bookings")
        st.plotly_chart(
            px.pie(statuses, names="status", values="bookings", hole=0.45, title="Booking status breakdown"),
            width="stretch",
        )
    hourly = filtered.groupby("booking_hour", as_index=False).size().rename(columns={"size": "bookings"})
    st.plotly_chart(
        px.bar(hourly, x="booking_hour", y="bookings", title="Ride demand by hour",
               labels={"booking_hour": "Hour of day", "bookings": "Bookings"}),
        width="stretch",
    )

with vehicle:
    vehicle_distance = (
        successful.loc[successful["ride_distance"].gt(0)]
        .groupby("vehicle_type", as_index=False)["ride_distance"]
        .sum()
        .nlargest(5, "ride_distance")
        .sort_values("ride_distance")
    )
    st.plotly_chart(
        px.bar(vehicle_distance, x="ride_distance", y="vehicle_type", orientation="h",
               title="Top 5 vehicle types by successful ride distance", labels={"ride_distance": "Distance (km)"}),
        width="stretch",
    )
    vehicle_rating = successful.groupby("vehicle_type", as_index=False)["customer_rating"].mean()
    st.plotly_chart(
        px.bar(vehicle_rating, x="vehicle_type", y="customer_rating",
               title="Average customer rating by vehicle type", labels={"customer_rating": "Average rating"}),
        width="stretch",
    )

with revenue_tab:
    payment_revenue = (
        successful.dropna(subset=["payment_method"])
        .groupby("payment_method", as_index=False)["booking_value"]
        .sum()
        .sort_values("booking_value", ascending=False)
    )
    st.plotly_chart(
        px.bar(payment_revenue, x="payment_method", y="booking_value",
               title="Successful booking value by payment method", labels={"booking_value": "Value (INR)"}),
        width="stretch",
    )
    customer_revenue = (
        successful.groupby("customer_id", as_index=False)["booking_value"]
        .sum()
        .nlargest(5, "booking_value")
        .sort_values("booking_value")
    )
    st.plotly_chart(
        px.bar(customer_revenue, x="booking_value", y="customer_id", orientation="h",
               title="Top 5 customers by successful booking value", labels={"booking_value": "Value (INR)"}),
        width="stretch",
    )
    distances = filtered.loc[filtered["ride_distance"].gt(0)].copy()
    distances["booking_day"] = distances["booking_datetime"].dt.day
    st.plotly_chart(
        px.box(distances, x="booking_day", y="ride_distance", points=False,
               title="Ride distance distribution per day", labels={"booking_day": "Day of month", "ride_distance": "Distance (km)"}),
        width="stretch",
    )

with cancellation:
    cancelled = filtered.loc[filtered["booking_status"].eq("Canceled by Customer")]
    driver_cancelled = filtered.loc[filtered["booking_status"].eq("Canceled by Driver")]
    left, right = st.columns(2)
    with left:
        customer_reasons = cancelled["canceled_rides_by_customer"].fillna("Not provided").value_counts().rename_axis("reason").reset_index(name="rides")
        st.plotly_chart(
            px.bar(customer_reasons, x="rides", y="reason", orientation="h", title="Customer cancellation reasons"),
            width="stretch",
        )
    with right:
        driver_reasons = driver_cancelled["canceled_rides_by_driver"].fillna("Not provided").value_counts().rename_axis("reason").reset_index(name="rides")
        st.plotly_chart(
            px.bar(driver_reasons, x="rides", y="reason", orientation="h", title="Driver cancellation reasons"),
            width="stretch",
        )
    st.caption(f"Driver Not Found bookings in this filter: {int(filtered['booking_status'].eq('Driver Not Found').sum()):,}")

with ratings:
    left, right = st.columns(2)
    with left:
        driver_ratings = successful.dropna(subset=["driver_ratings"])
        st.plotly_chart(
            px.histogram(driver_ratings, x="driver_ratings", nbins=10, title="Driver ratings distribution"),
            width="stretch",
        )
    with right:
        customer_ratings = successful.dropna(subset=["customer_rating"])
        st.plotly_chart(
            px.histogram(customer_ratings, x="customer_rating", nbins=10, title="Customer ratings distribution"),
            width="stretch",
        )
    comparison = successful[["driver_ratings", "customer_rating"]].dropna()
    st.plotly_chart(
        px.scatter(comparison, x="customer_rating", y="driver_ratings", opacity=0.35,
                   title="Customer vs. driver ratings", labels={"customer_rating": "Customer rating", "driver_ratings": "Driver rating"}),
        width="stretch",
    )

with sql_tab:
    st.write("Run one of the project SQL questions against the currently filtered bookings.")
    query_catalog = get_query_catalog()
    query_name = st.selectbox("SQL question", list(query_catalog))
    if st.button("Run query", type="primary"):
        try:
            connection = create_database(filtered)
            try:
                result = pd.read_sql_query(query_catalog[query_name], connection)
            finally:
                connection.close()
            st.success(f"Returned {len(result):,} row(s).")
            st.dataframe(result.head(500), width="stretch", hide_index=True)
            st.download_button(
                "Download full query result (CSV)",
                result.to_csv(index=False).encode("utf-8"),
                file_name=f"ola_{query_name.lower().replace(' ', '_')}.csv",
                mime="text/csv",
            )
        except (sqlite3.Error, pd.errors.DatabaseError) as exc:
            st.error(f"Query failed: {exc}")

with data_tab:
    st.write(f"Source: `{configured_path}`. Rows after cleaning: **{len(bookings):,}**.")
    st.dataframe(quality_report(bookings), width="stretch", hide_index=True)
    st.download_button(
        "Download filtered bookings (CSV)",
        filtered.to_csv(index=False).encode("utf-8"),
        file_name="ola_filtered_bookings.csv",
        mime="text/csv",
    )
