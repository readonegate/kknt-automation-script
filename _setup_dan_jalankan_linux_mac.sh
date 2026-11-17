#!/usr/bin/env bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

VENV_DIR="$SCRIPT_DIR/.venv"
VENV_PYTHON="$VENV_DIR/bin/python"

selesai() {
    local kode="$1"
    echo
    if [ "$kode" -ne 0 ]; then
        echo "[ERROR] Persiapan berhenti dengan kode $kode."
    fi
    read -r -p "Tekan Enter untuk menutup jendela ini ... " _
    exit "$kode"
}

gagal() {
    echo
    echo "Persiapan gagal. Periksa koneksi internet, lalu coba lagi."
    selesai 1
}

if [ ! -f "requirements.txt" ]; then
    echo "[ERROR] File requirements.txt tidak ditemukan di folder ini."
    gagal
fi

if [ ! -x "$VENV_PYTHON" ]; then
    if [ -e "$VENV_DIR" ]; then
        echo "[ERROR] Folder .venv sudah ada tetapi tidak dapat digunakan."
        echo "        Hapus folder .venv tersebut, lalu jalankan kembali."
        gagal
    fi

    PYTHON_EXE=""
    if command -v python3 >/dev/null 2>&1 && python3 -c 'import sys; raise SystemExit(sys.version_info < (3, 9))' >/dev/null 2>&1; then
        PYTHON_EXE="$(command -v python3)"
        echo "[OK] Python ditemukan: $PYTHON_EXE"
        echo "[PERSIAPAN] Membuat virtual environment ..."
        if ! "$PYTHON_EXE" -m venv "$VENV_DIR"; then
            rm -rf "$VENV_DIR"
            PYTHON_EXE=""
        fi
    fi

    if [ -z "$PYTHON_EXE" ]; then
        echo "[PERSIAPAN] Python belum tersedia. Mengunduh Python 3.12 ..."
        if command -v curl >/dev/null 2>&1; then
            curl -LsSf https://astral.sh/uv/install.sh | sh || gagal
        elif command -v wget >/dev/null 2>&1; then
            wget -qO- https://astral.sh/uv/install.sh | sh || gagal
        else
            echo "[ERROR] curl atau wget diperlukan untuk mengunduh Python."
            gagal
        fi

        UV_EXE="$(command -v uv 2>/dev/null || true)"
        if [ -z "$UV_EXE" ] && [ -x "$HOME/.local/bin/uv" ]; then
            UV_EXE="$HOME/.local/bin/uv"
        fi
        if [ -z "$UV_EXE" ] && [ -x "$HOME/.cargo/bin/uv" ]; then
            UV_EXE="$HOME/.cargo/bin/uv"
        fi
        if [ -z "$UV_EXE" ]; then
            echo "[ERROR] Installer Python tidak dapat ditemukan setelah diunduh."
            gagal
        fi

        "$UV_EXE" python install 3.12 || gagal
        "$UV_EXE" venv --python 3.12 --seed "$VENV_DIR" || gagal
    fi
fi

echo "[PERSIAPAN] Memasang dependencies ..."
"$VENV_PYTHON" -m pip install --disable-pip-version-check -r "requirements.txt" || gagal

echo "[PERSIAPAN] Memastikan browser Chromium tersedia ..."
if [ "$(uname -s)" = "Linux" ]; then
    "$VENV_PYTHON" -m playwright install --with-deps chromium || gagal
else
    "$VENV_PYTHON" -m playwright install chromium || gagal
fi

echo
echo "[SELESAI] Persiapan berhasil."
exit 0
