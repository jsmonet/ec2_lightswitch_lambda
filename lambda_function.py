import os
import boto3
import sys
from botocore.exceptions import ClientError

# not that we change env vars later on, but for the sake of specificity,
# let's use environ

error_list = []

try:
    PREFIX = os.environ['PREFIX']
except KeyError as K:
    error_list.append("PREFIX")
    pass

try:
    REGION = os.environ['AWS_DEFAULT_REGION']
except KeyError as K:
    error_list.append("REGION")
    pass

if error_list:
    print("The following environment variables have been left undefined: {}".format(error_list))
    sys.exit(1)


def gatherec2():
    """
    returns dict of {"instance id": { tags }}
    """
    client = boto3.client('ec2', region_name=REGION)
    instance_list = client.describe_instances()['Reservations']
    return instance_list


def find_by_prefix(prefix, instance_list):
    """
    consume string PREFIX and look for it, instance by instance,
    in the tag Values
    """
    output_list = []
    for line in instance_list:
        for vals in line['Instances'][0]['Tags']:
            if prefix in vals['Value']:
                output_list.append(line['Instances'][0]['InstanceId'])
    return output_list


def turn_off(instance_id_list):
    """
    consumes a LIST var of instance ids.
    sets the instance states to STOPPED (does not terminate)
    the request conditions Hibernate and Force default to false
    """
    client = boto3.client('ec2', region_name=REGION)
    response = client.stop_instances(
        InstanceIds=[
            instance_id_list
        ]
    )
    return response


def turn_on(instance_id_list):
    """
    consumes a LIST var of instance ids.
    sets the instance states to running
    """
    client = boto3.client('ec2', region_name=REGION)
    response = client.start_instances(
        InstanceIds=[
            instance_id_list
        ]
    )
    return response


instances = gatherec2()
endresult = find_by_prefix(PREFIX,instances)

print(endresult)