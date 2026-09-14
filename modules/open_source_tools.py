"""KyzerTool Open Source Tools manager.

This module deliberately does not reimplement or silently deploy webshells.
It discovers user-installed upstream projects and launches them as external
programs, while keeping KyzerTool's Turkish management UI separate.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

TOOLS = {
    "1": {
        "name": "Weevely",
        "repo": "https://github.com/epinna/weevely3",
        "commands": ["weevely"],
        "hints": ["weevely", "weevely.py"],
    },
    "2": {
        "name": "AntSword",
        "repo": "https://github.com/AntSwordProject/antSword",
        "commands": [],
        "hints": ["AntSword", "antsword"],
    },
    "3": {
        "name": "EtherGhost",
        "repo": "https://github.com/Marven11/EtherGhost",
        "commands": [],
        "hints": ["EtherGhost", "etherghost"],
    },
}


def _clear():
    os.system("cls" if os.name == "nt" else "clear")


def _find_tool(tool):
    for cmd in tool["commands"]:
        path = shutil.which(cmd)
        if path:
            return path
    roots = [Path.cwd(), Path.home() / "tools", Path.home() / "Tools"]
    for root in roots:
        if not root.exists():
            continue
        for hint in tool["hints"]:
            matches = list(root.glob(f"**/{hint}"))[:3]
            if matches:
                return str(matches[0])
    return None


def _run(path):
    if not path:
        return
    p = Path(path)
    try:
        if p.suffix == ".py":
            subprocess.run([sys.executable, str(p)], check=False)
        else:
            subprocess.run([str(p)], check=False)
    except OSError as exc:
        print(f"\n[!] Başlatılamadı: {exc}")


def status():
    print("\n  ARAÇ DURUMU\n  " + "─" * 46)
    for key, tool in TOOLS.items():
        found = _find_tool(tool)
        if found:
            print(f"  [{key}] {tool['name']:<12} [✓] {found}")
        else:
            print(f"  [{key}] {tool['name']:<12} [!] Kurulum bulunamadı")
    print()


def dependencies():
    print("\n  BAĞIMLILIK KONTROLÜ\n  " + "─" * 46)
    checks = [("Python", "python3"), ("Git", "git"), ("Node.js", "node"), ("npm", "npm")]
    for label, cmd in checks:
        found = shutil.which(cmd)
        print(f"  {label:<12} [{'✓' if found else '!'}] {found or 'bulunamadı'}")
    print()


def _tool_menu(key):
    tool = TOOLS[key]
    while True:
        _clear()
        print("╔══════════════════════════════════════════╗")
        print(f"║ {tool['name']:^40} ║")
        print("╠══════════════════════════════════════════╣")
        print("║ [1] Durumu kontrol et                    ║")
        print("║ [2] Kurulu aracı başlat                  ║")
        print("║ [3] Resmî açık kaynak deposu             ║")
        print("║ [0] Geri                                  ║")
        print("╚══════════════════════════════════════════╝")
        choice = input("\n  [KyzerTool] > ").strip()
        if choice == "0":
            return
        if choice == "1":
            path = _find_tool(tool)
            print(f"\n  {'[✓] '+path if path else '[!] Kurulum bulunamadı'}")
            input("\n  Enter...")
        elif choice == "2":
            path = _find_tool(tool)
            if not path:
                print("\n  [!] Araç bulunamadı. Önce upstream projeyi kendi lab ortamında kur.")
            else:
                print(f"\n  [+] Başlatılıyor: {path}\n")
                _run(path)
            input("\n  Enter...")
        elif choice == "3":
            print(f"\n  {tool['repo']}")
            input("\n  Enter...")


def run_open_source_tools():
    while True:
        _clear()
        print("╔══════════════════════════════════════════╗")
        print("║        OPEN SOURCE TOOLS                 ║")
        print("╠══════════════════════════════════════════╣")
        print("║ [1] Weevely                               ║")
        print("║ [2] AntSword                              ║")
        print("║ [3] EtherGhost                            ║")
        print("║ [4] WebShell Lab                          ║")
        print("║ [5] Tool Status                            ║")
        print("║ [6] Dependency Check                      ║")
        print("║ [0] Geri                                   ║")
        print("╚══════════════════════════════════════════╝")
        choice = input("\n  [KyzerTool] > ").strip()
        if choice == "0":
            return
        if choice in TOOLS:
            _tool_menu(choice)
        elif choice == "4":
            try:
                from modules.webshell_lab import run_webshell_lab
                run_webshell_lab()
            except ImportError:
                print("\n  [!] Web Shell Lab modülü bulunamadı.")
                input("\n  Enter...")
        elif choice == "5":
            _clear(); status(); input("  Enter...")
        elif choice == "6":
            _clear(); dependencies(); input("  Enter...")
        else:
            print("\n  [!] Geçersiz seçim!")
