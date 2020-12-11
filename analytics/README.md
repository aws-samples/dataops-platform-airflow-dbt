# Analytics

This repository contains code and instructions to manage and deploy *Airflow* and *dbt* DAGs on the DataOps platform.

## Project structure

```
.
├── .github/                // GitHub Actions definitions
├── airflow_dags/           // Airflow DAGs
└── dbt_dags/               // dbt DAGs
```

## Prerequisites

The **AWS CLI** will be used to upload *Airflow* and *dbt* artifacts to **Amazon S3**.

Ensure [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html) is installed and configured on your machine.

### Update *dbt* Fargate task networking configurations

*Airflow* uses the [`ECSOperator`](https://airflow.apache.org/docs/stable/_api/airflow/contrib/operators/ecs_operator/index.html) to spawn a new **dbt** Fargate task. To do that the correct `network_configuration` needs to be provided in the [DAG code](airflow_dags/redshift_transformations.py#L39-L44).

Replace the values of `securityGroups` and `subnets` with the ones created when deploying the Data Platform [infrastructure](../dataops-infra).

```py
network_configuration={
    "awsvpcConfiguration": {
        "securityGroups": ["sg-1234abcd5678efgh9"],
        "subnets": ["subnet-1234abcd5678efgh9", "subnet-abcd1234efgh5678j"]
    }
}
```

As an alternative to get the Security Group ID, run the following command:

```sh
$ aws ec2 describe-security-groups --filters Name=group-name,Values=airflow-sg-cdk --query "SecurityGroups[*].{Name:GroupName,ID:GroupId}"
```

To get the Subnets' IDs run the following command:

```sh
$ aws ec2 describe-subnets --filters Name=tag:Name,Values=isolated-subnet-eu-west-1a,isolated-subnet-eu-west-1b --query 'Subnets[*].SubnetId'
```

## Deploy DAGs

As shown in the [architecture diagram](../README.md), *Airflow* and *dbt* DAGs are fetched from Amazon S3 by the AWS Fargate tasks running on Amazon ECS. 

*Airflow* Fargate tasks use a subprocess to continuously sync the local DAGs with the latest artifacts version available in Amazon S3. *dbt* DAGs are fetched from Amazon S3 when a new Fargate task is spawn by *Airflow* instead.

To upload the latest version of the DAGs using the AWS CLI, update the `BUCKET_NAME` with the name of Amazon S3 bucket used to store the DAGs artifacts and run:

```sh
# from the root directory

$ aws s3 sync . s3://<BUCKET_NAME> --delete --exclude "*" --include "airflow_dags/*" --include "dbt_dags/*"
```

### GitHub Actions

A preconfigured GitHub Actions [workflow](.github/workflows/aws.yml) is also provided to automate the upload of the latest version of DAGs to Amazon S3. To use it replace the `<BUCKET_NAME>` with the name of Amazon S3 bucket used to store the DAGs artifacts and update the [trigger rule](.github/workflows/aws.yml#L1-L6) based on the desired branching strategy.
