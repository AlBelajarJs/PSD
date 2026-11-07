# -*- coding: utf-8 -*-
"""Buat folder maps/ berisi peta Folium layar-penuh untuk situs Jupyter Book.

6.4 merujuk maps/folium_*.html tapi folder itu tidak ada -> 3 link rusak.
Sumber: jatim/folium_*.html (hasil 6.1/6.3/6.5/6.6); fallback ke salinan di root.
Jalankan SETELAH 6.3/6.5/6.6 selesai supaya peta yang dikopi adalah yang terbaru.
"""
import os
import shutil
import sys

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

BASE = os.path.dirname(os.path.abspath(__file__))
MAPS = os.path.join(BASE, "maps")
os.makedirs(MAPS, exist_ok=True)

# nama di maps/  -> kandidat sumber (urut prioritas)
WANT = {
    "folium_jatim_samples.html": [r"jatim\folium_jatim_samples.html",
                                  r"folium_jatim_samples.html"],
    "folium_demo_klasifikasi.html": [r"jatim\folium_demo_klasifikasi.html",
                                     r"folium_demo_klasifikasi.html"],
    "folium_wonoayu.html": [r"jatim\folium_wonoayu.html",
                            r"folium_wonoayu.html"],
    # tambahan (opsional, ikut disalin bila ada)
    "folium_eval_jatim.html": [r"jatim\folium_eval_jatim.html",
                               r"folium_eval_jatim.html"],
    "folium_eval_wonoayu.html": [r"jatim\folium_eval_wonoayu.html",
                                 r"folium_eval_wonoayu.html"],
}

ok = miss = 0
for dest_name, srcs in WANT.items():
    src = next((os.path.join(BASE, s) for s in srcs if os.path.exists(os.path.join(BASE, s))),
               None)
    if not src:
        print(f"[--] SUMBER TIDAK ADA: {dest_name} (coba: {srcs[0]})")
        miss += 1
        continue
    dst = os.path.join(MAPS, dest_name)
    shutil.copy2(src, dst)
    kb = os.path.getsize(dst) / 1024
    mtime = os.path.getmtime(src)
    print(f"[ok] {dest_name:34s} {kb:8.0f} KB  (sumber {os.path.relpath(src, BASE)})")
    ok += 1

# link wajib untuk6.4
for req in ("folium_jatim_samples.html", "folium_demo_klasifikasi.html",
            "folium_wonoayu.html"):
    p = os.path.join(MAPS, req)
    if not os.path.exists(p):
        print(f"[!!] LINK WAJIB MASIH KOSONG: maps/{req}")

print(f"\nmaps/: {ok} tersalin, {miss} tidak ada")
print("isi:", ", ".join(sorted(os.listdir(MAPS))) or "(kosong)")
