from aws_cdk import aws_ec2 as ec2, core
from typing import List


class VpcStack(core.Stack):
    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        self._instance = ec2.Vpc(
            self,
            "dataops-vpc",
            max_azs=2,
            cidr="10.0.0.0/16",
            subnet_configuration=self.subnets,
            enable_dns_hostnames=True,
            enable_dns_support=True,
        )

        self.create_security_groups()
        self.create_endpoints()
        self.tag_subnets()
        core.CfnOutput(self, "Output", value=self._instance.vpc_id)

    @property
    def instance(self) -> core.Resource:
        return self._instance

    @property
    def get_vpc_private_subnet_ids(self) -> ec2.SelectedSubnets:
        return self.instance.select_subnets(
            subnet_type=ec2.SubnetType.ISOLATED
        ).subnet_ids

    @property
    def subnets(self) -> List:
        return [
            ec2.SubnetConfiguration(
                subnet_type=ec2.SubnetType.PUBLIC, name="public", cidr_mask=24
            ),
            ec2.SubnetConfiguration(
                subnet_type=ec2.SubnetType.ISOLATED, name="dataops", cidr_mask=24
            ),
        ]

    def create_security_groups(self) -> None:
        self.airflow_sg = ec2.SecurityGroup(
            self,
            "airflow-sg-cdk",
            security_group_name="airflow-sg-cdk",
            description="Airflow SG",
            vpc=self.instance,
            allow_all_outbound=True,
        )
        self.alb_sg = ec2.SecurityGroup(
            self,
            "airflow-alb-sg-cdk",
            security_group_name="airflow-alb-sg-cdk",
            description="Airflow ALB SG",
            vpc=self.instance,
            allow_all_outbound=True,
        )
        self.vpc_endpoint_sg = ec2.SecurityGroup(
            self,
            "vpc-endpoint-sg",
            security_group_name="vpc-endpoint-sg",
            description="VPC Endpoint SG",
            vpc=self.instance,
            allow_all_outbound=False,
        )
        self.postgres_sg = ec2.SecurityGroup(
            self,
            "airflow-db-sg",
            security_group_name="airflow-db-sg-cdk",
            description="Airflow Postgres SG",
            vpc=self.instance,
            allow_all_outbound=True,
        )
        self.redshift_sg = ec2.SecurityGroup(
            self,
            "redshift-sg",
            security_group_name="redshift-sg-cdk",
            description="Redshift cluster SG",
            vpc=self.instance,
            allow_all_outbound=True,
        )
        self.redis_sg = ec2.SecurityGroup(
            self,
            "redis-sg",
            security_group_name="redis-sg-cdk",
            description="Redis SG",
            vpc=self.instance,
            allow_all_outbound=True,
        )

        self.airflow_sg.connections.allow_from(
            self.airflow_sg, ec2.Port.all_traffic(), "Ingress"
        )
        self.airflow_sg.connections.allow_from(
            self.alb_sg, ec2.Port.tcp(8080), "Ingress"
        )
        self.airflow_sg.connections.allow_from(
            self.redshift_sg, ec2.Port.tcp(5439), "Ingress"
        )
        self.airflow_sg.connections.allow_from(
            self.redis_sg, ec2.Port.tcp(6379), "Ingress"
        )
        self.airflow_sg.connections.allow_from(
            self.vpc_endpoint_sg, ec2.Port.tcp(443), "Ingress"
        )
        self.redis_sg.connections.allow_from(
            self.airflow_sg, ec2.Port.tcp(6379), "Ingress"
        )
        self.redshift_sg.connections.allow_from(
            self.airflow_sg, ec2.Port.tcp(5439), "Ingress"
        )
        self.postgres_sg.connections.allow_from(
            self.airflow_sg, ec2.Port.tcp(5432), "Ingress"
        )

    def create_endpoints(self) -> None:
        endpoints = {
            "ECS": ec2.InterfaceVpcEndpointAwsService.ECS,
            "ECR": ec2.InterfaceVpcEndpointAwsService.ECR,
            "ECR_DOCKER": ec2.InterfaceVpcEndpointAwsService.ECR_DOCKER,
            "CLOUDWATCH_LOGS": ec2.InterfaceVpcEndpointAwsService.CLOUDWATCH_LOGS,
        }

        for name, service in endpoints.items():
            ec2.InterfaceVpcEndpoint(
                self,
                name,
                vpc=self.instance,
                service=service,
                subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.ISOLATED),
                private_dns_enabled=True,
                security_groups=[self.vpc_endpoint_sg],
            )

        self.instance.add_gateway_endpoint(
            "s3-endpoint",
            service=ec2.GatewayVpcEndpointAwsService.S3,
            subnets=[ec2.SubnetSelection(subnet_type=ec2.SubnetType.ISOLATED)],
        )

    def tag_subnets(self) -> None:
        subnet_types = {
            "public": ec2.SubnetType.PUBLIC,
            "isolated": ec2.SubnetType.ISOLATED,
        }
        for st_name, st in subnet_types.items():
            selection = self.instance.select_subnets(subnet_type=st)
            for subnet in selection.subnets:
                core.Tag.add(
                    subnet, "Name", f"{st_name}-subnet-{subnet.availability_zone}"
                )
        core.Tag.add(self.instance, "Name", "dataops-vpc")
