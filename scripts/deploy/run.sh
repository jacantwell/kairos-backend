#!/bin/bash
set -e

# Load .env variables       
source .env

docker run -p 9000:8080 $STACK_NAME