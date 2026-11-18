#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KKN Tematik Sampah Tuntas (LLDIKTI IV) — Auto isi Log Harian & Pendataan Sampah
================================================================================
Script CLI satu file. Peserta menjalankan script ini, mengisi email + password,
lalu script mengisi Log Harian dan Pendataan Sampah Penduduk dari file JSON
sesuai tanggal yang sudah jatuh tempo.

CARA PAKAI (peserta)
--------------------
1. Install sekali saja:
       pip install playwright
       playwright install chromium
2. Letakkan file JSON (PKM_08_Data_Per_Peserta_Timeline_KK_Fix.json) di folder
   yang sama dengan script ini.
3. Jalankan:
       python kkn_log_harian_auto.py
   Lalu isi email dan password akun KKN saat diminta. Password tidak
   ditampilkan di layar dan tidak disimpan di mana pun.

ATURAN YANG DIPATUHI SCRIPT
---------------------------
1. Cek duplikat: sebelum mengisi, script membaca tabel yang sudah ada.
   - Log harian dicek di halaman /logkegiatan (kunci: tanggal + nama aktivitas).
   - Pendataan dicek di halaman /pendataanpemilahan
     (kunci: tanggal + nama kepala keluarga + RT + RW).
   Record yang sudah ada dilewati (tidak diinput dua kali). Jika ingin program
   langsung BERHENTI saat menemukan duplikat pertama, ubah STOP_ON_DUPLICATE
   menjadi True di bawah.
2. Hanya mengisi tanggal yang sudah jatuh tempo: tanggal <= hari ini.
   Jika peserta lupa menjalankan program, data hari-hari sebelumnya ikut
   terisi (catch-up) sampai hari ini.
3. Jeda 5 detik setelah setiap submit.
4. Hanya email yang ada di ALLOWED_EMAILS yang bisa menjalankan program.
   Email lain langsung ditolak dan program berhenti.

CATATAN PENTING
---------------
- Log harian ini dinilai atas nama masing-masing peserta. Pastikan pengisian
  otomatis seperti ini dibolehkan oleh program, dan pastikan data JSON adalah
  data asli kelompok. Script hanya memindahkan isi JSON ke form.
- Field yang kosong di JSON dan wajib di form TIDAK dikarang oleh script:
  record seperti itu dilewati dan dilaporkan di akhir, kecuali Residu yang
  memakai default 0 (sesuai keputusan koordinator).
- Jika muncul CAPTCHA saat login, selesaikan manual di jendela browser,
  lalu tekan Enter di terminal saat diminta.
"""

import argparse
import getpass
import json
import re
import sys
import time
from datetime import date
from pathlib import Path

# =============================================================================
# KONFIGURASI — DIISI/DIUBAH OLEH KOORDINATOR
# =============================================================================

BASE_URL = "https://kknt-sampahtuntas.lldikti4.id"
LOKASI_PROGRAM = "Kota Bandung"
JSON_FILENAME = "PKM_08_Data_Per_Peserta_Timeline_KK_Fix.json"

# Daftar email yang diizinkan menjalankan program (nama peserta -> email).
# Ganti "nanti saya isi sendiri" dengan email asli peserta. Baris yang masih
# berisi placeholder TIDAK bisa dipakai untuk login (ditolak program).
ALLOWED_EMAILS = {
    "ridwan": "ridwan20123030@digitechuniversity.ac.id",
    "ali":"ali20223050@digitechuniversity.ac.id",
    "willy":"willyi10223013@digitechuniversity.ac.id",
    "amel":"amelia20123028@digitechuniversity.ac.id",
    "rizal":"mrizal30123016@digitechuniversity.ac.id",
    "billa":"nabila20123027@digitechuniversity.ac.id",
    "shidqi":"muhammad20223009@digitechuniversity.ac.id",
    "shello":"shellomita30123015@digitechuniversity.ac.id",
    "fariz":"rb.fariz30123069@digitechuniversity.ac.id",
}

# Nilai default untuk field wajib yang tidak ada di JSON (keputusan koordinator).
VOLUME_DEFAULT = 1                # Volume/Kuantitas Output log harian
SATUAN_DEFAULT = "1 koordinasi"   # Satuan log harian
RESIDU_DEFAULT = 0                # Residu (kg) pendataan jika di JSON null

# Jumlah Anggota Keluarga kosong di JSON untuk semua record pendataan.
# None = lewati record yang kosong (laporkan di akhir). Isi dengan angka
# (mis. 4) jika koordinator menetapkan nilai default untuk semua KK.
DEFAULT_JUMLAH_ANGGOTA = None

SUBMIT_DELAY_SECONDS = 5  # jeda setelah setiap submit
# False = record yang sudah diinput dilewati, program lanjut ke record berikut.
# True  = program langsung berhenti saat menemukan record yang sudah diinput.
STOP_ON_DUPLICATE = False

# Pemetaan kategori kegiatan JSON (Inggris) -> label dropdown di form.
ACTIVITY_MAP = {
    "documentation": "Dokumentasi",
    "education": "Edukasi",
    "evaluation": "Evaluasi",
    "implementation": "Implementasi",
    "communication": "Komunikasi",
}

# =============================================================================
# UTILITAS
# =============================================================================

BULAN_ID = {
    "januari": 1, "jan": 1, "februari": 2, "feb": 2, "maret": 3, "mar": 3,
    "april": 4, "apr": 4, "mei": 5, "juni": 6, "jun": 6, "juli": 7, "jul": 7,
    "agustus": 8, "agu": 8, "aug": 8, "september": 9, "sep": 9, "sept": 9,
    "oktober": 10, "okt": 10, "oct": 10, "november": 11, "nov": 11,
    "desember": 12, "des": 12, "dec": 12,
}


def log(msg=""):
    """Cetak progres ke terminal (langsung tampil, tidak tertahan buffer)."""
    print(msg, flush=True)


def normalisasi_teks(s):
    """Normalisasi untuk perbandingan kunci duplikat."""
    if s is None:
        return ""
    return " ".join(str(s).lower().split())


def normalisasi_rt_rw(s):
    """RT/RW dinormalisasi tanpa nol di depan ('001' == '01' == '1')."""
    s = str(s).strip()
    if s.isdigit():
        return str(int(s))
    return s


def parse_tanggal_fleksibel(s):
    """Parse tanggal dari berbagai format tampilan tabel.

    Menerima: 2026-11-17, 17/11/2026, 17-11-2026, 17 Nov 2026,
    17 November 2026. Mengembalikan datetime.date atau None.
    """
    if not s:
        return None
    s = str(s).strip()
    m = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})$", s)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            return None
    m = re.match(r"^(\d{1,2})[/-](\d{1,2})[/-](\d{4})$", s)
    if m:
        try:
            return date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
        except ValueError:
            return None
    m = re.match(r"^(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})$", s)
    if m:
        bulan = BULAN_ID.get(m.group(2).lower())
        if bulan:
            try:
                return date(int(m.group(3)), bulan, int(m.group(1)))
            except ValueError:
                return None
    return None


def rt_rw_3_digit(s):
    """Form meminta RT/RW 3 digit angka (contoh 001); JSON berisi 2 digit."""
    s = str(s).strip()
    if s.isdigit():
        return s.zfill(3)
    return s


# =============================================================================
# DATA JSON
# =============================================================================

def muat_json(path_json):
    with open(path_json, "r", encoding="utf-8") as f:
        return json.load(f)


def cari_peserta(email):
    """Cocokkan email ke peserta. Kembalikan key peserta atau None."""
    email_norm = email.strip().lower()
    for key, email_terdaftar in ALLOWED_EMAILS.items():
        if "@" not in str(email_terdaftar):
            continue  # placeholder "nanti saya isi sendiri" -> belum dikonfigurasi
        if email_terdaftar.strip().lower() == email_norm:
            return key
    return None


def record_jatuh_tempo(records, hari_ini):
    """Ambil record dengan tanggal <= hari ini, urut tanggal (log dulu)."""
    hasil = []
    for r in records:
        tgl = parse_tanggal_fleksibel(r.get("date"))
        if tgl is None:
            continue
        if tgl <= hari_ini:
            hasil.append(r)
    hasil.sort(key=lambda r: (
        parse_tanggal_fleksibel(r.get("date")),
        0 if r.get("type") == "log/daily" else 1,
        str(r.get("id", "")),
    ))
    return hasil


def validasi_record(r):
    """Periksa apakah record bisa diisi ke form.

    Mengembalikan (bisa_diisi, alasan). Field wajib yang kosong di JSON
    membuat record dilewati, kecuali Residu (default 0).
    """
    tipe = r.get("type")
    if parse_tanggal_fleksibel(r.get("date")) is None:
        return False, "tanggal tidak valid/kosong"
    if tipe == "log/daily":
        aktivitas = (r.get("activity") or "").strip().lower()
        if not aktivitas or aktivitas not in ACTIVITY_MAP:
            return False, "kategori kegiatan belum ada di JSON (menunggu rincian)"
        if not (r.get("name") or "").strip():
            return False, "nama aktivitas kosong"
        if not (r.get("description") or "").strip():
            return False, "deskripsi kegiatan kosong"
        return True, ""
    if tipe == "data-collection":
        if not (r.get("head-of-family") or "").strip():
            return False, "nama kepala keluarga kosong"
        if not (r.get("address") or "").strip():
            return False, "alamat rumah kosong"
        if not (r.get("RT") or "").strip() or not (r.get("RW") or "").strip():
            return False, "RT/RW kosong"
        if r.get("number-of-family-numbers") is None and DEFAULT_JUMLAH_ANGGOTA is None:
            return False, "jumlah anggota keluarga kosong di JSON"
        if r.get("have-sorted-the-waste") is None:
            return False, "status pemilahan sampah kosong di JSON"
        if r.get("organic_kg") is None or r.get("unorganic_kg") is None:
            return False, "timbulan sampah organik/anorganik kosong"
        return True, ""
    return False, "tipe record tidak dikenal: %s" % tipe


def kunci_log(r):
    """Kunci duplikat log harian: (tanggal, nama aktivitas)."""
    return (parse_tanggal_fleksibel(r.get("date")).isoformat(),
            normalisasi_teks(r.get("name")))


def kunci_pendataan(r):
    """Kunci duplikat pendataan: (tanggal, nama KK, RT, RW)."""
    return (parse_tanggal_fleksibel(r.get("date")).isoformat(),
            normalisasi_teks(r.get("head-of-family")),
            normalisasi_rt_rw(r.get("RT")),
            normalisasi_rt_rw(r.get("RW")))


def label_record(r):
    """Label singkat record untuk tampilan progres."""
    tgl = r.get("date")
    if r.get("type") == "log/daily":
        return "%s | LOG  %s" % (tgl, r.get("name"))
    return "%s | DATA KK %s (RT %s/RW %s)" % (
        tgl, r.get("head-of-family"),
        rt_rw_3_digit(r.get("RT")), rt_rw_3_digit(r.get("RW")))


# =============================================================================
# BROWSER (Playwright)
# =============================================================================

def buka_browser(headless):
    from playwright.sync_api import sync_playwright
    pw = sync_playwright().start()
    browser = pw.chromium.launch(headless=headless)
    context = browser.new_context(viewport={"width": 1280, "height": 900})
    page = context.new_page()
    page.set_default_timeout(20000)
    return pw, browser, page


def pilih_lokasi_program(page):
    """Pilih 'Kota Bandung' di dropdown Lokasi Program halaman login."""
    select = page.locator('select[name="lokasi"]')
    try:
        select.select_option(label=LOKASI_PROGRAM)
        return
    except Exception:
        pass
    # Fallback: cari option yang teksnya mengandung nama lokasi.
    opsi = select.locator("option").all_inner_texts()
    for teks in opsi:
        if LOKASI_PROGRAM.lower() in teks.lower():
            select.select_option(label=teks.strip())
            return
    raise RuntimeError("Opsi lokasi program '%s' tidak ditemukan." % LOKASI_PROGRAM)


def login(page, email, password):
    log("[LOGIN] Membuka halaman login ...")
    page.goto(BASE_URL + "/login")
    page.wait_for_selector('input[name="password"]', timeout=20000)
    pilih_lokasi_program(page)
    log("[LOGIN] Lokasi program: %s" % LOKASI_PROGRAM)
    page.locator('input[name="username"]').fill(email)
    page.locator('input[name="password"]').fill(password)
    page.locator("#btnSubmit_formAuthentication").click()
    try:
        page.wait_for_url("**/home**", timeout=25000)
    except Exception:
        # Mungkin muncul CAPTCHA atau login gagal: beri kesempatan intervensi.
        log("[LOGIN] Belum masuk dashboard. Jika muncul CAPTCHA, selesaikan "
            "manual di jendela browser.")
        try:
            input("       Tekan Enter setelah login berhasil di browser ... ")
        except KeyboardInterrupt:
            raise RuntimeError("Login dibatalkan pengguna.")
        page.wait_for_url("**/home**", timeout=30000)
    log("[LOGIN] Berhasil masuk sebagai %s" % email)


def _set_tampil_100(page):
    """Ubah 'Show entries' menjadi 100 agar pembacaan tabel lebih cepat."""
    try:
        sel = page.locator("select").first
        sel.select_option("100")
        page.wait_for_timeout(1500)
    except Exception:
        pass


def _klik_next_jika_aktif(page):
    """Klik pagination Next jika masih aktif. Kembalikan True jika pindah."""
    for selector in ("a.paginate_button.next:not(.disabled)",
                     "li.paginate_button.next:not(.disabled) a"):
        tombol = page.locator(selector)
        if tombol.count() > 0:
            tombol.first.click()
            page.wait_for_timeout(1500)
            return True
    return False


def _baca_baris_tabel(page):
    """Baca semua baris <tr> yang terlihat di tabel halaman saat ini."""
    baris = []
    for row in page.locator("table tbody tr").all():
        sel = [c.inner_text().strip() for c in row.locator("td").all()]
        if len(sel) < 4:
            continue  # baris status kosong ("Tidak ada data yang tersedia")
        baris.append(sel)
    return baris


def baca_log_yang_sudah_ada(page):
    """Baca /logkegiatan -> set kunci (tanggal, nama aktivitas)."""
    log("[CEK] Membaca log harian yang sudah ada di /logkegiatan ...")
    page.goto(BASE_URL + "/logkegiatan")
    page.wait_for_selector("table tbody tr", timeout=20000)
    page.wait_for_timeout(1000)
    _set_tampil_100(page)
    sudah = set()
    while True:
        for sel in _baca_baris_tabel(page):
            tgl = parse_tanggal_fleksibel(sel[1])  # kolom TANGGAL
            if tgl is not None:
                sudah.add((tgl.isoformat(), normalisasi_teks(sel[3])))  # NAMA AKTIVITAS
        if not _klik_next_jika_aktif(page):
            break
    log("[CEK] Ditemukan %d log harian yang sudah ada." % len(sudah))
    return sudah


def baca_pendataan_yang_sudah_ada(page):
    """Baca /pendataanpemilahan -> set kunci (tanggal, nama KK, RT, RW)."""
    log("[CEK] Membaca pendataan yang sudah ada di /pendataanpemilahan ...")
    page.goto(BASE_URL + "/pendataanpemilahan")
    page.wait_for_selector("table tbody tr", timeout=20000)
    page.wait_for_timeout(1000)
    _set_tampil_100(page)
    sudah = set()
    while True:
        for sel in _baca_baris_tabel(page):
            tgl = parse_tanggal_fleksibel(sel[1])  # kolom TANGGAL
            if tgl is not None:
                sudah.add((tgl.isoformat(),
                           normalisasi_teks(sel[2]),       # NAMA KEPALA KELUARGA
                           normalisasi_rt_rw(sel[5]),      # RT
                           normalisasi_rt_rw(sel[6])))     # RW
        if not _klik_next_jika_aktif(page):
            break
    log("[CEK] Ditemukan %d pendataan yang sudah ada." % len(sudah))
    return sudah


def _buka_modal_tambah(page):
    page.goto(BASE_URL + "/logkegiatan")
    page.wait_for_selector("table tbody tr", timeout=20000)
    page.locator("#btnTambahLog").click()
    modal = page.locator("#modalku")
    modal.wait_for(state="visible", timeout=15000)
    page.wait_for_timeout(800)  # tunggu "Loading, mohon tunggu..." selesai
    return modal


def _pilih_jenis_form(modal, label_radio):
    modal.locator("label", has_text=label_radio).first.click()
    modal.page.wait_for_timeout(600)


def _pilih_kategori_select2(page, modal, kategori):
    """Pilih kategori di dropdown Select2 (dengan fallback select native)."""
    native = modal.locator('select[name="id_kategori"]')
    if native.count() > 0:
        try:
            native.first.select_option(label=kategori)
            return
        except Exception:
            pass
    modal.locator(".select2-selection").first.click()
    cari = page.locator(".select2-search__field")
    if cari.count() > 0:
        cari.last.fill(kategori)
        page.wait_for_timeout(400)
    page.locator(".select2-results__option", has_text=kategori).first.click()
    page.wait_for_timeout(300)



def _simpan_atau_tutup(page, modal, dry_run, record_id):
    """Simpan form lalu tutup modal; dry-run hanya menutup modal."""
    tombol_tutup = modal.locator('button:has-text("Tutup")').first
    if dry_run:
        tombol_tutup.click()
        modal.wait_for(state="hidden", timeout=10000)
        return

    try:
        with page.expect_response(
                lambda r: r.request.method == "POST"
                and r.url.endswith("/logkegiatan/insert"), timeout=20000) as info:
            modal.locator('button:has-text("Simpan")').first.click()
        response = info.value
        hasil = response.json()
        if not response.ok or not hasil.get("success"):
            raise RuntimeError(hasil.get("message") or
                               "Server menolak data tanpa memberikan alasan.")
        tombol_tutup.click()
        modal.wait_for(state="hidden", timeout=10000)
    except Exception as exc:
        try:
            page.screenshot(path="error_%s.png" % record_id)
            log("       (screenshot error disimpan: error_%s.png)" % record_id)
        except Exception:
            pass
        raise RuntimeError("Gagal menyimpan atau menutup form: %s" % exc)


def isi_log_harian(page, r, dry_run):
    modal = _buka_modal_tambah(page)
    _pilih_jenis_form(modal, "Log Harian / Kegiatan")
    modal.locator('input[name="tanggal"]:visible').fill(r["date"])
    _pilih_kategori_select2(page, modal, ACTIVITY_MAP[r["activity"].strip().lower()])
    modal.locator('input[name="nama_aktivitas"]:visible').fill(str(r["name"]))
    modal.locator('textarea[name="deskripsi"]:visible').fill(str(r["description"]))
    modal.locator('input[name="volume"]:visible').fill(str(VOLUME_DEFAULT))
    modal.locator('input[name="satuan"]:visible').fill(SATUAN_DEFAULT)
    if r.get("proof_link"):
        modal.locator('input[name="tautan"]:visible').fill(str(r["proof_link"]))
    _simpan_atau_tutup(page, modal, dry_run, str(r.get("id", "log")))


def isi_pendataan(page, r, dry_run):
    modal = _buka_modal_tambah(page)
    _pilih_jenis_form(modal, "Pendataan Sampah Penduduk")
    modal.locator('input[name="tanggal"]:visible').fill(r["date"])
    modal.locator('input[name="nama_kepala_keluarga"]:visible').fill(
        str(r["head-of-family"]))
    modal.locator('input[name="alamat_rumah"]:visible').fill(str(r["address"]))
    modal.locator('input[name="rt"]:visible').fill(rt_rw_3_digit(r["RT"]))
    modal.locator('input[name="rw"]:visible').fill(rt_rw_3_digit(r["RW"]))
    memilah = "1" if str(r.get("have-sorted-the-waste")).lower() == "yes" else "0"
    modal.locator('input[name="memilah"][value="%s"]' % memilah).click()
    jumlah = r.get("number-of-family-numbers")
    if jumlah is None:
        jumlah = DEFAULT_JUMLAH_ANGGOTA
    residu = r.get("residue_kg")
    if residu is None:
        residu = RESIDU_DEFAULT
    modal.locator('input[name="jumlah_anggota_keluarga"]:visible').fill(str(jumlah))
    modal.locator('input[name="organik_kg"]:visible').fill(str(r["organic_kg"]))
    modal.locator('input[name="anorganik_kg"]:visible').fill(str(r["unorganic_kg"]))
    modal.locator('input[name="residu_kg"]:visible').fill(str(residu))
    _simpan_atau_tutup(page, modal, dry_run, str(r.get("id", "kk")))


# =============================================================================
# PROGRAM UTAMA
# =============================================================================

def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    parser = argparse.ArgumentParser(
        description="Auto isi Log Harian & Pendataan Sampah KKN Tematik Sampah Tuntas.")
    parser.add_argument("--json", default=None,
                        help="Path file JSON (default: file JSON di folder script).")
    parser.add_argument("--headless", action="store_true",
                        help="Jalankan browser tanpa jendela (default: tampil).")
    parser.add_argument("--dry-run", action="store_true",
                        help="Latihan: isi form lalu tutup tanpa menyimpan.")
    args = parser.parse_args()

    log("=" * 68)
    log("  KKN TEMATIK SAMPAH TUNTAS — AUTO ISI LOG HARIAN")
    log("  Kelompok 08 — Kelurahan Derwati")
    log("=" * 68)

    # --- 1. Identifikasi peserta (email dicek SEBELUM meminta password) ---
    email = input("Email akun KKN: ").strip()
    peserta = cari_peserta(email)
    if peserta is None:
        log("")
        log("[DITOLAK] Email %s tidak terdaftar sebagai peserta program ini." % email)
        log("          Program berhenti.")
        return 1
    nama_peserta = peserta.capitalize()
    try:
        password = getpass.getpass("Password akun KKN: ")
    except KeyboardInterrupt:
        log("\n[DIBATALKAN] Program berhenti.")
        return 1
    if not password:
        log("[DITOLAK] Password kosong. Program berhenti.")
        return 1
    log("[OK] Peserta dikenali: %s (%s)" % (nama_peserta, email))

    # --- 2. Muat JSON dan tentukan record yang jatuh tempo ---
    path_json = Path(args.json) if args.json else Path(__file__).resolve().parent / JSON_FILENAME
    if not path_json.exists():
        log("[ERROR] File JSON tidak ditemukan: %s" % path_json)
        log("        Letakkan file %s di folder yang sama dengan script ini."
            % JSON_FILENAME)
        return 1
    data = muat_json(path_json)
    try:
        records = data["participants"][peserta]["records"]
    except KeyError:
        log("[ERROR] Peserta '%s' tidak ada di file JSON." % peserta)
        return 1

    hari_ini = date.today()
    log("[INFO] Hari ini: %s" % hari_ini.isoformat())
    due = record_jatuh_tempo(records, hari_ini)
    log("[INFO] Total record %s di JSON: %d | jatuh tempo (<= hari ini): %d"
        % (nama_peserta, len(records), len(due)))
    if not due:
        log("[SELESAI] Tidak ada data yang jatuh tempo. Program berhenti.")
        return 0
    if args.dry_run:
        log("[DRY-RUN] Mode latihan aktif: form diisi lalu ditutup TANPA disimpan.")

    # --- 3. Login dan baca data yang sudah ada (cek duplikat) ---
    pw, browser, page = buka_browser(headless=args.headless)
    try:
        login(page, email, password)
        log_sudah = baca_log_yang_sudah_ada(page)
        data_sudah = baca_pendataan_yang_sudah_ada(page)

        # --- 4. Proses record satu per satu ---
        terkirim, sudah_ada, dilewati, gagal = [], [], [], []
        total = len(due)
        for i, r in enumerate(due, start=1):
            label = "[%d/%d] %s" % (i, total, label_record(r))

            bisa, alasan = validasi_record(r)
            if not bisa:
                log("%s ... DILEWATI (%s)" % (label, alasan))
                dilewati.append((label_record(r), alasan))
                continue

            kunci = kunci_log(r) if r["type"] == "log/daily" else kunci_pendataan(r)
            sudah_set = log_sudah if r["type"] == "log/daily" else data_sudah
            if kunci in sudah_set:
                log("%s ... DILEWATI (sudah diinput sebelumnya)" % label)
                sudah_ada.append(label_record(r))
                if STOP_ON_DUPLICATE:
                    log("[BERHENTI] Menemukan record yang sudah diinput "
                        "(STOP_ON_DUPLICATE aktif).")
                    break
                continue

            try:
                if r["type"] == "log/daily":
                    isi_log_harian(page, r, args.dry_run)
                else:
                    isi_pendataan(page, r, args.dry_run)
            except KeyboardInterrupt:
                raise
            except Exception as exc:
                log("%s ... GAGAL (%s)" % (label, exc))
                gagal.append((label_record(r), str(exc)))
                try:
                    page.goto(BASE_URL + "/logkegiatan")
                except Exception:
                    pass
                continue

            if args.dry_run:
                log("%s ... OK (dry-run, tidak disimpan)" % label)
            else:
                log("%s ... OK (tersimpan)" % label)
                sudah_set.add(kunci)
                terkirim.append(label_record(r))
                log("       Jeda %d detik sebelum lanjut ..." % SUBMIT_DELAY_SECONDS)
                time.sleep(SUBMIT_DELAY_SECONDS)

        # --- 5. Verifikasi akhir (baca ulang tabel) ---
        if terkirim and not args.dry_run:
            log("")
            log("[VERIFIKASI] Membaca ulang tabel untuk memastikan data tersimpan ...")
            try:
                log_akhir = baca_log_yang_sudah_ada(page)
                data_akhir = baca_pendataan_yang_sudah_ada(page)
                terverifikasi = 0
                for r in due:
                    if r["type"] == "log/daily":
                        if kunci_log(r) in log_akhir:
                            terverifikasi += 1
                    else:
                        if kunci_pendataan(r) in data_akhir:
                            terverifikasi += 1
                log("[VERIFIKASI] %d dari %d record yang dikirim terkonfirmasi "
                    "di tabel." % (terverifikasi, len(terkirim)))
            except Exception as exc:
                log("[VERIFIKASI] Gagal membaca ulang tabel (%s). "
                    "Silakan periksa manual di website." % exc)

        # --- 6. Ringkasan ---
        log("")
        log("=" * 68)
        log("  RINGKASAN — %s (%s)" % (nama_peserta, hari_ini.isoformat()))
        log("=" * 68)
        log("  Terkirim        : %d" % len(terkirim))
        log("  Sudah ada       : %d (dilewati, tidak diduplikasi)" % len(sudah_ada))
        log("  Dilewati        : %d (data di JSON belum lengkap)" % len(dilewati))
        log("  Gagal           : %d" % len(gagal))
        if dilewati:
            log("")
            log("  Dilewati karena data belum lengkap:")
            for lbl, alasan in dilewati:
                log("    - %s | %s" % (lbl, alasan))
        if gagal:
            log("")
            log("  Gagal diinput (coba jalankan ulang program):")
            for lbl, alasan in gagal:
                log("    - %s | %s" % (lbl, alasan))
        log("")
        log("[SELESAI] Program selesai.")
        return 0
    finally:
        try:
            browser.close()
        except Exception:
            pass
        try:
            pw.stop()
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
