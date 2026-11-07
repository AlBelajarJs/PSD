# -*- coding: utf-8 -*-
"""Cek apakah output peta Folium benar-benar tersimpan di dalam notebook."""
import sys

import nbformat

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

CHECK = {
    "6.3_peta_demo.ipynb": [5],
    "6.6_evaluasi_poligon.ipynb": [8, 9],
    "6.1_persiapan_klasifikasi.ipynb": None,   # semua sel
    "6.5_klasifikasi_wonoayu.ipynb": None,
}

for path, cells in CHECK.items():
    nb = nbformat.read(path, as_version=4)
    idxs = cells if cells else [i for i, c in enumerate(nb.cells) if c.cell_type == "code"]
    print("=" * 60)
    print(path)
    found = 0
    for i in idxs:
        c = nb.cells[i]
        for j, o in enumerate(c.get("outputs", [])):
            t = o.get("output_type")
            if t in ("display_data", "execute_result"):
                data = o.get("data", {})
                html = data.get("text/html", "")
                has_map = ("leaflet-container" in html) or ("folium-map" in html)
                print(f"  sel{i}[{j}] {t} keys={list(data)} "
                      f"html={len(html)}B PETA={'YA' if has_map else 'tidak'}")
                if has_map:
                    found += 1
    if not found:
        print("  >>> TIDAK ADA OUTPUT PETA TERSIMPAN <<<")
