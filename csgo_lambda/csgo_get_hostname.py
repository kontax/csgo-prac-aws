import json
import os

from aws import get_running_task_count, get_task_details, get_public_ip, create_route53_record
from common import return_code

ECS_CLUSTER = os.environ.get('ECS_CLUSTER')
TASK_FAMILY = os.environ.get('TASK_FAMILY')
HOSTED_ZONE_ID = os.environ.get('HOSTED_ZONE_ID')
DNS_HOSTNAME = os.environ.get('DNS_HOSTNAME')
GET_HOSTNAME_QUEUE = os.environ.get('GET_HOSTNAME_QUEUE')


def handler(event, context):
    """ Creates a Route53 record pointing to the IP address sent on.

    Once a task has started, a hostname needs to be created to allow easy
    public access to the ECS container. This function creates that hostname
    using incremental subdomains, and points it to the IP address of the
    container. The message simply contains the ARN of the task.

    Args:
        event (dict): Event getting passed to the function via an API
        context (dict): The context the function runs in

    Returns:
        dict: Details of the container being started
    """

    print(json.dumps(event))
    hostname = []
    for record in event['Records']:
        task_arn = record['body']
        hostname = get_hostname(task_arn)

        # Sometimes the host might not be ready - just resend to the queue
        if not hostname:
            send_to_queue(GET_HOSTNAME_QUEUE, task_arn)
            continue

        hostnames.append(hostname)

    return return_code(200, {'hostnames': hostnames})


def get_hostname(task_arn):
    public_ip = get_public_ip(ECS_CLUSTER, task_arn)
    if not public_ip:
        return None

    task_count = get_running_task_count(ECS_CLUSTER, TASK_FAMILY)
    subdomain = f"csgo{task_count}"
    hostname = f"{subdomain}.{DNS_HOSTNAME}"

    create_route53_record(HOSTED_ZONE_ID, hostname, public_ip)
    return hostname

