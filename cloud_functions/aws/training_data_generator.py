import os
import logging
import json
import requests
from boto3 import client

# file deepcode ignore W0703: Any Exception should be updated as status for Training Data processor
def lambda_handler(event, context):
    cluster = os.getenv("CLUSTER", 'default')
    logging.info(cluster)
    task_definition = os.getenv("TASK_DEFINITION", 'default')
    capacity_provider = os.getenv("CAPACITY_PROVIDER", 'FARGATE_SPOT')
    subnets = os.getenv("SUBNETS", "").split(",")
    region_name = os.getenv("REGION_NAME", 'us-east-1')
    security_groups = os.getenv('SECURITY_GROUPS', '').split(",")
    container_name = os.getenv('CONTAINER_NAME')
    ecs = client('ecs', region_name=region_name)
    body = json.loads(event['body'])
    if 'user' in body and 'bot' in body:
        try:
            env_data = [
                {
                    'name': 'BOT',
                    'value': body['bot']
                },
                {
                    'name': 'USER',
                    'value': body['user']
                }
            ]
            if body.get('token'):
                env_data.append({
                    'name': 'TOKEN',
                    'value': body.get('token')
                })
            if body.get('kairon_url') and body.get('token'):
                status = {"status": "Creating ECS Task"}
                headers = {
                    'content-type': 'application/json',
                    'X-USER': body['user'],
                    'Authorization': 'Bearer ' + body.get('token')
                }
                requests.put(
                    body.get('kairon_url') + "/api/bot/processing-status",
                    headers=headers,
                    json=status
                )

            task_response = ecs.run_task(
                capacityProviderStrategy=[
                    {
                        'capacityProvider': capacity_provider,
                        'weight': 1,
                        'base': 0
                    },
                ],
                cluster=cluster,
                taskDefinition=task_definition,  # replace with your task definition name and revision
                count=1,
                platformVersion='1.4.0',
                networkConfiguration={
                    'awsvpcConfiguration': {
                        'subnets': subnets,
                        'assignPublicIp': 'ENABLED',
                        'securityGroups': security_groups
                    }
                },
                overrides={
                    'containerOverrides': [
                        {
                            "name": container_name,
                            'environment': env_data
                        },
                    ]
                },
            )
            print(task_response)
            response = "success"
        except Exception as e:
            response = str(e)
    else:
        response = "Invalid lambda handler request: user and bot are required"

    output = {
        "statusCode": 200,
        "statusDescription": "200 OK",
        "isBase64Encoded": False,
        "headers": {
            "Content-Type": "text/html; charset=utf-8"
        },
        "body": response
    }
    if body.get('kairon_url') and body.get('token'):
        status = {"status": response}
        headers = {
            'content-type': 'application/json',
            'X-USER': body['user'],
            'Authorization': 'Bearer ' + body.get('token')
        }
        requests.put(
            body.get('kairon_url') + "/api/bot/processing-status",
            headers=headers,
            json=status
        )
    return output
