# AWS Security Group Remediation Lambda

This Lambda function automatically remediates open ingress rules (0.0.0.0/0) in AWS Security Groups by replacing them with specified internal CIDR ranges. This helps maintain security best practices by preventing unrestricted access to AWS resources.

## Features

- Identifies and removes ingress rules that allow access from 0.0.0.0/0
- Replaces open rules with specified internal CIDR ranges
- Preserves original protocol and port configurations
- Provides detailed logging for troubleshooting
- Returns clear status messages about remediation actions

## Prerequisites

- AWS Lambda execution role with the following permissions:
  - `ec2:DescribeSecurityGroups`
  - `ec2:RevokeSecurityGroupIngress`
  - `ec2:AuthorizeSecurityGroupIngress`
- Python 3.x runtime
- boto3 AWS SDK

## Configuration

The function uses a predefined list of internal CIDR ranges to replace open ingress rules. Modify the `internal_cidr_ranges` list to match your organization's internal network ranges:

```python
internal_cidr_ranges = ['10.0.0.0/16', '10.1.0.0/16']
```

## Usage

The function expects an event with the following parameter:

```json
{
    "target_sg_id": "sg-xxxxxxxxxxxxxxxxx"
}
```

### Input Parameters

- `target_sg_id` (required): The ID of the security group to remediate

### Response Format

The function returns a JSON object with:
- `statusCode`: HTTP status code (200 for success, 400/500 for errors)
- `body`: Description of the action taken or error message

#### Success Response Example
```json
{
    "statusCode": 200,
    "body": "Ingress rules for security group sg-xxxxxxxxxxxxxxxxx have been remediated."
}
```

#### Error Response Example
```json
{
    "statusCode": 400,
    "body": "Error: target_sg_id is required"
}
```

## Error Handling

The function includes error handling for:
- Missing target security group ID
- Invalid security group ID
- Permissions issues
- AWS API errors

## Logging

The function logs detailed information about:
- Security group evaluation
- Rule modifications
- Error conditions
- Remediation actions

## Best Practices

1. Test the function in a non-production environment first
2. Review and update the internal CIDR ranges regularly
3. Monitor the Lambda execution logs for any issues
4. Consider implementing additional validation for security group modifications

## Security Considerations

- Ensure the Lambda execution role follows the principle of least privilege
- Regularly audit the internal CIDR ranges being used
- Consider implementing additional controls for sensitive security groups
- Monitor CloudTrail logs for security group modifications

## Limitations

- The function only remediates IPv4 CIDR-based rules
- Only processes ingress rules (not egress)
- Does not handle security group references or IPv6 rules
