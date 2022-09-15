* Use sample commands in `cluster.sh` to create EKS CLUSTER and AWS IAM roles

* Update `artifact.json` with the values from previous step

Update the contents to AWS SSM paraeter store, that will be used by subsequent stages in AWS Codepipelime
```
aws ssm put-parameter --name "EKS_OUT_SSM" --type "String" --value "`cat artifact.json`" --overwrite --region us-west-2
```