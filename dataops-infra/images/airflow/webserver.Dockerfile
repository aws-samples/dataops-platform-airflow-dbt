FROM public.ecr.aws/bitnami/airflow:1.10.13
USER root

# Install aws cli
RUN apt-get update -yqq && apt-get install -y unzip
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
RUN unzip awscliv2.zip
RUN ./aws/install

COPY scripts/entrypoint.sh /entrypoint.sh
COPY scripts/sync_dags.sh /sync_dags.sh
COPY requirements.txt /bitnami/python/requirements.txt

ENTRYPOINT [ "/entrypoint.sh" ]
CMD [ "/run.sh" ]
