<div align="center">

```
   ▄█   ▄▄▄▄███▄▄▄▄       ▄███████▄     ▄████████    ▄████████
  ███ ▄██▀▀▀███▀▀▀██▄   ██▀     ▄██   ███    ███   ███    ███
  ███ ███   ███   ███         ▄███▀   ███    █▀    ███    ███
  ███ ███   ███   ███   ▀█▀▄███▀▄▄    ███         ▄███▄▄▄▄██▀
  ███ ███   ███   ███    ▄███▀   ▀  ▀███████████ ▀▀███▀▀▀▀▀
  ███ ███   ███   ███  ▄███▀                ███ ▀███████████
  ███ ███   ███   ███ ███▄     ▄█    ▄█    ███    ███    ███
█▄ ███  ▀█   ███   █▀  ▀████████▀  ▄████████▀     ███    ███

   ▄████████    ▄██████▄     ▄██████▄   ▄█           ▄████████
  ███    ███   ███    ███   ███    ███ ███          ███    ███
  ███    ███   ███    ███   ███    ███ ███          ███    █▀
 ▄███▄▄▄▄██▀   ███    ███   ███    ███ ███          ███
▀▀███▀▀▀▀▀     ███    ███   ███    ███ ███        ▀███████████
▀███████████   ███    ███   ███    ███ ███                 ███
  ███    ███   ███    ███   ███    ███ ███▌    ▄      ▄▄    ███
  ███    ███    ▀██████▀     ▀██████▀  █████▄▄██    ▄████████▀
```

### All-In-One Web Security & Recon Framework

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-00ff41?style=for-the-badge)](LICENSE)
[![Version](https://img.shields.io/badge/Version-2.0.0-red?style=for-the-badge)]()
[![Made by](https://img.shields.io/badge/created%20by-vNez-ff00ff?style=for-the-badge)]()
[![GitHub](https://img.shields.io/badge/GitHub-Kyzerz53-black?style=for-the-badge&logo=github)](https://github.com/Kyzerz53)

*Türkçe arayüzlü, modüler, Tor/Proxy destekli açık kaynak web güvenlik ve recon çatısı.*

</div>

---

## 📦 İçerik

| # | Modül | Motor | Açıklama |
|---|-------|-------|----------|
| 1 | **KyzerXSS** | Kendi motoru | Canary-probe + context-farkında reflected XSS, form taraması, DOM sink tespiti |
| 2 | SQL Injection | Kendi motoru | Error-based SQLi tespiti |
| 3 | LFI | Kendi motoru | Local File Inclusion, path traversal |
| 4 | SSRF | Kendi motoru | Server-Side Request Forgery |
| 5 | Open Redirect | Kendi motoru | Açık yönlendirme zafiyeti |
| 6 | CRLF Injection | Kendi motoru | HTTP header enjeksiyonu |
| 7 | **KyzerSubfinder** | Hibrit | Passive (crt.sh, Wayback, AlienVault OTX, RapidDNS, CertSpotter, HackerTarget) + Active DNS brute force |
| 8 | **KyzerNmap** | Hibrit | Gerçek `nmap` (varsa) + kendi Python TCP-connect/banner-grab motoru |
| 9 | Directory Bruteforce | Kendi motoru | Gizli dizin/dosya keşfi |
| 10 | DNS & Whois | Kendi motoru | DNS kayıtları, whois sorgulama |
| ⭐ 11 | **Tam Tarama** | — | Tüm modülleri sırayla otomatik çalıştırır |

## 🧠 Neden "Hibrit" Motor?

KyzerSubfinder ve KyzerNmap, sıfırdan yeniden icat etmek yerine **sektörün en iyi açık kaynak araçlarının mantığını** temel alır:

- **Subdomain keşfi**, [ProjectDiscovery/subfinder](https://github.com/projectdiscovery/subfinder)'ın passive-source + active-bruteforce yaklaşımından ilham alır.
- **Port tarama**, sistemde kuruluysa gerçek **nmap** binary'sini doğrudan çalıştırır (SYN scan, `-sV` versiyon tespiti, NSE scriptleri dahil endüstri standardı tüm güç elinizde). Nmap yoksa devreye Kyzer'in kendi Python tabanlı TCP-connect + banner-grabbing motoru girer.

Bu sayede hem güç hem taşınabilirlik (nmap kurulu olmayan ortamlarda bile çalışma) garanti edilir.

## 🕵️ Anonimlik: Tor & Proxy Desteği

Her modülde **Tor** veya **SOCKS5 Proxy** üzerinden bağlanma seçeneği vardır. Tool, seçtiğiniz modun **gerçekten çalışıp çalışmadığını canlı olarak doğrular**:

```
[*] TOR bağlantısı test ediliyor...
[🧅 TOR BAĞLANTISI BAŞARILI] Çıkış IP: 185.220.101.45
[✓] Tüm istekler artık Tor ağı üzerinden gönderilecek.
```

Bağlantı başarısız olursa (Tor servisi kapalıysa vb.) bu **açıkça** gösterilir, sessizce normal bağlantıya düşülmez:

```
[✗ TOR BAĞLANTISI BAŞARISIZ]
[!] Hata: Connection refused
[!] Tor servisi çalışmıyor olabilir. Kontrol et: sudo service tor start
```

> **Not:** Ham port taraması (nmap SYN scan) Tor SOCKS5 üzerinden native çalışmaz. Anonim port taraması için KyzerNmap'in "Kyzer Motoru" seçeneğini Tor ile kullanın.

## 📚 Payload Kütüphanesi

`payloads/` klasörü, kendi yazdığımız payloadlara ek olarak **[coffinxp/payloads](https://github.com/coffinxp/payloads)** reposundan derlenmiş **81.000+ satır** teknik payload/wordlist içerir:

```
payloads/
├── xss/        (2765 payload — basic, WAF bypass, polyglot)
├── sqli/       (error-based, blind, union-based)
├── lfi/        (traversal + 70K+ hassas dosya yolu)
├── ssrf/       (cloud metadata, internal IP payloadları)
├── crlf/       (header injection)
├── dirbrute/   (admin, config, backup, juicy paths...)
├── bypass403/  (403 bypass header/url teknikleri)
├── ssti/       (Server-Side Template Injection — yakında)
├── xxe/        (XML External Entity — yakında)
├── jwt/        (JWT zayıf secret listesi — yakında)
└── osint/      (GitHub dork listesi — yakında)
```

## ⚙️ Kurulum

```bash
git clone https://github.com/Kyzerz53/KyzerTool
cd KyzerTool
pip3 install -r requirements.txt --break-system-packages
python3 kyzertool.py
```

**Gerçek nmap için (opsiyonel ama önerilir):**
```bash
sudo apt install nmap
```

**Tor desteği için (opsiyonel):**
```bash
sudo apt install tor
sudo service tor start
```

## 🖥️ Kullanım

```bash
python3 kyzertool.py
```

Menüden istediğin modülü seç, hedefi gir. Her modül kendi interaktif alt menüsünü sunar (anonimlik ayarı, payload kategorisi, thread sayısı vb.).

## ⚠️ Yasal Uyarı

> Bu araç **yalnızca eğitim amaçlı** ve **yazılı izniniz olan sistemlerde** kullanım içindir. İzinsiz sistemlere karşı kullanmak birçok ülkede suçtur (TR: TCK madde 243-245). Tüm sorumluluk kullanıcıya aittir. Geliştirici (vNez / Kyzerz53) herhangi bir kötüye kullanımdan sorumlu tutulamaz.

## 🗺️ Yol Haritası (Roadmap)

- [x] KyzerXSS (context-aware detection)
- [x] KyzerSubfinder (passive + active)
- [x] KyzerNmap (real nmap + fallback)
- [x] Tor/Proxy canlı doğrulama
- [ ] SSTI / XXE / JWT modülleri
- [ ] Gelişmiş OSINT modülü (Shodan, Censys, Wayback entegrasyonu)
- [ ] HTML/PDF rapor çıktısı

## 👤 Geliştirici

**vNez** — Bug Bounty Hunter & Security Researcher
**GitHub:** [Kyzerz53](https://github.com/Kyzerz53)

---

<div align="center">
<sub>Payload katkısı: <a href="https://github.com/coffinxp/payloads">coffinxp/payloads</a> · Made with 🧠 by vNez</sub>
</div>
