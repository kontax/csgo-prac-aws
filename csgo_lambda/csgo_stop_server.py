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
    task_arn = event['task_arn']
    response = stop_task(ECS_CLUSTER, task_arn)

    return return_code(200, {'task_status': response})


def stop_task(cluster, task_arn):
    fmt = '%Y-%m-%d %H:%M:%S'
    client = boto3.client('ecs')
    resp = client.stop_task(
        cluster=cluster,
        task=task_arn
    )
    task = resp['task']
    output = {
        'taskArn': task['taskArn'],
        'startedAt': task['startedAt'].strftime(fmt),
        'lastStatus': task['lastStatus'],
        'desiredStatus': task['desiredStatus'],
        'cpu': task['cpu'],
        'memory': task['memory'],
        'overrides': task['overrides'],
        'stopCode': task['stopCode'] if 'stopCode' in task else None,
        'stoppedReason': task['stoppedReason'] if 'stoppedReason' in task else None,
        'stoppingAt': task['stoppingAt'].strftime(fmt) if 'stoppingAt' in task else None,
        'stoppedAt': task['stoppedAt'].strftime(fmt) if 'stoppedAt' in task else None
    }

    return output

