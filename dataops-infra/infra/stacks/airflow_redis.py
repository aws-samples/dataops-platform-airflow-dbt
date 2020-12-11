from aws_cdk import (
    aws_elasticache as ecache,
    aws_ec2 as ec2,
    core,
)
from stacks.vpc_stack import VpcStack


class RedisStack(core.Stack):
    def __init__(self, scope: core.Construct, id: str, vpc: VpcStack, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        subnet_group = ecache.CfnSubnetGroup(
            self,
            "RedisClusterSG",
            subnet_ids=vpc.get_vpc_private_subnet_ids,
            description="Airflow Redis private subnet group",
        )

        redis = ecache.CfnCacheCluster(
            self,
            "AirflowRedis",
            engine="redis",
            port=6379,
            cache_node_type="cache.t2.small",
            num_cache_nodes=1,
            cluster_name="airflow-redis",
            vpc_security_group_ids=[vpc.redis_sg.security_group_id],
            cache_subnet_group_name=subnet_group.ref,
        )
        self._instance = redis

    @property
    def instance(self) -> core.Resource:
        return self._instance
