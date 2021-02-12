import os
import secrets
from aws_cdk import aws_s3 as s3, core


class S3Stack(core.Stack):
    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        rand_int = secrets.randbelow(1000001)

        self._instance = s3.Bucket(
            self,
            "dataops-analytics-bucket",
            bucket_name=os.environ.get("BUCKET_NAME", f"dataops-analytics-{rand_int}"),
            block_public_access=s3.BlockPublicAccess(
                block_public_acls=True,
                block_public_policy=True,
                ignore_public_acls=True,
                restrict_public_buckets=True,
            ),
            removal_policy=core.RemovalPolicy.DESTROY,
            versioned=False,
        )

    @property
    def instance(self) -> core.Resource:
        return self._instance
