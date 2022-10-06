#!/bin/bash
export ACCOUNT_ID=$(aws sts get-caller-identity --query "Account" --output text)
export OIDC_PROVIDER=$(aws eks describe-cluster --name ${CLUSTER_NAME} --query "cluster.identity.oidc.issuer" --output text | sed -e "s/^https:\/\///")
export CLUSTER_SG_ID=$(aws eks describe-cluster --name sample-cluster --query "cluster.resourcesVpcConfig.securityGroupIds" --output text)
#create trust policy
cat <<EOF > trust.json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::${ACCOUNT_ID}:oidc-provider/${OIDC_PROVIDER}"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "${OIDC_PROVIDER}:aud": "sts.amazonaws.com"
        }
      }
    }
  ]
}
EOF
#create role policy
cat <<EOF > EbsCsiDriverRolePolicy.json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
         "ec2:CreateSnapshot",
         "ec2:CreateVolume",
         "ec2:DeleteVolume",
         "ec2:DeleteSnapshot",
         "ec2:AttachVolume",
         "ec2:DetachVolume",
         "ec2:ModifyVolume",
         "ec2:DescribeAvailabilityZones",
         "ec2:DescribeInstances",
         "ec2:DescribeSnapshots",
         "ec2:DescribeTags",
         "ec2:DescribeVolumes",
         "ec2:DescribeVolumesModifications",
         "ec2:CreateTags",
         "ec2:DeleteTags"
      ],
      "Resource": "*"
    }
  ]
}
EOF

cat <<EOF > EfsCsiDriverRolePolicy.json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
         "elasticfilesystem:DescribeAccessPoints", 
         "elasticfilesystem:DescribeFileSystems",
         "elasticfilesystem:CreateAccessPoint",
         "elasticfilesystem:DeleteAccessPoint"
      ],
      "Resource": "*"
    }
  ]
}
EOF

cat <<EOF > AlbControllerRolePolicy.json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
            "ec2:DescribeTags",
            "elasticloadbalancing:DescribeLoadBalancers",
            "elasticloadbalancing:DescribeLoadBalancerAttributes",
            "elasticloadbalancing:DescribeListeners",
            "elasticloadbalancing:DescribeListenerCertificates",
            "elasticloadbalancing:DescribeSSLPolicies",
            "elasticloadbalancing:DescribeRules",
            "elasticloadbalancing:DescribeTargetGroups",
            "elasticloadbalancing:DescribeTargetGroupAttributes",
            "elasticloadbalancing:DescribeTargetHealth",
            "elasticloadbalancing:DescribeTags",
            "acm:ListCertificates",
            "acm:DescribeCertificate",
            "ec2:AuthorizeSecurityGroupIngress",
            "ec2:RevokeSecurityGroupIngress",
            "ec2:AuthorizeSecurityGroupIngress",
            "ec2:RevokeSecurityGroupIngress",
            "ec2:DeleteSecurityGroup",
            "ec2:CreateSecurityGroup",
            "elasticloadbalancing:CreateLoadBalancer",
            "elasticloadbalancing:CreateTargetGroup",
            "elasticloadbalancing:CreateListener",
            "elasticloadbalancing:DeleteListener",
            "elasticloadbalancing:CreateRule",
            "elasticloadbalancing:DeleteRule",
            "elasticloadbalancing:AddTags",
            "elasticloadbalancing:RemoveTags",
            "elasticloadbalancing:ModifyLoadBalancerAttributes",
            "elasticloadbalancing:SetIpAddressType",
            "elasticloadbalancing:SetSecurityGroups",
            "elasticloadbalancing:SetSubnets",
            "elasticloadbalancing:DeleteLoadBalancer",
            "elasticloadbalancing:ModifyTargetGroup",
            "elasticloadbalancing:ModifyTargetGroupAttributes",
            "elasticloadbalancing:DeleteTargetGroup",
            "elasticloadbalancing:RegisterTargets",
            "elasticloadbalancing:DeregisterTargets",
            "elasticloadbalancing:SetWebAcl",
            "elasticloadbalancing:ModifyListener",
            "elasticloadbalancing:AddListenerCertificates",
            "elasticloadbalancing:RemoveListenerCertificates",
            "elasticloadbalancing:ModifyRule"
      ],
      "Resource": "*"
    }
  ]
}
EOF

cat <<EOF > ExternalDnsControllerRolePolicy.json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
            "route53:ChangeResourceRecordSets",
            "route53:ListResourceRecordSets",
            "route53:ListHostedZones"
      ],
      "Resource": "*"
    }
  ]
}
EOF

cat <<EOF > MonitoringRolePolicy.json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
            "logs:CreateLogGroup",
            "logs:CreateLogStream",
            "logs:PutLogEvents",
            "cloudwatch:PutMetricData",
            "ec2:DescribeTags"
      ],
      "Resource": "*"
    }
  ]
}
EOF
#create sample roles
for i in MonitoringRole ExternalDnsControllerRole EfsCsiDriverRole AlbControllerRole EbsCsiDriverRole
do
aws iam create-policy --policy-name ${i}Policy --policy-document file://${i}Policy.json
aws iam create-role --role-name ${i} --assume-role-policy-document file://trust.json --description  "Used for ${i}"
aws iam attach-role-policy --role-name ${i} --policy-arn=arn:aws:iam::${ACCOUNT_ID}:policy/${i}Policy
done

rm -rf *Policy.json
rm -rf trust.json


cat <<EOF > artifact.json
{
    "MonitoringRole": "arn:aws:iam::${ACCOUNT_ID}:role/MonitoringRole",
    "ExternalDnsControllerRole": "arn:aws:iam::${ACCOUNT_ID}:role/ExternalDnsControllerRole",
    "EfsCsiDriverRole": "arn:aws:iam::${ACCOUNT_ID}:role/EfsCsiDriverRole",
    "EksSecurityGroup": "${CLUSTER_SG_ID}",
    "AlbControllerRole": "arn:aws:iam::${ACCOUNT_ID}:role/AlbControllerRole",
    "EksClusterName": "${CLUSTER_NAME}",
    "EbsCsiDriverRole": "arn:aws:iam::${ACCOUNT_ID}:role/EbsCsiDriverRole",
    "myVolume1" : "${EFS_ID}"
}
EOF

aws ssm put-parameter --name "EKS_OUT_SSM" --type "String" --value "`cat artifact.json`" --overwrite --region us-west-2
export ROLE_ARN=$(aws cloudformation describe-stacks --stack-name EksDemoBootstrapInfra --query "Stacks[0].Outputs[0].OutputValue" --output text)
eksctl create iamidentitymapping --cluster ${CLUSTER_NAME} --region=${AWS_REGION} --arn ${ROLE_ARN} --group system:masters --username admin
