#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ╔══════════════════════════════════════════════════╗
# ║   KyzerTool - XSS Tarama Motoru                  ║
# ║   Wordlist tabanlı, context-farkında, DOM sink   ║
# ║   Created by Kyzerz53                             ║
# ╚══════════════════════════════════════════════════╝
"""
KyzerXSS - Reflected & DOM-based XSS tespit motoru

Yaklaşım:
  1. CANARY PROBE: Her parametreye benzersiz rastgele bir iz (canary) enjekte
     edilir. Cevapta bu iz nerede, nasıl (encode edilmiş mi, ham mı) döndüğü
     analiz edilir. Bu, gerçek payload denemeden önce "burası enjekte edilebilir mi?"
     sorusuna hızlı cevap verir (subfinder'daki passive/active ayrımına benzer:
     önce keşif, sonra doğrulama).
  2. PAYLOAD DOĞRULAMA: Canary reflection bulunan noktalara wordlist'ten
     gerçek payloadlar denenir. Payload'ın response içinde HTML-encode
     EDİLMEDEN (ham haliyle) döndüğü durumlar zafiyet olarak işaretlenir.
  3. DOM SINK TARAMASI: Sayfa kaynağında innerHTML, document.write, eval
     gibi tehlikeli JS sink'leri aranır (DOM-based XSS'e potansiyel giriş
     noktaları olarak bilgilendirme amaçlı raporlanır).
"""

import os
import re
import glob
import random
import string
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin, urlparse, quote, parse_qs, urlencode

try:
    from bs4 import BeautifulSoup
except ImportError:
    os.system("pip install beautifulsoup4 -q --break-system-packages")
    from bs4 import BeautifulSoup

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from network_utils import get_session


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


# DOM-based XSS'e sebep olabilecek tehlikeli JS sink'leri
DOM_SINKS = [
    "document.write(", "document.writeln(",
    "innerHTML", "outerHTML",
    "eval(", "setTimeout(", "setInterval(",
    "location.hash", "location.href", "location.search",
    "document.URL", "document.referrer", "document.cookie",
    "window.name", "postMessage",
    "$(location).", ".html(", "dangerouslySetInnerHTML",
    "insertAdjacentHTML", "Function(",
]

PAYLOAD_DIR_DEFAULT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "payloads", "xss")


class XSSScanner:
    """
    Kyzerz53 tarafından geliştirilmiş XSS tarama motoru.
    Ayrı payload dosyalarından (payloads/xss/*.txt) veya kullanıcı
    wordlist'inden payload okuyarak reflected XSS + DOM sink taraması yapar.
    """

    def __init__(self, url, threads=30, timeout=10, proxy=None, tor=False, verbose=True):
        self.url = url
        self.threads = threads
        self.timeout = timeout
        self.session = get_session(proxy=proxy, tor=tor, random_ua=True)
        self.verbose = verbose
        self.findings = []
        self.dom_findings = []
        self.lock = threading.Lock()

    def log(self, msg, tag="*", color=Colors.C):
        if self.verbose:
            print(f"  {color}[{tag}]{Colors.RS} {msg}")

    def vuln_log(self, msg):
        with self.lock:
            print(f"  {Colors.R}{Colors.BOLD}[ZAFİYET]{Colors.RS} {Colors.G}{msg}{Colors.RS}")

    def info_log(self, msg):
        with self.lock:
            print(f"  {Colors.M}[BİLGİ]{Colors.RS} {Colors.W}{msg}{Colors.RS}")

    # ══════════════════════════════════════
    #        PAYLOAD YÜKLEME
    # ══════════════════════════════════════

    @staticmethod
    def load_payloads(payload_files=None, custom_wordlist=None, category="all"):
        """
        payloads/xss/ klasöründeki dosyalardan veya kullanıcı wordlist'inden
        payload listesi oluşturur.

        category: "all", "basic", "waf_bypass", "polyglots"
        """
        payloads = []

        if custom_wordlist:
            try:
                with open(custom_wordlist, "r", encoding="utf-8", errors="ignore") as f:
                    payloads = [line.rstrip("\n") for line in f if line.strip() and not line.startswith("#")]
                return payloads
            except FileNotFoundError:
                return []

        if payload_files:
            files = payload_files
        else:
            if category == "all":
                files = glob.glob(os.path.join(PAYLOAD_DIR_DEFAULT, "*.txt"))
            else:
                files = [os.path.join(PAYLOAD_DIR_DEFAULT, f"{category}.txt")]

        for fpath in files:
            try:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        line = line.rstrip("\n")
                        if line.strip() and not line.startswith("#"):
                            payloads.append(line)
            except FileNotFoundError:
                continue

        # Tekrarları temizle, sırayı koru
        seen = set()
        unique = []
        for p in payloads:
            if p not in seen:
                seen.add(p)
                unique.append(p)
        return unique

    # ══════════════════════════════════════
    #        CANARY (İZ SÜRME) PROBE
    # ══════════════════════════════════════

    @staticmethod
    def generate_canary():
        """Her test için benzersiz, tahmin edilemez bir iz üretir"""
        rand = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        return f"kyz{rand}xss"

    def probe_reflection(self, param, base_url):
        """
        Bir parametreye canary enjekte edip nasıl yansıdığını analiz eder.
        Döndürür: (yansıyor_mu, encode_edilmis_mi, context_snippet)
        """
        canary = self.generate_canary()
        test_marker = f"<{canary}>"

        test_url = re.sub(
            rf'([?&]{re.escape(param)}=)[^&]*',
            rf'\g<1>{quote(test_marker)}',
            base_url
        )

        try:
            r = self.session.get(test_url, timeout=self.timeout, verify=False)
            body = r.text

            if canary not in body:
                return False, None, None

            # Ham (encode edilmemiş) mi yansıyor kontrolü
            raw_reflected = test_marker in body
            encoded_reflected = f"&lt;{canary}&gt;" in body

            # Context snippet al (canary çevresi 40 karakter)
            idx = body.find(canary)
            start = max(0, idx - 30)
            end = min(len(body), idx + 30)
            snippet = body[start:end].replace("\n", " ")

            return True, (raw_reflected and not encoded_reflected), snippet

        except Exception:
            return False, None, None

    # ══════════════════════════════════════
    #        PAYLOAD DOĞRULAMA (URL param)
    # ══════════════════════════════════════

    # ══════════════════════════════════════
    #        CONTEXT SINIFLANDIRMA
    # ══════════════════════════════════════

    @staticmethod
    def classify_confidence(body, payload, idx):
        """
        Bir payload'ın gerçekten çalışabilir olup olmadığını context'e göre
        değerlendirir. Ham reflection tek başına yeterli değildir:
          - <script>, <img onerror=...> gibi tag-tabanlı payloadlar HTML body
            içinde herhangi bir yerde bulunursa YÜKSEK güvenilirlik.
          - "javascript:" şemalı payloadlar SADECE bir href=/src=/action=
            attribute değeri olarak yer alıyorsa çalışır; düz metinse ÇALIŞMAZ.
          - Tırnak kaçışlı payloadlar ('-alert(1)-' gibi) sadece <script> bloğu
            içinde veya bir attribute değeri içindeyse anlamlıdır.
        Döndürür: "Yüksek", "Orta" veya "Düşük"
        """
        payload_stripped = payload.strip()

        # 1) Tag tabanlı payload (< ile başlıyor) → HTML body'de her zaman tehlikeli
        if payload_stripped.startswith("<"):
            return "Yüksek"

        # 2) javascript: şeması → sadece attribute içindeyse geçerli
        if payload_stripped.lower().startswith("javascript:"):
            before = body[max(0, idx - 15):idx]
            if re.search(r'(href|src|action|formaction|data)\s*=\s*["\']?$', before, re.IGNORECASE):
                return "Yüksek"
            return "Düşük (düz metin olarak yansıyor, çalışmaz)"

        # 3) Tırnak kaçışlı / script breakout payloadlar
        if any(payload_stripped.startswith(p) for p in ["'", '"', "';", '";']) or \
           any(tok in payload_stripped for tok in ["alert(", "confirm(", "prompt("]):
            # <script> bloğu içinde mi kontrol et
            script_start = body.rfind("<script", 0, idx)
            script_end = body.find("</script>", script_start) if script_start != -1 else -1
            if script_start != -1 and (script_end == -1 or idx < script_end):
                return "Yüksek"

            # Attribute değeri içinde mi kontrol et (tırnak hemen öncesinde mi)
            before = body[max(0, idx - 5):idx]
            if re.search(r'=["\']$', before):
                return "Orta"

            return "Düşük (JS/attribute context dışında, muhtemelen çalışmaz)"

        return "Orta"

    def test_payload_on_param(self, param, payload, base_url):
        """Tek bir payload'ı tek bir parametrede dener"""
        test_url = re.sub(
            rf'([?&]{re.escape(param)}=)[^&]*',
            rf'\g<1>{quote(payload)}',
            base_url
        )

        try:
            r = self.session.get(test_url, timeout=self.timeout, verify=False)
            body = r.text

            # Payload ham haliyle (HTML-encode edilmeden) döndü mü?
            if payload in body:
                idx = body.find(payload)
                start = max(0, idx - 25)
                end = min(len(body), idx + len(payload) + 25)
                snippet = body[start:end].replace("\n", " ")

                confidence = self.classify_confidence(body, payload, idx)

                # "Düşük" güven seviyesindekiler gerçek zafiyet olarak sayılmaz
                if confidence.startswith("Düşük"):
                    return None

                finding = {
                    "type": "Reflected XSS",
                    "param": param,
                    "payload": payload,
                    "url": test_url,
                    "context": snippet,
                    "confidence": confidence,
                }
                with self.lock:
                    self.findings.append(finding)
                self.vuln_log(f"[{confidence}] Param: {Colors.Y}{param}{Colors.RS} | Payload: {Colors.Y}{payload[:50]}{Colors.RS}")
                return finding
        except Exception:
            pass
        return None

    def scan_url_params(self, custom_wordlist=None, category="all", smart_probe=True):
        """
        URL'deki tüm parametreleri XSS için tarar.
        smart_probe=True ise önce canary ile reflection var mı bakılır,
        yoksa o parametre için payload denemesi atlanır (hız optimizasyonu).
        """
        params = re.findall(r'[?&]([^=&]+)=', self.url)

        if not params:
            self.log("URL'de test edilecek parametre bulunamadı. (örn: ?id=1)", "!", Colors.Y)
            return []

        self.log(f"Bulunan parametreler: {', '.join(params)}", "*", Colors.C)

        payloads = self.load_payloads(custom_wordlist=custom_wordlist, category=category)
        self.log(f"{len(payloads)} payload yüklendi (kategori: {category})", "*", Colors.C)

        testable_params = []

        if smart_probe:
            self.log("Canary probe ile reflection noktaları taranıyor...", "*", Colors.C)
            for param in params:
                reflects, is_raw, snippet = self.probe_reflection(param, self.url)
                if reflects:
                    status = f"{Colors.G}HAM (encode edilmemiş){Colors.RS}" if is_raw else f"{Colors.Y}encode edilmiş{Colors.RS}"
                    self.info_log(f"'{param}' parametresi yansıyor → {status}")
                    if is_raw:
                        testable_params.append(param)
                else:
                    self.log(f"'{param}' parametresi yansımıyor, atlanıyor.", "-", Colors.W)
        else:
            testable_params = params

        if not testable_params:
            self.log("Ham yansıma bulunan parametre yok. Yine de tüm parametreler tam payload seti ile deneniyor...", "!", Colors.Y)
            testable_params = params

        self.log(f"{len(testable_params)} parametre × {len(payloads)} payload test ediliyor ({self.threads} thread)...", "*", Colors.C)

        with ThreadPoolExecutor(max_workers=self.threads) as ex:
            futures = []
            for param in testable_params:
                for payload in payloads:
                    futures.append(ex.submit(self.test_payload_on_param, param, payload, self.url))
            for _ in as_completed(futures):
                pass

        return self.findings

    # ══════════════════════════════════════
    #        FORM TABANLI XSS
    # ══════════════════════════════════════

    def scan_forms(self, custom_wordlist=None, category="all"):
        """Sayfadaki HTML formlarını bulur ve her input'a payload dener"""
        try:
            r = self.session.get(self.url, timeout=self.timeout, verify=False)
            soup = BeautifulSoup(r.text, "html.parser")
            forms = soup.find_all("form")
        except Exception as e:
            self.log(f"Sayfa alınamadı: {e}", "!", Colors.R)
            return []

        if not forms:
            self.log("Sayfada form bulunamadı.", "*", Colors.C)
            return []

        self.log(f"{len(forms)} form bulundu, taranıyor...", "*", Colors.C)
        payloads = self.load_payloads(custom_wordlist=custom_wordlist, category=category)

        # Formlarda payload sayısını sınırla (form testleri POST/GET karışık, çok yavaş olabilir)
        test_payloads = payloads[:15] if len(payloads) > 15 else payloads

        form_findings = []

        for i, form in enumerate(forms):
            action = form.get("action") or self.url
            if not action.startswith("http"):
                action = urljoin(self.url, action)
            method = form.get("method", "get").lower()
            inputs = form.find_all(["input", "textarea"])
            input_names = [inp.get("name") for inp in inputs if inp.get("name")]

            if not input_names:
                continue

            self.log(f"Form #{i+1}: {method.upper()} {action} | Alanlar: {', '.join(input_names)}", "*", Colors.C)

            for payload in test_payloads:
                data = {name: payload for name in input_names}
                try:
                    if method == "post":
                        r = self.session.post(action, data=data, timeout=self.timeout, verify=False)
                    else:
                        r = self.session.get(action, params=data, timeout=self.timeout, verify=False)

                    if payload in r.text:
                        finding = {
                            "type": "Reflected XSS (Form)",
                            "form_index": i + 1,
                            "action": action,
                            "method": method.upper(),
                            "payload": payload,
                            "fields": input_names,
                        }
                        form_findings.append(finding)
                        self.vuln_log(f"Form #{i+1} ({method.upper()}) | Payload: {payload[:50]}")
                except Exception:
                    continue

        self.findings.extend(form_findings)
        return form_findings

    # ══════════════════════════════════════
    #        DOM SINK TARAMASI
    # ══════════════════════════════════════

    def scan_dom_sinks(self):
        """
        Sayfa kaynağında tehlikeli JS sink'lerini arar.
        Bu, gerçek bir exploit değil, "burada DOM-XSS riski olabilir"
        bilgilendirmesidir — manuel inceleme için işaret verir.
        """
        try:
            r = self.session.get(self.url, timeout=self.timeout, verify=False)
            body = r.text
        except Exception as e:
            self.log(f"Sayfa alınamadı: {e}", "!", Colors.R)
            return []

        found_sinks = []
        for sink in DOM_SINKS:
            count = body.count(sink)
            if count > 0:
                found_sinks.append({"sink": sink, "count": count})
                self.info_log(f"DOM sink bulundu: {Colors.Y}{sink}{Colors.RS} ({count} kez)")

        if not found_sinks:
            self.log("Tehlikeli DOM sink tespit edilmedi.", "✓", Colors.G)
        else:
            self.log(f"{len(found_sinks)} farklı DOM sink türü bulundu. Manuel incelemeniz önerilir.", "!", Colors.Y)

        self.dom_findings = found_sinks
        return found_sinks

    # ══════════════════════════════════════
    #        TAM TARAMA
    # ══════════════════════════════════════

    def run_full(self, custom_wordlist=None, category="all", scan_forms=True, scan_dom=True, smart_probe=True):
        """URL parametreleri + formlar + DOM sink taramasını birlikte çalıştırır"""
        print(f"\n  {Colors.BOLD}{Colors.M}╔══════════════════════════════════════════╗")
        print(f"  ║   KyzerXSS — by Kyzerz53                   ║")
        print(f"  ╚══════════════════════════════════════════╝{Colors.RS}")
        print(f"  {Colors.W}Hedef: {Colors.Y}{self.url}{Colors.RS}\n")

        print(f"  {Colors.BOLD}{Colors.C}━━━ URL PARAMETRE TARAMASI ━━━{Colors.RS}\n")
        self.scan_url_params(custom_wordlist=custom_wordlist, category=category, smart_probe=smart_probe)

        if scan_forms:
            print(f"\n  {Colors.BOLD}{Colors.C}━━━ FORM TARAMASI ━━━{Colors.RS}\n")
            self.scan_forms(custom_wordlist=custom_wordlist, category=category)

        if scan_dom:
            print(f"\n  {Colors.BOLD}{Colors.C}━━━ DOM SINK TARAMASI ━━━{Colors.RS}\n")
            self.scan_dom_sinks()

        print(f"\n  {Colors.C}{'─'*60}{Colors.RS}")
        if self.findings:
            print(f"  {Colors.BOLD}{Colors.R}[✗] {len(self.findings)} XSS ZAFİYETİ BULUNDU!{Colors.RS}")
        else:
            print(f"  {Colors.BOLD}{Colors.G}[✓] XSS zafiyeti tespit edilmedi.{Colors.RS}")
        print(f"  {Colors.C}{'─'*60}{Colors.RS}\n")

        return self.findings


def save_results(url, findings, dom_findings, output_dir="output"):
    """Sonuçları JSON olarak kaydeder"""
    import json
    from datetime import datetime
    from urllib.parse import urlparse

    os.makedirs(output_dir, exist_ok=True)
    domain = urlparse(url).netloc or "target"
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    path = f"{output_dir}/xss_scan_{domain}_{ts}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump({
            "target": url,
            "findings": findings,
            "dom_sinks": dom_findings,
        }, f, ensure_ascii=False, indent=2)

    return path


# ══════════════════════════════════════════
#   BAĞIMSIZ ÇALIŞTIRMA (test amaçlı)
# ══════════════════════════════════════════
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Kullanım: python3 xss_scanner.py <url> [--category basic|waf_bypass|polyglots|all] [--tor]")
        sys.exit(1)

    url = sys.argv[1]
    category = "all"
    tor = "--tor" in sys.argv

    if "--category" in sys.argv:
        idx = sys.argv.index("--category")
        category = sys.argv[idx + 1]

    scanner = XSSScanner(url, threads=30, tor=tor)
    findings = scanner.run_full(category=category)

    if findings:
        path = save_results(url, findings, scanner.dom_findings)
        print(f"  {Colors.G}[✓] Sonuçlar kaydedildi: {Colors.Y}{path}{Colors.RS}\n")
