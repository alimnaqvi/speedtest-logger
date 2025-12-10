import argparse
import json
import subprocess
from pathlib import Path
import sys

CSV_LOCATION = Path("speedtest.csv")

def run_speedtest() -> dict:
    print("The speedtest is running...")
    completed_process = subprocess.run(["speedtest", "-f", "json-pretty"], capture_output=True, text=True)
    print("Speedtest completed.")
    output_text = completed_process.stdout
    result = None
    try:
        result = json.loads(output_text)
    except Exception as e:
        print(f"Speedtest output could not be loaded as JSON: {e}")
        print(f"stdout of subprocess:\n{completed_process.stdout}" if completed_process.stdout else "Subprocess did not produce any stdout")
        print(f"stderr of subprocess:\n{completed_process.stderr}" if completed_process.stderr else "Subprocess did not produce any stderr")
    return result

def bytes_to_megabits(num_bytes) -> float:
    return (num_bytes * 8) / 1_000_000

def to_csv_friendly_dict(speedtest_result: dict) -> dict:
    server_info = speedtest_result.get('server')
    ping_info = speedtest_result.get('ping')
    download_info = speedtest_result.get('download')
    upload_info = speedtest_result.get('upload')
    interface_info = speedtest_result.get('interface')
    url_info = speedtest_result.get('result')

    return {
        "Time": speedtest_result.get("timestamp").replace('Z', '+00:00'),
        "Server": f"{server_info.get('name')} - {server_info.get('location')}",
        "ISP": f"{server_info.get('isp')}",
        "Idle Latency": f"{ping_info.get('latency')} ms",
        "Download": f"",
        "Upload": f"",
        "Packet loss": f"",
        "URL": f"",
    }

def display_one(csv_fiendly: dict):
    pass

def display_last_n(number):
    pass

def log_to_file(speedtest_result: dict, write_mode: str, message: str):
    pass

def main():
    parser = argparse.ArgumentParser(description='A utility for running Ookla Speedtest and logging the results.')
    parser.add_argument('-c', '--check', help='Run the speedtest now and print the results without logging.')
    parser.add_argument('-l', '--log', help='Run the speedtest now and log the results.')
    parser.add_argument('-m', '--message', default="", help='Log message. This option has no effect if not used with the -l (--log) option.')
    parser.add_argument('-s', '--show', help='Show (print to stdout) the results of the last n (default 10) speed checks.')
    parser.add_argument('-n', '--number', default="10", type=int, help='The number of last speed checks to print with -s (--show) option. -n option has no effect without the -s option.')
    args = parser.parse_args()

    if len(sys.argv) == 1:
        parser.print_help()
    elif (not args.show) and (not args.check) and (not args.log):
        parser.print_help()

    if args.show:
        display_last_n(args.number)
    
    speedtest_result : dict | None = None
    if args.check or args.log:
        speedtest_result = run_speedtest()
        if not speedtest_result:
            print("Exiting because no JSON result available.")
            exit(1)
        display_one(speedtest_result)
    
        if args.log:
            write_mode = 'a' if CSV_LOCATION.exists() else 'w'
            log_to_file(speedtest_result, write_mode, args.message)

