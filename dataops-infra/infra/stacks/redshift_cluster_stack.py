import os
from aws_cdk import (
    aws_redshift as redshift,
    aws_secretsmanager as sm,
    aws_ec2 as ec2,
    aws_iam as iam,
    core,
)
from stacks.vpc_stack import VpcStack


class RedshiftClusterStack(core.Stack):
    def __init__(self, scope: core.Construct, id: str, vpc: VpcStack, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        self.redshift_user = "redshift-user"
        subnet_group = redshift.ClusterSubnetGroup(
            self,
            id="RedshiftSubnetGroup",
            description="Redshift private subnet group",
            vpc=vpc.instance,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.ISOLATED),
        )

        redshift_login = redshift.Login(
            master_username=self.redshift_user,
            master_password=sm.Secret.from_secret_complete_arn(
                self, "redshiftPasswordSecret", os.environ.get("REDSHIFT_PWD_ARN")
            ).secret_value,
        )

        redshift_s3_read_access_role = iam.Role(
            self,
            "redshiftS3AccessRole",
            role_name="redshiftS3AccessRole",
            assumed_by=iam.ServicePrincipal("redshift.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3ReadOnlyAccess")
            ],
        )

        redshift_cluster = redshift.Cluster(
            self,
            id="redshift-cluster",
            master_user=redshift_login,
            vpc=vpc,
            cluster_type=redshift.ClusterType.SINGLE_NODE,
            default_database_name="redshift-db",
            encrypted=True,
            node_type=redshift.NodeType.DC2_LARGE,
            port=5439,
            roles=[redshift_s3_read_access_role],
            security_groups=[vpc.redshift_sg],
            subnet_group=subnet_group,
            removal_policy=core.RemovalPolicy.DESTROY,
        )
        self._instance = redshift_cluster

    @property
    def instance(self) -> core.Resource:
        return self._instance