#!/usr/bin/env bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
printf '%s\n' \
    '============================================================' \
    '  MODE AMAN - FORM TIDAK AKAN DISIMPAN / DI-SUBMIT' \
    '============================================================' \
    ''
"$SCRIPT_DIR/_setup_dan_jalankan_linux_mac.sh" || exit 1

echo
echo "[MULAI] Menjalankan program ..."
echo
"$SCRIPT_DIR/.venv/bin/python" "$SCRIPT_DIR/kkn_log_harian_auto.py" --dry-run
HASIL=$?

echo
if [ "$HASIL" -ne 0 ]; then
    echo "[ERROR] Program berhenti dengan kode $HASIL."
fi
read -r -p "Tekan Enter untuk menutup jendela ini ... " _
exit "$HASIL"
