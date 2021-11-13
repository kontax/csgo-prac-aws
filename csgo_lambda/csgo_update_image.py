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
    print(json.dumps(event))
    subnets = SUBNETS.split(',')
    security_groups = SECURITY_GROUPS.split(',')
    start_ecs_task(ECS_CLUSTER, TASK_DEFN, subnets, security_groups, get_env_overrides())
    return return_code(200, {'status': 'ECS task starting'})


def get_env_overrides():
    return {
        'containerOverrides': [{
            'name': CONTAINER_NAME,
            'environment': [{
                'name': 'UPDATE_ONLY',
                'value': '1'
            }]
        }]
    }

