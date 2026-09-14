#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ╔══════════════════════════════════════════════════╗
# ║   KyzerTool - Port Tarama Menü Arayüzü           ║
# ║   Created by Kyzerz53                             ║
# ╚══════════════════════════════════════════════════╝

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from modules.port_scanner import RealNmapScanner, KyzerPortScanner, get_nmap_path, save_results, Colors
from modules import network_utils


def run_port_menu():
    print(f"\n  {Colors.C}{'─'*60}{Colors.RS}")
    print(f"  {Colors.BOLD}{Colors.M}KYZER NMAP{Colors.RS} {Colors.W}— by Kyzerz53{Colors.RS}")
    print(f"  {Colors.C}{'─'*60}{Colors.RS}\n")

    target = input(f"  {Colors.C}Hedef (IP veya domain, örn: example.com): {Colors.RS}").strip()
    target = target.replace("http://", "").replace("https://", "").split("/")[0]

    if not target:
        print(f"  {Colors.R}[!] Geçersiz hedef.{Colors.RS}")
        return

    nmap_path = get_nmap_path()

    if nmap_path:
        print(f"\n  {Colors.G}[✓] Sistemde nmap tespit edildi: {nmap_path}{Colors.RS}")
    else:
        print(f"\n  {Colors.Y}[!] Sistemde nmap bulunamadı. Kyzer'in kendi Python motoru kullanılacak.{Colors.RS}")
        print(f"  {Colors.Y}    (Nmap kurmak için: sudo apt install nmap){Colors.RS}")

    print(f"\n  {Colors.C}╔══════════════════════════════════════════╗")
    print(f"  ║        TARAMA MOTORU                       ║")
    print(f"  ╠══════════════════════════════════════════╣")
    if nmap_path:
        print(f"  ║  {Colors.W}[1]{Colors.C} Gerçek Nmap (önerilen, güçlü)          ║")
        print(f"  ║  {Colors.W}[2]{Colors.C} Kyzer Motoru (Python, Tor destekli)    ║")
    else:
        print(f"  ║  {Colors.W}[1]{Colors.C} Kyzer Motoru (tek seçenek, nmap yok)   ║")
    print(f"  ╚══════════════════════════════════════════╝{Colors.RS}")

    engine_choice = input(f"  {Colors.C}Seçim [1]: {Colors.RS}").strip() or "1"

    use_real_nmap = nmap_path and engine_choice == "1"

    # ═══ Anonimlik notu ═══
    tor = False
    proxy = None

    if not use_real_nmap:
        print(f"\n  {Colors.C}╔══════════════════════════════════════╗")
        print(f"  ║        ANONİMLİK AYARI                ║")
        print(f"  ╠══════════════════════════════════════╣")
        print(f"  ║  {Colors.W}[1]{Colors.C} Normal (anonim değil)         ║")
        print(f"  ║  {Colors.W}[2]{Colors.C} Tor üzerinden bağlan (yavaş)  ║")
        print(f"  ║  {Colors.W}[3]{Colors.C} SOCKS5 Proxy kullan           ║")
        print(f"  ╚══════════════════════════════════════╝{Colors.RS}")
        print(f"  {Colors.Y}[!] Not: Ham port taraması Tor üzerinden ÇOK YAVAŞTIR{Colors.RS}")
        print(f"  {Colors.Y}    (her port için ayrı Tor devresi kurulur). Az port önerilir.{Colors.RS}")

        anon_choice = input(f"  {Colors.C}Seçim [1]: {Colors.RS}").strip() or "1"

        if anon_choice == "2":
            tor = True
            # Gerçek bağlantı testi - kullanıcı Tor'un çalışıp çalışmadığını görsün
            ok, _, _ = network_utils.display_anonymity_status(tor=True)
            if not ok:
                return
        elif anon_choice == "3":
            proxy = input(f"  {Colors.C}SOCKS5 proxy (örn: socks5://127.0.0.1:1080): {Colors.RS}").strip()
    else:
        print(f"\n  {Colors.Y}[!] Not: Gerçek nmap'in ham SYN/TCP taraması Tor SOCKS5 üzerinden{Colors.RS}")
        print(f"  {Colors.Y}    native çalışmaz (proxychains gerektirir). Anonim taramak için{Colors.RS}")
        print(f"  {Colors.Y}    'Kyzer Motoru'nu Tor seçeneğiyle kullanmanız önerilir.{Colors.RS}")

    # ═══ Tarama modu ═══
    if use_real_nmap:
        print(f"\n  {Colors.C}╔══════════════════════════════════════════╗")
        print(f"  ║        NMAP TARAMA MODU                    ║")
        print(f"  ╠══════════════════════════════════════════╣")
        for key, preset in RealNmapScanner.PRESETS.items():
            print(f"  ║  {Colors.W}[{key}]{Colors.C} {preset['name']:<38}║")
        print(f"  ╚══════════════════════════════════════════╝{Colors.RS}")

        preset = input(f"  {Colors.C}Seçim [2]: {Colors.RS}").strip() or "2"

        scanner = RealNmapScanner(target)
        result = scanner.run(preset=preset)

        if result:
            save = input(f"  {Colors.C}Sonuçları kaydet? [E/h]: {Colors.RS}").strip().lower()
            if save != "h":
                path = save_results(target, result, "nmap")
                print(f"  {Colors.G}[✓] Kaydedildi: {Colors.Y}{path}{Colors.RS}")

    else:
        print(f"\n  {Colors.C}╔══════════════════════════════════════════╗")
        print(f"  ║        PORT ARALIĞI                        ║")
        print(f"  ╠══════════════════════════════════════════╣")
        print(f"  ║  {Colors.W}[1]{Colors.C} Yaygın portlar (~55 port, hızlı)       ║")
        print(f"  ║  {Colors.W}[2]{Colors.C} Top 1024 port                          ║")
        print(f"  ║  {Colors.W}[3]{Colors.C} Tüm portlar (1-65535, çok yavaş)       ║")
        print(f"  ║  {Colors.W}[4]{Colors.C} Özel aralık (örn: 1-500)               ║")
        print(f"  ╚══════════════════════════════════════════╝{Colors.RS}")

        range_choice = input(f"  {Colors.C}Seçim [1]: {Colors.RS}").strip() or "1"
        range_map = {"1": "common", "2": "top1000", "3": "full"}
        port_range = range_map.get(range_choice, "common")

        if range_choice == "4":
            port_range = input(f"  {Colors.C}Aralık (örn: 1-500): {Colors.RS}").strip() or "1-1024"

        threads_input = input(f"  {Colors.C}Thread sayısı [200]: {Colors.RS}").strip()
        threads = int(threads_input) if threads_input.isdigit() else 200

        scanner = KyzerPortScanner(target, threads=threads, tor=tor, proxy=proxy)
        result = scanner.run(port_range=port_range)

        if result:
            save = input(f"  {Colors.C}Sonuçları kaydet? [E/h]: {Colors.RS}").strip().lower()
            if save != "h":
                path = save_results(target, result, "kyzer")
                print(f"  {Colors.G}[✓] Kaydedildi: {Colors.Y}{path}{Colors.RS}")


if __name__ == "__main__":
    run_port_menu()
