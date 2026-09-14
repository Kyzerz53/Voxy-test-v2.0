#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ╔══════════════════════════════════════════════════╗
# ║   KyzerTool - Port Tarama Motoru (KyzerNmap)     ║
# ║   Gerçek nmap + Kyzerz53 kendi motoru (hibrit)   ║
# ║   Created by Kyzerz53                             ║
# ╚══════════════════════════════════════════════════╝
"""
KyzerNmap - İki modlu port tarama motoru:

  1. GERÇEK NMAP MODU: Sistemde nmap kuruluysa (shutil.which ile tespit
     edilir), doğrudan nmap'in kendi açık kaynak motorunu subprocess
     üzerinden çalıştırır. Bu, endüstri standardı SYN scan, servis/versiyon
     tespiti (-sV), NSE script taraması (-sC) gibi tüm güçlü nmap
     özelliklerinden faydalanır — tekerleği yeniden icat etmiyoruz.

  2. KYZER MOTORU (fallback): nmap kurulu değilse veya kullanıcı tercih
     ederse, saf Python ile yazılmış TCP connect-scan + banner grabbing +
     basit servis parmak izi çıkarma motoru devreye girer. Nmap kadar
     güçlü değildir ama harici bağımlılık gerektirmez ve Tor/proxy
     üzerinden (SOCKS monkey-patch ile) çalışabilir — ki gerçek nmap'in
     ham TCP/SYN taramaları Tor SOCK5 üzerinden native çalışmaz.
"""

import os
import re
import socket
import shutil
import subprocess
import threading
import time
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import socks
except ImportError:
    os.system("pip install PySocks -q --break-system-packages")
    import socks


class Colors:
    R = '\033[91m'; G = '\033[92m'; Y = '\033[93m'; C = '\033[96m'
    M = '\033[95m'; W = '\033[97m'; BOLD = '\033[1m'; RS = '\033[0m'


def log(msg, tag="*", color=Colors.C):
    print(f"  {color}[{tag}]{Colors.RS} {msg}")


# ══════════════════════════════════════════
#   YAYGIN PORT + SERVİS VERİTABANI
# ══════════════════════════════════════════
COMMON_PORTS = {
    21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS",
    80: "HTTP", 88: "Kerberos", 110: "POP3", 111: "RPCBind",
    135: "MSRPC", 139: "NetBIOS-SSN", 143: "IMAP", 389: "LDAP",
    443: "HTTPS", 445: "SMB", 465: "SMTPS", 587: "SMTP-Submission",
    631: "IPP", 993: "IMAPS", 995: "POP3S", 1433: "MSSQL",
    1521: "Oracle", 1723: "PPTP", 2049: "NFS", 2181: "Zookeeper",
    2375: "Docker", 2376: "Docker-TLS", 3000: "Node/Grafana",
    3306: "MySQL", 3389: "RDP", 4443: "HTTPS-Alt", 4444: "Metasploit",
    5000: "Flask/UPnP", 5432: "PostgreSQL", 5601: "Kibana",
    5672: "RabbitMQ", 5900: "VNC", 5984: "CouchDB", 6379: "Redis",
    6443: "Kubernetes-API", 7001: "WebLogic", 8000: "HTTP-Alt",
    8080: "HTTP-Proxy", 8081: "HTTP-Alt2", 8443: "HTTPS-Alt",
    8888: "HTTP-Alt3", 9000: "PHP-FPM/SonarQube", 9090: "Prometheus",
    9200: "Elasticsearch", 9300: "Elasticsearch-Transport",
    11211: "Memcached", 15672: "RabbitMQ-Mgmt", 27017: "MongoDB",
    27018: "MongoDB-Shard", 50000: "SAP",
}

TOP_1000_EXTRA_SAMPLE = list(range(1, 1025))  # Well-known port aralığı


def get_nmap_path():
    """Sistemde nmap kurulu mu kontrol eder, varsa yolunu döndürür"""
    return shutil.which("nmap")


# ══════════════════════════════════════════
#   MOD 1: GERÇEK NMAP (subprocess wrapper)
# ══════════════════════════════════════════
class RealNmapScanner:
    """
    Sistemde kurulu gerçek nmap binary'sini çalıştırıp çıktısını
    Türkçe, okunabilir formatta sunan sarmalayıcı (wrapper) sınıf.
    Nmap'in kendi açık kaynak tarama motorunu birebir kullanır.
    """

    PRESETS = {
        "1": {"name": "Hızlı Tarama (Top 100 port)",        "flags": ["-T4", "-F"]},
        "2": {"name": "Standart Tarama (Top 1000 port)",     "flags": ["-T4"]},
        "3": {"name": "Servis & Versiyon Tespiti (-sV)",     "flags": ["-T4", "-sV", "--top-ports", "200"]},
        "4": {"name": "Agresif Tarama (-A: OS+versiyon+script)", "flags": ["-T4", "-A", "--top-ports", "200"]},
        "5": {"name": "NSE Script Taraması (-sC)",           "flags": ["-T4", "-sC", "-sV", "--top-ports", "200"]},
        "6": {"name": "UDP Tarama (yavaş, root gerekir)",    "flags": ["-sU", "--top-ports", "50"]},
        "7": {"name": "Tüm Portlar (1-65535, yavaş)",        "flags": ["-T4", "-p-"]},
        "8": {"name": "Zafiyet Tarama Scriptleri (vuln)",    "flags": ["-T4", "--script", "vuln", "--top-ports", "200"]},
    }

    def __init__(self, target, nmap_path=None):
        self.target = target
        self.nmap_path = nmap_path or get_nmap_path()

    def is_available(self):
        return self.nmap_path is not None

    def run(self, preset="2", custom_flags=None, output_dir="output"):
        """Nmap'i seçilen preset veya özel flag'lerle çalıştırır"""
        if not self.is_available():
            log("Nmap sistemde bulunamadı!", "!", Colors.R)
            return None

        flags = custom_flags if custom_flags else self.PRESETS.get(preset, self.PRESETS["2"])["flags"]
        preset_name = self.PRESETS.get(preset, {}).get("name", "Özel tarama")

        print(f"\n  {Colors.BOLD}{Colors.M}╔══════════════════════════════════════════╗")
        print(f"  ║   KyzerNmap (Gerçek Nmap Motoru)          ║")
        print(f"  ╚══════════════════════════════════════════╝{Colors.RS}")
        print(f"  {Colors.W}Hedef: {Colors.Y}{self.target}{Colors.RS}")
        print(f"  {Colors.W}Mod: {Colors.Y}{preset_name}{Colors.RS}")

        cmd = [self.nmap_path] + flags + [self.target]
        print(f"  {Colors.C}[*] Çalıştırılan komut: {' '.join(cmd)}{Colors.RS}\n")

        os.makedirs(output_dir, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        raw_output_path = f"{output_dir}/nmap_{self.target.replace('/', '_')}_{ts}.txt"

        start = time.time()
        try:
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1, universal_newlines=True
            )
            full_output = []
            for line in process.stdout:
                print(f"  {Colors.W}{line.rstrip()}{Colors.RS}")
                full_output.append(line)
            process.wait()
            elapsed = time.time() - start

            with open(raw_output_path, "w", encoding="utf-8") as f:
                f.writelines(full_output)

            parsed = self.parse_output("".join(full_output))

            print(f"\n  {Colors.C}{'─'*60}{Colors.RS}")
            print(f"  {Colors.BOLD}{Colors.G}[✓] Nmap taraması tamamlandı{Colors.RS} ({elapsed:.1f} saniye)")
            print(f"  {Colors.W}Açık port sayısı: {Colors.G}{len(parsed['open_ports'])}{Colors.RS}")
            print(f"  {Colors.W}Ham çıktı kaydedildi: {Colors.Y}{raw_output_path}{Colors.RS}")
            print(f"  {Colors.C}{'─'*60}{Colors.RS}\n")

            return parsed

        except FileNotFoundError:
            log("Nmap çalıştırılamadı (binary bulunamadı).", "!", Colors.R)
            return None
        except Exception as e:
            log(f"Nmap çalıştırma hatası: {e}", "!", Colors.R)
            return None

    @staticmethod
    def parse_output(output):
        """Nmap ham çıktısından açık portları ve servisleri ayrıştırır"""
        open_ports = []
        # Örnek satır: "80/tcp   open  ssl/http    nginx 1.18.0"
        # NOT: \s+ yerine [ \t]+ kullanılıyor çünkü \s newline'ı da yer,
        # bu satırlar arası bilgi karışmasına (parse hatasına) yol açardı.
        pattern = re.compile(r'^(\d+)/(tcp|udp)\s+(open|open\|filtered)[ \t]+(\S+)(?:[ \t]+([^\n]*))?$', re.MULTILINE)
        for match in pattern.finditer(output):
            port, proto, state, service, version = match.groups()
            open_ports.append({
                "port": int(port),
                "protocol": proto,
                "state": state,
                "service": service,
                "version": (version or "").strip(),
            })

        os_match = re.search(r'OS details?: (.+)', output)
        os_guess = os_match.group(1) if os_match else None

        return {"open_ports": open_ports, "os_guess": os_guess, "raw": output}


# ══════════════════════════════════════════
#   MOD 2: KYZER MOTORU (saf Python fallback)
# ══════════════════════════════════════════
class KyzerPortScanner:
    """
    Nmap kurulu olmayan ortamlar için saf Python TCP connect-scan motoru.
    Banner grabbing ile basit servis tespiti yapar. Tor/Proxy üzerinden
    (SOCKS monkey-patch ile) çalışabilir — nmap'in ham SYN taraması bunu
    native yapamaz, bu yüzden anonim tarama gerektiğinde bu motor tercih
    edilmelidir.
    """

    def __init__(self, target, threads=200, timeout=1.5, tor=False, proxy=None):
        self.target = target
        self.threads = threads
        self.timeout = timeout
        self.tor = tor
        self.proxy = proxy
        self.open_ports = []
        self.lock = threading.Lock()

        try:
            self.ip = socket.gethostbyname(target)
        except socket.gaierror:
            self.ip = None

    def _make_socket(self):
        """Tor/proxy ayarına göre normal veya SOCKS soketi oluşturur"""
        if self.tor:
            s = socks.socksocket()
            s.set_proxy(socks.SOCKS5, "127.0.0.1", 9050)
            return s
        elif self.proxy:
            # proxy formatı: socks5://ip:port
            m = re.match(r'socks5://([^:]+):(\d+)', self.proxy)
            if m:
                s = socks.socksocket()
                s.set_proxy(socks.SOCKS5, m.group(1), int(m.group(2)))
                return s
            return socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        else:
            return socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def grab_banner(self, sock, port):
        """Açık bir porttan banner (servis tanıtım verisi) okumaya çalışır"""
        try:
            sock.settimeout(2)
            # HTTP portlarına basit bir istek gönder
            if port in (80, 8080, 8000, 8888, 5000, 3000, 8081):
                sock.send(b"HEAD / HTTP/1.0\r\n\r\n")
            banner = sock.recv(256).decode(errors="ignore").strip()
            return banner.split("\n")[0][:100] if banner else ""
        except Exception:
            return ""

    @staticmethod
    def fingerprint_service(port, banner):
        """Banner içeriğine göre servis/versiyon tahmini yapar"""
        banner_lower = banner.lower()
        if "ssh-" in banner_lower:
            return f"SSH ({banner.split()[0] if banner else ''})"
        if "http/" in banner_lower or "server:" in banner_lower:
            return "HTTP"
        if "ftp" in banner_lower:
            return "FTP"
        if "smtp" in banner_lower or "mail" in banner_lower:
            return "SMTP"
        if "mysql" in banner_lower:
            return "MySQL"
        return COMMON_PORTS.get(port, "Bilinmiyor")

    def scan_port(self, port):
        """Tek bir portu tarar, açıksa banner alır"""
        try:
            sock = self._make_socket()
            sock.settimeout(self.timeout)
            result = sock.connect_ex((self.ip, port))
            if result == 0:
                banner = self.grab_banner(sock, port)
                service = self.fingerprint_service(port, banner)
                with self.lock:
                    entry = {
                        "port": port,
                        "service": service,
                        "banner": banner,
                        "base_guess": COMMON_PORTS.get(port, "?"),
                    }
                    self.open_ports.append(entry)
                    banner_str = f" | Banner: {Colors.M}{banner[:60]}{Colors.RS}" if banner else ""
                    print(f"  {Colors.M}[AÇIK]{Colors.RS} Port {Colors.Y}{port:6}{Colors.RS} → {Colors.G}{service}{Colors.RS}{banner_str}")
            sock.close()
        except Exception:
            pass

    def run(self, port_range="common"):
        """
        port_range: "common" (bilinen ~60 port), "top1000" (1-1024),
                    "full" (1-65535, çok yavaş) veya "1-100" gibi özel aralık
        """
        print(f"\n  {Colors.BOLD}{Colors.M}╔══════════════════════════════════════════╗")
        print(f"  ║   KyzerPortScanner (Kyzer Motoru)          ║")
        print(f"  ╚══════════════════════════════════════════╝{Colors.RS}")
        print(f"  {Colors.W}Hedef: {Colors.Y}{self.target}{Colors.RS}")

        if not self.ip:
            log(f"'{self.target}' çözümlenemedi (DNS hatası).", "!", Colors.R)
            return []

        print(f"  {Colors.W}IP: {Colors.G}{self.ip}{Colors.RS}")

        if self.tor:
            print(f"  {Colors.Y}[!] TOR üzerinden port taraması ÇOK YAVAŞTIR (her port ayrı Tor devresi).{Colors.RS}")
            print(f"  {Colors.Y}[!] Sadece az sayıda kritik port taramanız önerilir.{Colors.RS}")

        if port_range == "common":
            ports = list(COMMON_PORTS.keys())
        elif port_range == "top1000":
            ports = TOP_1000_EXTRA_SAMPLE
        elif port_range == "full":
            ports = list(range(1, 65536))
        elif "-" in port_range:
            start, end = map(int, port_range.split("-"))
            ports = list(range(start, end + 1))
        else:
            ports = list(COMMON_PORTS.keys())

        threads = min(self.threads, 20) if (self.tor or self.proxy) else self.threads

        print(f"  {Colors.C}[*] {len(ports)} port taranıyor ({threads} thread)...{Colors.RS}\n")

        start_time = time.time()
        with ThreadPoolExecutor(max_workers=threads) as ex:
            futures = [ex.submit(self.scan_port, p) for p in ports]
            for _ in as_completed(futures):
                pass
        elapsed = time.time() - start_time

        self.open_ports.sort(key=lambda x: x["port"])

        print(f"\n  {Colors.C}{'─'*60}{Colors.RS}")
        print(f"  {Colors.BOLD}{Colors.G}[✓] Tarama tamamlandı{Colors.RS} ({elapsed:.1f} saniye)")
        print(f"  {Colors.W}Açık port sayısı: {Colors.G}{len(self.open_ports)}{Colors.RS}")
        print(f"  {Colors.C}{'─'*60}{Colors.RS}\n")

        return self.open_ports


def save_results(target, data, mode, output_dir="output"):
    """Sonuçları JSON olarak kaydeder"""
    os.makedirs(output_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = f"{output_dir}/portscan_{target.replace('/', '_')}_{ts}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"target": target, "mode": mode, "data": data}, f, ensure_ascii=False, indent=2, default=str)
    return path


# ══════════════════════════════════════════
#   BAĞIMSIZ ÇALIŞTIRMA (test amaçlı)
# ══════════════════════════════════════════
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Kullanım: python3 port_scanner.py <hedef> [--kyzer] [--tor]")
        sys.exit(1)

    target = sys.argv[1]
    force_kyzer = "--kyzer" in sys.argv
    tor = "--tor" in sys.argv

    if not force_kyzer and get_nmap_path():
        scanner = RealNmapScanner(target)
        result = scanner.run(preset="3")
        if result:
            save_results(target, result, "nmap")
    else:
        scanner = KyzerPortScanner(target, tor=tor)
        result = scanner.run(port_range="common")
        if result:
            save_results(target, result, "kyzer")
