import json
from tabulate import tabulate
import matplotlib.pyplot as plt


def load_metrics(filename):
    with open(filename, "r") as f:
        return json.load(f)


def compare_metrics(normal, error):
    comparison = []
    keys = ["Total Requests", "Total Failures", "MTBF (sec)", "Failure Rate (failures/min)", "MTTR (sec)",
            "System Availability (%)"]
    for key in keys:
        normal_value = normal.get(key, "N/A")
        error_value = error.get(key, "N/A")
        try:
            if normal_value == "Infinity" or error_value == "Infinity":
                diff = "N/A"
            else:
                diff = error_value - normal_value
        except Exception:
            diff = "N/A"
        comparison.append([key, normal_value, error_value, diff])
    return comparison


if __name__ == "__main__":
    normal_metrics = json.load(open("normal_metrics.json"))
    error_metrics = json.load(open("error_metrics.json"))
    comparison = compare_metrics(normal_metrics, error_metrics)
    print("\n=== Comparison of Aggregated Metrics ===")
    print(tabulate(comparison, headers=["Metric", "Normal", "Error", "Difference"], tablefmt="grid"))

    labels = ["Total Requests", "Total Failures", "MTBF (sec)", "Failure Rate (/min)", "MTTR (sec)", "Availability (%)"]
    normal_vals = []
    error_vals = []
    for key in labels:
        n_val = normal_metrics.get(key, 0)
        e_val = error_metrics.get(key, 0)
        # Якщо значення "Infinity", замінимо його на 300 (як placeholder для графіку)
        if n_val == "Infinity":
            n_val = 300
        if e_val == "Infinity":
            e_val = 300
        normal_vals.append(float(n_val))
        error_vals.append(float(e_val))

    x = range(len(labels))
    width = 0.35

    plt.figure(figsize=(12, 6))
    plt.bar([i - width / 2 for i in x], normal_vals, width, label="Normal Operation", color="skyblue")
    plt.bar([i + width / 2 for i in x], error_vals, width, label="Error Operation", color="salmon")
    plt.xticks(x, labels, rotation=45)
    plt.ylabel("Value")
    plt.title("Comparison of Aggregated Reliability Metrics")
    plt.legend()
    plt.tight_layout()
    plt.show()
