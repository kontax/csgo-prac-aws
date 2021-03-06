import json
import os

from aws import start_ecs_task, send_to_queue
from common import return_code
from datetime import datetime

ECS_CLUSTER = os.environ.get('ECS_CLUSTER')
TASK_DEFN = os.environ.get('TASK_DEFN')
SUBNETS = os.environ.get('SUBNETS')
SECURITY_GROUPS = os.environ.get('SECURITY_GROUPS')
CONTAINER_NAME = os.environ.get('CONTAINER_NAME')
GET_HOSTNAME_QUEUE = os.environ.get('GET_HOSTNAME_QUEUE')


def handler(event, context):
    """ Start a CSGO server with the specified options.

    The server options that can be modified are as follows:

        TICKRATE: 64 or 128 (default: 128)
        MAP: The starting map of the server (default: de_dust2)
        MAPGROUP: The map group to use (default: mg_active)
        HOST_WORKSHOP_COLLECTION: Which workshop ID to get maps from (default: null)
        WORKSHOP_START_MAP: Which workshop map to start on (default: null)

    An example of the message sent is as follows:
    [
        {"name": "TICKRATE", "value": "64"},
        {"name": "MAP", "value", "de_dust2"},
        {"name": "MAPGROUP", "value", "mg_active"}
    ]

    Args:
        event (dict): Event getting passed to the function via an API
        context (dict): The context the function runs in

    Returns:
        dict: Details of the container being started
    """

    print(json.dumps(event))
    body = json.loads(event['body'])
    fmt = "%Y-%m-%d %H:%M:%S"

    subnets = SUBNETS.split(',')
    security_groups = SECURITY_GROUPS.split(',')
    task_details = start_ecs_task(
            ECS_CLUSTER, TASK_DEFN, subnets, security_groups,
            get_env_overrides(body))

    task_arns = []
    for task in task_details:

        msg = {
            'task_arn': task['taskArn'],
            'start_time': datetime.now().strftime(fmt)
        }

        # Send task to get a hostname assigned
        send_to_queue(GET_HOSTNAME_QUEUE, json.dumps(msg))
        task_arns.append(task['taskArn'])

    return return_code(200, {'taskArns': task_arns})


def get_env_overrides(environment_list):
    return {
        'containerOverrides': [{
            'name': CONTAINER_NAME,
            'environment': environment_list
        }]
    }

