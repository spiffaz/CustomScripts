# Necessary Lambda permissions "ec2:DescribeSecurityGroups", "ec2:RevokeSecurityGroupIngress","ec2:AuthorizeSecurityGroupIngress"
import boto3
import json

# Initialize EC2 client
ec2 = boto3.client('ec2')

# List of internal CIDR ranges
internal_cidr_ranges = ['10.0.0.0/16', '10.1.0.0/16']  # Include additional CIDR ranges

def lambda_handler(event, context):
    # Check if the 'target_sg_id' exists in the event
    if 'target_sg_id' not in event:
        print("Error: target_sg_id not provided in the event.")
        return {
            'statusCode': 400,
            'body': 'Error: target_sg_id is required'
        }
    
    target_sg_id = event['target_sg_id']
    print(f"Target Security Group ID: {target_sg_id}")
    
    # Describe the specific security group
    try:
        security_group = ec2.describe_security_groups(GroupIds=[target_sg_id])
        print(f"Successfully described security group {target_sg_id}.")
    except Exception as e:
        print(f"Error describing security group: {str(e)}")
        return {
            'statusCode': 500,
            'body': f"Error describing security group: {str(e)}"
        }
    
    # Flag to check if any rules were remediated
    remediation_done = False

    # Iterate through the permissions (rules) of the security group
    for permission in security_group['SecurityGroups'][0]['IpPermissions']:
        print(f"Evaluating rule with protocol {permission['IpProtocol']}, "
              f"ports {permission.get('FromPort', 'All')} to {permission.get('ToPort', 'All')}.")
        
        # Check the IP ranges for open ingress (0.0.0.0/0)
        for ip_range in permission.get('IpRanges', []):
            if ip_range['CidrIp'] == '0.0.0.0/0':
                print(f"Found rule allowing ingress from 0.0.0.0/0 on ports "
                      f"{permission.get('FromPort', 'All')} to {permission.get('ToPort', 'All')}.")
                
                try:
                    # Revoke the open ingress rule
                    ec2.revoke_security_group_ingress(
                        GroupId=target_sg_id,
                        IpProtocol=permission['IpProtocol'],
                        FromPort=permission.get('FromPort'),
                        ToPort=permission.get('ToPort'),
                        CidrIp='0.0.0.0/0'
                    )
                    print(f"Revoked rule allowing ingress from 0.0.0.0/0 on ports "
                          f"{permission.get('FromPort')} to {permission.get('ToPort')}.")
                    
                    # Authorize new rules for each internal CIDR range using the same protocol and port range
                    for cidr in internal_cidr_ranges:
                        ec2.authorize_security_group_ingress(
                            GroupId=target_sg_id,
                            IpProtocol=permission['IpProtocol'],
                            FromPort=permission.get('FromPort'),
                            ToPort=permission.get('ToPort'),
                            CidrIp=cidr
                        )
                        print(f"Authorized rule allowing ingress from {cidr} on ports "
                              f"{permission.get('FromPort')} to {permission.get('ToPort')}.")
                    
                    # Set the remediation flag to True
                    remediation_done = True
                
                except Exception as e:
                    print(f"Error modifying security group: {str(e)}")
                    return {
                        'statusCode': 500,
                        'body': f"Error modifying security group: {str(e)}"
                    }
    
    # If no remediation was done, return that no changes were necessary
    if not remediation_done:
        print(f"No open ingress rules found for security group {target_sg_id}. No remediation was necessary.")
        return {
            'statusCode': 200,
            'body': f"No remediation necessary for security group {target_sg_id}. No open ingress rules were found."
        }
    
    print(f"Ingress rules for security group {target_sg_id} have been remediated.")
    return {
        'statusCode': 200,
        'body': f"Ingress rules for security group {target_sg_id} have been remediated."
    }
