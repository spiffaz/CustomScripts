import boto3
import csv
from datetime import datetime
import configparser
import os
from botocore.exceptions import ClientError, ProfileNotFound, TokenRetrievalError
import sys
import logging
import subprocess
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sg_audit.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

# AWS Config Path
AWS_CONFIG_PATH = '/Users/spiff.azeta/.aws'

# Specify the regions you want to scan
REGIONS_TO_SCAN = [
    'us-east-1',
    'us-east-2',
    'us-west-2'
]

class Progress:
    def __init__(self, total_profiles):
        self.total_profiles = total_profiles
        self.total_regions = len(REGIONS_TO_SCAN)
        self.total_steps = total_profiles * self.total_regions
        self.current_step = 0
        
    def update(self, profile_name, region, current_profile_num):
        self.current_step += 1
        percentage = (self.current_step / self.total_steps) * 100
        region_num = REGIONS_TO_SCAN.index(region) + 1
        
        logging.info(f"\nProgress: {percentage:.1f}% complete")
        logging.info(f"Profile {current_profile_num}/{self.total_profiles}: {profile_name}")
        logging.info(f"Region {region_num}/{self.total_regions}: {region}")
        logging.info(f"Step {self.current_step}/{self.total_steps}\n")

class IncrementalCSVWriter:
    def __init__(self, filename, fieldnames):
        self.filename = filename
        self.fieldnames = fieldnames
        # Create file and write header
        with open(self.filename, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self.fieldnames)
            writer.writeheader()
    
    def append_results(self, results):
        """Append new results to the CSV file"""
        if not results:
            return
            
        with open(self.filename, 'a', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self.fieldnames)
            writer.writerows(results)

def refresh_sso_token(profile_name):
    """Refresh SSO token for a profile using AWS CLI."""
    try:
        logging.info(f"Attempting to refresh SSO token for profile {profile_name}")
        subprocess.run(['aws', 'sso', 'login', '--profile', profile_name], 
                      check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to refresh SSO token for profile {profile_name}: {str(e)}")
        return False

def get_aws_profiles():
    """Get list of AWS profiles from config file."""
    profiles = set()
    
    try:
        config = configparser.ConfigParser()
        config_path = os.path.join(AWS_CONFIG_PATH, 'config')
        if os.path.exists(config_path):
            config.read(config_path)
            config_profiles = [s.replace('profile ', '') for s in config.sections() if 'profile ' in s]
            profiles.update(config_profiles)
            logging.info(f"Found {len(config_profiles)} profiles in config file")
            logging.info(f"Profiles: {', '.join(sorted(profiles))}")
        return list(profiles)
    except Exception as e:
        logging.error(f"Error reading AWS configuration: {str(e)}")
        return []

def analyze_security_groups(session, region, profile_name, csv_writer):
    """Analyze security groups for a specific region."""
    results = []
    
    try:
        ec2 = session.client('ec2', region_name=region)
        elb = session.client('elb', region_name=region)
        elbv2 = session.client('elbv2', region_name=region)
        
        # Get account ID
        sts = session.client('sts')
        account_id = sts.get_caller_identity()['Account']
        
        # Get all security groups
        paginator = ec2.get_paginator('describe_security_groups')
        for page in paginator.paginate():
            for sg in page['SecurityGroups']:
                # Get security group tags
                tags = {tag['Key']: tag['Value'] for tag in sg.get('Tags', [])}
                
                # Check inbound rules
                for rule in sg.get('IpPermissions', []):
                    for ip_range in rule.get('IpRanges', []):
                        if ip_range.get('CidrIp') == '0.0.0.0/0':
                            from_port = rule.get('FromPort', 'All')
                            to_port = rule.get('ToPort', 'All')
                            protocol = rule.get('IpProtocol', 'All')
                            
                            # Get load balancer information
                            lb_info = "Not attached to LB"
                            try:
                                # Check Classic LBs
                                classic_lbs = elb.describe_load_balancers()['LoadBalancerDescriptions']
                                for lb in classic_lbs:
                                    if sg['GroupId'] in lb['SecurityGroups']:
                                        lb_info = f"Classic LB: {lb['LoadBalancerName']}"
                                        break
                                
                                # Check ALB/NLB
                                if lb_info == "Not attached to LB":
                                    v2_lbs = elbv2.describe_load_balancers()['LoadBalancers']
                                    for lb in v2_lbs:
                                        if 'SecurityGroups' in lb and sg['GroupId'] in lb['SecurityGroups']:
                                            lb_info = f"{lb['Type']}: {lb['LoadBalancerName']}"
                                            break
                            except ClientError:
                                lb_info = "Error checking LB"
                            
                            results.append({
                                'Timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                'Profile': profile_name,
                                'AccountID': account_id,
                                'Region': region,
                                'SecurityGroupID': sg['GroupId'],
                                'SecurityGroupName': sg['GroupName'],
                                'VpcId': sg.get('VpcId', 'Default VPC'),
                                'Protocol': protocol,
                                'FromPort': from_port,
                                'ToPort': to_port,
                                'Source': ip_range['CidrIp'],
                                'Description': ip_range.get('Description', 'No description'),
                                'LoadBalancerInfo': lb_info,
                                'Tags': json.dumps(tags),
                                'Owner': tags.get('Owner', 'Not specified'),
                                'Environment': tags.get('Environment', 'Not specified'),
                                'Project': tags.get('Project', 'Not specified')
                            })
                            
    except ClientError as e:
        logging.error(f"Error in {region} for profile {profile_name}: {str(e)}")
        results.append({
            'Timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'Profile': profile_name,
            'AccountID': account_id if 'account_id' in locals() else 'Unknown',
            'Region': region,
            'Error': str(e)
        })
    
    # Write results for this region immediately
    csv_writer.append_results(results)
    return results

def process_profile(profile_name, csv_writer, progress_tracker, current_profile_num):
    """Process a single profile completely before moving to the next."""
    profile_results = []
    
    try:
        logging.info(f"\n{'='*50}")
        logging.info(f"Starting to process profile: {profile_name}")
        
        # Create session
        session = boto3.Session(profile_name=profile_name)
        
        # Test if credentials are valid
        try:
            sts = session.client('sts')
            sts.get_caller_identity()
            logging.info(f"Credentials are valid for profile {profile_name}")
        except (ClientError, TokenRetrievalError):
            # If credentials are invalid, try to refresh SSO token
            logging.info(f"Credentials need refresh for profile {profile_name}")
            if refresh_sso_token(profile_name):
                # Create new session with refreshed credentials
                session = boto3.Session(profile_name=profile_name)
                logging.info(f"Successfully refreshed credentials for {profile_name}")
            else:
                logging.error(f"Failed to refresh credentials for profile {profile_name}")
                return []

        # Process each region sequentially
        for region in REGIONS_TO_SCAN:
            progress_tracker.update(profile_name, region, current_profile_num)
            logging.info(f"Scanning region {region} with profile {profile_name}")
            try:
                results = analyze_security_groups(session, region, profile_name, csv_writer)
                profile_results.extend(results)
                logging.info(f"Completed scanning {region} for profile {profile_name}")
            except Exception as e:
                logging.error(f"Error scanning {region} with profile {profile_name}: {str(e)}")
        
        logging.info(f"Completed processing profile: {profile_name}")
        logging.info(f"{'='*50}\n")
                    
    except Exception as e:
        logging.error(f"Error processing profile {profile_name}: {str(e)}")
    
    return profile_results

def main():
    try:
        # Get all AWS profiles
        profiles = get_aws_profiles()
        if not profiles:
            logging.error("No AWS profiles found")
            return

        # Initialize progress tracker
        progress = Progress(len(profiles))

        # Initialize CSV writer
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        csv_filename = f'security_groups_audit_{timestamp}.csv'
        fieldnames = ['Timestamp', 'Profile', 'AccountID', 'Region', 'SecurityGroupID', 
                     'SecurityGroupName', 'VpcId', 'Protocol', 'FromPort', 'ToPort', 
                     'Source', 'Description', 'LoadBalancerInfo', 'Tags', 'Owner',
                     'Environment', 'Project', 'Error']
        
        csv_writer = IncrementalCSVWriter(csv_filename, fieldnames)
        
        # Process profiles one at a time
        for i, profile_name in enumerate(profiles, 1):
            results = process_profile(profile_name, csv_writer, progress, i)
            
            logging.info(f"Results for profile {profile_name} processed")
            
        logging.info(f"Audit complete! All results written to: {csv_filename}")
            
    except Exception as e:
        logging.error(f"Critical error in main execution: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
