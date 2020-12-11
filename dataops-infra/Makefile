# export environment variables from .env
include .env
export

VENV=infra/venv/bin
WITH_VENV=. $(VENV)/activate;

.PHONY: all
all:
	@echo "make venv                 - create virtual environment"
	@echo "make synth                - test CDK stacks with .env variables"
	@echo "make generate_fernet      - generate Fernet Key for Airflow"
	@echo "make bootstrap            - bootstrap AWS architecture (S3, ECR, VPC, RDS, Redis)"
	@echo "make push_images          - push Docker images (Airflow, DBT) to ECR"
	@echo "make deploy               - deploy ECS cluster and services"

.PHONY: venv
venv: venv/bin/activate

venv/bin/activate: requirements-dev.txt
	@echo "Installing dependencies"
	@test -d infra/venv || python3 -m venv infra/venv
	@$(VENV)/pip install --upgrade pip
	@$(VENV)/pip install -Ur requirements-dev.txt
	@touch $(VENV)/activate

.PHONY: synth
synth: venv
	@$(WITH_VENV) cd infra; cdk synth "*"

.PHONY: generate_fernet
generate_fernet: venv
	@$(WITH_VENV) python scripts/fernet.py

.PHONY: bootstrap
bootstrap: venv
	@echo "Bootstrap infrastructure"
	@$(WITH_VENV) cd infra; cdk bootstrap
	@$(WITH_VENV) cd infra; cdk deploy VpcStack S3Stack ECRStack RDSStack RedisStack RedshiftClusterStack
	@echo "Bootstrap finished. You can now push Docker images and deploy Airflow cluster"

.PHONY: push_images
push_images: venv bootstrap
	@echo "Push Docker images (Airflow, DBT)"
	@bash scripts/ecr.sh
	@echo "All Docker images are pushed. You can now deploy Airflow cluster"

.PHONY: deploy
deploy: venv bootstrap push_images
	@$(WITH_VENV) cd infra; cdk deploy AirflowClusterStack airflow dbt


.PHONY: destroy
destroy: venv
	@bash scripts/empty_s3.sh
	@bash scripts/empty_ecr.sh
	@$(WITH_VENV) cd infra; cdk destroy --all
	
# CodeBuild rules

.PHONY: codebuild_deploy_airflow
codebuild_deploy_airflow:
	@cd infra; cdk deploy airflow --require-approval=never

.PHONY: codebuild_deploy_dbt
codebuild_deploy_dbt:
	@cd infra; cdk deploy dbt --require-approval=never
