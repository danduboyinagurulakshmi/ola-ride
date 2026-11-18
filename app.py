from __future__ import annotations

import os
import sqlite3
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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

if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

dark_mode = st.session_state.dark_mode
palette = {
    "background": "#0B1110" if dark_mode else "#F5F7F2",
    "surface": "#121B19" if dark_mode else "#FFFFFF",
    "surface_alt": "#182320" if dark_mode else "#EDF2EB",
    "text": "#ECF4EA" if dark_mode else "#15221D",
    "muted": "#9BAFA6" if dark_mode else "#69776E",
    "border": "#263630" if dark_mode else "#E1E8DF",
    "accent": "#B9F36A",
    "accent_text": "#16230E",
    "grid": "#293832" if dark_mode else "#E6EBE4",
}

def render_chart(figure: go.Figure, width: str = "stretch") -> None:
    figure.update_layout(
        template="none",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Inter, Segoe UI, sans-serif", "color": palette["muted"]},
        colorway=["#8AD56B", "#58B5A7", "#F2B84B", "#8A9AF5", "#EA829A", "#53C9D8"],
        xaxis={"gridcolor": palette["grid"], "zerolinecolor": palette["grid"], "linecolor": palette["border"]},
        yaxis={"gridcolor": palette["grid"], "zerolinecolor": palette["grid"], "linecolor": palette["border"]},
        title={"font": {"size": 15, "color": palette["text"]}, "x": 0.02, "xanchor": "left"},
        legend={"font": {"color": palette["muted"]}, "bgcolor": "rgba(0,0,0,0)"},
        margin={"l": 22, "r": 18, "t": 58, "b": 26},
    )
    st.plotly_chart(figure, width=width, theme=None)


st.markdown(
    f"""
    <style>
    :root {{
        color-scheme: {"dark" if dark_mode else "light"};
        --page: {palette["background"]};
        --surface: {palette["surface"]};
        --surface-alt: {palette["surface_alt"]};
        --ink: {palette["text"]};
        --muted: {palette["muted"]};
        --line: {palette["border"]};
        --lime: {palette["accent"]};
        --lime-ink: {palette["accent_text"]};
    }}
    [data-testid="stAppViewContainer"] {{
        background:
            radial-gradient(ellipse at 86% 0%, {"rgba(125, 196, 81, .10)" if dark_mode else "rgba(139, 184, 112, .13)"} 0, transparent 34rem),
            var(--page);
        color: var(--ink);
    }}
    [data-testid="stHeader"] {{ background: transparent; }}
    [data-testid="stSidebar"] {{
        background: var(--surface);
        border-right: 1px solid var(--line);
    }}
    [data-testid="stSidebar"] > div:first-child {{ padding-top: 1.4rem; }}
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {{ color: var(--muted); }}
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] h4 {{ color: var(--ink) !important; }}
    [data-testid="stSidebar"] [data-baseweb="input"] > div,
    [data-testid="stSidebar"] [data-baseweb="select"] > div,
    [data-testid="stSidebar"] [data-testid="stDateInput"] input {{
        background: var(--surface-alt) !important;
        color: var(--ink) !important;
        border-color: var(--line) !important;
    }}
    [data-testid="stSidebar"] [data-baseweb="popover"],
    [data-testid="stSidebar"] [role="listbox"] {{
        background: var(--surface) !important;
        color: var(--ink) !important;
    }}
    [data-testid="stMain"] .block-container {{
        max-width: 1540px;
        padding: 2.4rem clamp(1.2rem, 3.2vw, 3.5rem) 4rem;
    }}
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {{ gap: .75rem; }}
    .brand {{
        display: flex; align-items: center; gap: .7rem;
        color: var(--ink); font-size: 1.05rem; font-weight: 750;
        letter-spacing: -.035em; margin: .15rem 0 1.3rem;
    }}
    .brand-mark {{
        display: grid; place-items: center; width: 2rem; height: 2rem;
        border-radius: .7rem; background: var(--lime); color: var(--lime-ink);
        font-weight: 900; box-shadow: 0 5px 18px rgba(145, 207, 89, .22);
    }}
    .hero {{
        position: relative; overflow: hidden;
        padding: clamp(1.5rem, 3.4vw, 2.65rem);
        margin: .5rem 0 1.45rem;
        border: 1px solid var(--line); border-radius: 1.35rem;
        background: linear-gradient(118deg, var(--surface) 30%, var(--surface-alt) 100%);
        animation: rise-in .55s cubic-bezier(.2,.8,.2,1) both;
    }}
    .hero::after {{
        content: ""; position: absolute; width: 19rem; height: 19rem;
        right: -5rem; top: -11rem; border-radius: 50%;
        border: 1px solid {"rgba(185,243,106,.17)" if dark_mode else "rgba(87,130,66,.13)"};
        box-shadow: 0 0 0 2.2rem {"rgba(185,243,106,.035)" if dark_mode else "rgba(87,130,66,.035)"},
                    0 0 0 4.4rem {"rgba(185,243,106,.025)" if dark_mode else "rgba(87,130,66,.025)"};
        pointer-events: none;
    }}
    .eyebrow {{
        color: var(--muted); font-size: .73rem; font-weight: 750;
        letter-spacing: .13em; text-transform: uppercase; margin-bottom: .65rem;
    }}
    .hero h1 {{
        color: var(--ink); font-size: clamp(2rem, 4vw, 3.1rem);
        letter-spacing: -.065em; line-height: 1.04; margin: 0 0 .7rem;
    }}
    .hero p {{ color: var(--muted); font-size: .98rem; max-width: 42rem; margin: 0; }}
    .hero-chip {{
        display: inline-flex; align-items: center; gap: .45rem;
        border: 1px solid var(--line); border-radius: 999px;
        color: var(--ink); background: var(--surface); padding: .45rem .72rem;
        font-size: .76rem; font-weight: 650; margin-top: 1.15rem;
    }}
    .hero-chip span {{
        width: .43rem; height: .43rem; background: #83CE69; border-radius: 50%;
        box-shadow: 0 0 0 .22rem rgba(131,206,105,.12);
    }}
    [data-testid="stMetric"] {{
        background: var(--surface); border: 1px solid var(--line);
        border-radius: 1rem; padding: 1.1rem 1.2rem;
        min-height: 7.3rem;
        transition: transform .2s ease, border-color .2s ease, box-shadow .2s ease;
        animation: rise-in .48s cubic-bezier(.2,.8,.2,1) both;
    }}
    [data-testid="stMetric"]:hover {{
        transform: translateY(-3px); border-color: {"#465C4B" if dark_mode else "#B8CDAE"};
        box-shadow: 0 12px 30px rgba(24, 45, 28, .08);
    }}
    [data-testid="stMetricLabel"] p {{
        color: var(--muted); font-size: .78rem; font-weight: 600;
    }}
    [data-testid="stMetricValue"] {{ color: var(--ink); font-size: 1.75rem; font-weight: 760; }}
    [data-testid="stMetricDelta"] {{ font-size: .75rem; }}
    [data-testid="stTabs"] {{ margin-top: 1.7rem; }}
    [data-testid="stTabs"] [role="tablist"] {{
        gap: .35rem; border-bottom: 1px solid var(--line);
    }}
    [data-testid="stTabs"] button[role="tab"] {{
        border-radius: .7rem .7rem 0 0; color: var(--muted);
        padding: .75rem .95rem; font-size: .83rem; font-weight: 650;
        transition: color .18s ease, background .18s ease;
    }}
    [data-testid="stTabs"] button[role="tab"][aria-selected="true"] {{
        background: var(--surface-alt); color: var(--ink);
    }}
    [data-testid="stTabs"] button[role="tab"][aria-selected="true"] p {{
        color: var(--ink);
    }}
    [data-testid="stPlotlyChart"] {{
        background: var(--surface); border: 1px solid var(--line);
        border-radius: 1rem; padding: .5rem .35rem .1rem;
        animation: rise-in .5s ease both;
    }}
    [data-testid="stDataFrame"] {{
        border: 1px solid var(--line); border-radius: .85rem; overflow: hidden;
    }}
    [data-testid="stButton"] button[kind="primary"] {{
        background: var(--lime); color: var(--lime-ink); border: 0;
        border-radius: .7rem; font-weight: 700;
    }}
    [data-testid="stButton"] button {{ border-radius: .7rem; }}
    hr {{ border-color: var(--line); }}
    @keyframes rise-in {{
        from {{ opacity: 0; transform: translateY(10px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    @media (prefers-reduced-motion: reduce) {{
        *, *::before, *::after {{
            animation-duration: .01ms !important; animation-iteration-count: 1 !important;
            scroll-behavior: auto !important; transition-duration: .01ms !important;
        }}
    }}
    @media (max-width: 760px) {{
        [data-testid="stMain"] .block-container {{ padding-top: 1rem; }}
        [data-testid="stMetric"] {{ min-height: 6rem; padding: .85rem; }}
        [data-testid="stTabs"] [role="tablist"] {{ overflow-x: auto; }}
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

st.sidebar.markdown(
    '<div class="brand"><span class="brand-mark">O</span> Ola <span style="font-weight:450">Insights</span></div>',
    unsafe_allow_html=True,
)
st.sidebar.toggle("Dark appearance", key="dark_mode")
st.markdown(
    """
    <section class="hero">
      <div class="eyebrow">Mobility intelligence · Bengaluru</div>
      <h1>Every ride tells<br>you something.</h1>
      <p>A clear view of demand, service quality, and revenue across your ride network.</p>
      <div class="hero-chip"><span></span> July 2024 · 31 days of ride activity</div>
    </section>
    """,
    unsafe_allow_html=True,
)


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

st.sidebar.markdown("### Refine your view")
st.sidebar.caption("Choose what to include in your analysis.")
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
missing_payment_label = "Not recorded"
if bookings["payment_method"].isna().any():
    payment_options.append(missing_payment_label)
selected_statuses = st.sidebar.multiselect("Booking status", status_options, default=status_options)
selected_vehicles = st.sidebar.multiselect("Vehicle type", vehicle_options, default=vehicle_options)
selected_payments = st.sidebar.multiselect("Payment method", payment_options, default=payment_options)

date_mask = bookings["booking_datetime"].dt.date.between(start_date, end_date)
payment_mask = (
    bookings["payment_method"].astype("string").fillna(missing_payment_label).isin(selected_payments)
)
filtered = bookings.loc[
    date_mask
    & bookings["booking_status"].isin(selected_statuses)
    & bookings["vehicle_type"].isin(selected_vehicles)
    & payment_mask
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
        render_chart(
            px.line(daily, x="date", y="bookings", markers=True, title="Ride volume over time"),
            width="stretch",
        )
    with right:
        statuses = filtered["booking_status"].value_counts().rename_axis("status").reset_index(name="bookings")
        render_chart(
            px.pie(statuses, names="status", values="bookings", hole=0.45, title="Booking status breakdown"),
            width="stretch",
        )
    hourly = filtered.groupby("booking_hour", as_index=False).size().rename(columns={"size": "bookings"})
    render_chart(
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
    render_chart(
        px.bar(vehicle_distance, x="ride_distance", y="vehicle_type", orientation="h",
               title="Top 5 vehicle types by successful ride distance", labels={"ride_distance": "Distance (km)"}),
        width="stretch",
    )
    vehicle_rating = successful.groupby("vehicle_type", as_index=False)["customer_rating"].mean()
    render_chart(
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
    render_chart(
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
    render_chart(
        px.bar(customer_revenue, x="booking_value", y="customer_id", orientation="h",
               title="Top 5 customers by successful booking value", labels={"booking_value": "Value (INR)"}),
        width="stretch",
    )
    distances = filtered.loc[filtered["ride_distance"].gt(0)].copy()
    distances["booking_day"] = distances["booking_datetime"].dt.day
    render_chart(
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
        render_chart(
            px.bar(customer_reasons, x="rides", y="reason", orientation="h", title="Customer cancellation reasons"),
            width="stretch",
        )
    with right:
        driver_reasons = driver_cancelled["canceled_rides_by_driver"].fillna("Not provided").value_counts().rename_axis("reason").reset_index(name="rides")
        render_chart(
            px.bar(driver_reasons, x="rides", y="reason", orientation="h", title="Driver cancellation reasons"),
            width="stretch",
        )
    st.caption(f"Driver Not Found bookings in this filter: {int(filtered['booking_status'].eq('Driver Not Found').sum()):,}")

with ratings:
    left, right = st.columns(2)
    with left:
        driver_ratings = successful.dropna(subset=["driver_ratings"])
        render_chart(
            px.histogram(driver_ratings, x="driver_ratings", nbins=10, title="Driver ratings distribution"),
            width="stretch",
        )
    with right:
        customer_ratings = successful.dropna(subset=["customer_rating"])
        render_chart(
            px.histogram(customer_ratings, x="customer_rating", nbins=10, title="Customer ratings distribution"),
            width="stretch",
        )
    comparison = successful[["driver_ratings", "customer_rating"]].dropna()
    render_chart(
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
