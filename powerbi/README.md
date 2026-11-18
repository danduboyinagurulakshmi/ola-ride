# Power BI report build

## Load and model the data

1. Run `python -m scripts.run_eda` from the project root.
2. In Power BI Desktop, select **Get data > Text/CSV** and choose `reports/cleaned_bookings.csv`.
3. Confirm `booking_datetime` is a Date/Time column, `booking_value` and `ride_distance` are numeric, and the rating fields are decimal numbers.
4. Create a date hierarchy from `booking_datetime` or use `date` for daily analysis. Set `booking_id` to **Don't summarize**.
5. Add measures from `DAX_Measures.dax`.

The dataset is a single July 2024 fact table; no relationships are required for the proposed visuals. The measures reference the loaded table name `bookings`. Rename the imported query to `bookings` or update the table names in the measures.

## Suggested report pages and visuals

### Overall

- Line chart: booking count by `booking_datetime` (day); use **Total Bookings**.
- Column chart: booking count by `booking_hour` to identify demand peaks.
- Donut: `booking_status` by **Total Bookings**.
- KPI cards: **Total Bookings**, **Success Rate**, **Successful Booking Value (INR)**.

### Vehicle type

- Bar chart: vehicle type by successful ride distance. Use a visual filter for `booking_status = Success`, `ride_distance > 0`, aggregate distance as Sum, and Top N 5 by Sum of `ride_distance`.
- Bar chart: vehicle type by **Average Customer Rating**.

### Revenue

- Bar chart: `payment_method` by **Successful Booking Value (INR)**.
- Bar chart: `customer_id` by successful booking value, Top N 5.
- Box plot custom visual or daily column chart with `ride_distance` distribution by day. Exclude zero distances and unsuccessful bookings for completed-trip analysis.

### Cancellations

- Two bar charts filtered separately to `Canceled by Customer` and `Canceled by Driver`, using `canceled_rides_by_customer` and `canceled_rides_by_driver` as reason.
- Keep `Driver Not Found` visible as its own booking status rather than silently combining it with driver cancellations.

### Ratings

- Histograms of `driver_ratings` and `customer_rating` for successful bookings.
- Scatter plot: customer rating versus driver rating, successful bookings only.

Add slicers for date, `vehicle_type`, `booking_status`, and `payment_method`. Use descriptive titles and label currency as INR. Publish through the organization's Power BI workspace when ready.
