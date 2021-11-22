import boto3
import json
import os


def send_to_queue_name(queue_name, message):
    # Create SQS client
    if os.getenv("AWS_SAM_LOCAL"):
        sqs = boto3.resource('sqs', endpoint_url='http://localhost:4566')
    else:
        sqs = boto3.resource('sqs')
    # Get queue
    queue = sqs.get_queue_by_name(QueueName=queue_name)
    # Send message
    response = queue.send_message(
        MessageBody=message
    )
    print(f"Message sent: {response['MessageId']}")


def send_to_queue(queue_url, message):
    # Create SQS client
    print(f"Sending the following message to SQS {queue_url}:")
    print(message)
    if os.getenv("AWS_SAM_LOCAL"):
        sqs = boto3.client('sqs', endpoint_url='http://localhost:4566')
    else:
        sqs = boto3.client('sqs')
    response = sqs.send_message(
        QueueUrl=queue_url,
        MessageBody=(message)
    )
    print(f"Message sent: {response['MessageId']}")


def start_ecs_task(cluster, task_definition, subnets, security_groups, overrides={}):
    """Starts a new ECS task within a Fargate cluster to build the packages

    The ECS task pulls each package built one by one from the queue and adds
    them to the personal repository.

    Args:
        cluster (str): The name of the cluster to start the task in
        task_definition (str); The name of the task definition to run
        subnets (list): List of subnet id's to connect the task to
        security_groups (list): List of security groups to apply to the task
        overrides (dict): Any ECS variable overrides to push to the container
    """

    print(f"Starting new ECS task")

    # Note: There's no ECS in the free version of localstack
    client = boto3.client('ecs')
    response = client.run_task(
        cluster=cluster,
        launchType='FARGATE',
        taskDefinition=task_definition,
        count=1,
        platformVersion='LATEST',
        networkConfiguration={
            'awsvpcConfiguration': {
                'subnets':  subnets,
                'securityGroups': security_groups,
                'assignPublicIp': 'ENABLED'
            }
        },
        overrides=overrides
    )
    print(f"Run task complete: {str(response)}")
    return response['tasks']


def stop_ecs_task(cluster, task_arn):
    """ Stop an ECS task given the task's ARN

    Args:
        cluster (str): The name of the cluster containing the task to stop
        task_arn (str): The ARN of the task to stop

    Returns:
        dict: Details of the task being stopped
    """

    client = boto3.client('ecs')
    resp = client.stop_task(
        cluster=cluster,
        task=task_arn
    )
    task = resp['task']


def get_running_tasks(cluster, task_definition):
    """ Retrieves the list of ECS task arns for a specified cluster and task
    family that are currently either running or are in a pending state waiting
    to be run.

    Args:
        cluster (str): The name of the cluster containing the running tasks
        task_definition (str): The family of task to search for

    Returns:
        dict: A JSON of task ARNs in a running/soon to be running state
    """

    client = boto3.client('ecs')
    response = client.list_tasks(
        cluster=cluster,
        family=task_definition,
        desiredStatus="RUNNING"
    )
    return response['taskArns']


def get_running_task_count(cluster, task_family):
    """ Retrieves the number of ECS tasks for a specified cluster and task
    family that are currently either running or are in a pending state waiting
    to be run.

    Args:
        cluster (str): The name of the cluster containing the running tasks
        task_family (str): The family of task to search for

    Returns:
        (int): The number of tasks in a running/soon to be running state
    """

    client = boto3.client('ecs')
    response = client.list_tasks(
        cluster=cluster,
        family=task_family,
        desiredStatus="RUNNING"
    )
    return len(response['taskArns'])


def get_task_details(cluster, task_arns):
    """ Get details of the tasks specified

    Args:
        cluster (str): Name of the cluster to check
        task_arns (list): List of task arns to check

    Returns:
        dict: Details of the tasks specified
    """

    client = boto3.client('ecs')
    response = client.describe_tasks(
        cluster=cluster,
        tasks=task_arns
    )

    return response['tasks']


def get_public_ip(cluster, task_arn):
    """ Get the public IP address for the task from the attached interface.

    Each task should only have 1 attached network interface and 1 public IP.

    Args:
        cluster (str): Name of the cluster containing the task
        task_arn (str): The ARN of the running task

    Returns:
        str: IP address of the task
    """

    # Get details of the task - there should only be one, as we're only passing
    # one ARN into the function
    tasks = get_task_details(cluster, [task_arn])
    assert len(tasks) <= 1
    if len(tasks) == 0:
        print("No tasks found")
        return None

    task = tasks[0]
    print(task)

    # Get a list of the attached ENI's, there should only be one per task
    enis = [a for a in task['attachments']
            if 'type' in a and a['type'] == 'ElasticNetworkInterface']
    assert len(enis) == 1

    # Get the network ID for the ENI, again there should only be one
    network_ids = [n['value'] for n in enis[0]['details']
                   if n['name'] == 'networkInterfaceId']
    print(network_ids)
    assert len(network_ids) <= 1

    # Return nothing if the server isn't ready
    if len(network_ids) == 0:
        return None

    # Get the details of the ENI and return the IP address
    resource = boto3.resource('ec2').NetworkInterface(network_ids[0])
    if not resource.association_attribute:
        return None

    return resource.association_attribute['PublicIp']


def get_dynamo_resource():
    """
    Get a dynamodb resource depending on which environment the function is
    running in
    """

    if os.getenv("AWS_SAM_LOCAL"):
        dynamo = boto3.resource('dynamodb', endpoint_url="http://dynamodb:8000")
    else:
        dynamo = boto3.resource('dynamodb')
    return dynamo


def create_route53_record(hosted_zone_id, hostname, ip_address):
    """ Creates an A record within Route53 within the specified hosted zone,
    pointing `hostname` to `ip_address`.

    Args:
        hosted_zone_id (str): Route53 hosted zone ID to create the record in
        hostname (str): Hostname of the record
        ip_address (str): IP Address to point the record to

    Returns:
        dict: Response of the API call
    """

    client = boto3.client('route53')
    response = client.change_resource_record_sets(
    ChangeBatch={
        'Changes': [
            {
                'Action': 'CREATE',
                'ResourceRecordSet': {
                    'Name': hostname,
                    'ResourceRecords': [
                        {
                            'Value': ip_address,
                        },
                    ],
                    'TTL': 60,
                    'Type': 'A',
                },
            },
        ],
        'Comment': 'Create CSGO server record',
    },
    HostedZoneId=hosted_zone_id,
)


def delete_route53_record(hosted_zone_id, hostname, ip_address):
    """ Deletes an existing Route53 A record within the specified hosted zone.

    Args:
        hosted_zone_id (str): Route53 hosted zone ID to delete the record from
        hostname (str): Hostname of the record
        ip_address (str): IP Address to point the record to

    Returns:
        dict: Response of the API call
    """

    client = boto3.client('route53')
    response = client.change_resource_record_sets(
    ChangeBatch={
        'Changes': [
            {
                'Action': 'DELETE',
                'ResourceRecordSet': {
                    'Name': hostname,
                    'ResourceRecords': [
                        {
                            'Value': ip_address,
                        },
                    ],
                    'TTL': 60,
                    'Type': 'A',
                },
            },
        ],
        'Comment': 'Create CSGO server record',
    },
    HostedZoneId=hosted_zone_id,
)

def retrieve_hostnames(hosted_zone_id, ip_address):
    """ Retrieve a list of hostnames that are mapped to a specific IP address

    As multiple hostnames can be mapped to an IP address, this function returns
    a list of hostnames rather than a single one.

    Args:
        hosted_zone_id (str): Route53 hosted zone ID to delete the record from
        ip_address (str): IP Address to point the record to

    Returns:
        List: A list of name values within Route53
    """

    client = boto3.client('route53')
    response = client.list_resource_record_sets(HostedZoneId=hosted_zone_id)
    hostnames = [ rec['Name'] for rec in response['ResourceRecordSets']
                  if 'ResourceRecords' in rec
                  and {'Value': ip_address} in rec['ResourceRecords']]
    return hostnames
