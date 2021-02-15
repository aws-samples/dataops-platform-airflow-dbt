import os

from aws_cdk import core, aws_ecs as ecs, aws_iam as iam, aws_logs
from stacks.vpc_stack import VpcStack
from stacks.s3_stack import S3Stack
from types import SimpleNamespace
from typing_extensions import TypedDict

props_type = TypedDict("props_type", {"vpc": VpcStack, "s3": S3Stack})


class AirflowClusterStack(core.Stack):
    def __init__(
        self, scope: core.Construct, id: str, props: props_type, **kwargs
    ) -> None:
        super().__init__(scope, id, **kwargs)
        ns = SimpleNamespace(**props)

        # Fargate task execution role
        self.task_execution_role = iam.Role(
            self,
            "AirlfowTaskExecutionRole",
            role_name="AirlfowTaskExecutionRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AmazonECSTaskExecutionRolePolicy"
                )
            ],
        )

        # Airflow cluster task role
        self.airflow_task_role = iam.Role(
            self,
            "AirflowTaskRole",
            role_name="AirflowTaskRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AmazonECSTaskExecutionRolePolicy"
                )
            ],
        )

        # Attach policies to Airflow task role
        iam.Policy(
            self,
            "AirflowECSOperatorPolicy",
            statements=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "ecs:RunTask",
                        "logs:GetLogEvents",
                        "logs:FilterLogEvents",
                        "ecs:DescribeTasks",
                    ],
                    resources=["*"],
                ),
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=["iam:PassRole"],
                    resources=[self.task_execution_role.role_arn, self.airflow_task_role.role_arn],
                    conditions={
                        "StringLike": {"iam:PassedToService": "ecs-tasks.amazonaws.com"}
                    },
                ),
            ],
            roles=[self.airflow_task_role],
        )
        iam.Policy(
            self,
            "AiflowSecretsAccess",
            statements=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=["secretsmanager:GetSecretValue"],
                    resources=["*"],
                ),
            ],
            roles=[self.airflow_task_role],
        )
        iam.Policy(
            self,
            "AirflowS3Access",
            statements=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "s3:ListBucket",
                        "s3:GetObject",
                        "s3:GetBucketLocation",
                    ],
                    resources=[
                        f"{ns.s3.instance.bucket_arn}",
                        f"{ns.s3.instance.bucket_arn}/*",
                    ],
                ),
            ],
            roles=[self.airflow_task_role],
        )

        # Airflow cluster
        self._instance = ecs.Cluster(
            self,
            "MyCluster",
            cluster_name="MyCluster",
            vpc=ns.vpc.instance,
            container_insights=True,
        )

        # Create log groups
        self.webserver_log_group = aws_logs.LogGroup(
            self,
            "webserverLogGroup",
            log_group_name="/ecs/webserver-cdk",
            retention=aws_logs.RetentionDays.ONE_MONTH,
            removal_policy=core.RemovalPolicy.DESTROY,
        )
        self.scheduler_log_group = aws_logs.LogGroup(
            self,
            "schedulerLogGroup",
            log_group_name="/ecs/scheduler-cdk",
            retention=aws_logs.RetentionDays.ONE_MONTH,
            removal_policy=core.RemovalPolicy.DESTROY,
        )
        self.worker_log_group = aws_logs.LogGroup(
            self,
            "workerLogGroup",
            log_group_name="/ecs/worker-cdk",
            retention=aws_logs.RetentionDays.ONE_MONTH,
            removal_policy=core.RemovalPolicy.DESTROY,
        )
        self.dbt_log_group = aws_logs.LogGroup(
            self,
            "dbtLogGroup",
            log_group_name="/ecs/dbt-cdk",
            retention=aws_logs.RetentionDays.ONE_MONTH,
            removal_policy=core.RemovalPolicy.DESTROY,
        )

    @property
    def instance(self) -> core.Resource:
        return self._instance