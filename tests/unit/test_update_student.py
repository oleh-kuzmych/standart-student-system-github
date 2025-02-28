import json
from unittest import mock
from src.update_student import lambda_handler


@mock.patch("src.update_student.boto3.resource")
def test_update_student_success(mock_boto_resource):
    # Імітуємо існуючий студентський запис
    existing_student = {"id": "1234", "name": "Old Name", "age": 20, "email": "old@example.com"}
    mock_table = mock.MagicMock()
    mock_table.get_item.return_value = {"Item": existing_student}
    mock_table.put_item.return_value = {}

    mock_dynamodb = mock.MagicMock()
    mock_dynamodb.Table.return_value = mock_table
    mock_boto_resource.return_value = mock_dynamodb

    updated_data = {"name": "New Name", "age": 21, "email": "new@example.com"}
    event = {
        "httpMethod": "PUT",
        "pathParameters": {"id": "1234"},
        "body": json.dumps(updated_data)
    }
    response = lambda_handler(event, None)
    assert response["statusCode"] == 200
    data = json.loads(response["body"])
    assert data["id"] == "1234"
    assert data["name"] == "New Name"


@mock.patch("src.update_student.boto3.resource")
def test_update_student_missing_id(mock_boto_resource):
    event = {
        "httpMethod": "PUT",
        "pathParameters": {},
        "body": json.dumps({"name": "New Name"})
    }
    response = lambda_handler(event, None)
    assert response["statusCode"] == 400
    data = json.loads(response["body"])
    assert "error" in data
