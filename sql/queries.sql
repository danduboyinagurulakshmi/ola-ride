-- name: Successful bookings
SELECT *
FROM bookings
WHERE booking_status = 'Success';

-- name: Average successful ride distance by vehicle
SELECT vehicle_type, ROUND(AVG(ride_distance), 2) AS average_ride_distance_km
FROM bookings
WHERE booking_status = 'Success'
  AND ride_distance > 0
GROUP BY vehicle_type
ORDER BY average_ride_distance_km DESC;

-- name: Customer-cancelled rides
SELECT COUNT(*) AS customer_cancelled_rides
FROM bookings
WHERE booking_status = 'Canceled by Customer';

-- name: Top 5 customers by number of bookings
SELECT customer_id, COUNT(*) AS booking_count
FROM bookings
WHERE customer_id IS NOT NULL
GROUP BY customer_id
ORDER BY booking_count DESC, customer_id
LIMIT 5;

-- name: Driver cancellations by reason
SELECT canceled_rides_by_driver AS cancellation_reason, COUNT(*) AS cancelled_rides
FROM bookings
WHERE booking_status = 'Canceled by Driver'
  AND canceled_rides_by_driver IS NOT NULL
GROUP BY canceled_rides_by_driver
ORDER BY cancelled_rides DESC;

-- name: Prime Sedan driver rating range
SELECT MIN(driver_ratings) AS minimum_driver_rating,
       MAX(driver_ratings) AS maximum_driver_rating
FROM bookings
WHERE vehicle_type = 'Prime Sedan'
  AND booking_status = 'Success';

-- name: UPI bookings
SELECT *
FROM bookings
WHERE payment_method = 'UPI';

-- name: Average customer rating by vehicle
SELECT vehicle_type, ROUND(AVG(customer_rating), 2) AS average_customer_rating
FROM bookings
WHERE booking_status = 'Success'
  AND customer_rating IS NOT NULL
GROUP BY vehicle_type
ORDER BY average_customer_rating DESC;

-- name: Successful booking value
SELECT COALESCE(SUM(booking_value), 0) AS successful_booking_value
FROM bookings
WHERE booking_status = 'Success';

-- name: Incomplete rides and reason
SELECT booking_id, customer_id, vehicle_type, incomplete_rides_reason
FROM bookings
WHERE LOWER(CAST(incomplete_rides AS TEXT)) IN ('yes', 'true', '1')
   OR booking_status = 'Incomplete';
