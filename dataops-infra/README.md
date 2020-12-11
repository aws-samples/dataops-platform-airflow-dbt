# DataOps Platform Infrastructure

This folder contains code and intructions to deploy the platform infrastructure illustrated in the main [README.md](../README.md).

## Project structure

```
.
├── .github/                // GitHub Actions definitions
├── images/                 // Docker Images' definitions
├── infra/                  // CDK project 
├── scripts/                // Automation scripts
├── .env                    // Environment variables
├── Makefile                // Make rules for automation
└── requirements-dev.txt    // Python packages for automation scripts
```

This project is defined and deployed using [**AWS Cloud Development Kit (AWS CDK)**](https://aws.amazon.com/cdk/). The CDK Stacks' definitions can be found in [`infra/stacks`](infra/stacks).

In order to automate the deployment steps, [`make`](https://www.gnu.org/software/make/) rules are used. More information on these rules are be provided in the [deployment](#deployment) section later on.

## Airflow webserver login credentials

You need to login with user credentials when accessing Airflow web UI:
- username: **user**
- password: **bitnami**

You can alter these credentials by setting environment variables for the *Apache Airflow* `webserver` Fargate task in [`infra/stacks/fargate_services/airflow.py`](infra/stack/../stacks/fargate_services/airflow.py):

```python
environment={
    "AIRFLOW_USER": "<YOUR_USERNAME>",
    ...
},
secrets={
    "AIRFLOW_PASSWORD": ecs.Secret.from_secrets_manager(
        <YOUR_USER_PASSWORD_SECRET>
    ),
    ...
}
```

## Setup

A few steps need to be perfomed to setup the local environment.

### Prerequisites

Before moving on with the deployment of the project complete the following checks: 

* Install [`npm`](https://www.npmjs.com/get-npm) on your machine
* Install [`python`](https://www.python.org/downloads/) on your machine
* Ensure [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html) is installed and configured on your machine.
* Ensure CDK is [installed and configured](https://docs.aws.amazon.com/cdk/latest/guide/getting_started.html#getting_started_prerequisites) on your machine

_**NOTE:** This project uses CDK library version `1.73.0`, hence the same version or higher of the CDK CLI is required._

### Python Virtual Environment

To create a Python virtual environment for the project run the following `make` rule:

```sh
# from the root directory

$ make venv
```

This rule will create a virtual environment in `infra/venv` and install all necessary dependencies for the project to work. 

### Generate Fernet Key

*Airflow* uses [Fernet](https://github.com/fernet/spec/) to encrypt passwords in the connection configuration and the variable configuration. In order to generate a Fernet key for the project run the following `make` rule:

```sh
# from the root directory

$ make generate_fernet
This is your Fernet key:  <fernet_key>
```

Store your `fernet_key` to [**AWS Secrets Manager**](https://aws.amazon.com/secrets-manager/):
```sh
aws secretsmanager create-secret –name fernetKeySecret –-description “Fernet key for Airflow” –secret-string YOUR_FERNET_KEY
```

### Secrets

This project relies on **AWS Secrets Manager** to safely store credentials to access Redshift and RDS from the Fargate tasks running *Airflow* and *dbt*. Once all secrets are created, environment variables can be set in `.env` file.

* `BUCKET_NAME`: choose a unique name for the Amazon S3 bucket that will host the artifacts for *Airflow* DAGs and *dbt* models
* `FERNET_SECRET_ARN`: ARN of the secret storing the `fernet_key`
* `REDSHIFT_PWD_ARN`: ARN of the secret storing the password to access the Redshift cluster
* `POSTGRESS_PASS_ARN`: ARN of the secret storing the password to access the RDS PostgreSQL metadata store for *Airflow* 
* `ECR_URI`: unique identifier of the Amazon ECR repository to be used. This identifier depends on the AWS Account ID and the region only, hence can be easily derived from `<AWS_ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com`

Assuming that the project will be deployed in `eu-west-1` region, the `.env` file will look similar to the following:

```txt
BUCKET_NAME=my-unique-dataops-bucket-name
FERNET_SECRET_ARN=arn:aws:secretsmanager:eu-west-1:123456789012:secret:airflow/fernet_key-AbCdEf
REDSHIFT_PWD_ARN=arn:aws:secretsmanager:eu-west-1:123456789012:secret:redshift/password-AbCdEf
POSTGRESS_PASS_ARN=arn:aws:secretsmanager:eu-west-1:123456789012:secret:airflow/postgres/password-AbCdEf
ECR_URI=123456789012.dkr.ecr.eu-west-1.amazonaws.com
```

## Deployment

Assuming that all the steps listed in the [Prerequisites](#prerequisites) have been performed, the project can now be deployed.

The deployment process is divided in three `make` rules:
* a `bootstrap` rule deploying components of the infrastructure that are not involved in frequent changes (VPC, S3, ECR, Redis, RDS, Redshift)
* a `push_images` rule uploading Docker Images of *Airflow* and *dbt* to Amazon ECR
* a `deploy` rule deploying ECS cluster and *Airflow* and *dbt* services

### Bootstrap

Let's [bootstrap](https://docs.aws.amazon.com/cdk/latest/guide/bootstrapping.html) an AWS CDK environment and deploy the baseline resources of the project executing the `bootstrap` rule:

```sh
# from the root directory

$ make bootstrap
```

The CDK CLI will ask for permissions to deploy specific resources *security groups*, when asked please acknowledge with `y` and press **Enter**.

### Upload Docker Images to Amazon ECR

Now that the baseline resources are created, let's upload the Docker Images of *Airflow* and *dbt* to Amazon ECR to make them available to the ECS task definitions later on. 

Docker needs to be installed and running on your machine in order to be able to upload the images to Amazon ECR. To install and configure Docker please refer to the [official documentation](https://docs.docker.com/get-docker/).

A helper script is provided in [`scripts/ecr.sh`](scripts/ecr.sh) to perfom the upload of the Docker Images to Amazon ECR. 

_**NOTE:** If you are deploying to a region different than `eu-west-1` please update the region parameter in the second line of the script:_

```sh
# Login to ECR
aws ecr get-login-password --region <YOUR_AWS_REGION> | \
docker login --username AWS --password-stdin $ECR_URI
...
```

Check that Docker is running on your machine then execute the `push_images` rule:

```sh
# from the root directory

$ make push_images
```

### Deploy ECS cluster and services

Last step is to finally deploy the ECS cluster and the *Aiflow* and *dbt* services. To do that execute the `deploy` rule:

```sh
# from the root directory

$ make deploy
```

The CDK CLI will ask for your permissions to deploy specific resources *IAM Roles* and *IAM Polices*, when asked please acknowledge with `y` and press **Enter**.

### Loading example data into Redshift

Using the [Redshift Query Editor](https://docs.aws.amazon.com/redshift/latest/mgmt/query-editor.html) follow this [Redshift tutorial](https://docs.aws.amazon.com/redshift/latest/gsg/rs-gsg-create-sample-db.html) to load example data into the cluster. To log in to the Query Editor, use the username `"redshift-user"` and the password chosen during deployment. 

For uploading the sample data into Amazon S3, use the bucket that was created during deployment.

To copy the data from S3 into Redshift, the `copy` command needs the ARN of the Redshift IAM role which was created during deployment. Execute the following AWS CLI command and look under "IamRoles".

```sh
aws redshift describe-clusters --output json
```

### Clean up 

To destroy all the resources created for this project execute the `destroy` rule:

```sh
# from the root directory

$ make destroy
```

The CDK CLI will ask for your permissions to destroy the CDK stacks, when asked please acknowledge with `y` and press **Enter**.

## GitHub Actions

Preconfigured GitHub Actions [workflows](.github/workflows/) are also provided to automate the upload of new versions of the Docker Images to Amazon ECR and the deployment of the Fargate tasks. These are ment to be an automated alternative to the process implemented with `make`.

To use them:
* replace the `<AWS_ACCOUNT_ID>` with the ID of the AWS Account used to deploy the infrastructure 
* replace the `<CODEBUILD_PROJECT_NAME>` with the name of the AWS CodeBuild project created to build and push the Docker Images
* update the [trigger rule](.github/workflows/airflow.yml#L1-L6) based on the desired branching strategy.

These workflows are designed to work in conjuction with [AWS CodeBuild](https://aws.amazon.com/codebuild/) using the [`aws-actions/aws-codebuild-run-build`](https://github.com/aws-actions/aws-codebuild-run-build) action. The build specifications files are located in [`images/airflow_buildspec.yml`](images/airflow_buildspec.yml) and [`images/dbt_buildspec.yml`](images/dbt_buildspec.yml) respectively.

To use these GitHub Actions workflows, a CodeBuild project needs to be created and connected to the GitHub repository hosting the infrastructure code. Instructions on how to do that in the AWS console can be found in [this documentation page](https://docs.aws.amazon.com/codebuild/latest/userguide/create-project-console.html). It is worth mentioning that to configure GitHub as a *Source* for a CodeBuild project, a [*GitHub personal access token*](https://docs.github.com/en/free-pro-team@latest/github/authenticating-to-github/creating-a-personal-access-token) needs to be [generated and added](https://docs.aws.amazon.com/codebuild/latest/userguide/sample-access-tokens.html#sample-access-tokens-console) to the CodeBuild *Source*.

When creating the CodeBuild project pay attention to the following:
* add the necessary IAM policies to the CodeBuild service IAM Role to grant access to Amazon ECR
* when creating a CodeBuild project choose:
  * **Ubuntu**, for *Operating system*
  * **Standard**, for *Runtime*
  * **aws/codebuild/standard:4.0**, for *Image*
  * and enable **Privileged** mode

All these indications can be found in the [Docker sample](https://docs.aws.amazon.com/codebuild/latest/userguide/sample-docker.html#sample-docker-running) section of the CodeBuild documentation.
