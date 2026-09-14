"""Local-only Web Shell Lab manager for KyzerTool.

Creates a benign local PHP lab page and starts PHP's development server on
127.0.0.1 only. It is intentionally not a remote command webshell.
"""
from __future__ import annotations
import http.server
import os
import socketserver
from pathlib import Path
import threading

LAB = Path(__file__).resolve().parent.parent / "lab" / "webshell_lab"
INDEX = LAB / "index.php"


def _ensure_lab():
    LAB.mkdir(parents=True, exist_ok=True)
    INDEX.write_text('''<?php\nheader("Content-Type: text/plain; charset=utf-8");\necho "KyzerTool Web Shell LAB\\n";\necho "Bu sayfa yalnızca localhost eğitim ortamıdır.\\n";\necho "PHP sürümü: " . PHP_VERSION . "\\n";\n?>\n''', encoding="utf-8")


def run_webshell_lab():
    _ensure_lab()
    while True:
        print("\n╔══════════════════════════════════════════╗")
        print("║          WEB SHELL LAB                   ║")
        print("╠══════════════════════════════════════════╣")
        print("║ [1] Lab durumunu göster                  ║")
        print("║ [2] PHP lokal sunucuyu başlat           ║")
        print("║ [3] Lab dizinini göster                  ║")
        print("║ [0] Geri                                 ║")
        print("╚══════════════════════════════════════════╝")
        c = input("\n  [KyzerTool] > ").strip()
        if c == "0": return
        if c == "1":
            print(f"\n  [+] Lab: {LAB}")
            print(f"  [+] Test dosyası: {INDEX}")
            print("  [+] Ağ sınırı: 127.0.0.1")
            input("\n  Enter...")
        elif c == "2":
            import shutil, subprocess
            php = shutil.which("php")
            if not php:
                print("\n  [!] PHP bulunamadı.")
            else:
                print("\n  [+] Lokal lab: http://127.0.0.1:8088")
                print("  [+] Durdurmak için Ctrl+C")
                try:
                    subprocess.run([php, "-S", "127.0.0.1:8088", "-t", str(LAB)], check=False)
                except KeyboardInterrupt:
                    pass
        elif c == "3":
            print(f"\n  {LAB}")
            input("\n  Enter...")
        else:
            print("\n  [!] Geçersiz seçim!")
