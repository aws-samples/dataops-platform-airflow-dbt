import os
from aws_cdk import (
    core,
    aws_ecs as ecs,
)
from types import SimpleNamespace
from stacks.airflow_cluster_stack import AirflowClusterStack
from stacks.ecr_stack import ECRStack
from stacks.redshift_cluster_stack import RedshiftClusterStack
from types import SimpleNamespace
from typing_extensions import TypedDict

props_type = TypedDict(
    "props_type",
    {
        "airflow_cluster": AirflowClusterStack,
        "ecr": ECRStack,
        "redshift": RedshiftClusterStack,
    },
)


class DBT(core.Stack):
    def __init__(
        self, scope: core.Construct, id: str, props: props_type, **kwargs
    ) -> None:
        super().__init__(scope, id, **kwargs)
        ns = SimpleNamespace(**props)

        bucket_name = os.environ.get("BUCKET_NAME")
        dbt_task = ecs.FargateTaskDefinition(
            self,
            "dbt-cdk",
            family="dbt-cdk",
            cpu=512,
            memory_limit_mib=1024,
            task_role=ns.airflow_cluster.airflow_task_role,
            execution_role=ns.airflow_cluster.task_execution_role,
        )
        dbt_task.add_container(
            "dbt-cdk-container",
            image=ecs.ContainerImage.from_ecr_repository(
                ns.ecr.dbt_repo,
                os.environ.get("IMAGE_TAG", "latest"),
            ),
            logging=ecs.AwsLogDriver(
                stream_prefix="ecs", log_group=ns.airflow_cluster.dbt_log_group
            ),
            environment={
                "BUCKET_NAME": bucket_name,
                "REDSHIFT_HOST": ns.redshift.instance.cluster_endpoint.hostname,
            },
            secrets={
                "REDSHIFT_USER": ecs.Secret.from_secrets_manager(
                    ns.redshift.redshift_secret, field="username"
                ),
                "REDSHIFT_PASSWORD": ecs.Secret.from_secrets_manager(
                    ns.redshift.redshift_secret, field="password"
                ),
            },
        )
