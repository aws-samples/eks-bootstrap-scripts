# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
from .context import FileContext, GenericMultiMuxContext, JSONContext
from .helm import Helm
from os import environ

def addHelmValues(config: str, artifact: str, helm: Helm):
    """
    Add required values for Helm chart deployment. Includes values for daemons
    and initial networking.
    """
    # Add values for the monitoring role ARN for CW Agent and Fluentbit
    helm.add_context(FileContext(artifact, {
        'pathfilter': '.MonitoringRole',
        'key': 'monitoring_serviceAccount_annotations_eks.amazonaws.com/role-arn',
        'separator': '_'
    }))
    # Add values for the ALB controller IAM role
    helm.add_context(FileContext(artifact, {
        'pathfilter': '.AlbControllerRole',
        'key': 'awslbc_serviceAccount_annotations_eks.amazonaws.com/role-arn',
        'separator': '_'
    }))
    # Add values for the EFS CSI Driver IAM role
    helm.add_context(FileContext(artifact, {
        'pathfilter': '.EfsCsiDriverRole',
        'key': 'awsefscsi_controller_serviceAccount_annotations_eks.amazonaws.com/role-arn',
        'separator': '_'
    }))
    # Add values for the EBS CSI Driver IAM role
    helm.add_context(FileContext(artifact, {
        'pathfilter': '.EbsCsiDriverRole',
        'key': 'awsebscsi_serviceAccount_controller_annotations_eks.amazonaws.com/role-arn',
        'separator': '_'
    }))
    #Add configuration for the AWS Loadbalancer Controller
    helm.add_context(FileContext(config, {
        'pathfilter': '.loadbalancercontroller',
        'key': 'awslbc'
    }))
    # Add custom networking values for the EKS Cluster SG
    helm.add_context(FileContext(artifact, {
    'pathfilter': '.EksSecurityGroup',
    'key': 'cniCustomNw.cniSG'
    }))
    # Add custom networking values for the subnets to deploy ENIs for Pods
    helm.add_context(FileContext(config, {
    'pathfilter': '.createCustomNetworking.cniSubnets',
    'key': 'cniCustomNw.cniSubnet'
    }))
    # Add value to enable/disable custom networking
    helm.add_context(FileContext(config, {
    'pathfilter': '.createCustomNetworking.enabled',
    'key': 'cniCustomNw.enabled'
    }))
    # Add value for the IAM role for the ExternalDNS controller
    helm.add_context(FileContext(artifact, {
        'pathfilter': '.ExternalDnsControllerRole',
        'key': 'externaldns_serviceAccount_annotations_eks.amazonaws.com/role-arn',
        'separator': '_'
    }))

    # Add value for the domain filter for ExternalDNS to use
    helm.add_context(FileContext(config, {
        'pathfilter': '.externaldns.hostedZoneDomain',
        'key': 'externaldns_deployment_args_domain-filter',
        'separator': '_'
    }))
    # Add Hosted Zone ID Values for ExternalDNS
    helm.add_context(FileContext(config, {
      'pathfilter': '.externaldns.hostedZoneId',
      'key': 'externaldns_deployment_args_txt-owner-id',
      'separator': '_',
      'type' : 'json'
    }))
    parameters = environ.get("PARAMETER_STORE", default="{}")
    """
    Uses a FileContext to read values from .ebs in the target file, and place them
    in .ebs in the calues context.
    """
    context = FileContext(config, {
        'pathfilter': '.ebs',
        'key': 'ebs'
    })
    helm.add_context(context)
    """
    Uses a Mux Context to map the EFS FS IDs to their storage class definitions
    in the config file. EFS IDs come dynamically from previous stages, and should have
    the following format: $volume_name_from_config=fs-xxxxxxxx.
    """
    context = GenericMultiMuxContext("N/A", {
        "TargetSchemaFile": config,
        "SourceMappingFile": artifact,
        "TargetKey": "efs",
        "TargetLookupKey": "name",
        "TargetDestinationKey": "id"
    })
    helm.add_context(context)
