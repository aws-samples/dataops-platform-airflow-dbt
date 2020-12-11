/*
    Get data on top 10 buyers by quantity.
*/

{{ config(materialized='table') }}

SELECT firstname, lastname, total_quantity 
FROM {{ ref('top_buyers_by_quantity_model') }} q, users
WHERE q.buyerid = userid
ORDER BY q.total_quantity DESC
