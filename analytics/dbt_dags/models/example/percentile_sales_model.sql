/*
    Get percentiles of all time gross sales.
*/

{{ config(materialized='table') }}

SELECT eventid, total_price, ntile(1000) over(order by total_price desc) as percentile 
FROM {{ ref('all_gross_sales_model') }} 
