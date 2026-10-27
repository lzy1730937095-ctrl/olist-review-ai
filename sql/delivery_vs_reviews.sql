-- Olist 订单与评价分析（SQLite）
-- 表名对应 Kaggle 原始 CSV：orders = olist_orders_dataset，reviews = olist_order_reviews_dataset，customers = olist_customers_dataset

-- 1. 各订单状态的平均评分与订单数
SELECT o.order_status,
       ROUND(AVG(r.review_score), 2) AS avg_score,
       COUNT(*) AS n
FROM orders o
JOIN reviews r ON o.order_id = r.order_id
GROUP BY o.order_status
ORDER BY avg_score;

-- 2. 订单量最多的 5 个州
SELECT c.customer_state, COUNT(*) AS n_orders
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
GROUP BY c.customer_state
ORDER BY n_orders DESC
LIMIT 5;

-- 3. 核心问题：配送延迟 vs 准时的评分与差评率（只看已送达订单）
--    口径：只比较日期部分，避免“当天送达但晚于 00:00”被误判为延迟
WITH t AS (
    SELECT o.order_id,
           r.review_score,
           CASE
             WHEN DATE(o.order_delivered_customer_date) > DATE(o.order_estimated_delivery_date) THEN '延迟'
             ELSE '准时'
           END AS delivery_status
    FROM orders o
    JOIN reviews r ON o.order_id = r.order_id
    WHERE o.order_status = 'delivered'
      AND o.order_delivered_customer_date IS NOT NULL   -- 有 8 笔“已送达”订单缺少送达时间，排除，避免被 ELSE 误归为准时
)
SELECT delivery_status,
       COUNT(*) AS n,
       ROUND(AVG(review_score), 2) AS avg_score,
       ROUND(100.0 * SUM(review_score <= 2) / COUNT(*), 1) AS low_score_pct
FROM t
GROUP BY delivery_status;

-- 4. 剂量效应：延迟天数越长，评分是否越低
WITH t AS (
    SELECT julianday(DATE(o.order_delivered_customer_date))
             - julianday(DATE(o.order_estimated_delivery_date)) AS days_late,
           r.review_score
    FROM orders o
    JOIN reviews r ON o.order_id = r.order_id
    WHERE o.order_status = 'delivered'
      AND o.order_delivered_customer_date IS NOT NULL
)
SELECT CASE
         WHEN days_late <= 0  THEN '0 准时'
         WHEN days_late <= 3  THEN '1 晚1-3天'
         WHEN days_late <= 7  THEN '2 晚4-7天'
         WHEN days_late <= 14 THEN '3 晚8-14天'
         ELSE '4 晚15天以上'
       END AS bucket,
       COUNT(*) AS n,
       ROUND(AVG(review_score), 2) AS avg_score,
       ROUND(100.0 * SUM(review_score <= 2) / COUNT(*), 1) AS low_score_pct
FROM t
GROUP BY bucket
ORDER BY bucket;

-- 5. 差评来源：已送达 vs 其他状态的差评数量
SELECT CASE WHEN o.order_status = 'delivered' THEN '已送达' ELSE '其他状态' END AS status_group,
       COUNT(*) AS n_reviews,
       SUM(r.review_score <= 2) AS n_low_score
FROM orders o
JOIN reviews r ON o.order_id = r.order_id
GROUP BY status_group;

-- 6. 控制变量：按州比较准时 / 延迟订单的评分（检验“地区用户本来就爱打低分”）
WITH t AS (
    SELECT c.customer_state,
           r.review_score,
           CASE
             WHEN DATE(o.order_delivered_customer_date) > DATE(o.order_estimated_delivery_date) THEN '延迟'
             ELSE '准时'
           END AS delivery_status
    FROM orders o
    JOIN reviews r   ON o.order_id = r.order_id
    JOIN customers c ON o.customer_id = c.customer_id
    WHERE o.order_status = 'delivered'
      AND o.order_delivered_customer_date IS NOT NULL
)
SELECT customer_state,
       COUNT(*) AS n,
       ROUND(AVG(CASE WHEN delivery_status = '准时' THEN review_score END), 2) AS on_time_avg,
       ROUND(AVG(CASE WHEN delivery_status = '延迟' THEN review_score END), 2) AS late_avg
FROM t
GROUP BY customer_state
ORDER BY n DESC
LIMIT 5;
