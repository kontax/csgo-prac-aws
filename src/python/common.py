import json


def return_code(code, body):
    """Returns a JSON response

    Args:
        code (int): HTTP response code
        body (dict): Data to return

    Returns:
        (dict): JSON object containing the code and body
    """

    return {
        "statusCode": code,
        "headers": {
            "Access-Control-Allow-Headers" : "Content-Type",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "OPTIONS,POST,GET"
        },
        "body": json.dumps(body)
    }
