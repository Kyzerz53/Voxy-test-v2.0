#!/bin/bash
echo "╔══════════════════════════════════════╗"
echo "║     KyzerTool v2 Kurulum Başlıyor    ║"
echo "╚══════════════════════════════════════╝"

if ! command -v python3 &> /dev/null; then
    echo "[!] Python3 bulunamadı, kuruluyor..."
    sudo apt-get install -y python3 python3-pip 2>/dev/null
fi

echo "[*] Gereksinimler yükleniyor..."
pip3 install -r requirements.txt -q --break-system-packages 2>/dev/null || pip3 install -r requirements.txt -q

echo "[*] İzinler ayarlanıyor..."
chmod +x kyzertool.py

echo ""
echo "[✓] Kurulum tamamlandı!"
echo "[*] Çalıştırmak için: python3 kyzertool.py"
echo ""
