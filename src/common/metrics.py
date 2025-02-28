import boto3
from datetime import datetime

# Створюємо CloudWatch клієнта для регіону eu-central-1
cloudwatch = boto3.client("cloudwatch", region_name="eu-central-1")


def put_custom_metric(metric_name, value, unit="Count"):
    """
    Відправляє кастомну метрику до CloudWatch.

    :param metric_name: Назва метрики.
    :param value: Значення метрики.
    :param unit: Одиниця вимірювання (наприклад, "Count", "Seconds").
    """
    try:
        cloudwatch.put_metric_data(
            Namespace="StudentServiceMetrics",
            MetricData=[
                {
                    "MetricName": metric_name,
                    "Timestamp": datetime.utcnow(),
                    "Value": value,
                    "Unit": unit
                }
            ]
        )
    except Exception as e:
        print("Error putting custom metric:", e)
