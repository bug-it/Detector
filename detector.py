#!/usr/bin/env python3
import psutil
import time
from datetime import datetime
from collections import defaultdict
import os
import subprocess

# ================= CONFIGURAÇÕES ================= #
LIMITE_CONEXOES = 100
INTERVALO = 5
LOG_PATH = "/var/log/dos_alertas.log"
BLOQUEAR_IP = True
# ================================================= #

# ANSI Colors
VERDE = "\033[92m"
AMARELO = "\033[93m"
VERMELHO = "\033[91m"
AZUL = "\033[94m"
RESET = "\033[0m"

ips_bloqueados = set()

def limpar_terminal():
    os.system("clear" if os.name == "posix" else "cls")

def obter_conexoes():
    contagem_ips = defaultdict(int)
    for conn in psutil.net_connections(kind='inet'):
        if conn.status == psutil.CONN_ESTABLISHED and conn.raddr:
            ip = conn.raddr.ip
            if ip.startswith("::ffff:"):
                ip = ip.replace("::ffff:", "")
            if ip not in ips_bloqueados:  # Ignorar IPs já bloqueados
                contagem_ips[ip] += 1
    return contagem_ips

def exibir_banner():
    print(f"{AZUL}🔍 Monitorando Conexões - Limite: {LIMITE_CONEXOES} conexões/IP{RESET}")

def exibir_alerta(ip, total):
    print(f"{VERMELHO}⚠️  ALTA ATIVIDADE: {ip} - {total} conexões (ESTABLISHED: {total}){RESET}")
    registrar_log(ip, total)
    if BLOQUEAR_IP:
        bloquear_ip(ip)

def exibir_status(total_conexoes):
    agora = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    print(f"{AMARELO}📡 {agora} - Total de conexões monitoradas: {total_conexoes}{RESET}")

def registrar_log(ip, total):
    try:
        with open(LOG_PATH, "a") as log:
            log.write(f"{datetime.now()} - ALERTA: {ip} com {total} conexões suspeitas.\n")
    except PermissionError:
        print(f"{VERMELHO}❌ Permissão negada ao gravar log em {LOG_PATH}.{RESET}")

def bloquear_ip(ip):
    if ip in ips_bloqueados:
        return
    print(f"{AMARELO}🚫 BLOQUEANDO IP: {ip} via iptables...{RESET}")
    resultado = subprocess.call(["iptables", "-A", "INPUT", "-s", ip, "-j", "DROP"])
    if resultado == 0:
        print(f"{VERDE}✔️  IP {ip} bloqueado com sucesso.{RESET}")
        # Encerrar conexões ativas
        subprocess.call(["conntrack", "-D", "-s", ip], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        ips_bloqueados.add(ip)
    else:
        print(f"{VERMELHO}❌ Falha ao bloquear o IP {ip}.{RESET}")

def main():
    try:
        limpar_terminal()
        exibir_banner()
        while True:
            ips = obter_conexoes()
            total_conexoes = sum(ips.values())
            exibir_status(total_conexoes)
            for ip, total in ips.items():
                if total >= LIMITE_CONEXOES:
                    exibir_alerta(ip, total)
            time.sleep(INTERVALO)
    except KeyboardInterrupt:
        print(f"\n{AMARELO}🚦 Monitoramento encerrado pelo usuário.{RESET}")

if __name__ == "__main__":
    main()
