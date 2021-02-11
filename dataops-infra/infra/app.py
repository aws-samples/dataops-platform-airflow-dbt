#!/usr/bin/env python3
import os
from aws_cdk import core

from stacks.vpc_stack import VpcStack
from stacks.ecr_stack import ECRStack
from stacks.s3_stack import S3Stack
from stacks.airflow_rds import RDSStack
from stacks.airflow_cluster_stack import AirflowClusterStack
from stacks.airflow_redis import RedisStack
from stacks.fargate_services.airflow import AirflowServices
from stacks.fargate_services.dbt import DBT
from stacks.redshift_cluster_stack import RedshiftClusterStack

env = core.Environment(region=os.environ.get("AWS_REGION"))
app = core.App()

ecr = ECRStack(app, "ECRStack", env=env)
s3 = S3Stack(app, "S3Stack", env=env)
vpc = VpcStack(app, "VpcStack", env=env)

redshift = RedshiftClusterStack(app, "RedshiftClusterStack", vpc, env=env)
redshift.add_dependency(vpc)

rds = RDSStack(app, "RDSStack", vpc, env=env)
rds.add_dependency(vpc)

redis = RedisStack(app, "RedisStack", vpc, env=env)
redis.add_dependency(vpc)

airflow_cluster_props = {
    "vpc": vpc,
    "s3": s3,
}
airflow_cluster = AirflowClusterStack(
    app,
    "AirflowClusterStack",
    airflow_cluster_props,
    env=env,
)
airflow_cluster.add_dependency(redis)
airflow_cluster.add_dependency(rds)
airflow_cluster.add_dependency(ecr)

airflow_services_props = {
    "airflow_cluster": airflow_cluster,
    "ecr": ecr,
    "vpc": vpc,
    "rds": rds,
    "redis": redis,
}
airflow_services = AirflowServices(app, "airflow", airflow_services_props, env=env)

dbt_props = {"airflow_cluster": airflow_cluster, "ecr": ecr, "redshift": redshift}
dbt = DBT(app, "dbt", dbt_props, env=env)

app.synth()
