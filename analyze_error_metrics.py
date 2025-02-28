import boto3
import datetime
from tabulate import tabulate
import json

NAMESPACE = "StudentServiceMetrics"

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


def analyze_interval(start_time, end_time, period):
    results = {}
    for metric in METRICS:
        total, avg = get_metric_data(metric, start_time, end_time, period)
        results[metric] = {"Total": total, "Average": avg}
    print("\n=== Error Operation Metrics ===")
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
    mttr = recovery_avg if recovery_total > 0 else 30

    availability = 100 if mtbf == float('inf') else (mtbf / (mtbf + mttr)) * 100

    aggregated = {
        "Total Requests": total_requests,
        "Total Failures": total_failures,
        "MTBF (sec)": mtbf if mtbf != float('inf') else "Infinity",
        "Failure Rate (failures/min)": round(failure_rate, 2),
        "MTTR (sec)": mttr,
        "System Availability (%)": round(availability, 2)
    }
    print("\n=== Aggregated Error Metrics ===")
    agg_table = []
    for key, value in aggregated.items():
        desc = ""
        if key == "MTBF (sec)":
            desc = "Середній час між відмовами"
        elif key == "Failure Rate (failures/min)":
            desc = "Відмов за хвилину"
        elif key == "MTTR (sec)":
            desc = "Середній час відновлення"
        elif key == "System Availability (%)":
            desc = "Доступність системи"
        elif key == "Total Requests":
            desc = "Всі запити"
        elif key == "Total Failures":
            desc = "Сума помилок"
        agg_table.append([key, value, desc])
    print(tabulate(agg_table, headers=["Metric", "Value", "Description"], tablefmt="grid"))
    return aggregated


if __name__ == "__main__":
    now = datetime.datetime.utcnow()
    # Для режиму з помилками – останні 5 хвилин (від now - 300 сек до now)
    error_start = now - datetime.timedelta(seconds=300)
    error_end = now
    period = int((error_end - error_start).total_seconds())  # 300 секунд

    results = analyze_interval(error_start, error_end, period)
    aggregated = compute_aggregated(results, period, error_start, error_end)

    with open("error_metrics.json", "w") as f:
        json.dump(aggregated, f, indent=4)
