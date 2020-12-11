from aws_cdk import aws_ecr as ecr, core


class ECRStack(core.Stack):
    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        self.airflow_webserver_repo = ecr.Repository(
            self,
            "airflow_webserver_repo",
            repository_name="airflow_webserver_cdk",
            removal_policy=core.RemovalPolicy.DESTROY,
        )
        self.airflow_scheduler_repo = ecr.Repository(
            self,
            "airflow_scheduler_repo",
            repository_name="airflow_scheduler_cdk",
            removal_policy=core.RemovalPolicy.DESTROY,
        )
        self.airflow_worker_repo = ecr.Repository(
            self,
            "airflow_worker_repo",
            repository_name="airflow_worker_cdk",
            removal_policy=core.RemovalPolicy.DESTROY,
        )
        self.dbt_repo = ecr.Repository(
            self,
            "dbt_ecr_repository",
            repository_name="dbt_cdk",
            removal_policy=core.RemovalPolicy.DESTROY,
        )