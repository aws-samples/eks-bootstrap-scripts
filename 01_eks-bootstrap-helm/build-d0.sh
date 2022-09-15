#!/bin/bash
export HELM_EXPERIMENTAL_OCI=1
version=$1
oldpwd=$(pwd)
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin $(aws sts get-caller-identity --output text --query 'Account').dkr.ecr.us-west-2.amazonaws.com
aws ecr create-repository --repository-name helm-eks-bootstrap --region us-west-2
helm chart save stable/helm/ $(aws sts get-caller-identity --output text --query 'Account').dkr.ecr.us-west-2.amazonaws.com/helm-eks-bootstrap:$version
helm chart push $(aws sts get-caller-identity --output text --query 'Account').dkr.ecr.us-west-2.amazonaws.com/helm-eks-bootstrap:$version
