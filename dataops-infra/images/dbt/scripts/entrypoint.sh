#!/usr/bin/env bash

aws s3 sync s3://$BUCKET_NAME/dbt_dags dbt_dags
cd dbt_dags
dbt debug
exec "$@"
