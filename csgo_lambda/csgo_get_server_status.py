import boto3
import json
import os

from aws import get_running_tasks, get_task_details
from common import return_code

ECS_CLUSTER = os.environ.get('ECS_CLUSTER')
TASK_FAMILY = os.environ.get('TASK_FAMILY')


def handler(event, context):
    """ Get the status of running CSGO servers.

    There should only be one running server at any time.

    Args:
        event (dict): Event getting passed to the function via an API
        context (dict): The context the function runs in

    Returns:
        dict: Details of the running containers
    """

    fmt = '%Y-%m-%d %H:%M:%S'
    task_arns = get_running_tasks(ECS_CLUSTER, TASK_FAMILY)
    if len(task_arns) == 0:
        return return_code(200, {'task_details': None})

    task_details = get_task_details(ECS_CLUSTER, task_arns)

    output = []
    for task in task_details:

        public_ip = get_public_ip(task)

        single_task = {
            'taskArn': task['taskArn'],
            'publicIp': public_ip,
            'startedAt': task['startedAt'].strftime(fmt) if 'startedAt' in task else None,
            'lastStatus': task['lastStatus'],
            'desiredStatus': task['desiredStatus'],
            'cpu': task['cpu'],
            'memory': task['memory'],
            'overrides': task['overrides'] if 'overrides' in task else None,
            'stopCode': task['stopCode'] if 'stopCode' in task else None,
            'stoppedReason': task['stoppedReason'] if 'stoppedReason' in task else None,
            'stoppingAt': task['stoppingAt'].strftime(fmt) if 'stoppingAt' in task else None,
            'stoppedAt': task['stoppedAt'].strftime(fmt) if 'stoppedAt' in task else None
        }
        output.append(single_task)

    return return_code(200, {'task_details': output})


def get_public_ip(task):
    """ Get the public IP address for the task from the attached interface.

    Each task should only have 1 attached network interface and 1 public IP.

    Args:
        task (dict): The JSON returned from the describe_tasks function

    Returns:
        str: IP address of the task
    """

    # Get a list of the attached ENI's, there should only be one per task
    enis = [a for a in task['attachments']
            if 'type' in a and a['type'] == 'ElasticNetworkInterface']
    assert len(enis) == 1

    # Get the network ID for the ENI, again there should only be one
    network_ids = [n['value'] for n in enis[0]['details']
                   if n['name'] == 'networkInterfaceId']
    assert len(network_ids) == 1

    # Get the details of the ENI and return the IP address
    resource = boto3.resource('ec2').NetworkInterface(network_ids[0])
    return resource.association_attribute['PublicIp']

