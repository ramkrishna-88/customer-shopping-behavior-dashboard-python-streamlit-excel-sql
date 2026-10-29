-- Customer Shopping Behavior Analysis (SQLite-compatible)
-- Run these queries after importing data into a table named shopping_behavior.

-- 1. Overall business KPIs
SELECT COUNT(*) AS total_orders,
       COUNT(DISTINCT Customer_ID) AS unique_customers,
       ROUND(SUM(Purchase_Amount_USD), 2) AS total_revenue,
       ROUND(AVG(Purchase_Amount_USD), 2) AS average_order_value,
       ROUND(AVG(Review_Rating), 2) AS average_rating
FROM shopping_behavior;

-- 2. Revenue and order count by category
SELECT Category, COUNT(*) AS orders,
       ROUND(SUM(Purchase_Amount_USD), 2) AS revenue,
       ROUND(AVG(Purchase_Amount_USD), 2) AS average_order_value
FROM shopping_behavior
GROUP BY Category
ORDER BY revenue DESC;

-- 3. Monthly revenue trend
SELECT substr(Purchase_Date, 1, 7) AS month,
       COUNT(*) AS orders,
       ROUND(SUM(Purchase_Amount_USD), 2) AS revenue
FROM shopping_behavior
GROUP BY substr(Purchase_Date, 1, 7)
ORDER BY month;

-- 4. Most purchased products
SELECT Item_Purchased, COUNT(*) AS orders,
       ROUND(SUM(Purchase_Amount_USD), 2) AS revenue
FROM shopping_behavior
GROUP BY Item_Purchased
ORDER BY orders DESC
LIMIT 10;

-- 5. Customer spending tiers (based on total recorded spend)
WITH customer_spend AS (
    SELECT Customer_ID, COUNT(*) AS orders,
           SUM(Purchase_Amount_USD) AS total_spend
    FROM shopping_behavior
    GROUP BY Customer_ID
)
SELECT Customer_ID, orders, ROUND(total_spend, 2) AS total_spend,
       CASE
         WHEN total_spend >= 500 THEN 'High Spend'
         WHEN total_spend >= 200 THEN 'Medium Spend'
         ELSE 'Low Spend'
       END AS spending_segment
FROM customer_spend
ORDER BY total_spend DESC;

-- 6. Discount vs non-discount purchase behavior
SELECT Discount_Applied, COUNT(*) AS orders,
       ROUND(AVG(Purchase_Amount_USD), 2) AS average_order_value,
       ROUND(AVG(Review_Rating), 2) AS average_rating
FROM shopping_behavior
GROUP BY Discount_Applied;

-- 7. Ratings by category
SELECT Category, ROUND(AVG(Review_Rating), 2) AS average_rating,
       COUNT(*) AS review_count
FROM shopping_behavior
GROUP BY Category
ORDER BY average_rating DESC;

-- 8. Payment method popularity
SELECT Payment_Method, COUNT(*) AS orders,
       ROUND(SUM(Purchase_Amount_USD), 2) AS revenue
FROM shopping_behavior
GROUP BY Payment_Method
ORDER BY orders DESC;

-- 9. Subscription status comparison
SELECT Subscription_Status, COUNT(*) AS orders,
       ROUND(AVG(Purchase_Amount_USD), 2) AS average_order_value,
       ROUND(AVG(Review_Rating), 2) AS average_rating
FROM shopping_behavior
GROUP BY Subscription_Status;

-- 10. Regional performance
SELECT Location, COUNT(*) AS orders,
       ROUND(SUM(Purchase_Amount_USD), 2) AS revenue
FROM shopping_behavior
GROUP BY Location
ORDER BY revenue DESC;
