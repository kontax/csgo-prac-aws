import json
import os

from aws import get_running_task_count, get_task_details, get_public_ip, create_route53_record, send_to_queue
from common import return_code
from datetime import datetime

ECS_CLUSTER = os.environ.get('ECS_CLUSTER')
TASK_FAMILY = os.environ.get('TASK_FAMILY')
HOSTED_ZONE_ID = os.environ.get('HOSTED_ZONE_ID')
DNS_HOSTNAME = os.environ.get('DNS_HOSTNAME')
GET_HOSTNAME_QUEUE = os.environ.get('GET_HOSTNAME_QUEUE')
SECONDS_TO_RUN = 10*60


def handler(event, context):
    """ Creates a Route53 record pointing to the IP address sent on.

    Once a task has started, a hostname needs to be created to allow easy
    public access to the ECS container. This function creates that hostname
    using incremental subdomains, and points it to the IP address of the
    container. The message structure looks like this:

    {
        'task_arn': 'arn:aws:ecs:eu-west-1:150673653788:task/csgo-prac-aws-cluster/253a4a666c09494aa5d3ae69011e08d1',
        'start_time': '2021-10-05 10:00:00'
    }

    The start_time represents the time the request happened, as the function
    needs to stop running after a period of time to prevent running forever.

    Args:
        event (dict): Event getting passed to the function via an API
        context (dict): The context the function runs in

    Returns:
        dict: Details of the container being started
    """

    print(json.dumps(event))
    fmt = "%Y-%m-%d %H:%M:%S"
    hostnames = []
    for record in event['Records']:
        body = json.loads(record['body'])
        task_arn = body['task_arn']
        start_time = datetime.strptime(body['start_time'], fmt)
        hostname = create_hostname(task_arn)

        # Sometimes the host might not be ready - just resend to the queue
        if not hostname:

            # Only resend if we're still within the threshold
            if check_time_passed(start_time) <= SECONDS_TO_RUN:
                print("Resending message to queue")
                send_to_queue(GET_HOSTNAME_QUEUE, task_arn)
            else:
                print("Time expired, create hostname failed")

            continue

        hostnames.append(hostname)

    return return_code(200, {'hostnames': hostnames})


def create_hostname(task_arn):
    """ Create a hostname pointing to the public IP of the task.

    Args:
        task_arn (str): The ARN of the task

    Returns:
        str: The hostname assigned to the task
    """

    public_ip = get_public_ip(ECS_CLUSTER, task_arn)
    if not public_ip:
        print("No public IP - task is not ready")
        return None

    task_count = get_running_task_count(ECS_CLUSTER, TASK_FAMILY)
    if task_count == 0:
        print("Task is not yet running - trying again later")
        return None

    subdomain = f"csgo{task_count}"
    hostname = f"{subdomain}.{DNS_HOSTNAME}"
    print(f"Creating {hostname} record for {public_ip}")

    create_route53_record(HOSTED_ZONE_ID, hostname, public_ip)
    return hostname


def check_time_passed(time):
    return (datetime.now()-time).total_seconds()
