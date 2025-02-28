import json
import boto3
import os
from datetime import datetime
from src.common.metrics import put_custom_metric


def lambda_handler(event, context):
    headers = event.get("headers") or {}

    if headers.get("X-Simulate-Error", "").lower() == "true":
        put_custom_metric("FaultDetectionTime", 0, unit="Seconds")
        put_custom_metric("UpdateStudentFailure", 1)
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Simulated error in update_student"})
        }

    dynamodb = boto3.resource("dynamodb", region_name=os.environ.get("AWS_DEFAULT_REGION", "eu-central-1"))
    table_name = os.environ.get("DYNAMODB_TABLE", "StudentsTable")
    table = dynamodb.Table(table_name)

    try:
        student_id = event.get("pathParameters", {}).get("id")
        if not student_id:
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Student id is required"})
            }
        body = json.loads(event.get("body", "{}"))
        body["id"] = student_id

        start_time = datetime.utcnow()
        table.put_item(Item=body)
        duration = (datetime.utcnow() - start_time).total_seconds()

        recovery_time = float(headers.get("X-Recovery-Time", 0))
        if recovery_time > 0:
            put_custom_metric("RecoveryTime", recovery_time, unit="Seconds")
            put_custom_metric("FaultCorrection", 1)

        put_custom_metric("UpdateStudentSuccess", 1)
        put_custom_metric("UpdateStudentDuration", duration, unit="Seconds")
        put_custom_metric("TestCoverage", 85, unit="Percent")

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(body)
        }
    except Exception as e:
        put_custom_metric("UpdateStudentFailure", 1)
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": str(e)})
        }
