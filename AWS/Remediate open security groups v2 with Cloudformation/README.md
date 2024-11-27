# AWS Security Group Remediation Lambda

This Lambda function automatically remediates open ingress rules (0.0.0.0/0) in AWS Security Groups by replacing them with specified internal CIDR ranges. It is triggered automatically when security groups are created or modified.

## Features

- Automatically triggered by security group changes through EventBridge
- Configurable internal CIDR ranges via CloudFormation parameters
- Identifies and removes ingress rules that allow access from 0.0.0.0/0
- Replaces open rules with specified internal CIDR ranges
- Preserves original protocol and port configurations
- Skips remediation for specified ports on security groups attached to load balancers
- Provides detailed logging for troubleshooting

## Architecture

The solution consists of:
1. An EventBridge rule that monitors for security group changes
2. A Lambda function that performs the remediation
3. IAM roles and permissions for secure execution
4. Environment variables for CIDR range and port configuration

## Prerequisites

- AWS CLI installed and configured
- Appropriate permissions to deploy CloudFormation templates
- Python 3.x
- boto3 AWS SDK

## Deployment Options

### As a Standalone Stack

Deploy using AWS CLI:
```bash
aws cloudformation create-stack \
  --stack-name security-group-remediation \
  --template-body file://template.yaml \
  --capabilities CAPABILITY_IAM \
  --parameters \
    ParameterKey=InternalCIDRRanges,ParameterValue="10.0.0.0/16,172.16.0.0/12,192.168.0.0/16" \
    ParameterKey=IsStackSetExecution,ParameterValue=false \
    ParameterKey=AdditionalSkipPorts,ParameterValue="22,3389"
```

### As a StackSet

Deploy using AWS CLI:
```bash
aws cloudformation create-stack-set \
  --stack-set-name security-group-remediation \
  --template-body file://template.yaml \
  --capabilities CAPABILITY_IAM \
  --parameters \
    ParameterKey=InternalCIDRRanges,ParameterValue="10.0.0.0/16,172.16.0.0/12,192.168.0.0/16" \
    ParameterKey=IsStackSetExecution,ParameterValue=true \
    ParameterKey=AdditionalSkipPorts,ParameterValue="22,3389"
```

Then create stack instances:
```bash
aws cloudformation create-stack-instances \
  --stack-set-name security-group-remediation \
  --accounts "111111111111" "222222222222" \
  --regions "eu-west-1" "us-east-1"
```

## Configuration

### CloudFormation Parameters

| Parameter | Description | Default | Required |
|-----------|-------------|---------|----------|
| InternalCIDRRanges | Comma-separated list of internal CIDR ranges | 10.0.0.0/16,10.1.0.0/16 | Yes |
| IsStackSetExecution | Indicates if deployment is via StackSet | false | Yes |
| AdditionalSkipPorts | Comma-separated list of additional ports to skip remediation for load balancer security groups | None | No |

### Resource Tags

The following tags are automatically applied to supported resources:
- CreatedBy: Stack name
- StackId: Full stack ID
- StackSetName: Name of the StackSet (if applicable, "N/A" if not)
- CreatedMethod: CloudFormation

## Triggering Events

The function automatically responds to the following EC2 API calls:
- CreateSecurityGroup
- AuthorizeSecurityGroupIngress  
- ModifySecurityGroupRules

## Monitoring and Logs

### CloudWatch Logs
The Lambda function logs the following information:  
- Received events
- CIDR range and port configurations
- Load balancer association checks
- Security group modifications
- Remediation actions  
- Error messages

### Lambda Metrics
Monitor the following CloudWatch metrics:
- Invocations
- Errors
- Duration
- Throttles
- ConcurrentExecutions

## Error Handling

The function includes error handling for:
- Invalid or missing event data
- Missing security group ID 
- Invalid security group ID
- Invalid CIDR range or port format
- AWS API errors

## Security Considerations

1. IAM Role Permissions
   - Lambda execution role has minimal required permissions  
   - Only allows specific EC2, ELB, and ALB actions

2. Network Security
   - Function replaces 0.0.0.0/0 with specified internal ranges
   - Original port and protocol settings are preserved
   - Skips remediation for specified ports on load balancer security groups

## Limitations

- Only processes IPv4 CIDR-based rules
- Only handles ingress rules
- Does not process security group references  
- Does not handle IPv6 rules

## Troubleshooting 

### Common Issues

1. Lambda Not Triggering
   - Verify EventBridge rule is active
   - Check CloudTrail is enabled  
   - Review IAM permissions

2. Rule Modification Failures  
   - Verify security group exists
   - Check CIDR ranges and ports are valid
   - Review Lambda execution role permissions

3. StackSet Deployment Issues
   - Ensure target accounts have required StackSet execution role
   - Verify region is supported
   - Check account limits   

### Logs Analysis

To analyze issues:
1. Open CloudWatch Logs
2. Find the log group for the Lambda function  
3. Look for ERROR level messages
4. Check event processing details

## Maintenance

Regular maintenance tasks:
1. Review and update CIDR ranges and skip ports as needed
2. Monitor CloudWatch logs for errors
3. Check CloudTrail for security group modifications
4. Verify EventBridge rule is functioning
5. Review IAM roles and permissions

## Updating the Stack

To update CIDR ranges, skip ports or other parameters:

```bash
aws cloudformation update-stack \
  --stack-name security-group-remediation \
  --template-body file://template.yaml \
  --capabilities CAPABILITY_IAM \
  --parameters \
    ParameterKey=InternalCIDRRanges,ParameterValue="10.0.0.0/8,172.16.0.0/12" \  
    ParameterKey=IsStackSetExecution,ParameterValue=false \
    ParameterKey=AdditionalSkipPorts,ParameterValue="22,3389,8080"  
```

For StackSets:
```bash 
aws cloudformation update-stack-set \
  --stack-set-name security-group-remediation \
  --template-body file://template.yaml \
  --capabilities CAPABILITY_IAM \   
  --parameters \
    ParameterKey=InternalCIDRRanges,ParameterValue="10.0.0.0/8,172.16.0.0/12" \
    ParameterKey=IsStackSetExecution,ParameterValue=true \
    ParameterKey=AdditionalSkipPorts,ParameterValue="22,3389,8080"
```
