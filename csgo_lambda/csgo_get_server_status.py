import json
import os

from aws import get_running_tasks, get_task_details, get_public_ip, retrieve_hostnames
from common import return_code

ECS_CLUSTER = os.environ.get('ECS_CLUSTER')
TASK_FAMILY = os.environ.get('TASK_FAMILY')
HOSTED_ZONE_ID = os.environ.get('HOSTED_ZONE_ID')


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

        public_ip = get_public_ip(ECS_CLUSTER, task['taskArn'])
        hostnames = retrieve_hostnames(HOSTED_ZONE_ID, public_ip)

        single_task = {
            'taskArn': task['taskArn'],
            'publicIp': public_ip,
            'hostnames': hostnames,
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

