#!/bin/bash
set -e

# Load .env variables       
source .env

docker build -t $STACK_NAME .
