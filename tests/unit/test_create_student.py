import json
from unittest import mock
from src.create_student import lambda_handler


@mock.patch("src.create_student.boto3.resource")
@mock.patch("src.create_student.put_custom_metric", return_value=None)
def test_create_student_success(mock_put_metric, mock_boto_resource):
    # Мок для таблиці DynamoDB
    mock_table = mock.MagicMock()
    mock_table.put_item.return_value = {}

    mock_dynamodb = mock.MagicMock()
    mock_dynamodb.Table.return_value = mock_table
    mock_boto_resource.return_value = mock_dynamodb

    test_body = {
        "name": "Test Student",
        "age": 22,
        "email": "test@example.com"
    }
    event = {
        "httpMethod": "POST",
        "body": json.dumps(test_body)
    }

    response = lambda_handler(event, None)
    assert response["statusCode"] == 201
    data = json.loads(response["body"])
    assert "id" in data
    assert data["name"] == test_body["name"]
    mock_table.put_item.assert_called_once()
    # Використовуємо assert_any_call, щоб переконатися, що виклик "CreateStudentSuccess" був зроблений
    mock_put_metric.assert_any_call("CreateStudentSuccess", 1)


def test_create_student_failure():
    with mock.patch("src.create_student.boto3.resource") as mock_boto_resource, \
            mock.patch("src.create_student.put_custom_metric", return_value=None) as mock_put_metric:
        mock_table = mock.MagicMock()
        mock_table.put_item.side_effect = Exception("DynamoDB error")
        mock_dynamodb = mock.MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        mock_boto_resource.return_value = mock_dynamodb

        test_body = {
            "name": "Test Student",
            "age": 22,
            "email": "test@example.com"
        }
        event = {
            "httpMethod": "POST",
            "body": json.dumps(test_body)
        }
        response = lambda_handler(event, None)
        assert response["statusCode"] == 500
        data = json.loads(response["body"])
        assert "error" in data
        mock_put_metric.assert_any_call("CreateStudentFailure", 1)
