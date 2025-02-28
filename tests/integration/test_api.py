import json
import boto3
import os
import pytest
from unittest import mock

# --- Заглушки для DynamoDB ---

class DummyTable:
    def __init__(self):
        self.items = {}

    def scan(self):
        # Повертає всі записи як список
        return {"Items": list(self.items.values())}

    def put_item(self, Item):
        # Додає або оновлює запис за ключем "id"
        self.items[Item["id"]] = Item
        return {}

    def get_item(self, Key):
        # Повертає запис, якщо існує, або пустий словник
        item = self.items.get(Key["id"])
        if item:
            return {"Item": item}
        return {}

    def delete_item(self, Key):
        # Видаляє запис, якщо існує
        if Key["id"] in self.items:
            del self.items[Key["id"]]
        return {}

class DummyDynamoDB:
    def __init__(self):
        # Використовуємо одну заглушку таблиці для всіх операцій
        self.table = DummyTable()

    def Table(self, name):
        # Ігноруємо ім'я таблиці та завжди повертаємо одну й ту саму таблицю
        return self.table

# Створюємо глобальний екземпляр DummyDynamoDB
def dummy_resource(service, region_name=None):
    if service == "dynamodb":
        return dummy_resource.dynamodb_instance
    raise ValueError("Unsupported service: " + service)

dummy_resource.dynamodb_instance = DummyDynamoDB()

# --- Фікстура, що патчить boto3.resource ---
@pytest.fixture(autouse=True)
def patch_boto3_resource(monkeypatch):
    monkeypatch.setattr(boto3, "resource", dummy_resource)
    os.environ["AWS_DEFAULT_REGION"] = "eu-central-1"
    os.environ["DYNAMODB_TABLE"] = "StudentsTable"

# --- Імпорт Lambda-функцій ---
from src.create_student import lambda_handler as create_student_handler
from src.get_students import lambda_handler as get_students_handler
from src.update_student import lambda_handler as update_student_handler
from src.delete_student import lambda_handler as delete_student_handler

# --- Інтеграційний тест CRUD-потоку ---
def test_crud_flow():
    # 1. Створення студента
    create_event = {
        "httpMethod": "POST",
        "body": json.dumps({
            "name": "Integration Test Student",
            "age": 23,
            "email": "integration@example.com"
        })
    }
    create_response = create_student_handler(create_event, None)
    assert create_response["statusCode"] == 201, f"Expected 201, got {create_response['statusCode']}"
    created_student = json.loads(create_response["body"])
    student_id = created_student.get("id")
    assert student_id, "Student id is missing in the response"

    # 2. Отримання списку студентів
    get_event = {
        "httpMethod": "GET",
        "body": None
    }
    get_response = get_students_handler(get_event, None)
    assert get_response["statusCode"] == 200, f"Expected 200, got {get_response['statusCode']}"
    students_list = json.loads(get_response["body"])
    assert isinstance(students_list, list), "Response is not a list"
    assert any(s.get("id") == student_id for s in students_list), "Created student not found in students list"

    # 3. Оновлення даних студента
    update_event = {
        "httpMethod": "PUT",
        "pathParameters": {"id": student_id},
        "body": json.dumps({
            "name": "Updated Student",
            "age": 24,
            "email": "updated@example.com"
        })
    }
    update_response = update_student_handler(update_event, None)
    assert update_response["statusCode"] == 200, f"Expected 200, got {update_response['statusCode']}"
    updated_student = json.loads(update_response["body"])
    assert updated_student.get("name") == "Updated Student", "Student name was not updated"

    # 4. Видалення студента
    delete_event = {
        "httpMethod": "DELETE",
        "pathParameters": {"id": student_id},
        "body": None
    }
    delete_response = delete_student_handler(delete_event, None)
    assert delete_response["statusCode"] == 200, f"Expected 200, got {delete_response['statusCode']}"
    delete_result = json.loads(delete_response["body"])
    assert delete_result.get("message") == "Student deleted", "Deletion message not returned as expected"

    # 5. (Опціонально) Перевірка, що студент більше не існує
    # Якщо у вас є окрема функція для отримання конкретного студента, ви можете додати цей крок.
