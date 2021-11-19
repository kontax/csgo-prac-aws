import boto3
import json
import os

from aws import start_ecs_task
from common import return_code

ECS_CLUSTER = os.environ.get('ECS_CLUSTER')


def handler(event, context):
    """ Stop a running CSGO server.

    An example of the message sent is as follows:
    {
        'task_arn': 'arn:aws:ecs:eu-west-1:150673653788:task/csgo-prac-aws-cluster/253a4a666c09494aa5d3ae69011e08d1'
    }

    Args:
        event (dict): Event getting passed to the function via an API
        context (dict): The context the function runs in

    Returns:
        dict: Details of the container being started
    """

    print(json.dumps(event))
    body = json.loads(event['body'])
    task_arn = body['task_arn']
    stop_task(ECS_CLUSTER, task_arn)
    msg = f"Stopping task {task_arn}"

    return return_code(200, {'task_status': msg})


def stop_task(cluster, task_arn):
    fmt = '%Y-%m-%d %H:%M:%S'
    client = boto3.client('ecs')
    resp = client.stop_task(
        cluster=cluster,
        task=task_arn
    )
    task = resp['task']

