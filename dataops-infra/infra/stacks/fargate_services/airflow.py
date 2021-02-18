import os

from aws_cdk import (
    core,
    aws_ecs as ecs,
    aws_secretsmanager as sm,
    aws_elasticloadbalancingv2 as elbv2,
    aws_servicediscovery as sd,
)
from stacks.vpc_stack import VpcStack
from stacks.airflow_cluster_stack import AirflowClusterStack
from stacks.ecr_stack import ECRStack
from stacks.airflow_rds import RDSStack
from stacks.airflow_redis import RedisStack
from types import SimpleNamespace
from typing_extensions import TypedDict

props_type = TypedDict(
    "props_type",
    {
        "airflow_cluster": AirflowClusterStack,
        "vpc": VpcStack,
        "ecr": ECRStack,
        "rds": RDSStack,
        "redis": RedisStack,
    },
)


class AirflowServices(core.Stack):
    def __init__(
        self, scope: core.Construct, id: str, props: props_type, **kwargs
    ) -> None:
        super().__init__(scope, id, **kwargs)
        ns = SimpleNamespace(**props)

        bucket_name = os.environ.get("BUCKET_NAME")
        fernet_key_secret = sm.Secret.from_secret_arn(
            self, "fernetSecret", os.environ.get("FERNET_SECRET_ARN")
        )

        webserver_ns = sd.PrivateDnsNamespace(
            self,
            "webserver-dns-namespace",
            vpc=ns.vpc.instance,
            name="airflow",
            description="Private DNS for Airflow webserver",
        )

        # Webserver
        webserver_task = ecs.FargateTaskDefinition(
            self,
            "webserver-cdk",
            family="webserver-cdk",
            cpu=512,
            memory_limit_mib=1024,
            task_role=ns.airflow_cluster.airflow_task_role,
            execution_role=ns.airflow_cluster.task_execution_role,
        )
        webserver_container = webserver_task.add_container(
            "webserver-cdk-container",
            image=ecs.ContainerImage.from_ecr_repository(
                ns.ecr.airflow_webserver_repo,
                os.environ.get("IMAGE_TAG", "latest"),
            ),
            logging=ecs.AwsLogDriver(
                stream_prefix="ecs", log_group=ns.airflow_cluster.webserver_log_group
            ),
            environment={
                "AIRFLOW_DATABASE_NAME": ns.rds.db_name,
                "AIRFLOW_DATABASE_PORT_NUMBER": "5432",
                "AIRFLOW_DATABASE_HOST": ns.rds.instance.db_instance_endpoint_address,
                "AIRFLOW_EXECUTOR": "CeleryExecutor",
                "AIRFLOW_LOAD_EXAMPLES": "no",
                "AIRFLOW__SCHEDULER__DAG_DIR_LIST_INTERVAL": "30",
                "BUCKET_NAME": bucket_name,
            },
            secrets={
                "AIRFLOW_DATABASE_USERNAME": ecs.Secret.from_secrets_manager(
                    ns.rds.rds_secret, field="username"
                ),
                "AIRFLOW_DATABASE_PASSWORD": ecs.Secret.from_secrets_manager(
                    ns.rds.rds_secret, field="password"
                ),
                "AIRFLOW_FERNET_KEY": ecs.Secret.from_secrets_manager(
                    fernet_key_secret
                ),
            },
        )

        ws_port_mapping = ecs.PortMapping(
            container_port=8080, host_port=8080, protocol=ecs.Protocol.TCP
        )
        webserver_container.add_port_mappings(ws_port_mapping)

        # Webserver service
        webserver_service = ecs.FargateService(
            self,
            "webserverService",
            service_name="webserver_cdk",
            cluster=ns.airflow_cluster.instance,
            task_definition=webserver_task,
            desired_count=1,
            security_group=ns.vpc.airflow_sg,
            assign_public_ip=False,
            cloud_map_options=ecs.CloudMapOptions(
                cloud_map_namespace=webserver_ns,
                name="webserver",
                dns_record_type=sd.DnsRecordType.A,
                dns_ttl=core.Duration.seconds(30),
            ),
        )

        # Scheduler
        scheduler_task = ecs.FargateTaskDefinition(
            self,
            "scheduler-cdk",
            family="scheduler-cdk",
            cpu=512,
            memory_limit_mib=2048,
            task_role=ns.airflow_cluster.airflow_task_role,
            execution_role=ns.airflow_cluster.task_execution_role,
        )

        scheduler_task.add_container(
            "scheduler-cdk-container",
            image=ecs.ContainerImage.from_ecr_repository(
                ns.ecr.airflow_scheduler_repo,
                os.environ.get("IMAGE_TAG", "latest"),
            ),
            logging=ecs.AwsLogDriver(
                stream_prefix="ecs", log_group=ns.airflow_cluster.scheduler_log_group
            ),
            environment={
                "AIRFLOW_DATABASE_NAME": ns.rds.db_name,
                "AIRFLOW_DATABASE_PORT_NUMBER": "5432",
                "AIRFLOW_DATABASE_HOST": ns.rds.instance.db_instance_endpoint_address,
                "AIRFLOW_EXECUTOR": "CeleryExecutor",
                "AIRFLOW_WEBSERVER_HOST": "webserver.airflow",
                "AIRFLOW_LOAD_EXAMPLES": "no",
                "AIRFLOW__SCHEDULER__DAG_DIR_LIST_INTERVAL": "30",
                "REDIS_HOST": ns.redis.instance.attr_redis_endpoint_address,
                "BUCKET_NAME": bucket_name,
            },
            secrets={
                "AIRFLOW_DATABASE_USERNAME": ecs.Secret.from_secrets_manager(
                    ns.rds.rds_secret, field="username"
                ),
                "AIRFLOW_DATABASE_PASSWORD": ecs.Secret.from_secrets_manager(
                    ns.rds.rds_secret, field="password"
                ),
                "AIRFLOW_FERNET_KEY": ecs.Secret.from_secrets_manager(
                    fernet_key_secret
                ),
            },
        )
        # Scheduler service
        ecs.FargateService(
            self,
            "schedulerService",
            service_name="scheduler_cdk",
            cluster=ns.airflow_cluster.instance,
            task_definition=scheduler_task,
            desired_count=1,
            security_group=ns.vpc.airflow_sg,
            assign_public_ip=False,
        )

        # Worker
        worker_task = ecs.FargateTaskDefinition(
            self,
            "worker-cdk",
            family="worker-cdk",
            cpu=1024,
            memory_limit_mib=3072,
            task_role=ns.airflow_cluster.airflow_task_role,
            execution_role=ns.airflow_cluster.task_execution_role,
        )

        worker_container = worker_task.add_container(
            "worker-cdk-container",
            image=ecs.ContainerImage.from_ecr_repository(
                ns.ecr.airflow_worker_repo,
                os.environ.get("IMAGE_TAG", "latest"),
            ),
            logging=ecs.AwsLogDriver(
                stream_prefix="ecs", log_group=ns.airflow_cluster.worker_log_group
            ),
            environment={
                "AIRFLOW_DATABASE_NAME": ns.rds.db_name,
                "AIRFLOW_DATABASE_PORT_NUMBER": "5432",
                "AIRFLOW_DATABASE_HOST": ns.rds.instance.db_instance_endpoint_address,
                "AIRFLOW_EXECUTOR": "CeleryExecutor",
                "AIRFLOW_WEBSERVER_HOST": "webserver.airflow",
                "AIRFLOW__SCHEDULER__DAG_DIR_LIST_INTERVAL": "30",
                "AIRFLOW_LOAD_EXAMPLES": "no",
                "REDIS_HOST": ns.redis.instance.attr_redis_endpoint_address,
                "BUCKET_NAME": bucket_name,
            },
            secrets={
                "AIRFLOW_DATABASE_USERNAME": ecs.Secret.from_secrets_manager(
                    ns.rds.rds_secret, field="username"
                ),
                "AIRFLOW_DATABASE_PASSWORD": ecs.Secret.from_secrets_manager(
                    ns.rds.rds_secret, field="password"
                ),
                "AIRFLOW_FERNET_KEY": ecs.Secret.from_secrets_manager(
                    fernet_key_secret
                ),
            },
        )

        worker_port_mapping = ecs.PortMapping(
            container_port=8793, host_port=8793, protocol=ecs.Protocol.TCP
        )
        worker_container.add_port_mappings(worker_port_mapping)

        # Worker service
        ecs.FargateService(
            self,
            "workerService",
            service_name="worker_cdk",
            cluster=ns.airflow_cluster.instance,
            task_definition=worker_task,
            desired_count=1,
            security_group=ns.vpc.airflow_sg,
            assign_public_ip=False,
        )

        # ALB
        lb = elbv2.ApplicationLoadBalancer(
            self,
            "LB",
            vpc=ns.vpc.instance,
            internet_facing=True,
            security_group=ns.vpc.alb_sg,
        )

        listener = lb.add_listener("airflow-webserver-cdk-listener", port=80, open=True)

        webserver_hc = elbv2.HealthCheck(
            interval=core.Duration.seconds(60),
            path="/health",
            timeout=core.Duration.seconds(5),
        )

        # Attach ALB to ECS Service
        listener.add_targets(
            "airflow-webserver-cdk-default",
            port=80,
            targets=[webserver_service],
            health_check=webserver_hc,
        )
