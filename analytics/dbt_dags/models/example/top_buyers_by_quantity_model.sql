/*
    Find top 10 buyers by quantity.
*/

{{ config(materialized='table') }}

SELECT buyerid, sum(qtysold) total_quantity
FROM sales
GROUP BY buyerid
ORDER BY total_quantity DESC
LIMIT 10
