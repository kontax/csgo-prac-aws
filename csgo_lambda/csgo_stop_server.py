import boto3
import json
import os

from aws import stop_ecs_task, get_public_ip, delete_route53_record, retrieve_hostnames
from common import return_code

ECS_CLUSTER = os.environ.get('ECS_CLUSTER')
HOSTED_ZONE_ID = os.environ.get('HOSTED_ZONE_ID')


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

    print("Deleting the A record of the task")
    delete_hostname(task_arn)

    msg = f"Stopping task {task_arn}"
    print(msg)
    stop_ecs_task(ECS_CLUSTER, task_arn)

    return return_code(200, {'task_status': msg})


def delete_hostname(task_arn):
    public_ip = get_public_ip(ECS_CLUSTER, task_arn)
    if not public_ip:
        return None

    hostnames = retrieve_hostnames(HOSTED_ZONE_ID, public_ip)
    for hostname in hostnames:
        print(f"Deleting {hostname} from {HOSTED_ZONE_ID}")
        delete_route53_record(HOSTED_ZONE_ID, hostname, public_ip)

