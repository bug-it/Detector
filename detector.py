#!/usr/bin/env python3
import os
import subprocess
import sys

def instalar_pip():
    """Instala o pip se não estiver presente no sistema."""
    try:
        print("🔄 Instalando o pip...")
        subprocess.call(["apt", "update"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.call(["apt", "install", "-y", "python3-pip"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        print(f"❌ Erro ao tentar instalar o pip: {e}")
        sys.exit(1)

def verificar_pacote(pacote):
    """Verifica se um pacote Python está instalado."""
    try:
        subprocess.call([sys.executable, "-m", "pip", "show", pacote], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except FileNotFoundError:
        return False

# Função para instalar pacotes automaticamente
def instalar_pacotes():
    """Instala pacotes Python necessários."""
    pacotes = ["psutil"]
    try:
        for pacote in pacotes:
            if not verificar_pacote(pacote):
                print(f"🔄 Instalando o pacote {pacote}...")
                subprocess.call([sys.executable, "-m", "pip", "install", "--quiet", pacote, "--break-system-packages"])
    except Exception as e:
        print(f"❌ Erro ao tentar instalar pacotes: {e}")
        sys.exit(1)

# Verifica se o pip está instalado e o instala se necessário
try:
    subprocess.call([sys.executable, "-m", "pip", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
except FileNotFoundError:
    instalar_pip()

# Instalar pacotes necessários
instalar_pacotes()

import psutil
import time
from datetime import datetime
from collections import defaultdict

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
NEGRITO = "\033[1m"

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
            contagem_ips[ip] += 1
    return contagem_ips

def exibir_banner():
    print(f"{AZUL}{NEGRITO}🔍 Monitorando Conexões...{RESET}")

def exibir_alerta(ip, total):
    print(f"{VERMELHO}{NEGRITO}⚠️  ALTA ATIVIDADE: {ip} com {total} conexões simultâneas suspeitas.{RESET}")
    registrar_log(ip, total)
    if BLOQUEAR_IP:
        bloquear_ip(ip)

def exibir_status():
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{AMARELO}📡 {agora} - Verificando conexões...{RESET}")

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
    else:
        print(f"{VERMELHO}❌ Falha ao bloquear o IP {ip}.{RESET}")
    ips_bloqueados.add(ip)

def main():
    try:
        limpar_terminal()
        exibir_banner()
        while True:
            exibir_status()
            ips = obter_conexoes()
            for ip, total in ips.items():
                if total >= LIMITE_CONEXOES:
                    exibir_alerta(ip, total)
            time.sleep(INTERVALO)
    except KeyboardInterrupt:
        print(f"\n{AMARELO}{NEGRITO}🚦 Monitoramento encerrado pelo usuário.{RESET}")

if __name__ == "__main__":
    main()
