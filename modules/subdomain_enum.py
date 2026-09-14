#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ╔══════════════════════════════════════════════════╗
# ║   KyzerTool - Subdomain Keşif Modülü             ║
# ║   Passive + Active Enumeration (Subfinder mantığı)║
# ║   Created by Kyzerz53                             ║
# ╚══════════════════════════════════════════════════╝

import requests
import socket
import json
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import quote

try:
    import dns.resolver
except ImportError:
    import os
    os.system("pip install dnspython -q --break-system-packages")
    import dns.resolver

requests.packages.urllib3.disable_warnings()


class Colors:
    R  = '\033[91m'
    G  = '\033[92m'
    Y  = '\033[93m'
    B  = '\033[94m'
    M  = '\033[95m'
    C  = '\033[96m'
    W  = '\033[97m'
    BOLD = '\033[1m'
    RS = '\033[0m'


def get_session(proxy=None, tor=False):
    """Proxy veya Tor destekli session oluşturur"""
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    })
    if tor:
        session.proxies = {
            "http": "socks5h://127.0.0.1:9050",
            "https": "socks5h://127.0.0.1:9050"
        }
    elif proxy:
        session.proxies = {"http": proxy, "https": proxy}
    return session


class SubdomainEnum:
    """
    Kyzerz53 tarafından geliştirilmiş subdomain keşif motoru.
    Subfinder mimarisinden ilham alınmıştır:
      - Passive kaynaklardan toplama (crt.sh, Wayback, HackerTarget, AlienVault OTX, RapidDNS)
      - Active DNS brute force (wordlist tabanlı, threading)
      - DNS doğrulama ve wildcard filtreleme
    """

    def __init__(self, domain, threads=50, timeout=10, proxy=None, tor=False, verbose=True):
        self.domain = domain.strip().lower()
        self.threads = threads
        self.timeout = timeout
        self.proxy = proxy
        self.tor = tor
        self.verbose = verbose
        self.session = get_session(proxy, tor)
        self.found = set()
        self.resolved = {}
        self.lock = threading.Lock()

    def log(self, msg, tag="*", color=Colors.C):
        if self.verbose:
            print(f"  {color}[{tag}]{Colors.RS} {msg}")

    def found_log(self, sub, ip=None):
        with self.lock:
            if sub not in self.found:
                self.found.add(sub)
                ip_str = f" {Colors.W}→ {Colors.G}{ip}{Colors.RS}" if ip else ""
                print(f"  {Colors.M}[BULUNDU]{Colors.RS} {Colors.Y}{sub}{Colors.RS}{ip_str}")

    # ══════════════════════════════════════
    #        PASSIVE KAYNAKLAR
    # ══════════════════════════════════════

    def source_crtsh(self):
        """crt.sh - Sertifika şeffaflığı (Certificate Transparency) kayıtları"""
        subs = set()
        try:
            url = f"https://crt.sh/?q=%.{self.domain}&output=json"
            r = self.session.get(url, timeout=self.timeout + 10, verify=False)
            if r.status_code == 200:
                data = r.json()
                for entry in data:
                    name = entry.get("name_value", "")
                    for line in name.split("\n"):
                        line = line.strip().lower()
                        if line.endswith(self.domain) and "*" not in line:
                            subs.add(line)
        except Exception as e:
            self.log(f"crt.sh hata: {e}", "!", Colors.R)
        return subs

    def source_wayback(self):
        """Wayback Machine (archive.org) - Geçmiş kayıtlı URL'lerden subdomain çıkarma"""
        subs = set()
        try:
            url = f"http://web.archive.org/cdx/search/cdx?url=*.{self.domain}/*&output=json&fl=original&collapse=urlkey&limit=10000"
            r = self.session.get(url, timeout=self.timeout + 10, verify=False)
            if r.status_code == 200:
                data = r.json()
                pattern = re.compile(rf'https?://([a-zA-Z0-9_-]+\.)*{re.escape(self.domain)}')
                for row in data[1:]:
                    if row:
                        match = pattern.match(row[0])
                        if match:
                            host = row[0].split("/")[2].split(":")[0].lower()
                            if host.endswith(self.domain):
                                subs.add(host)
        except Exception as e:
            self.log(f"Wayback hata: {e}", "!", Colors.R)
        return subs

    def source_hackertarget(self):
        """HackerTarget API - Hosts bulma servisi"""
        subs = set()
        try:
            url = f"https://api.hackertarget.com/hostsearch/?q={self.domain}"
            r = self.session.get(url, timeout=self.timeout, verify=False)
            if r.status_code == 200 and "error" not in r.text.lower():
                for line in r.text.split("\n"):
                    if "," in line:
                        host = line.split(",")[0].strip().lower()
                        if host.endswith(self.domain):
                            subs.add(host)
        except Exception as e:
            self.log(f"HackerTarget hata: {e}", "!", Colors.R)
        return subs

    def source_alienvault(self):
        """AlienVault OTX - Open Threat Exchange passive DNS"""
        subs = set()
        try:
            url = f"https://otx.alienvault.com/api/v1/indicators/domain/{self.domain}/passive_dns"
            r = self.session.get(url, timeout=self.timeout + 5, verify=False)
            if r.status_code == 200:
                data = r.json()
                for record in data.get("passive_dns", []):
                    hostname = record.get("hostname", "").lower()
                    if hostname.endswith(self.domain):
                        subs.add(hostname)
        except Exception as e:
            self.log(f"AlienVault hata: {e}", "!", Colors.R)
        return subs

    def source_rapiddns(self):
        """RapidDNS.io - subdomain veritabanı taraması"""
        subs = set()
        try:
            url = f"https://rapiddns.io/subdomain/{self.domain}?full=1"
            r = self.session.get(url, timeout=self.timeout, verify=False)
            if r.status_code == 200:
                matches = re.findall(rf'([a-zA-Z0-9_-]+\.)*{re.escape(self.domain)}', r.text)
                for m in re.findall(rf'>([a-zA-Z0-9_.-]+\.{re.escape(self.domain)})<', r.text):
                    subs.add(m.lower())
        except Exception as e:
            self.log(f"RapidDNS hata: {e}", "!", Colors.R)
        return subs

    def source_certspotter(self):
        """CertSpotter API - SSL sertifika izleme"""
        subs = set()
        try:
            url = f"https://api.certspotter.com/v1/issuances?domain={self.domain}&include_subdomains=true&expand=dns_names"
            r = self.session.get(url, timeout=self.timeout, verify=False)
            if r.status_code == 200:
                data = r.json()
                for entry in data:
                    for name in entry.get("dns_names", []):
                        name = name.lower().lstrip("*.")
                        if name.endswith(self.domain):
                            subs.add(name)
        except Exception as e:
            self.log(f"CertSpotter hata: {e}", "!", Colors.R)
        return subs

    def run_passive(self):
        """Tüm passive kaynakları paralel çalıştırır"""
        print(f"\n  {Colors.BOLD}{Colors.C}━━━ PASSIVE KAYNAK TARAMASI ━━━{Colors.RS}\n")

        sources = {
            "crt.sh (Certificate Transparency)": self.source_crtsh,
            "Wayback Machine": self.source_wayback,
            "HackerTarget": self.source_hackertarget,
            "AlienVault OTX": self.source_alienvault,
            "CertSpotter": self.source_certspotter,
            "RapidDNS": self.source_rapiddns,
        }

        all_subs = set()
        with ThreadPoolExecutor(max_workers=len(sources)) as ex:
            futures = {ex.submit(fn): name for name, fn in sources.items()}
            for future in as_completed(futures):
                name = futures[future]
                try:
                    result = future.result()
                    self.log(f"{name}: {Colors.G}{len(result)}{Colors.RS} sonuç", "✓", Colors.G)
                    all_subs.update(result)
                except Exception as e:
                    self.log(f"{name}: hata - {e}", "✗", Colors.R)

        # Ana domain'i çıkar, gereksiz karakterleri temizle
        clean_subs = set()
        for s in all_subs:
            s = s.strip().lower()
            s = re.sub(r'^\*\.', '', s)
            s = re.sub(r'[^a-z0-9.\-]', '', s)
            if s.endswith(self.domain) and s != self.domain and len(s) > len(self.domain):
                clean_subs.add(s)

        print(f"\n  {Colors.Y}[*] Passive taramadan toplam {len(clean_subs)} benzersiz subdomain bulundu{Colors.RS}\n")
        return clean_subs

    # ══════════════════════════════════════
    #        ACTIVE BRUTE FORCE
    # ══════════════════════════════════════

    def resolve_dns(self, subdomain):
        """Bir subdomain'i DNS üzerinden çözer"""
        try:
            resolver = dns.resolver.Resolver()
            resolver.timeout = 3
            resolver.lifetime = 3
            answers = resolver.resolve(subdomain, 'A')
            ip = str(answers[0])
            return ip
        except Exception:
            return None

    def bruteforce_worker(self, word):
        """Wordlist'ten bir kelime alıp subdomain testi yapar"""
        candidate = f"{word}.{self.domain}"
        ip = self.resolve_dns(candidate)
        if ip:
            with self.lock:
                self.resolved[candidate] = ip
            self.found_log(candidate, ip)
            return candidate, ip
        return None, None

    def run_bruteforce(self, wordlist_path=None, wordlist=None):
        """
        Active brute force - wordlist dosyasından veya listeden subdomain dener.
        Subfinder'ın active modülüne benzer mantık: yüksek threading, hızlı DNS çözümleme.
        """
        print(f"\n  {Colors.BOLD}{Colors.C}━━━ ACTIVE BRUTE FORCE (DNS) ━━━{Colors.RS}\n")

        words = []
        if wordlist_path:
            try:
                with open(wordlist_path, "r", encoding="utf-8", errors="ignore") as f:
                    words = [line.strip() for line in f if line.strip() and not line.startswith("#")]
            except FileNotFoundError:
                self.log(f"Wordlist bulunamadı: {wordlist_path}", "!", Colors.R)
                return set()
        elif wordlist:
            words = wordlist
        else:
            words = DEFAULT_WORDLIST

        self.log(f"{len(words)} kelime ile brute force başlıyor ({self.threads} thread)...", "*", Colors.C)

        with ThreadPoolExecutor(max_workers=self.threads) as ex:
            futures = [ex.submit(self.bruteforce_worker, w) for w in words]
            for _ in as_completed(futures):
                pass

        print(f"\n  {Colors.Y}[*] Brute force tamamlandı. {len(self.resolved)} aktif subdomain doğrulandı{Colors.RS}\n")
        return self.resolved

    def verify_all(self, subdomains):
        """Bulunan tüm subdomainleri DNS ile doğrular (canlı mı kontrol eder)"""
        print(f"\n  {Colors.BOLD}{Colors.C}━━━ DNS DOĞRULAMA ━━━{Colors.RS}\n")
        self.log(f"{len(subdomains)} subdomain doğrulanıyor...", "*", Colors.C)

        def verify_one(sub):
            ip = self.resolve_dns(sub)
            if ip:
                with self.lock:
                    self.resolved[sub] = ip
                self.found_log(sub, ip)

        with ThreadPoolExecutor(max_workers=self.threads) as ex:
            futures = [ex.submit(verify_one, s) for s in subdomains]
            for _ in as_completed(futures):
                pass

        return self.resolved

    # ══════════════════════════════════════
    #        TAM TARAMA (subfinder gibi)
    # ══════════════════════════════════════

    def run_full(self, wordlist_path=None, do_bruteforce=True):
        """
        Tam subdomain keşfi:
          1. Passive kaynaklardan toplama
          2. Bulunanları DNS ile doğrulama
          3. (Opsiyonel) Wordlist ile ek brute force
        """
        start = time.time()

        print(f"  {Colors.BOLD}{Colors.M}╔══════════════════════════════════════════╗")
        print(f"  ║   KyzerSubfinder — by Kyzerz53             ║")
        print(f"  ║   Hedef: {self.domain:<33}║")
        print(f"  ╚══════════════════════════════════════════╝{Colors.RS}")

        # 1) Passive
        passive_subs = self.run_passive()

        # 2) DNS doğrulama
        if passive_subs:
            self.verify_all(passive_subs)

        # 3) Brute force (opsiyonel ek)
        if do_bruteforce:
            self.run_bruteforce(wordlist_path=wordlist_path)

        elapsed = time.time() - start

        # ÖZET
        print(f"\n  {Colors.C}{'─'*60}{Colors.RS}")
        print(f"  {Colors.BOLD}{Colors.G}[✓] TARAMA TAMAMLANDI{Colors.RS}")
        print(f"  {Colors.W}  Toplam bulunan (aktif): {Colors.G}{len(self.resolved)}{Colors.RS}")
        print(f"  {Colors.W}  Süre: {Colors.Y}{elapsed:.2f} saniye{Colors.RS}")
        print(f"  {Colors.C}{'─'*60}{Colors.RS}\n")

        return self.resolved


# Varsayılan mini wordlist (harici wordlist verilmezse kullanılır)
DEFAULT_WORDLIST = [
    "www", "mail", "ftp", "localhost", "webmail", "smtp", "pop", "ns1", "ns2",
    "vpn", "m", "mobile", "blog", "api", "dev", "staging", "test", "admin",
    "portal", "shop", "app", "cdn", "static", "secure", "login", "dashboard",
    "panel", "cpanel", "whm", "autodiscover", "autoconfig", "direct", "imap",
    "intranet", "internal", "beta", "alpha", "remote", "db", "database",
    "mysql", "sql", "support", "help", "new", "old", "demo", "cloud",
    "media", "images", "img", "video", "download", "upload", "files",
    "store", "wiki", "docs", "forum", "status", "monitor", "analytics",
    "search", "news", "git", "gitlab", "jenkins", "jira", "confluence",
    "ns3", "ns4", "mx", "mx1", "mx2", "mail1", "mail2", "cp", "webdisk",
]


def save_results(domain, resolved, output_dir="output"):
    """Sonuçları hem txt hem json olarak kaydeder"""
    import os
    from datetime import datetime
    os.makedirs(output_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    txt_path = f"{output_dir}/subdomains_{domain}_{ts}.txt"
    with open(txt_path, "w", encoding="utf-8") as f:
        for sub, ip in sorted(resolved.items()):
            f.write(f"{sub}\t{ip}\n")

    json_path = f"{output_dir}/subdomains_{domain}_{ts}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(resolved, f, ensure_ascii=False, indent=2)

    return txt_path, json_path


# ══════════════════════════════════════════
#   BAĞIMSIZ ÇALIŞTIRMA (test amaçlı)
# ══════════════════════════════════════════
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Kullanım: python3 subdomain_enum.py <domain> [wordlist_path] [--tor] [--proxy socks5://ip:port]")
        sys.exit(1)

    domain = sys.argv[1]
    wordlist_path = None
    tor = "--tor" in sys.argv
    proxy = None

    if "--proxy" in sys.argv:
        idx = sys.argv.index("--proxy")
        proxy = sys.argv[idx + 1]

    for arg in sys.argv[2:]:
        if not arg.startswith("--") and arg != proxy:
            wordlist_path = arg

    enum = SubdomainEnum(domain, threads=50, tor=tor, proxy=proxy)
    resolved = enum.run_full(wordlist_path=wordlist_path)

    if resolved:
        txt, js = save_results(domain, resolved)
        print(f"  {Colors.G}[✓] Sonuçlar kaydedildi:{Colors.RS}")
        print(f"      {Colors.Y}{txt}{Colors.RS}")
        print(f"      {Colors.Y}{js}{Colors.RS}\n")
