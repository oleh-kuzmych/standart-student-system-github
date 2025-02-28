import json
from unittest import mock
from src.get_students import lambda_handler


@mock.patch("src.get_students.boto3.resource")
def test_get_students_success(mock_boto_resource):
    fake_items = [{"id": "1", "name": "Student A"}, {"id": "2", "name": "Student B"}]
    mock_table = mock.MagicMock()
    mock_table.scan.return_value = {"Items": fake_items}

    mock_dynamodb = mock.MagicMock()
    mock_dynamodb.Table.return_value = mock_table
    mock_boto_resource.return_value = mock_dynamodb

    event = {
        "httpMethod": "GET",
        "path": "/students",
        "body": None
    }
    response = lambda_handler(event, None)
    assert response["statusCode"] == 200
    data = json.loads(response["body"])
    assert isinstance(data, list)
    assert len(data) == 2
