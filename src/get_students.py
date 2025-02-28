import json
import boto3
import os
from datetime import datetime
from src.common.metrics import put_custom_metric


def lambda_handler(event, context):
    headers = event.get("headers") or {}

    # Якщо встановлено заголовок для симуляції помилки, повертаємо помилку
    if headers.get("X-Simulate-Error", "").lower() == "true":
        put_custom_metric("GetStudentsFailure", 1)
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Simulated error in get_students"})
        }

    try:
        dynamodb = boto3.resource("dynamodb", region_name=os.environ.get("AWS_DEFAULT_REGION", "eu-central-1"))
        table_name = os.environ.get("DYNAMODB_TABLE", "StudentsTable")
        table = dynamodb.Table(table_name)

        start_time = datetime.utcnow()
        response = table.scan()
        duration = (datetime.utcnow() - start_time).total_seconds()
        items = response.get("Items", [])

        # В нормальному режимі надсилаємо лише метрику успіху
        put_custom_metric("GetStudentsSuccess", 1)
        put_custom_metric("GetStudentsDuration", duration, unit="Seconds")

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(items)
        }
    except Exception as e:
        # Якщо трапляється виключення, реєструємо помилку
        put_custom_metric("GetStudentsFailure", 1)
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": str(e)})
        }
