import platform
import subprocess
import socket
from ipaddress import ip_network
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

ip_range = "89.0.0.0/16" # you can change it to any range the second hit in this range was an admin page for ABUS
output_file = "ip_with_open_ports.txt"
max_threads = 100

# Common IP camera ports
ports_to_check = [80, 554, 8000, 8080, 8888]

is_windows = platform.system().lower() == "windows"

def ping(ip):
    if is_windows:
        cmd = ["ping", "-n", "1", "-w", "1000", str(ip)]
    else:
        cmd = ["ping", "-c", "1", "-W", "1", str(ip)]
    try:
        result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return result.returncode == 0
    except:
        return False

def check_ports(ip, ports):
    open_ports = []
    for port in ports:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.5)
            try:
                if sock.connect_ex((str(ip), port)) == 0:
                    open_ports.append(port)
            except:
                continue
    return open_ports

def scan_ip(ip):
    if ping(ip):
        open_ports = check_ports(ip, ports_to_check)
        return str(ip), open_ports if open_ports else []
    return None

def main():
    print(f" Scanning range: {ip_range}")
    ip_list = list(ip_network(ip_range).hosts())
    results = []

    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures = {executor.submit(scan_ip, ip): ip for ip in ip_list}
        for future in tqdm(as_completed(futures), total=len(futures)):
            result = future.result()
            if result:
                ip, open_ports = result
                if open_ports:
                    print(f"{ip} has open ports: {open_ports}")
                    results.append((ip, open_ports))

    with open(output_file, "w") as f:
        for ip, ports in results:
            f.write(f"{ip}:{','.join(map(str, ports))}\n")

    print(f"\n {len(results)} IPs with open ports saved to {output_file}")

if __name__ == "__main__":
    main()
