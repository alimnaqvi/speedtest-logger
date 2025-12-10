import csv
import subprocess
from pathlib import Path
from datetime import datetime

CSV_LOCATION = Path("speedtest.csv")
HEADER_ROW = ["server name","server id","idle latency","idle jitter","packet loss","download","upload","download bytes","upload bytes","share url","download server count","download latency","download latency jitter","download latency low","download latency high","upload latency","upload latency jitter","upload latency low","upload latency high","idle latency low","idle latency high"]

def run_speedtest() -> dict:    
    print("The speedtest is running...")
    completed_process = subprocess.run(["speedtest", "-f", "csv"], capture_output=True, text=True)
    print("Speedtest completed.")
    output_text = completed_process.stdout
    result = None
    try:
        result = next(csv.DictReader([output_text], fieldnames=HEADER_ROW))
    except Exception as e:
        print(f"Speedtest output could not be converted to a dict: {e}")
        print(f"stdout of subprocess:\n{completed_process.stdout}" if completed_process.stdout else "Subprocess did not produce any stdout")
        print(f"stderr of subprocess:\n{completed_process.stderr}" if completed_process.stderr else "Subprocess did not produce any stderr")
    return result

def log_to_file(speedtest_result: dict, write_mode: str):
    insert_header = ["timestamp"] + HEADER_ROW
    speedtest_result["timestamp"] = datetime.now().isoformat()

    with open(CSV_LOCATION, write_mode) as f:

        writer = csv.DictWriter(f, fieldnames=insert_header)

        if write_mode == 'w':
            writer.writeheader()
        
        writer.writerow(speedtest_result)

    print(f"Successfully logged row to CSV file {CSV_LOCATION}")

def bytes_to_megabits(num_bytes: str) -> float:
    return (float(num_bytes) * 8) / 1_000_000

def main():
    speedtest_result: dict = run_speedtest()

    if not speedtest_result:
        print("Exiting because no CSV row result available.")
        exit(1)

    speedtest_result["download"] = f"{bytes_to_megabits(speedtest_result['download']):.2f}"
    speedtest_result["upload"] = f"{bytes_to_megabits(speedtest_result['upload']):.2f}"

    write_mode = 'a' if CSV_LOCATION.exists() else 'w'
    log_to_file(speedtest_result, write_mode)

if __name__ == "__main__":
    main()
