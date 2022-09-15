#create sample cluster
eksctl create cluster -f eksctl-config.yaml
eksctl utils associate-iam-oidc-provider --cluster=sample-cluster --approve