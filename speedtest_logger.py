import argparse
import json
import csv
import subprocess
from pathlib import Path
import sys
from datetime import datetime
import time
from collections import OrderedDict

SCRIPT_DIR = Path(__file__).parent.resolve()
CSV_LOCATION = SCRIPT_DIR / "speedtest.csv"
RAW_RESULTS_DIR = SCRIPT_DIR / "raw_results"
HEADER_ROW = [
    "timestamp","isp","server name","server id","server location",
    "internal ip","external ip","interface name","mac address","is vpn",
    "idle latency","idle latency low","idle latency high","idle jitter","packet loss",
    "download mbps","download bytes","download latency","download latency jitter","download latency low","download latency high",
    "upload mbps","upload bytes","upload latency","upload latency jitter","upload latency low","upload latency high",
    "share url","custom note",
]


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

    try:
        RAW_RESULTS_DIR.mkdir(exist_ok=True)
        file_path = RAW_RESULTS_DIR / f"speedtest_{time.time()}.json"
        with open(file_path, 'w') as f:
            json.dump(result, f, indent=2, ensure_ascii=True)
    except Exception as e:
        print(f"Error saving raw results to file: {e}")

    return result


def sizeof_fmt(num, suffix="B"):
    for unit in ("", "K", "M", "G", "T", "P", "E", "Z"):
        if abs(num) < 1024.0:
            return f"{num:.2f} {unit}{suffix}"
        num /= 1024.0
    return f"{num:.2f} Y{suffix}"


def bytes_to_megabits(num_bytes) -> float:
    return (num_bytes * 8) / 1_000_000


def float_to_str(num):
    """Convert a float to a string with 2 decimal places. Return empty string if num is neither int nor float"""
    if not isinstance(num, float) and not isinstance(num, int):
        print(f"WARN: float_to_str expected either float or int, but received '{num}', which is of type {type(num)}")
        return ""
    return f'{num:.2f}'


def to_csv_friendly_dict(speedtest_result: dict, message: str) -> dict:
    server_info = speedtest_result.get('server')
    ping_info = speedtest_result.get('ping')
    interface_info = speedtest_result.get('interface')
    download_info = speedtest_result.get('download')
    download_latency_info = download_info.get('latency')
    upload_info = speedtest_result.get('upload')
    upload_latency_info = upload_info.get('latency')
    interface_info = speedtest_result.get('interface')
    url_info = speedtest_result.get('result')

    csv_friendly_result = {
        "timestamp": speedtest_result.get("timestamp").replace('Z', '+00:00'),
        "isp": speedtest_result.get("isp"),

        # Server info
        "server name": server_info.get("name"),
        "server id": server_info.get("id"),
        "server location": ", ".join([server_info.get("location"), server_info.get("country")]),

        # Interface info
        "internal ip": interface_info.get("internalIp"),
        "external ip": interface_info.get("externalIp"),
        "interface name": interface_info.get("name"),
        "mac address": interface_info.get("macAddr"),
        "is vpn": interface_info.get("isVpn"),

        # Ping info
        "idle latency": f'{float_to_str(ping_info.get("latency"))}',
        "idle latency low": f'{float_to_str(ping_info.get("low"))}',
        "idle latency high": f'{float_to_str(ping_info.get("high"))}',
        "idle jitter": f'{float_to_str(ping_info.get("jitter"))}',

        "packet loss": speedtest_result.get("packetLoss"),

        # Download info
        "download mbps": f"{bytes_to_megabits(download_info.get('bandwidth')):.2f}",
        "download bytes": download_info.get("bytes"),
        "download latency": f'{float_to_str(download_latency_info.get("iqm"))}',
        "download latency jitter": f'{float_to_str(download_latency_info.get("jitter"))}',
        "download latency low": f'{float_to_str(download_latency_info.get("low"))}',
        "download latency high": f'{float_to_str(download_latency_info.get("high"))}',

        # Upload info
        "upload mbps": f"{bytes_to_megabits(upload_info.get('bandwidth')):.2f}",
        "upload bytes": upload_info.get("bytes"),
        "upload latency": f'{float_to_str(upload_latency_info.get("iqm"))}',
        "upload latency jitter": f'{float_to_str(upload_latency_info.get("jitter"))}',
        "upload latency low": f'{float_to_str(upload_latency_info.get("low"))}',
        "upload latency high": f'{float_to_str(upload_latency_info.get("high"))}',

        "share url": url_info.get("url"),
        "custom note": message,
    }

    if len(csv_friendly_result) != len(HEADER_ROW):
        raise RuntimeError("Likely programming error: Size of CSV friendly dict is not equal to size of header row")
    
    return csv_friendly_result


def display_one(data: dict | OrderedDict):
    dt = datetime.fromisoformat(data.get("timestamp")).astimezone()
    print("Time of test:", dt.strftime("%a, %d %b %Y, %H:%M %Z"), sep="\t\t")
    print("ISP:", data.get("isp"), sep="\t\t\t")
    print(
        "Server:",
        f'{data.get("server name")} - {data.get("server location")} (id: {data.get("server id")})',
        sep="\t\t\t"
    )
    print(
        "Idle Latency:",
        "\t\t",
        f'{data.get("idle latency")} ms',
        "\t",
        f'(jitter: {data.get("idle jitter")} ms, low: {data.get("idle latency low")} ms, high: {data.get("idle latency high")} ms)',
    )

    print(
        "Download:",
        "\t\t",
        f'{data.get("download mbps")} Mbps',
        "\t",
        f'(data used: {sizeof_fmt(int(data.get("download bytes")))})',
    )
    print(
        "Download latency:",
        "\t",
        f'{data.get("download latency")} ms',
        "\t",
        f'(jitter: {data.get("download latency jitter")} ms, low: {data.get("download latency low")} ms, high: {data.get("download latency high")} ms)',
    )

    print(
        "Upload:",
        "\t\t",
        f'{data.get("upload mbps")} Mbps',
        "\t",
        f'(data used: {sizeof_fmt(int(data.get("upload bytes")))})',
    )
    print(
        "Upload latency:",
        "\t",
        f'{data.get("upload latency")} ms',
        "\t",
        f'(jitter: {data.get("upload latency jitter")} ms, low: {data.get("upload latency low")} ms, high: {data.get("upload latency high")} ms)',
    )

    print("Packet loss:", f'{data.get("packet loss")}', sep="\t\t")
    print("Result URL:", f'{data.get("share url")}', sep="\t\t")
    print("Custom note:", f'{data.get("custom note")}', sep="\t\t")
    print("")


def display_last_n(n: int):
    with open(CSV_LOCATION, "r") as f:
        reader = csv.DictReader(f)
        all_rows = list(reader) # list of OrderedDict

    for row in all_rows[-n:]: # Slice only last n
        display_one(row)


def log_to_file(csv_fiendly_result: dict, write_mode: str):
    print(f"Opening {CSV_LOCATION.name} in {'append' if write_mode == 'a' else 'write'} mode")

    with open(CSV_LOCATION, write_mode, newline='') as f:
        writer = csv.DictWriter(f, fieldnames=HEADER_ROW)

        if write_mode == 'w':
            writer.writeheader()

        writer.writerow(csv_fiendly_result)

    print(f"Successfully logged row to CSV file {CSV_LOCATION.name}")


def main():
    parser = argparse.ArgumentParser(description='A utility for running Ookla Speedtest and logging the results.')
    parser.add_argument('-c', '--check', action='store_true', help='Run the speedtest now and print the results without logging.')
    parser.add_argument('-l', '--log', action='store_true', help='Run the speedtest now and log the results.')
    parser.add_argument('-m', '--message', default="", help='Log message. This option has no effect if not used with the -l (--log) option.')
    parser.add_argument('-s', '--show', action='store_true', help='Show (print to stdout) the results of the last n (default 10) speed checks.')
    parser.add_argument('-n', '--number', default="5", type=int, help='The number of last speed checks to print with -s (--show) option. -n option has no effect without the -s option.')
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
            print("Exiting because no JSON result is available.")
            exit(1)

        try:
            csv_fiendly_result: dict = to_csv_friendly_dict(speedtest_result, args.message)
        except Exception as e:
            print(f"An error occurred when converting result JSON to CSV friendly dict: {e}")
            exit(1)

        display_one(csv_fiendly_result)

        if args.log:
            write_mode = 'a' if CSV_LOCATION.exists() else 'w'
            log_to_file(csv_fiendly_result, write_mode)


if __name__ == "__main__":
    main()
