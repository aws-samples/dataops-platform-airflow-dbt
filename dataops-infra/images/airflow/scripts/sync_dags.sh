while :
do
    aws s3 sync s3://$BUCKET_NAME/airflow_dags /opt/bitnami/airflow/dags --delete
    sleep 60
done
