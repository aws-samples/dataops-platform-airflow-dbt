# Login to ECR
aws ecr get-login-password --region eu-west-1 | \
docker login --username AWS --password-stdin $ECR_URI
# Push Airflow webserver image
docker build -t airflow_webserver_cdk -f images/airflow/webserver.Dockerfile images/airflow/
docker tag airflow_webserver_cdk:latest $ECR_URI/airflow_webserver_cdk:latest
docker push $ECR_URI/airflow_webserver_cdk:latest
# Push Airflow scheduler image
docker build -t airflow_scheduler_cdk -f images/airflow/scheduler.Dockerfile images/airflow/
docker tag airflow_scheduler_cdk:latest $ECR_URI/airflow_scheduler_cdk:latest
docker push $ECR_URI/airflow_scheduler_cdk:latest
# Push Airflow worker image
docker build -t airflow_worker_cdk -f images/airflow/worker.Dockerfile images/airflow/
docker tag airflow_worker_cdk:latest $ECR_URI/airflow_worker_cdk:latest
docker push $ECR_URI/airflow_worker_cdk:latest
# Push DBT image
docker build -t dbt_cdk images/dbt/
docker tag dbt_cdk:latest $ECR_URI/dbt_cdk:latest
docker push $ECR_URI/dbt_cdk:latest
