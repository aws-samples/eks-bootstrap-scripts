#!/bin/bash
export ACCOUNT_ID=$(aws sts get-caller-identity --query "Account" --output text)
for i in MonitoringRole ExternalDnsControllerRole EfsCsiDriverRole AlbControllerRole EbsCsiDriverRole
do
aws iam detach-role-policy --role-name ${i}  --policy-arn arn:aws:iam::${ACCOUNT_ID}:policy/${i}Policy
aws iam delete-role --role-name ${i} 
aws iam delete-policy --policy-arn=arn:aws:iam::${ACCOUNT_ID}:policy/${i}Policy
done