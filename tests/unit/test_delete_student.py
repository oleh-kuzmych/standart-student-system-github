import json
from unittest import mock
from src.delete_student import lambda_handler

@mock.patch("src.delete_student.boto3.resource")
def test_delete_student_success(mock_boto_resource):
    existing_student = {"id": "1234", "name": "Test Student"}
    mock_table = mock.MagicMock()
    mock_table.get_item.return_value = {"Item": existing_student}
    mock_table.delete_item.return_value = {}

    mock_dynamodb = mock.MagicMock()
    mock_dynamodb.Table.return_value = mock_table
    mock_boto_resource.return_value = mock_dynamodb

    event = {
        "httpMethod": "DELETE",
        "pathParameters": {"id": "1234"},
        "body": None
    }
    response = lambda_handler(event, None)
    assert response["statusCode"] == 200
    data = json.loads(response["body"])
    assert data["message"] == "Student deleted"

@mock.patch("src.delete_student.boto3.resource")
def test_delete_student_missing_id(mock_boto_resource):
    event = {
        "httpMethod": "DELETE",
        "pathParameters": {},
        "body": None
    }
    response = lambda_handler(event, None)
    assert response["statusCode"] == 400
    data = json.loads(response["body"])
    assert "error" in data
