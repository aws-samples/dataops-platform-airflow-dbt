#!/bin/bash
declare -a ecr_repos=("airflow_webserver_cdk" "airflow_scheduler_cdk" "airflow_worker_cdk" "dbt_cdk")

for repo in "${ecr_repos[@]}"
do
    repo_uri=$(aws ecr describe-repositories --repository-names $repo --query "repositories[0].repositoryUri" --output text 2>&1 || true)
    if [ -z "$repo_uri" ]; then
        echo "empty_ecr.sh: Repository $repo is already deleted."
    else
        echo "empty_ecr.sh: Deleting images in $repo ECR repository..."
        image_digests=$(aws ecr list-images --repository-name $repo --query 'imageIds[*].imageDigest' --output text)
        for digest in $image_digests; do
            aws ecr batch-delete-image --repository-name $repo --image-ids imageDigest=$digest --output text >/dev/null
        done
        echo "empty_ecr.sh: $repo ECR repository is now empty."
    fi
done
