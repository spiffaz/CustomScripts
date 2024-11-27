# AWS Security Group Remediation Lambda

This Lambda function automatically remediates open ingress rules (0.0.0.0/0) in AWS Security Groups by replacing them with specified internal CIDR ranges. It is triggered automatically when security groups are created or modified.

## Features

- Automatically triggered by security group changes through EventBridge
- Configurable internal CIDR ranges via CloudFormation parameters
- Identifies and removes ingress rules that allow access from 0.0.0.0/0
- Replaces open rules with specified internal CIDR ranges
- Preserves original protocol and port configurations
- Provides detailed logging for troubleshooting

## Architecture

The solution consists of:
1. An EventBridge rule that monitors for security group changes
2. A Lambda function that performs the remediation
3. IAM roles and permissions for secure execution
4. Environment variables for CIDR range configuration

## Prerequisites

- AWS CLI installed and configured
- Appropriate permissions to deploy CloudFormation templates
- Python 3.x
- boto3 AWS SDK

## Deployment

### Initial Deployment

Deploy the CloudFormation stack using the AWS CLI:

```bash
aws cloudformation create-stack \
  --stack-name security-group-remediation \
  --template-body file://template.yaml \
  --capabilities CAPABILITY_IAM \
  --parameters ParameterKey=InternalCIDRRanges,ParameterValue="10.0.0.0/16,172.16.0.0/12,192.168.0.0/16"
```

Or using the AWS Console:
1. Navigate to CloudFormation
2. Choose "Create stack"
3. Upload the template.yaml file
4. Fill in the parameters:
   - Stack name: `security-group-remediation`
   - InternalCIDRRanges: Comma-separated list of CIDR ranges

### Updating CIDR Ranges

To update the CIDR ranges, update the stack with new parameters:

```bash
aws cloudformation update-stack \
  --stack-name security-group-remediation \
  --template-body file://template.yaml \
  --capabilities CAPABILITY_IAM \
  --parameters ParameterKey=InternalCIDRRanges,ParameterValue="10.0.0.0/8,172.16.0.0/12"
```

## Configuration

### CloudFormation Parameters

| Parameter | Description | Default | Example |
|-----------|-------------|---------|---------|
| InternalCIDRRanges | Comma-separated list of internal CIDR ranges | 10.0.0.0/16,10.1.0.0/16 | 10.0.0.0/8,172.16.0.0/12 |

### Environment Variables

The Lambda function uses the following environment variables:

| Variable | Description | Source |
|----------|-------------|--------|
| INTERNAL_CIDR_RANGES | Comma-separated list of CIDR ranges | CloudFormation parameter |

## Triggering Events

The function automatically responds to the following EC2 API calls:
- CreateSecurityGroup
- AuthorizeSecurityGroupIngress
- ModifySecurityGroupRules

## Response Format

The function returns a JSON object with:
- `statusCode`: HTTP status code (200 for success, 400/500 for errors)
- `body`: Description of the action taken or error message

### Success Response Example
```json
{
    "statusCode": 200,
    "body": "Ingress rules for security group sg-xxxxxxxxxxxxxxxxx have been remediated."
}
```

### Error Response Example
```json
{
    "statusCode": 400,
    "body": "Error processing event: Could not determine security group ID from event"
}
```

## Error Handling

The function includes error handling for:
- Invalid or missing event data
- Missing security group ID
- Invalid security group ID
- Invalid CIDR range format
- Permissions issues
- AWS API errors

## Logging

The function logs detailed information about:
- Received EventBridge events
- Configured CIDR ranges
- Security group evaluation
- Rule modifications
- Error conditions
- Remediation actions

## Best Practices

1. Test the function in a non-production environment first
2. Review and update the internal CIDR ranges regularly
3. Monitor the Lambda execution logs for any issues
4. Consider implementing additional validation for security group modifications
5. Use AWS Organizations SCPs to restrict modifications to the Lambda function and EventBridge rule

## Security Considerations

- Ensure the Lambda execution role follows the principle of least privilege
- Regularly audit the internal CIDR ranges being used
- Consider implementing additional controls for sensitive security groups
- Monitor CloudTrail logs for security group modifications
- Implement proper change management for CIDR range updates

## Limitations

- The function only remediates IPv4 CIDR-based rules
- Only processes ingress rules (not egress)
- Does not handle security group references or IPv6 rules
- Maximum of 100 comma-separated CIDR ranges due to Lambda environment variable size limits

## Monitoring and Maintenance

1. Monitor Lambda function metrics in CloudWatch
   - Invocation count
   - Error count
   - Duration
   - Memory usage

2. Review CloudWatch Logs for:
   - Function execution details
   - CIDR range configuration
   - Remediation actions
   - Error messages

3. Regular maintenance tasks:
   - Review and update CIDR ranges as network architecture changes
   - Verify EventBridge rule is properly triggering
   - Check IAM roles and permissions
   - Review CloudTrail logs for security group modifications

## Troubleshooting

Common issues and solutions:

1. Lambda not triggering:
   - Check EventBridge rule configuration
   - Verify CloudTrail is enabled
   - Check IAM permissions

2. CIDR range updates not taking effect:
   - Verify CloudFormation stack update completed successfully
   - Check Lambda environment variables
   - Review Lambda function logs

3. Remediation failures:
   - Check security group exists
   - Verify IAM permissions
   - Review error messages in CloudWatch Logs
