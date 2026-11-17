# Otomatisasi Log Harian KKN

Script ini membantu peserta mengisi **Log Harian** dan **Pendataan Sampah Penduduk** pada website KKN Tematik Sampah Tuntas berdasarkan data JSON.

Peserta tidak perlu memasang Python atau menjalankan perintah terminal secara manual. Pilih launcher sesuai sistem operasi dan mode yang ingin digunakan.

## Persiapan

1. Pastikan komputer terhubung ke internet, terutama saat pertama kali menjalankan program.
2. Simpan semua file program dalam satu folder.
3. Letakkan file berikut di folder yang sama:

   ```text
   PKM_08_Data_Per_Peserta_Timeline_KK_Fix.json
   ```

4. Jangan menutup jendela terminal atau browser selama program berjalan.

## Pilihan mode

### Mode aman

Mode aman mengisi form lalu menutupnya **tanpa menekan tombol Simpan**. Tidak ada data baru yang dikirim ke website.

Gunakan mode ini untuk percobaan pertama:

| Sistem operasi | File yang dijalankan |
|---|---|
| Windows | `JALANKAN_MODE_AMAN.bat` |
| Linux | `JALANKAN_MODE_AMAN_LINUX.sh` |
| macOS | `JALANKAN_MODE_AMAN_MAC.command` |

> Mode aman memastikan form dapat dibuka dan diisi. Validasi yang hanya dilakukan server setelah tombol Simpan ditekan tidak dapat diperiksa dalam mode ini.

### Mode submit

Mode submit mengisi form dan langsung menyimpannya ke website.

| Sistem operasi | File yang dijalankan |
|---|---|
| Windows | `JALANKAN_MODE_SUBMIT.bat` |
| Linux | `JALANKAN_MODE_SUBMIT_LINUX.sh` |
| macOS | `JALANKAN_MODE_SUBMIT_MAC.command` |

Sebelum program dimulai, pesan berikut muncul satu kali:

```text
data akan langsung tersubmit jika program ini dijalankan (Y/n)
```

- Tekan `Enter` atau masukkan `Y` untuk melanjutkan.
- Masukkan `N` untuk membatalkan.
- Setelah dilanjutkan, tidak ada konfirmasi lagi untuk setiap data.

Data yang sudah ada di website akan dilewati agar tidak dikirim dua kali.

## Cara menjalankan

### Windows

1. Klik dua kali launcher `.bat` sesuai mode.
2. Jika Windows meminta izin instalasi, pilih **Yes/Ya**.
3. Masukkan email dan password akun KKN ketika diminta.

Python 3.12 akan dipasang melalui Windows Package Manager (`winget`) jika belum tersedia.

### Linux

1. Klik dua kali launcher `.sh` sesuai mode.
2. Jika muncul pilihan, pilih **Run/Execute**.
3. Masukkan password sistem jika instalasi library Chromium memerlukannya.
4. Masukkan email dan password akun KKN ketika diminta.

Jika launcher tidak dapat diklik, buka terminal di folder program dan jalankan salah satu perintah berikut:

```bash
./JALANKAN_MODE_AMAN_LINUX.sh
./JALANKAN_MODE_SUBMIT_LINUX.sh
```

### macOS

1. Klik dua kali launcher `.command` sesuai mode.
2. Jika macOS memblokir file pada penggunaan pertama, klik kanan file lalu pilih **Open/Buka**.
3. Masukkan email dan password akun KKN ketika diminta.

## Proses setup otomatis

Setiap launcher menjalankan setup terlebih dahulu. Setup akan:

1. Mendeteksi Python yang tersedia.
2. Mengunduh Python 3.12 jika diperlukan.
3. Membuat virtual environment di folder `.venv`.
4. Menginstal dependency dari `requirements.txt`.
5. Menginstal browser Chromium untuk Playwright.
6. Keluar setelah persiapan selesai; launcher kemudian menjalankan script utama.

File setup internal:

- Windows: `_setup_dan_jalankan.bat`
- Linux/macOS: `_setup_dan_jalankan_linux_mac.sh`

Peserta tidak perlu menjalankan kedua file setup tersebut secara langsung.

## Login dan CAPTCHA

- Email harus terdaftar pada konfigurasi peserta di script.
- Password hanya digunakan untuk login dan tidak disimpan.
- Jika website menampilkan CAPTCHA, selesaikan CAPTCHA di browser lalu ikuti petunjuk pada terminal.

## Struktur file

```text
JALANKAN_MODE_AMAN.bat
JALANKAN_MODE_AMAN_LINUX.sh
JALANKAN_MODE_AMAN_MAC.command
JALANKAN_MODE_SUBMIT.bat
JALANKAN_MODE_SUBMIT_LINUX.sh
JALANKAN_MODE_SUBMIT_MAC.command
_setup_dan_jalankan.bat
_setup_dan_jalankan_linux_mac.sh
kkn_log_harian_auto.py
requirements.txt
PANDUAN_PESERTA.txt
PKM_08_Data_Per_Peserta_Timeline_KK_Fix.json
```

Jangan memindahkan launcher, script, `requirements.txt`, atau file JSON ke folder yang berbeda.

## Penyelesaian masalah

### File JSON tidak ditemukan

Pastikan nama file tepat seperti berikut dan berada di folder program:

```text
PKM_08_Data_Per_Peserta_Timeline_KK_Fix.json
```

### Setup gagal

1. Pastikan koneksi internet aktif.
2. Tutup jendela program.
3. Jalankan kembali launcher yang sama.
4. Pastikan antivirus atau firewall tidak memblokir Python, Chromium, `winget`, atau `uv`.

### Folder `.venv` tidak dapat digunakan

Hapus folder `.venv`, kemudian jalankan kembali launcher. Setup akan membuat virtual environment baru.

### Login tidak berhasil

- Periksa email dan password.
- Pastikan email sudah terdaftar sebagai peserta.
- Selesaikan CAPTCHA jika muncul.

### Sebagian data dilewati

Program melewati data yang:

- sudah tersedia di website; atau
- belum memiliki field wajib yang lengkap dalam file JSON.

Periksa ringkasan yang ditampilkan setelah program selesai untuk mengetahui alasannya.
