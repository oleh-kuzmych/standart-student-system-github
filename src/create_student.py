import json
import uuid
import boto3
import os
from datetime import datetime
from src.common.metrics import put_custom_metric


def lambda_handler(event, context):
    headers = event.get("headers") or {}

    # Якщо встановлено заголовок для симуляції помилки, фіксуємо FaultDetectionTime і повертаємо помилку.
    if headers.get("X-Simulate-Error", "").lower() == "true":
        # Фіксуємо час виявлення помилки (placeholder, наприклад, 0)
        put_custom_metric("FaultDetectionTime", 0, unit="Seconds")
        put_custom_metric("CreateStudentFailure", 1)
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Simulated error in create_student"})
        }

    dynamodb = boto3.resource("dynamodb", region_name=os.environ.get("AWS_DEFAULT_REGION", "eu-central-1"))
    table_name = os.environ.get("DYNAMODB_TABLE", "StudentsTable")
    table = dynamodb.Table(table_name)

    try:
        body = json.loads(event.get("body", "{}"))
        new_id = str(uuid.uuid4())
        body["id"] = new_id

        start_time = datetime.utcnow()
        table.put_item(Item=body)
        duration = (datetime.utcnow() - start_time).total_seconds()

        # Якщо операція проходить після того, як була помилка, можна передати RecoveryTime через заголовок (як приклад)
        recovery_time = float(headers.get("X-Recovery-Time", 0))
        if recovery_time > 0:
            put_custom_metric("RecoveryTime", recovery_time, unit="Seconds")
            put_custom_metric("FaultCorrection", 1)

        put_custom_metric("CreateStudentSuccess", 1)
        put_custom_metric("CreateStudentDuration", duration, unit="Seconds")

        # Також можна зафіксувати тестове покриття, якщо є така інформація (placeholder)
        # Наприклад, значення 85% покриття
        put_custom_metric("TestCoverage", 85, unit="Percent")

        return {
            "statusCode": 201,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(body)
        }
    except Exception as e:
        put_custom_metric("CreateStudentFailure", 1)
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": str(e)})
        }
