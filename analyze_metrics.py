import boto3
import datetime
from tabulate import tabulate
import matplotlib.pyplot as plt

# Простір імен для метрик
NAMESPACE = "StudentServiceMetrics"

# Список метрик, які збираються
METRICS = [
    "CreateStudentSuccess",
    "CreateStudentFailure",
    "GetStudentsSuccess",
    "GetStudentsFailure",
    "UpdateStudentSuccess",
    "UpdateStudentFailure",
    "DeleteStudentSuccess",
    "DeleteStudentFailure",
    "CreateStudentDuration",
    "GetStudentsDuration",
    "UpdateStudentDuration",
    "FaultDetectionTime",
    "RecoveryTime",
    "TestCoverage"
]

cloudwatch = boto3.client("cloudwatch", region_name="eu-central-1")

def get_metric_data(metric_name, start_time, end_time, period):
    try:
        response = cloudwatch.get_metric_statistics(
            Namespace=NAMESPACE,
            MetricName=metric_name,
            StartTime=start_time,
            EndTime=end_time,
            Period=period,
            Statistics=["Sum", "Average"]
        )
        datapoints = response.get("Datapoints", [])
        if datapoints:
            total = sum(dp.get("Sum", 0) for dp in datapoints)
            average = sum(dp.get("Average", 0) for dp in datapoints) / len(datapoints)
            return total, average
        else:
            return 0, 0
    except Exception as e:
        print(f"Error retrieving {metric_name}: {e}")
        return 0, 0

def analyze_interval(start_time, end_time, interval_name, period):
    results = {}
    for metric in METRICS:
        total, avg = get_metric_data(metric, start_time, end_time, period)
        results[metric] = {"Total": total, "Average": avg}
    print(f"\n=== Metrics for {interval_name} ===")
    table = []
    for metric, values in results.items():
        table.append([metric, values["Total"], values["Average"]])
    print(tabulate(table, headers=["Metric", "Total", "Average"], tablefmt="grid"))
    return results

def compute_aggregated(results, period, start_time, end_time):
    total_success = (
        results.get("CreateStudentSuccess", {}).get("Total", 0) +
        results.get("UpdateStudentSuccess", {}).get("Total", 0) +
        results.get("DeleteStudentSuccess", {}).get("Total", 0)
    )
    total_failures = (
        results.get("CreateStudentFailure", {}).get("Total", 0) +
        results.get("GetStudentsFailure", {}).get("Total", 0) +
        results.get("UpdateStudentFailure", {}).get("Total", 0) +
        results.get("DeleteStudentFailure", {}).get("Total", 0)
    )
    total_requests = total_success + total_failures

    mtbf = period / total_failures if total_failures > 0 else float('inf')
    failure_rate = (total_failures / period) * 60

    recovery_total, recovery_avg = get_metric_data("RecoveryTime", start_time, end_time, period)
    mttr = recovery_avg if recovery_total > 0 else 30  # якщо RecoveryTime немає, використовуємо 30 сек.
    availability = 100 if mtbf == float('inf') else (mtbf / (mtbf + mttr)) * 100

    aggregated = [
        ["Total Requests", total_requests, "Всі запити"],
        ["Total Failures", total_failures, "Сума помилок"],
        ["MTBF (sec)", mtbf if mtbf != float('inf') else "Infinity", "Середній час між відмовами"],
        ["Failure Rate (failures/min)", f"{failure_rate:.2f}", "Відмов за хвилину"],
        ["MTTR (sec)", mttr, "Середній час відновлення"],
        ["System Availability (%)", f"{availability:.2f}", "Доступність системи"]
    ]
    print("\n=== Aggregated Metrics ===")
    print(tabulate(aggregated, headers=["Metric", "Value", "Description"], tablefmt="grid"))
    return aggregated

if __name__ == "__main__":
    # Загальний період аналізу: останні 10 хвилин (600 секунд)
    end_time = datetime.datetime.utcnow()
    # Розділимо останні 10 хв на два інтервали по 5 хвилин:
    normal_start = end_time - datetime.timedelta(seconds=600)
    normal_end = end_time - datetime.timedelta(seconds=300)
    error_start = normal_end
    error_end = end_time

    normal_period = int((normal_end - normal_start).total_seconds())  # 300 секунд
    error_period = int((error_end - error_start).total_seconds())       # 300 секунд

    print("Analyzing Normal Operation Metrics (first 5 minutes)...")
    normal_results = analyze_interval(normal_start, normal_end, "Normal Operation", normal_period)
    normal_aggregated = compute_aggregated(normal_results, normal_period, normal_start, normal_end)

    print("\nAnalyzing Error Operation Metrics (last 5 minutes)...")
    error_results = analyze_interval(error_start, error_end, "Error Operation", error_period)
    error_aggregated = compute_aggregated(error_results, error_period, error_start, error_end)

    # Побудова графіка агрегованих метрик для обох режимів
    labels = ["Total Requests", "Total Failures", "MTBF (sec)", "Failure Rate (/min)", "MTTR (sec)", "Availability (%)"]

    def parse_value(val, default):
        return float(val) if val != "Infinity" else default

    normal_vals = [
        normal_aggregated[0][1],
        normal_aggregated[1][1],
        parse_value(normal_aggregated[2][1], normal_period),
        float(normal_aggregated[3][1]),
        normal_aggregated[4][1],
        float(normal_aggregated[5][1])
    ]
    error_vals = [
        error_aggregated[0][1],
        error_aggregated[1][1],
        parse_value(error_aggregated[2][1], error_period),
        float(error_aggregated[3][1]),
        error_aggregated[4][1],
        float(error_aggregated[5][1])
    ]

    x = range(len(labels))
    width = 0.35

    plt.figure(figsize=(12, 6))
    plt.bar([i - width/2 for i in x], normal_vals, width, label="Normal Operation", color="skyblue")
    plt.bar([i + width/2 for i in x], error_vals, width, label="Error Operation", color="salmon")
    plt.xticks(x, labels, rotation=45)
    plt.ylabel("Value")
    plt.title("Aggregated Reliability Metrics Comparison")
    plt.legend()
    plt.tight_layout()
    plt.show()
