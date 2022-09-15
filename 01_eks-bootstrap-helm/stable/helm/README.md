# EKS Bootstrap Chart

Helm chart for deploying  pods to a fresh EKS cluster.
Will deploy the following:

- AWS Cloudwatch Metrics Agents:
  - Container Insights
  - CW for Prometheus
- FluentBit

## Values

### Monitoring

Fluentbit outputs are configurable.
The following values are supported:

- `.fluentbit.output.elasticsearch`: If it exists, it should be an object with `host` and `port` keys.
  Do not set to disable ES.
- `.fleuntbit.output.kinesis.(application|dataplane|host)`: Kinesis output for specific streams.
  If set, should have the `stream` key.
  To enable, set any (application|dataplane|host) Kinesis config.
  To set none, `.fluentbit.output.kinesis` should equal `{}` or the empty object.
- `fluentbit.output.s3.(application|dataplane|host)`: S3 output for specific streams.
  If set, should have the `bucket` key.
  To enable, set any (application|dataplane|host) S3 config.
  To set none, `.fluentbit.output.s3` should equal `{}` or the empty object.

### Subcharts
Add sub charts like `ALB`, `EFS`, `EBS` in the `charts` folder in `.tgz` format

- AWS Load Balancer Controller will be installed if `awslbc.enabled` is set, and `awslbc.clusterName` is populated as the name of the cluster.
