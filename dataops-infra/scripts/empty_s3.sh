# check if bucket exists, then empty it for later deletion
BUCKET_EXISTS=$(aws s3api head-bucket --bucket $BUCKET_NAME 2>&1 || true)

if [ -z "$BUCKET_EXISTS" ]; then
  echo "empty_s3.sh: Deleting content from s3://$BUCKET_NAME"
  aws s3 rm s3://$BUCKET_NAME --recursive
else
  echo "empty_s3.sh: Bucket does not exist"
fi
