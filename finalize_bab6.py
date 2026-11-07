# -*- coding: utf-8 -*-
"""Orkestrasi akhir Bab 6: setelah training 6.2 selesai, jalankan sisa pipeline.

Urutan:
  1. update 6.4 (teks model/akurasi terbaru dari jatim_model_compare.csv)
  2. buat model train-only + raster evaluasi jujur (make_eval_raster.py)
  3. hapus demo_classified.tif LAMA (6.3 skip kalau file lama masih ada)
  4. eksekusi 6.3  -> peta Folium klasifikasi + demo_classified.tif (model deploy)
  5. eksekusi 6.5  -> peta Wonoayu (konsisten dengan raster ber-mask)
  6. eksekusi 6.6  -> peta evaluasi per poligon + metrik jujur poligon test
  7. lengkapi markdown 6.6 dgn angka poligon test jujur
  8. make_maps.py  -> folder maps/ (perbaiki 3 link rusak di 6.4)
  9. report_bab6   -> ringkasan sebelum vs sesudah

Pakai: python finalize_bab6.py [langkah...]
Tanpa argumen = semua langkah. Gagal di satu langkah -> berhenti (kode keluar 1).
"""
import os
import runpy
import subprocess
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
BASE = r"C:\Users\heker\Downloads\PSD-main"
os.chdir(BASE)

STEPS = {
    "64": ("perbarui teks 6.4 dari hasil training",
           [sys.executable, "update64.py"]),
    "fix": ("pastikan jatim_best.joblib portable (aman dibuka 6.3/6.6/streamlit)",
            [sys.executable, "fix_model_pickle.py"]),
    "evaltif": ("buat raster evaluasi jujur (model train-only, resumable)",
                [sys.executable, "make_eval_raster.py"]),
    "reset_tif": ("hapus demo_classified.tif lama (paksa 6.3 render ulang)",
                  "DEL_TIF"),
    "63": ("eksekusi 6.3 peta Folium klasifikasi",
           [sys.executable, "run_nb.py", "6.3_peta_demo.ipynb"]),
    "65": ("eksekusi 6.5 klasifikasi Wonoayu",
           [sys.executable, "run_nb.py", "6.5_klasifikasi_wonoayu.ipynb"]),
    "66": ("eksekusi 6.6 evaluasi per poligon + peta",
           [sys.executable, "run_nb.py", "6.6_evaluasi_poligon.ipynb"]),
    "md66": ("lengkapi bacaan hasil 6.6 dgn angka poligon test jujur",
             [sys.executable, "update66_md.py"]),
    "maps": ("buat folder maps/ (perbaiki link rusak)",
             [sys.executable, "make_maps.py"]),
    "report": ("laporan sebelum vs sesudah",
               [sys.executable, "report_bab6.py"]),
}

order = sys.argv[1:] or list(STEPS)

# syarat mutlak: training 6.2 harus sudah menghasilkan model baru
if "63" in order or "66" in order:
    cmp_csv = os.path.join(BASE, "jatim", "model", "jatim_model_compare.csv")
    best = os.path.join(BASE, "jatim", "model", "jatim_best.joblib")
    import pandas as pd
    ok = (os.path.exists(cmp_csv) and os.path.exists(best)
          and "test_accuracy" in pd.read_csv(cmp_csv).columns
          and pd.read_csv(cmp_csv)["test_accuracy"].notna().any())
    if not ok:
        raise SystemExit("HASIL TRAINING BELUM SIAP (jatim_model_compare.csv "
                         "belum berisi test_accuracy) -- jalankan 6.2 dulu.")
    if "64" not in order:
        print("[catatan] 6.4 belum diminta; teksnya bisa tetap basi.")

t_all = time.time()
for key in order:
    desc, cmd = STEPS[key]
    print(f"\n{'=' * 70}\n>>> [{key}] {desc}\n{'=' * 70}", flush=True)
    t0 = time.time()
    if cmd == "DEL_TIF":
        p = os.path.join(BASE, "jatim", "model", "demo_classified.tif")
        if os.path.exists(p):
            os.remove(p)
            print(f"[ok] dihapus: {os.path.relpath(p, BASE)}")
        else:
            print("[--] tidak ada (6.3 akan render pertama kali)")
    else:
        r = subprocess.run(cmd, cwd=BASE)
        if r.returncode != 0:
            print(f"\n[STOP] langkah '{key}' gagal (rc={r.returncode}) "
                  f"-- perbaiki lalu jalankan ulang: python finalize_bab6.py {key} ...")
            sys.exit(1)
    print(f"[ok] '{key}' selesai dalam {time.time() - t0:.0f}s", flush=True)

print(f"\nSEMUA LANGKAH SELESAI dalam {(time.time() - t_all) / 60:.1f} menit")
print("Langkah berikutnya: python build.bat, lalu push.bat")
