import os
from aws_cdk import (
    aws_ec2 as ec2,
    aws_rds as rds,
    aws_secretsmanager as sm,
    core,
)
from stacks.vpc_stack import VpcStack


class RDSStack(core.Stack):
    def __init__(self, scope: core.Construct, id: str, vpc: VpcStack, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        self.db_secret = sm.Secret.from_secret_complete_arn(
            self, "postgresSecret", os.environ.get("POSTGRESS_PASS_ARN")
        )
        credentials = rds.Credentials.from_password(
            username="airflow", password=self.db_secret.secret_value
        )

        postgres = rds.DatabaseInstance(
            self,
            "RDS",
            credentials=credentials,
            instance_identifier="airflow-cdk",
            database_name="airflow",
            engine=rds.DatabaseInstanceEngine.postgres(
                version=rds.PostgresEngineVersion.VER_9_6_18
            ),
            vpc=vpc.instance,
            vpc_placement=ec2.SubnetSelection(subnet_type=ec2.SubnetType.ISOLATED),
            port=5432,
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.BURSTABLE2,
                ec2.InstanceSize.MICRO,
            ),
            allocated_storage=20,
            security_groups=[vpc.postgres_sg],
            removal_policy=core.RemovalPolicy.DESTROY,
            parameter_group=rds.ParameterGroup.from_parameter_group_name(
                self, "para-group-postgres", parameter_group_name="default.postgres9.6"
            ),
            deletion_protection=False,
        )

        self._instance = postgres

    @property
    def instance(self) -> core.Resource:
        return self._instance
