# DBT Dockerfile
FROM python:3.7

# Install aws cli
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
RUN unzip awscliv2.zip
RUN ./aws/install
# Copy the required files
COPY requirements.txt ./
COPY scripts/entrypoint.sh /entrypoint.sh

RUN pip install --upgrade pip
RUN pip install -r requirements.txt
# Set DBT profiles location
ENV DBT_PROFILES_DIR=config

ENTRYPOINT ["/entrypoint.sh"]
