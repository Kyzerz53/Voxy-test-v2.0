#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ╔══════════════════════════════════════════════════╗
# ║   KyzerTool - XSS Menü Arayüzü                   ║
# ║   Created by Kyzerz53                             ║
# ╚══════════════════════════════════════════════════╝

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from modules.xss_scanner import XSSScanner, save_results, Colors
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


def run_xss_menu():
    """Ana menüden çağrılan XSS tarama arayüzü"""
    print(f"\n  {Colors.C}{'─'*60}{Colors.RS}")
    print(f"  {Colors.BOLD}{Colors.M}KYZER XSS{Colors.RS} {Colors.W}— by Kyzerz53{Colors.RS}")
    print(f"  {Colors.C}{'─'*60}{Colors.RS}\n")

    url = input(f"  {Colors.C}Hedef URL (örn: http://site.com/page?id=1): {Colors.RS}").strip()
    if not url:
        print(f"  {Colors.R}[!] Geçersiz URL.{Colors.RS}")
        return
    if not url.startswith("http"):
        url = "http://" + url

    tor, proxy = ask_anonymity()

    print(f"\n  {Colors.C}╔══════════════════════════════════════╗")
    print(f"  ║        PAYLOAD KATEGORİSİ              ║")
    print(f"  ╠══════════════════════════════════════╣")
    print(f"  ║  {Colors.W}[1]{Colors.C} Temel payloadlar (basic)       ║")
    print(f"  ║  {Colors.W}[2]{Colors.C} WAF bypass payloadları         ║")
    print(f"  ║  {Colors.W}[3]{Colors.C} Polyglot payloadları           ║")
    print(f"  ║  {Colors.W}[4]{Colors.C} Hepsi (all) — önerilen         ║")
    print(f"  ║  {Colors.W}[5]{Colors.C} Kendi wordlist'im               ║")
    print(f"  ╚══════════════════════════════════════╝{Colors.RS}")

    cat_choice = input(f"  {Colors.C}Seçim [4]: {Colors.RS}").strip() or "4"

    category_map = {"1": "basic", "2": "waf_bypass", "3": "polyglots", "4": "all"}
    category = category_map.get(cat_choice, "all")
    custom_wordlist = None

    if cat_choice == "5":
        custom_wordlist = input(f"  {Colors.C}Wordlist dosya yolu: {Colors.RS}").strip()

    smart = input(f"\n  {Colors.C}Akıllı probe kullanılsın mı? (hızlı ama bazı zafiyetleri atlayabilir) [E/h]: {Colors.RS}").strip().lower()
    smart_probe = smart != "h"

    forms_input = input(f"  {Colors.C}Formlar da taransın mı? [E/h]: {Colors.RS}").strip().lower()
    scan_forms_flag = forms_input != "h"

    threads_input = input(f"  {Colors.C}Thread sayısı [30]: {Colors.RS}").strip()
    threads = int(threads_input) if threads_input.isdigit() else 30

    scanner = XSSScanner(url, threads=threads, tor=tor, proxy=proxy)
    findings = scanner.run_full(
        custom_wordlist=custom_wordlist,
        category=category,
        scan_forms=scan_forms_flag,
        scan_dom=True,
        smart_probe=smart_probe,
    )

    if findings or scanner.dom_findings:
        save = input(f"  {Colors.C}Sonuçları kaydet? [E/h]: {Colors.RS}").strip().lower()
        if save != "h":
            path = save_results(url, findings, scanner.dom_findings)
            print(f"  {Colors.G}[✓] Kaydedildi: {Colors.Y}{path}{Colors.RS}")


if __name__ == "__main__":
    run_xss_menu()
