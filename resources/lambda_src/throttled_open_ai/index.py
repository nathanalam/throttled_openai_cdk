import json
import os
import openai
import boto3
from datetime import datetime
import tiktoken

secrets_manager = boto3.client("secretsmanager")
dynamo_db = boto3.client("dynamodb")

def handler(event, context):
    if "body" not in event or event["body"] is None:
        return {
            "statusCode": 400,
            "body": "A request body must be provided",
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*"
            }
        }
    messages = json.loads(event["body"])
    print("Received message history:")
    print(messages)

    if type(messages) != list:
        return {
            "statusCode": 400,
            "body": "Body must be a list of messages of format [{\"role\": \"system\" | \"user\" | \"assistant\", \"content\": \"<message_text>\"}]",
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*"
            }
        }

    token_table = os.environ['TOKEN_TABLE_NAME']
    token_threshold = int(os.environ['DAILY_TOKEN_THRESHOLD'])
    current_date = datetime.now().strftime('%Y-%m-%d')
    

    response = dynamo_db.get_item(
        TableName=token_table,
        Key={
            'date': {'S': current_date}
        }
    )

    current_usage = 0
    if 'Item' in response:
        current_usage = int(response['Item']['tokens']["N"])
    
    current_usage += len(tiktoken.get_encoding("cl100k_base").encode(str(messages)))
    
    if current_usage > token_threshold:
        return {
            "statusCode": 400,
            "body": f"Daily token usage threshold reached. Current usage: {current_usage} > {token_threshold}",
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*"
            }
        }
    
    print(f"Projected usage after execution: {current_usage}")

    dynamo_db.put_item(
        TableName=token_table,
        Item={
            'date': {'S': current_date},
            'tokens': {'N': str(current_usage)}
        }
    )

    openai.api_key = os.environ['OPEN_API_KEY']
    response = openai.ChatCompletion.create(
        model=os.environ["MODEL"],
        messages=messages,
        temperature=0.4,
    )

    dynamo_db.put_item(
        TableName=token_table,
        Item={
            'date': {'S': current_date},
            'tokens': {'N': str(current_usage + response['usage']['completion_tokens'])}
        }
    )
    
    return {
        "statusCode": 200,
        "body": json.dumps(response),
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*"
        }
    }
