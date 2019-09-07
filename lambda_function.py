import boto3
# import logging
import logging.handlers
import os
import sys
from botocore.exceptions import ClientError

# configure logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)-5.5s]  %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ])

logger = logging.getLogger()

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
    error_list.append("AWS_DEFAULT_REGION")
    pass

try:
    SCRIPT_ACTION = os.environ['SCRIPT_ACTION'].lower()
except KeyError as K:
    error_list.append("SCRIPT_ACTION")
    pass

if error_list:
    msg = "The following environment variables have been left undefined: {}".format(error_list)
    logger.error(msg)
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


def get_state(instance_id_list):
    """
    takes a list var of instance id's. returns a dict
    """


def turn_off(instance_id_list):
    """
    consumes a LIST var of instance ids.
    sets the instance states to STOPPED (does not terminate)
    the request conditions Hibernate and Force default to false
    """
    client = boto3.client('ec2', region_name=REGION)
    response = client.stop_instances(InstanceIds=instance_id_list)
    response_dictionary = {}
    for instance in response['StoppingInstances']:
        response_dictionary[instance['InstanceId']] = {"CurrentState": instance['CurrentState']['Name'],
                                                       "PreviousState": instance['PreviousState']['Name']
                                                       }
    return response_dictionary


def turn_on(instance_id_list):
    """
    consumes a LIST var of instance ids.
    sets the instance states to running
    """
    client = boto3.client('ec2', region_name=REGION)
    response = client.start_instances(InstanceIds=instance_id_list)
    response_dictionary = {}
    for instance in response['StartingInstances']:
        response_dictionary[instance['InstanceId']] = {"CurrentState": instance['CurrentState']['Name'],
                                                       "PreviousState": instance['PreviousState']['Name']
                                                       }
    return response_dictionary


def check_handler(event, context):
    """
    lambda function, rolls everything up
    """
    all_ec2 = gatherec2()
    instance_list = find_by_prefix(PREFIX, all_ec2)

    logger.info(instance_list)

    if SCRIPT_ACTION == "start":
        response = turn_on(instance_list)
        for item in response:
            if response[item]['CurrentState'] == response[item]['PreviousState']:
                logger.info("{} was already running".format(item))
            else:
                logger.info("{} has been started".format(item))
    elif SCRIPT_ACTION == "stop":
        response = turn_on(instance_list)
    else:
        logger.error("Your SCRIPT_ACTION environment variable is set to {}, which is not recognized. Please set it to either start or stop".format(SCRIPT_ACTION))
    return
