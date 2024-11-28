# AWS Security Group Remediation Solution

This solution provides automated remediation of open ingress rules (0.0.0.0/0) in AWS Security Groups. It deploys a serverless infrastructure that monitors and automatically modifies security groups to maintain security compliance by replacing open CIDR ranges with specified internal ranges.

## Solution Overview

The CloudFormation template deploys a complete security group remediation solution that consists of:

1. **EventBridge Rule** - Monitors the following security group-related events:
   - CreateSecurityGroup
   - AuthorizeSecurityGroupIngress
   - ModifySecurityGroupRules

2. **Lambda Function** - Performs the automated remediation of security groups

3. **IAM Role** - Provides necessary permissions for the Lambda function to:
   - Read security group configurations
   - Modify security group rules
   - Check load balancer associations
   - Write logs to CloudWatch

### Key Features

- Automatically detects and remediates open security group rules
- Special handling for load balancer security groups
- Configurable internal CIDR ranges for rule replacement
- Configurable port exceptions for load balancers
- Comprehensive logging and monitoring
- Support for both standalone and multi-account deployments via StackSets

### CloudFormation Template Structure

#### Parameters
- `InternalCIDRRanges` - Defines the internal CIDR ranges that will replace 0.0.0.0/0 rules
- `IsStackSetExecution` - Controls StackSet-specific configurations
- `AdditionalSkipPorts` - Specifies ports to exclude from remediation on load balancer security groups

#### Resources
1. **SecurityGroupRemediationLambda**
   - Python 3.9 runtime
   - 30-second timeout
   - 128MB memory allocation
   - Environment variables for configuration

2. **LambdaExecutionRole**
   - Basic Lambda execution permissions
   - Security group management permissions
   - Load balancer describibility permissions

3. **SecurityGroupEventRule**
   - EventBridge rule configuration
   - CloudTrail API event pattern matching
   - Lambda target specification

4. **LambdaInvokePermission**
   - Allows EventBridge to invoke the Lambda function

## Deployment Options

### Standalone Deployment

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

### Multi-Account Deployment (StackSet)

1. Create the StackSet:
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

2. Deploy to accounts:
```bash
aws cloudformation create-stack-instances \
  --stack-set-name security-group-remediation \
  --accounts "111111111111" "222222222222" \
  --regions "eu-west-1" "us-east-1"
```

## Lambda Function Implementation Details

The Lambda function serves as the core remediation engine. Here's how it works:

### Event Processing Flow

1. **Event Reception**
   - Receives CloudTrail events for security group changes
   - Extracts security group ID from the event
   - Validates event structure and required information

2. **Security Group Classification**
   - Checks if the security group is attached to a load balancer
   - Determines appropriate remediation strategy based on classification

3. **Rule Evaluation**
   - Identifies rules with 0.0.0.0/0 CIDR
   - Processes different rule types:
     - All protocols (-1)
     - Specific protocols with ports
     - Port ranges
     - Individual ports

4. **Remediation Actions**
   - For load balancer security groups:
     - Preserves allowed ports (80, 443, and configured exceptions)
     - Removes other open rules
   - For regular security groups:
     - Removes open rules
     - Creates new rules with internal CIDR ranges
     - Preserves original protocol and port configurations

### Load Balancer Security Group Handling

The function provides special handling for load balancer security groups:

- Automatically detects ELB/ALB/NLB associations
- Allows HTTP (80) and HTTPS (443) from 0.0.0.0/0 by default
- Supports additional allowed ports via configuration
- Removes non-allowed open rules without replacement
- Preserves allowed port configurations

### Error Handling and Logging

The function implements comprehensive error handling:

- Prevents remediation loops
- Handles AWS API errors
- Provides detailed logging
- Returns appropriate status codes:
  - 200: Success
  - 207: Partial success
  - 400: Invalid input
  - 500: AWS API errors

## Monitoring and Operations

### CloudWatch Logs

The solution provides detailed logging of:
- Event processing
- Security group modifications
- Rule evaluations
- Error conditions
- Remediation actions

### Metrics to Monitor

- Lambda invocations
- Error rates
- Duration
- Throttling events
- Concurrent executions

## Limitations

- IPv4 CIDR rules only
- Ingress rules only
- No security group reference processing
- No IPv6 support
- AWS limit of 60 rules per security group
- 30-second Lambda timeout

## Maintenance

### Regular Tasks

1. Review and update CIDR ranges as needed
2. Update skip ports configuration
3. Monitor CloudWatch logs
4. Review IAM permissions
5. Verify EventBridge rule status

### Configuration Updates

Update existing deployment:

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

Update StackSet:
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
