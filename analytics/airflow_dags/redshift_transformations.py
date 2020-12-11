import os
from airflow import DAG
from airflow.contrib.operators.ecs_operator import ECSOperator
from airflow.operators.bash_operator import BashOperator
from airflow.utils.dates import days_ago
from datetime import timedelta

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": days_ago(2),
    "retries": 0,
    "retry_delay": timedelta(minutes=5),
}

dag = DAG(
    "redshift_transformations",
    default_args=default_args,
    description="Runs dbt container",
    schedule_interval=None,
    is_paused_upon_creation=False,
)

bash_task = BashOperator(task_id="run_bash_echo", bash_command="echo 1", dag=dag)
post_task = BashOperator(task_id="post_dbt", bash_command="echo 0", dag=dag)

dbt_top_events = ECSOperator(
    task_id="dbt_top_events",
    dag=dag,
    aws_conn_id="aws_ecs",
    cluster="MyCluster",
    task_definition="dbt-cdk",
    launch_type="FARGATE",
    overrides={
        "containerOverrides": [
            {
                "name": "dbt-cdk-container",
                "command": ["dbt", "run"],
            },
        ],
    },
    network_configuration={
        "awsvpcConfiguration": {
            "securityGroups": ["<SECURITY_GROUP_ID>"],
            "subnets": ["<SUBNET_ID>", "<SUBNET_ID>"],
        },
    },
    awslogs_group="/ecs/dbt-cdk",
    awslogs_stream_prefix="ecs/dbt-cdk-container",
)

bash_task >> dbt_top_events >> post_task
