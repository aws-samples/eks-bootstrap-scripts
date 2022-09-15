# Bootstrap Templates

This repository contains the templates for bootstrapping EKS clusters. It installs 
- Cloudwatch
- ENIConfigs
- EBS
- EFS
- ExternalDns
- Fluent-Bit
- Prometheus
- Twistlock
- Custom ClusterRoles
- AWS Load Balancer

These scripts are packages in ECR

## Pulling package. Default region is us-west-2

To Downlaod the package, authenticate with ECR repository `helm-eks-bootstrap`.

Command:
```
aws ecr get-login-password --region  us-west-2 | docker login --username AWS --password-stdin $(aws sts get-caller-identity --output text --query 'Account').dkr.ecr.us-west-2.amazonaws.com
```


### `builspec.yml`

Distributed with this repo is a CodeBuild `buildspec.yml` file that will package the templates and publish them in `ECR`.


### Packaging files. Update the version as appropiate
`./build-d0.sh 1.0` 