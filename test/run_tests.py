import subprocess
import sys

def run_tests():
    test_files = [
        "test_health.py",
        "test_auth.py",
        "test_balance.py",
        "test_events.py"
    ]

    for test_file in test_files:
        print(f"\n=== Запуск {test_file} ===")
        result = subprocess.run([
            sys.executable, "-m", "pytest", test_file, "-v"
        ], capture_output=True, text=True)

        print(result.stdout)
        if result.stderr:
            print("Ошибки:")
            print(result.stderr)
        print("=" * 50)


if __name__ == "__main__":
    run_tests()

# Запуск всех тестов
#pytest app/test/test_auth.py
