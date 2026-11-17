#!/usr/bin/env bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
printf '%s\n' \
    '============================================================' \
    '  MODE SUBMIT - FORM AKAN DISIMPAN KE WEBSITE' \
    '============================================================' \
    ''
while true; do
    read -r -p 'data akan langsung tersubmit jika program ini dijalankan (Y/n) ' JAWABAN
    case "$JAWABAN" in
        Y|y|'') break ;;
        N|n) echo 'Dibatalkan. Tidak ada data yang dikirim.'; exit 0 ;;
        *) echo 'Masukkan Y untuk lanjut atau N untuk batal.' ;;
    esac
done

"$SCRIPT_DIR/_setup_dan_jalankan_linux_mac.sh" || exit 1

echo
echo "[MULAI] Menjalankan program ..."
echo
"$SCRIPT_DIR/.venv/bin/python" "$SCRIPT_DIR/kkn_log_harian_auto.py"
HASIL=$?

echo
if [ "$HASIL" -ne 0 ]; then
    echo "[ERROR] Program berhenti dengan kode $HASIL."
fi
read -r -p "Tekan Enter untuk menutup jendela ini ... " _
exit "$HASIL"
