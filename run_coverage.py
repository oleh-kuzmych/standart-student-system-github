import os
import subprocess
import sys

def run_command(cmd, env=None):
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, env=env)
    if result.returncode != 0:
        print(f"Command failed: {cmd}")
        sys.exit(result.returncode)

def run_tests(test_dir, coverage_file, html_dir):
    # Встановлюємо COVERAGE_FILE для даної групи тестів
    env = os.environ.copy()
    env["COVERAGE_FILE"] = coverage_file

    # Очищення попередніх даних покриття
    run_command("coverage erase", env=env)

    # Запуск тестів для заданої групи (наприклад, юніт, інтеграційні або E2E)
    run_command(f"coverage run -m pytest {test_dir}", env=env)

    # Вивід звіту покриття у консолі
    run_command("coverage report -m", env=env)

    # Генерація HTML звіту для зручного перегляду
    run_command(f"coverage html -d {html_dir}", env=env)
    print(f"HTML coverage report for {test_dir} generated in {html_dir}")

if __name__ == "__main__":
    # Шляхи до тестових директорій
    unit_tests = "tests/unit"
    integration_tests = "tests/integration"
    e2e_tests = "tests/e2e"

    # Файли для покриття (будуть створені окремо для кожної групи тестів)
    coverage_unit = ".coverage.unit"
    coverage_integration = ".coverage.integration"
    coverage_e2e = ".coverage.e2e"

    # HTML директорії для звітів
    html_unit = "htmlcov_unit"
    html_integration = "htmlcov_integration"
    html_e2e = "htmlcov_e2e"

    print("\n=== Running Unit Tests Coverage ===")
    run_tests(unit_tests, coverage_unit, html_unit)

    print("\n=== Running Integration Tests Coverage ===")
    run_tests(integration_tests, coverage_integration, html_integration)

    print("\n=== Running E2E Tests Coverage ===")
    run_tests(e2e_tests, coverage_e2e, html_e2e)

    print("\nAll coverage reports have been generated:")
    print(f"Unit tests: {html_unit}/index.html")
    print(f"Integration tests: {html_integration}/index.html")
    print(f"E2E tests: {html_e2e}/index.html")
