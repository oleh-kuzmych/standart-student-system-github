import json
from datetime import datetime

def extract_times(report_file):
    with open(report_file, "r") as f:
        report = json.load(f)
    # Спробуємо отримати часові мітки з кількох можливих ключів
    start_time_str = report.get("startTime") or report.get("start")
    end_time_str = report.get("endTime") or report.get("end")
    if not start_time_str or not end_time_str:
        raise ValueError("Поля startTime/start або endTime/end не знайдено у звіті.")
    # Замінюємо "Z" на "+00:00" для правильного парсингу
    start_time = datetime.fromisoformat(start_time_str.replace("Z", "+00:00"))
    end_time = datetime.fromisoformat(end_time_str.replace("Z", "+00:00"))
    return start_time, end_time

if __name__ == "__main__":
    report_file = "normal_report.json"  # Замініть, якщо потрібно, на потрібний файл
    try:
        start, end = extract_times(report_file)
        print("Start Time:", start)
        print("End Time:", end)
    except Exception as e:
        print("Error extracting times:", e)
