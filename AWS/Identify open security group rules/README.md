# AWS Security Groups Audit Tool

A Python script for auditing security groups across multiple AWS accounts within an AWS Organization. This tool helps identify potential security risks by scanning for security groups with inbound rules that allow access from any IP address (0.0.0.0/0).

## Features

- Multi-account scanning using AWS SSO profiles
- Multi-region support
- Automatic SSO token refresh
- Load balancer association detection (Classic LB, ALB, NLB)
- CSV report generation with detailed security group information
- Progress tracking and logging
- Incremental CSV writing to handle large datasets

## Prerequisites

- Python 3.x
- AWS CLI configured with SSO profiles
- Required Python packages:
  - boto3
  - configparser
  - logging

## Installation

1. Clone this repository
2. Install required packages:
```bash
pip install boto3
```

## Configuration

1. Ensure your AWS SSO profiles are configured in `~/.aws/config`
2. Modify the following constants in the script if needed:
   - `AWS_CONFIG_PATH`: Path to your AWS configuration directory
   - `REGIONS_TO_SCAN`: List of AWS regions to scan

## Usage

Run the script:
```bash
python sg_audit.py
```

The script will:
1. Scan all configured AWS profiles
2. Check each specified region
3. Generate a CSV report with timestamp: `security_groups_audit_YYYYMMDD_HHMMSS.csv`
4. Create a log file: `sg_audit.log`

## Output

The CSV report includes the following information for each security group:
- Timestamp
- AWS Profile
- Account ID
- Region
- Security Group ID and Name
- VPC ID
- Protocol details (ports, protocols)
- Source IP ranges
- Load Balancer associations
- Tags (Owner, Environment, Project)
- Error messages (if any)

## Error Handling

The script includes robust error handling:
- Automatic SSO token refresh
- Logging of all errors to both file and console
- Continued execution even if individual profiles or regions fail
- Incremental saving of results to prevent data loss

## Logging

Logs are written to:
- Console (stdout)
- `sg_audit.log` file

Log entries include:
- Timestamp
- Progress updates
- Error messages
- Profile and region processing status

## Security Considerations

This tool identifies security groups with potentially risky configurations, specifically:
- Inbound rules allowing 0.0.0.0/0
- Open ports accessible from any IP address
- Security groups associated with load balancers

## Best Practices

1. Review the generated reports regularly
2. Validate any open ports are necessary
3. Consider restricting IP ranges where possible
4. Document security group purposes using tags
5. Monitor changes through CloudTrail

## Disclaimer

This tool is provided as-is. Always review and validate security configurations before making changes to your AWS infrastructure.
