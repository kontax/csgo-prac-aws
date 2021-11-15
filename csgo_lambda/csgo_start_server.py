import json
import os

from aws import start_ecs_task
from common import return_code

ECS_CLUSTER = os.environ.get('ECS_CLUSTER')
TASK_DEFN = os.environ.get('TASK_DEFN')
SUBNETS = os.environ.get('SUBNETS')
SECURITY_GROUPS = os.environ.get('SECURITY_GROUPS')
CONTAINER_NAME = os.environ.get('CONTAINER_NAME')


def handler(event, context):
    """ Start a CSGO server with the specified options.

    The server options that can be modified are as follows:

        TICKRATE: 64 or 128 (default: 128)
        MAP: The starting map of the server (default: de_dust2)
        MAPGROUP: The map group to use (default: mg_active)
        HOST_WORKSHOP_COLLECTION: Which workshop ID to get maps from (default: null)
        WORKSHOP_START_MAP: Which workshop map to start on (default: null)

    An example of the message sent is as follows:
    {
        "TICKRATE": "64",
        "MAP": "de_mirage",
        "MAPGROUP": "mg_active"
    }

    Args:
        event (dict): Event getting passed to the function via an API
        context (dict): The context the function runs in

    Returns:
        dict: Details of the container being started
    """

    print(json.dumps(event))
    body = json.loads(event['body'])
    subnets = SUBNETS.split(',')
    security_groups = SECURITY_GROUPS.split(',')
    env_pairs = create_name_value_pairs(body)
    task_details = start_ecs_task(
            ECS_CLUSTER, TASK_DEFN, subnets, security_groups,
            get_env_overrides(env_pairs))

    task_arns = []
    for task in task_details:
        task_arns.append(task['taskArn'])

    return return_code(200, {'taskArns': task_arns})


def create_name_value_pairs(env_vars):
    """ Creates name/value JSON pairs to send as ECS overrides

    The event sent to the lambda contains details in the following format:
    { 'tickrate': '128' }
    Whereas to send the overrides to the container, they need to be in
    the following format:
    { 'name': 'tickrate', 'value': '128' }

    Args:
        env_vars (dict): Environment variables to convert

    Returns:
        dict: Same environment variables in the correct format
    """

    retval = []
    for key in env_vars:
        newdict = {}
        newdict['name'] = key
        newdict['value'] = env_vars[key]
        retval.append(newdict)

    return retval


def get_env_overrides(environment_list):
    return {
        'containerOverrides': [{
            'name': CONTAINER_NAME,
            'environment': environment_list
        }]
    }

