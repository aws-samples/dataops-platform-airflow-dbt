#!/usr/bin/env python3

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


ENV_EU = core.Environment(region="eu-west-1")

app = core.App()

ecr = ECRStack(app, "ECRStack", env=ENV_EU)
s3 = S3Stack(app, "S3Stack", env=ENV_EU)
vpc = VpcStack(app, "VpcStack", env=ENV_EU)

redshift = RedshiftClusterStack(app, "RedshiftClusterStack", vpc, env=ENV_EU)
redshift.add_dependency(vpc)

rds = RDSStack(app, "RDSStack", vpc, env=ENV_EU)
rds.add_dependency(vpc)

redis = RedisStack(app, "RedisStack", vpc, env=ENV_EU)
redis.add_dependency(vpc)

airflow_cluster_props = {
    "vpc": vpc,
    "s3": s3,
}
airflow_cluster = AirflowClusterStack(
    app,
    "AirflowClusterStack",
    airflow_cluster_props,
    env=ENV_EU,
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
airflow_services = AirflowServices(app, "airflow", airflow_services_props, env=ENV_EU)

dbt_props = {"airflow_cluster": airflow_cluster, "ecr": ecr, "redshift": redshift}
dbt = DBT(app, "dbt", dbt_props, env=ENV_EU)

app.synth()
