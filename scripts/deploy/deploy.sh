#!/bin/bash
set -e

# Read all command-line arguments with "--" prefixes and recreate them as
# environment variables. For example, "--foo bar" becomes a variable named "foo"
# with value "bar".
while [ $# -gt 0 ]; do
  if [[ $1 == "--"* ]]; then
    name="${1/--/}"
    declare "${name}"="${2}"
    shift
  fi
  shift
done

# Load .env variables       
source .env

echo "Deploying stack $STACK_NAME to region $REGION"

aws cloudformation deploy \
  --capabilities CAPABILITY_IAM \
  --stack-name $STACK_NAME \
  --template-file "${template_path}" \
  --region "${REGION}" \
  --parameter-overrides \
    ImageUri="${image}" \
    MongoUsername="${MONGO_USERNAME}" \
    MongoPassword="${MONGO_PASSWORD}" \
    MongoHost="${MONGO_HOST}" \
    MongoDbName="${MONGO_DB_NAME}" \