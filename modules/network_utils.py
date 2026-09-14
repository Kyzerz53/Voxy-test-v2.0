#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ╔══════════════════════════════════════════════════╗
# ║   KyzerTool - Ağ Yardımcı Modülü                 ║
# ║   Tor / Proxy destekli session yönetimi          ║
# ║   Created by Kyzerz53                             ║
# ╚══════════════════════════════════════════════════╝

import requests
import random

requests.packages.urllib3.disable_warnings()


class Colors:
    R    = '\033[91m'
    G    = '\033[92m'
    Y    = '\033[93m'
    C    = '\033[96m'
    M    = '\033[95m'
    W    = '\033[97m'
    BOLD = '\033[1m'
    RS   = '\033[0m'


USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]


def get_random_ua():
    return random.choice(USER_AGENTS)


def get_session(proxy=None, tor=False, random_ua=False):
    """
    Proxy veya Tor destekli requests.Session döndürür.

    proxy: "http://ip:port" veya "socks5://ip:port" formatında tekil proxy
    tor:   True ise 127.0.0.1:9050 üzerinden Tor SOCKS5 kullanılır
    """
    session = requests.Session()
    session.headers.update({
        "User-Agent": get_random_ua() if random_ua else USER_AGENTS[0],
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
    })

    if tor:
        session.proxies = {
            "http": "socks5h://127.0.0.1:9050",
            "https": "socks5h://127.0.0.1:9050",
        }
    elif proxy:
        session.proxies = {"http": proxy, "https": proxy}

    return session


def load_proxy_list(path):
    """Proxy dosyasından listeyi okur (# ile başlayan satırlar yorumdur)"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip() and not line.startswith("#")]
    except FileNotFoundError:
        return []


def get_rotating_session(proxy_list, random_ua=True):
    """Proxy listesinden rastgele biri seçilip session oluşturulur (rotasyon)"""
    proxy = random.choice(proxy_list) if proxy_list else None
    return get_session(proxy=proxy, random_ua=random_ua)


def _fetch_exit_ip(session, timeout=10):
    """Birden fazla IP-doğrulama servisi dener, ilkinden sonuç alan döner"""
    for url in ("https://api.ipify.org?format=json", "https://ifconfig.me/ip", "https://icanhazip.com"):
        try:
            r = session.get(url, timeout=timeout, verify=False)
            if r.status_code == 200:
                try:
                    return r.json().get("ip", r.text.strip())
                except Exception:
                    return r.text.strip()
        except Exception:
            continue
    return None


def verify_connection(tor=False, proxy=None, timeout=10, verbose=True):
    """
    Bağlantının GERÇEKTEN Tor/Proxy üzerinden gidip gitmediğini doğrular
    ve kullanıcıya net biçimde gösterir. Her modül (subdomain, XSS, SQLi,
    port, dizin, DNS...) taramaya başlamadan önce bunu çağırmalı, böylece
    kullanıcı isteklerinin gerçekten anonim gittiğini veya bağlantının
    başarısız olduğunu anında görür.

    Döndürür: (basarili: bool, ip: str|None)
    """
    if not tor and not proxy:
        if verbose:
            print(f"  {Colors.W}[i] Normal bağlantı kullanılıyor (anonim mod kapalı).{Colors.RS}")
        return True, None

    mode = "TOR" if tor else f"PROXY ({proxy})"
    if verbose:
        print(f"  {Colors.C}[*] {mode} bağlantısı doğrulanıyor, lütfen bekleyin...{Colors.RS}")

    session = get_session(proxy=proxy, tor=tor)

    if tor:
        try:
            r = session.get("https://check.torproject.org/api/ip", timeout=timeout, verify=False)
            data = r.json()
            is_tor = data.get("IsTor", False)
            ip = data.get("IP", "bilinmiyor")

            if is_tor:
                if verbose:
                    print(f"  {Colors.BOLD}{Colors.G}[✓ TOR AKTİF]{Colors.RS} {Colors.W}İstekleriniz Tor ağı üzerinden gidiyor.{Colors.RS}")
                    print(f"  {Colors.G}    Çıkış IP (gerçek IP'niz değil): {ip}{Colors.RS}")
                return True, ip
            else:
                if verbose:
                    print(f"  {Colors.BOLD}{Colors.R}[✗ TOR ÇALIŞMIYOR]{Colors.RS} {Colors.Y}İstek Tor üzerinden GİTMİYOR!{Colors.RS}")
                    print(f"  {Colors.Y}    Tespit edilen IP: {ip} (gerçek IP'niz olabilir!){Colors.RS}")
                    print(f"  {Colors.Y}    Kontrol edin: 'sudo service tor start' veya Tor Browser'ı açık tutun.{Colors.RS}")
                return False, ip
        except Exception as e:
            # check.torproject.org'a ulaşılamazsa, exit-IP'yi genel bir servisten dene
            ip = _fetch_exit_ip(session, timeout=timeout)
            if ip:
                if verbose:
                    print(f"  {Colors.Y}[~] Tor doğrulama servisine ulaşılamadı ama bağlantı proxy üzerinden gidiyor.{Colors.RS}")
                    print(f"  {Colors.Y}    Çıkış IP: {ip} (Tor olup olmadığı doğrulanamadı){Colors.RS}")
                return True, ip
            if verbose:
                print(f"  {Colors.BOLD}{Colors.R}[✗ TOR BAĞLANTI HATASI]{Colors.RS} {Colors.Y}{e}{Colors.RS}")
                print(f"  {Colors.Y}    Tor servisi çalışmıyor olabilir (varsayılan port: 9050).{Colors.RS}")
                print(f"  {Colors.Y}    Kurulum: sudo apt install tor && sudo service tor start{Colors.RS}")
            return False, None

    elif proxy:
        ip = _fetch_exit_ip(session, timeout=timeout)
        if ip:
            if verbose:
                print(f"  {Colors.BOLD}{Colors.G}[✓ PROXY AKTİF]{Colors.RS} {Colors.W}İstekleriniz proxy üzerinden gidiyor.{Colors.RS}")
                print(f"  {Colors.G}    Çıkış IP: {ip}{Colors.RS}")
            return True, ip
        else:
            if verbose:
                print(f"  {Colors.BOLD}{Colors.R}[✗ PROXY BAĞLANTI HATASI]{Colors.RS} {Colors.Y}Proxy'ye erişilemiyor: {proxy}{Colors.RS}")
                print(f"  {Colors.Y}    Normal bağlantıyla devam edilecek, DİKKAT: anonim DEĞİLSİNİZ.{Colors.RS}")
            return False, None

    return False, None


def check_target_reachable(session, url, label="Hedef"):
    """
    Hedefe seçili bağlantı modu (Tor/Proxy/Normal) üzerinden gerçekten
    ulaşılabiliyor mu kontrol eder. Ulaşılamıyorsa net biçimde bildirir.
    Bazı hedefler Tor çıkış node'larını engelleyebilir; bu fonksiyon
    kullanıcının bunu erkenden fark etmesini sağlar.
    """
    try:
        r = session.get(url, timeout=15, verify=False)
        print(f"  {Colors.G}[✓] {label} ulaşılabilir durumda.{Colors.RS} (HTTP {r.status_code})")
        return True
    except Exception as e:
        print(f"  {Colors.R}[✗] {label} bu bağlantı üzerinden ULAŞILAMIYOR!{Colors.RS}")
        print(f"  {Colors.R}    Hata: {e}{Colors.RS}")
        print(f"  {Colors.Y}    (Bazı siteler Tor çıkış node'larını engelliyor olabilir){Colors.RS}")
        return False
