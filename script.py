import paramiko
import threading
import time
import re
import argparse
import getpass
from datetime import datetime

# Détails des serveurs
servers = [
    {"hostname": ""},
    {"hostname": ""},
    {"hostname": ""},
    {"hostname": ""},
]

# Termes à mettre en évidence
highlight_terms = ["ERROR", "newsletters"]

# Couleurs possibles (autant de couleurs que de serveurs)
colors = ["\033[1;34m", "\033[1;35m", "\033[1;36m", "\033[1;37m"]

def highlight(line, terms):
    for term in terms:
        line = re.sub(f"({term})", r'\033[1;31m\1\033[0m', line, flags=re.IGNORECASE)
    return line

def contains_all_highlight_terms(line, terms):
    return all(term in line for term in terms)

def tail_log(server, password, log_file, color):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(server["hostname"], username="vdx", password=password)

    try:
        stdin, stdout, stderr = ssh.exec_command(f"tail -f {log_file}")
        for line in iter(stdout.readline, ""):
            if contains_all_highlight_terms(line, highlight_terms):
                highlighted_line = highlight(line, highlight_terms)
                print(f"{color}{server['hostname']}: {highlighted_line}\033[0m", end="")
    finally:
        ssh.close()

def start_tail_threads(password):
    threads = []
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = f"/data/www/echos/fo/prod/storage/logs/lumen-{today}.log"
    
    for i, server in enumerate(servers):
        color = colors[i % len(colors)]
        thread = threading.Thread(target=tail_log, args=(server, password, log_file, color))
        thread.start()
        threads.append(thread)
    
    for thread in threads:
        thread.join()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Suivi des logs sur plusieurs serveurs.")
    args = parser.parse_args()

    password = getpass.getpass("Mot de passe pour les serveurs: ")

    try:
        start_tail_threads(password)
    except KeyboardInterrupt:
        print("Interruption par l'utilisateur.")
