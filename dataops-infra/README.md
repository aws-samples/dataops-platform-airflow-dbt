# DataOps Platform Infrastructure

This folder contains code and intructions to deploy the platform infrastructure illustrated in the main [README.md](../README.md).

## Project structure

```
.
├── .github/                // GitHub Actions definitions
├── images/                 // Docker images' definitions
├── infra/                  // CDK project 
├── scripts/                // Automation scripts
├── .env                    // Environment variables
├── Makefile                // Make rules for automation
└── requirements-dev.txt    // Python packages for automation scripts
```

This project is defined and deployed using [**AWS Cloud Development Kit (AWS CDK)**](https://aws.amazon.com/cdk/). CDK Stacks' definitions are located in the [`infra/stacks`](infra/stacks) folder. 

[`Make`](https://www.gnu.org/software/make/) rules are used to automate deployment steps. Available rules are covered in the [Deployment](#deployment) section.

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

You need to perform a few steps to set up the local environment.

### Prerequisites

Before moving on with the project deployment, complete the following checks: 

* Install [`npm`](https://www.npmjs.com/get-npm) on your machine
* Install [`Python`](https://www.python.org/downloads/) on your machine
* Ensure that [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html) is installed and configured on your machine
* Ensure that CDK is [installed and configured](https://docs.aws.amazon.com/cdk/latest/guide/getting_started.html#getting_started_prerequisites) on your machine

_**NOTE:** :warning: This project uses CDK library version `1.90.0`, hence the same version or higher is required._

### Python virtual environment

To create a virtual environment run the following `make` rule:

```sh
# from the root directory

$ make venv
```

This rule will create a virtual environment in `infra/venv` and install all necessary dependencies for the project. 

### Generate Fernet Key

*Airflow* uses [Fernet](https://github.com/fernet/spec/) to encrypt passwords in the connection configuration and the variable configuration. To generate a new Fernet key for the project run:

```sh
# from the root directory

$ make generate_fernet
This is your Fernet key:  <fernet_key>
```

Store your `fernet_key` to [**AWS Secrets Manager**](https://aws.amazon.com/secrets-manager/):
```sh
aws secretsmanager create-secret –name fernetKeySecret –-description “Fernet key for Airflow” –secret-string YOUR_FERNET_KEY
```

### Environment variables

Once you created the `fernet_key` secret, you can set environment variables in `.env` file.

* `AWS_REGION`: AWS region to which you wish to deploy this project
* `BUCKET_NAME`: choose a unique name for an Amazon S3 bucket that will host artifacts for *Airflow* and *dbt* DAGs
* `FERNET_SECRET_ARN`: ARN of the secret with the `fernet_key`
* `ECR_URI`: a unique identifier for the Amazon ECR repository. It can be easily composed with your AWS Account ID and AWS region: `<AWS_ACCOUNT_ID>.dkr.ecr.<AWS_REGION>.amazonaws.com`

Assuming that the project will be deployed in `eu-west-1` region, the `.env` file will look like this:

```txt
AWS_REGION=eu-west-1
BUCKET_NAME=my-unique-dataops-bucket-name
FERNET_SECRET_ARN=arn:aws:secretsmanager:eu-west-1:123456789012:secret:airflow/fernet_key-AbCdEf
ECR_URI=123456789012.dkr.ecr.eu-west-1.amazonaws.com
```

## Deployment

If you've performed all steps from the [Prerequisites](#prerequisites), you can now deploy the project.

The deployment process is divided in three `make` rules:
* `bootstrap` rule deploys infrastructure components which are not frequently updated (VPC, S3, ECR, Redis, RDS, Redshift)
* `push_images` rule uploads *Airflow* and *dbt* Docker images to Amazon ECR
* `deploy` rule deploys ECS cluster, and *Airflow* and *dbt* services

### Bootstrap

Let's [bootstrap](https://docs.aws.amazon.com/cdk/latest/guide/bootstrapping.html) an AWS CDK environment and deploy baseline resources:

```sh
# from the root directory

$ make bootstrap
```
_**NOTE:** :warning: AWS CDK CLI will ask for permissions to deploy *security groups* for specific resources. When asked, please acknowledge with `y` and press **Enter**._

### Upload Docker images to Amazon ECR

Now that the baseline resources are created, let's upload Docker images for *Airflow* and *dbt* to Amazon ECR, which will be used in ECS task definitions later on. 

Docker needs to be installed and *running* on your machine in order to upload images to Amazon ECR. To install and configure Docker please refer to the [official documentation](https://docs.docker.com/get-docker/).

Make sure that Docker is running on your machine and then execute the `push_images` rule:

```sh
# from the root directory

$ make push_images
```

### Deploy ECS cluster and services

Finally, let's deploy the ECS cluster, and *Aiflow* and *dbt* services. To do that, execute the `deploy` rule:

```sh
# from the root directory

$ make deploy
```

_**NOTE:** :warning: AWS CDK CLI will ask for your permissions to deploy specific *IAM Roles* and *IAM Polices* resources. When asked, please acknowledge with `y` and press **Enter**._

### Load example data into Redshift

Follow this [tutorial](https://docs.aws.amazon.com/redshift/latest/gsg/rs-gsg-create-sample-db.html) to load example data into a Amazon Redshift cluster using the [Query Editor](https://docs.aws.amazon.com/redshift/latest/mgmt/query-editor.html). To log in to the Query Editor, use the following:
- Database name: `redshift-db`
- Database user: `redshift-user`

For uploading the sample data into Amazon S3, use the bucket that was created during deployment.

To copy data from Amazon S3 into Redshift, the `copy` command needs ARN of the Redshift IAM role that was created during deployment. Execute the following command to retrieve the ARN:

```sh
aws redshift describe-clusters --query 'Clusters[*].IamRoles[*].IamRoleArn'
```

### Clean up 

To destroy all resources created for this project execute the `destroy` rule:

```sh
# from the root directory

$ make destroy
```

_**NOTE:** :warning: AWS CDK CLI will ask for your permissions to destroy the CDK stacks. When asked, please acknowledge with `y` and press **Enter**._

## GitHub Actions

We have also provided preconfigured GitHub Actions [workflows](.github/workflows/) to automate the upload of new versions of Docker images to Amazon ECR, and the deployment of Fargate tasks. 

These workflows are designed to work in conjuction with [AWS CodeBuild](https://aws.amazon.com/codebuild/) using the [`aws-actions/aws-codebuild-run-build`](https://github.com/aws-actions/aws-codebuild-run-build) action. Build specifications files are located in [`images/airflow_buildspec.yml`](images/airflow_buildspec.yml) and [`images/dbt_buildspec.yml`](images/dbt_buildspec.yml), respectively.

To use provided GitHub Actions workflows, you need to create a AWS CodeBuild project and connect it with your GitHub repository. You can follow [this documentation page](https://docs.aws.amazon.com/codebuild/latest/userguide/create-project-console.html) to do that from your AWS Console. It is worth mentioning that [*GitHub personal access token*](https://docs.github.com/en/free-pro-team@latest/github/authenticating-to-github/creating-a-personal-access-token) needs to be [generated and added](https://docs.aws.amazon.com/codebuild/latest/userguide/sample-access-tokens.html#sample-access-tokens-console) to the CodeBuild *Source* in order to configure GitHub repository as a source for the project.


When creating AWS CodeBuild project, pay attention to the following:
* add necessary IAM policies to the CodeBuild service IAM Role to grant access to Amazon ECR
* when creating the project choose these settings:
  * **Ubuntu**, for the *Operating system*
  * **Standard**, for the *Runtime*
  * **aws/codebuild/standard:4.0**, for the *Image*
  * enable **Privileged** mode

All these details can be found in the [Docker sample](https://docs.aws.amazon.com/codebuild/latest/userguide/sample-docker.html#sample-docker-running) section of AWS CodeBuild documentation.

Finally, to use provided GitHub actions workflows in this project do the following:
* replace `<AWS_ACCOUNT_ID>` with your AWS Account ID
* replace `<AWS_REGION>` with your AWS region
* replace `<CODEBUILD_PROJECT_NAME>` with the name of AWS CodeBuild project that you created
* update the [trigger rule](.github/workflows/airflow.yml#L1-L6) based on on preferred events



