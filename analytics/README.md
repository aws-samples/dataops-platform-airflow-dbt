# Analytics

This folder contains code and instructions to manage and deploy *Airflow* and *dbt* DAGs.

## Project structure

```
.
├── .github/                // GitHub Actions definitions
├── airflow_dags/           // Airflow DAGs
└── dbt_dags/               // dbt DAGs
```

## Prerequisites

- Ensure that [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html) is installed and configured on your machine
- **AWS CLI** will be used to upload *Airflow* and *dbt* artifacts to **Amazon S3**

### Update network configuration of Airflow's DAG for *dbt*

*Airflow* uses [`ECSOperator`](https://airflow.apache.org/docs/stable/_api/airflow/contrib/operators/ecs_operator/index.html) to spawn a new **dbt** Fargate task, so you need to set the correct `network_configuration` for this particular [DAG](airflow_dags/redshift_transformations.py#L42-L47).

Replace values for `securityGroups` and `subnets` with ones created during the [infrastructure](../dataops-infra) deployment.

```py
network_configuration={
    "awsvpcConfiguration": {
        "securityGroups": ["sg-1234abcd5678efgh9"],
        "subnets": ["subnet-1234abcd5678efgh9", "subnet-abcd1234efgh5678j"]
    }
}
```

As an alternative, you can obtain security group's ID by run the following command:

```sh
$ aws ec2 describe-security-groups --filters Name=group-name,Values=airflow-sg-cdk --query "SecurityGroups[*].{Name:GroupName,ID:GroupId}"
```

To get subnets' IDs, run the following command:

_**NOTE:** :warning: This command assumes that you deployed the project to `eu-west-1`. Make sure to use the correct subnet names if you choose different region._
```sh
$ aws ec2 describe-subnets --filters Name=tag:Name,Values=isolated-subnet-eu-west-1a,isolated-subnet-eu-west-1b --query 'Subnets[*].SubnetId'
```

## Deploy DAGs

As we show in the [architecture diagram](../README.md), Airflow runs on AWS Fargate and fetches DAGs from an Amazon S3 bucket. Airflow Fargate tasks use a subprocess job to continuously sync local DAGs with the latest version available in Amazon S3. Whenever you trigger Airflow DAG that runs *dbt*, newly created Fargate task fetches *dbt* DAGs from Amazon S3 at runtime.

You can use AWS CLI to upload the latest version of both Airflow's and *dbt's* DAGs. To do so, update the `BUCKET_NAME` placeholder in the following command with the one that you have set in [`.env`](../dataops-infra/.env):

```sh
# from the analytics folder

$ aws s3 sync . s3://<BUCKET_NAME> --delete --exclude "*" --include "airflow_dags/*" --include "dbt_dags/*"
```

### GitHub Actions

We have also provided a preconfigured GitHub Actions [workflow](.github/workflows/aws.yml) to automate DAGs upload to Amazon S3. Update `<BUCKET_NAME>` and `<AWS_REGION>` placeholders with Amazon S3 bucket name that you have set in `.env` and AWS region to which you've deployed this project, respectively. Finally, update the [trigger rule](.github/workflows/aws.yml#L1-L6) based on preferred [events](https://docs.github.com/en/actions/reference/events-that-trigger-workflows#about-workflow-events).
