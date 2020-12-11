/*
    All time gross sales.
*/

{{ config(materialized='table') }}

SELECT eventid, sum(pricepaid) total_price
FROM sales
GROUP BY eventid
