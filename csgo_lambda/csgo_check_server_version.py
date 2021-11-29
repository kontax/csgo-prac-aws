import boto3
import json
import os
import requests

from aws import start_ecs_task
from common import return_code


ECS_CLUSTER = os.environ.get('ECS_CLUSTER')
TASK_DEFN = os.environ.get('TASK_DEFN')
SUBNETS = os.environ.get('SUBNETS')
SECURITY_GROUPS = os.environ.get('SECURITY_GROUPS')
CONTAINER_NAME = os.environ.get('CONTAINER_NAME')
SERVER_VERSION_PARAM = os.environ.get('SERVER_VERSION_PARAM')
URL = "http://api.steampowered.com/ISteamApps/UpToDateCheck/v0001/?appid=730&version={VERSION}&format=json"


def handler(event, context):
    print("Checking CSGO server version to see if update is required")

    current_version = get_current_version()
    print(f"Current Version: {current_version}")

    resp = check_version(current_version)
    print(resp)

    if not resp['up_to_date']:
        required_version = str(resp['required_version'])
        print(f"Version is out of date, need to update to {required_version}")
        update_version(required_version)
        return return_code(200, {'status': 'ECS task starting'})

    return return_code(200, {'status': 'Server is already up to date'})


def get_current_version():
    client = boto3.client('ssm')
    parameter = client.get_parameter(Name=SERVER_VERSION_PARAM)
    return parameter['Parameter']['Value']


def check_version(current_version):
    url = URL.format(VERSION=current_version)
    resp = requests.get(url)
    return resp.json()['response']


def update_version(required_version):
    update_version_parameter(required_version)
    start_server_update()


def update_version_parameter(required_version):
    print(f"Updating parameter store to {required_version}")
    client = boto3.client('ssm')
    parameter = client.put_parameter(
            Name=SERVER_VERSION_PARAM,
            Value=required_version,
            Overwrite=True)


def start_server_update():
    print("Starting ECS task to update server")
    subnets = SUBNETS.split(',')
    security_groups = SECURITY_GROUPS.split(',')
    start_ecs_task(ECS_CLUSTER, TASK_DEFN, subnets, security_groups, get_env_overrides())


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

