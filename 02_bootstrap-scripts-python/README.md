# Bootstrap Scripts

This repository contains the script for bootstrapping EKS clusters. These scripts are distributed as a pip package.

## Installing

To install the package, authenticate with CodeArtifact `eks-bootstrap` domain using repository `bootstrap-scripts-python`.

Command:
```
aws codeartifact login --tool pip --repository bootstrap-scripts-python --domain eks-bootstrap --domain-owner $(aws sts get-caller-identity --output text --query 'Account') --region us-west-2
```

then run `pip install bootstrap-cli`. This will install `bootstrapc-cli`.

## Running

The scripts included and how to run them are documented below.

### `cli`

The python cli for the bootstrap will run a helm update with values sourced from additional contexts like SSM parameters, repository config files or certain environment variables.

The helm chart will deploy cluster daemons such as fluentbit and efscsi, and also allows the specification of storage classes. 

The script takes the following flags:
  - `-h, --help`: show this help message and exit
  - `--json`: The path to the config JSON for setting up dynamic values
  - `--artifact`: The path to the output JSON from the previous stage containing stack output. This is required if --json is specified
  - `--context`: A context to register with helm, see details below. This flag can be set multiple times
  - `--chart`: Path to the helm chart to deploy, if not the application will pull the chart depending on the flags.
  - `--release`: Helm release name
  - `--print_values`: Print generated values.
  - `--helm`: Deploy helm Chart.
  - `--bindserviceaccounts`: Allow Helm to provision and bind IAM roles to K8S service accounts
  - `--helm_arg` Arguments to be passed to the helm upgrade command.
  - `--upgrade`: Upgrade the chart release.
  - `--template`: Print the generated template.

If the cli is run with `--upgrade` or `--template` command the bootstrap cli with use `install` flag for helm chart installation.

### Contexts

The bootstrap cli has a concept of "Contexts". Each context will pull variables into the helm values for deployment. Contexts are pluggable and modular. When specifying a context via the cli, the flag value should match the following format:
```
<context type>:<context primary id>:<context additional configuration>
```
The context type refers to the type of the context, see the list below. The primary id is a value specific to that context to configure the context. Context additional configuration is a comma separated list of key-value pairs with an "=" separator that allows specific configuration for the context. Supported contexts and their configurations are listed below:
- `file`: take values from a JSON file, supported optional JSONPath filter
  - Primary ID: path to the jsonfile
  - Additional Configuration:
    - pathfilter: A JSONpath query to filter parts of the input json. Requires key to be set.
    - key: The top level key to apply the filtered json to in the Helm values.
- `environment`: Add key-value pairs from environment variables to Helm values. Supports structured variables with the "__" separator (i.e. PREFIX_A__B=C will be value {A: {B: C}}).
  - Primary ID: Environment variable prefix to use (prefix will be stripped)
  - No additional configuration
- `varcontent`: Reads the structured content of an environment variable and adds it to the values. So far, only JSON is supported.
  - Primary ID: The name of the variable to read
  - Additional Configuration:
    - type: The type of structured content held by the variable, currently only "json" is supported
    - key: Optional, a top level key to store the values from the json in the values, i.e. if "MyKey" is specified, the values will have { ..., "MyKey": {...content from variable}, ...}
- `raw` : Set a value directly. The indicator is the path to set, the "value" option is the value that will get set.
  - Primary ID: The path of key value which need to be modified
  - value: Specifies the value  need to be set.

### Environment Variables used By `bootstrap-cli`

Below are the list environment variables directly used by bootstrap-cli

- `HELM_IMAGE_TAG` : Specifies the tag of helm image in ECR
- `BOOTSTRAP_DEFAULT_REPO` : Specifies the default repository for bootstrap helm charts
- `BOOTSTRAP_HELM_DEFAULT_IMAGE` : Specifies the name of the helm image
- `HELM_EXPERIMENTAL_OCI`: As the helm image support is an experimental feature the environment variable should be set as `1`

### Examples

Deploy helm chart with HELMD_* environment variables:

```
bootstrap-cli --release my_helm_chart \
    --context environment:HELMD_ \
    --json <path to cluster config> \
    --artifact <path to output JSON from previous stages> --helm
```

Deploy helm chart with raw value context to disable externaldns component. Additionlly any chart can be disabled by this method:

```
bootstrap-cli --release my_helm_chart \
    --context raw:externaldns.enabled:value=false \
    --json <path to cluster config> \
    --artifact <path to output JSON from previous stages> --helm
    
```

Deploy helm chart with a JSON variable for values:

```
bootstrap-cli --release my_helm_chart \ 
    --context varcontent:MY_JSON_VAR:type=json \
    --json <path to cluster config> \
    --artifact <path to output JSON from previous stages> --helm
```

Print helm chart values for various context:
```
      bootstrap-cli --json $CONFIG= --artifact $ARTIFACT \
      --helm --helm_arg='-n kube-system' \
      --release RELEASE_NAME --template --print_values
```

Print helm chart template with values for various context:
```
      bootstrap-cli --json $CONFIG= --artifact $ARTIFACT \
      --helm --helm_arg='-n kube-system' \
      --release RELEASE_NAME --template --print_values --template
```

### `builspec.yml`

Distributed with this repo is a CodeBuild buildspec.yml file that will retrieve the required dependencies and install the bootstrap helm chart in a cluster.


