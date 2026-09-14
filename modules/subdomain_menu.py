#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ╔══════════════════════════════════════════════════╗
# ║   KyzerTool - Subdomain Menü Arayüzü             ║
# ║   Created by Kyzerz53                             ║
# ╚══════════════════════════════════════════════════╝
"""
Bu dosya subdomain_enum.py motorunu ana menüye bağlar.
Kullanıcıya anonim mod (Tor/Proxy) seçeneği sunar.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from modules.subdomain_enum import SubdomainEnum, save_results, Colors
from modules.network_utils import verify_connection


def ask_anonymity():
    """Kullanıcıya anonim mod tercihini sorar"""
    print(f"\n  {Colors.C}╔══════════════════════════════════════╗")
    print(f"  ║        ANONİMLİK AYARI                ║")
    print(f"  ╠══════════════════════════════════════╣")
    print(f"  ║  {Colors.W}[1]{Colors.C} Normal (anonim değil)         ║")
    print(f"  ║  {Colors.W}[2]{Colors.C} Tor üzerinden bağlan          ║")
    print(f"  ║  {Colors.W}[3]{Colors.C} Proxy listesi kullan          ║")
    print(f"  ╚══════════════════════════════════════╝{Colors.RS}")

    choice = input(f"  {Colors.C}Seçim [1]: {Colors.RS}").strip() or "1"

    tor = False
    proxy = None

    if choice == "2":
        tor = True
        print(f"  {Colors.Y}[!] Tor servisinin çalışır durumda olduğundan emin ol!{Colors.RS}")
        print(f"  {Colors.Y}[!] Kurulum: sudo apt install tor && sudo service tor start{Colors.RS}")
        verify_connection(tor=True)
    elif choice == "3":
        proxy_file = input(f"  {Colors.C}Proxy dosya yolu [config/proxies.txt]: {Colors.RS}").strip()
        proxy_file = proxy_file or "config/proxies.txt"
        try:
            with open(proxy_file, "r") as f:
                proxies = [l.strip() for l in f if l.strip() and not l.startswith("#")]
            if proxies:
                proxy = proxies[0]
                verify_connection(proxy=proxy)
            else:
                print(f"  {Colors.R}[!] Proxy listesi boş, normal modda devam ediliyor.{Colors.RS}")
        except FileNotFoundError:
            print(f"  {Colors.R}[!] Dosya bulunamadı, normal modda devam ediliyor.{Colors.RS}")

    return tor, proxy


def run_subdomain_menu():
    """Ana menüden çağrılan subdomain keşif arayüzü"""
    print(f"\n  {Colors.C}{'─'*60}{Colors.RS}")
    print(f"  {Colors.BOLD}{Colors.M}KYZER SUBFINDER{Colors.RS} {Colors.W}— by Kyzerz53{Colors.RS}")
    print(f"  {Colors.C}{'─'*60}{Colors.RS}\n")

    domain = input(f"  {Colors.C}Hedef domain (örn: example.com): {Colors.RS}").strip()
    domain = domain.replace("http://", "").replace("https://", "").split("/")[0]

    if not domain:
        print(f"  {Colors.R}[!] Geçersiz domain.{Colors.RS}")
        return

    tor, proxy = ask_anonymity()

    print(f"\n  {Colors.C}╔══════════════════════════════════════╗")
    print(f"  ║        BRUTE FORCE AYARI               ║")
    print(f"  ╠══════════════════════════════════════╣")
    print(f"  ║  {Colors.W}[1]{Colors.C} Sadece passive kaynaklar       ║")
    print(f"  ║  {Colors.W}[2]{Colors.C} Passive + varsayılan wordlist  ║")
    print(f"  ║  {Colors.W}[3]{Colors.C} Passive + kendi wordlist'im    ║")
    print(f"  ╚══════════════════════════════════════╝{Colors.RS}")

    bf_choice = input(f"  {Colors.C}Seçim [2]: {Colors.RS}").strip() or "2"

    wordlist_path = None
    do_bruteforce = True

    if bf_choice == "1":
        do_bruteforce = False
    elif bf_choice == "3":
        wordlist_path = input(f"  {Colors.C}Wordlist dosya yolu: {Colors.RS}").strip()

    threads_input = input(f"  {Colors.C}Thread sayısı [50]: {Colors.RS}").strip()
    threads = int(threads_input) if threads_input.isdigit() else 50

    enum = SubdomainEnum(domain, threads=threads, tor=tor, proxy=proxy)
    resolved = enum.run_full(wordlist_path=wordlist_path, do_bruteforce=do_bruteforce)

    if resolved:
        save = input(f"\n  {Colors.C}Sonuçları kaydet? [E/h]: {Colors.RS}").strip().lower()
        if save != "h":
            txt, js = save_results(domain, resolved)
            print(f"  {Colors.G}[✓] Kaydedildi: {Colors.Y}{txt}{Colors.RS}")
            print(f"  {Colors.G}[✓] Kaydedildi: {Colors.Y}{js}{Colors.RS}")
    else:
        print(f"  {Colors.Y}[!] Hiç subdomain bulunamadı.{Colors.RS}")


if __name__ == "__main__":
    run_subdomain_menu()
