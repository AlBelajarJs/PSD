# -*- coding: utf-8 -*-
"""Perbaiki peta Folium 6.3 yang tidak pernah tampil di halaman build.

Penyebab: objek `m` adalah pernyataan terakhir DI DALAM blok `else:`.
IPython hanya menghasilkan execute_result bila node AST TERAKHIR sel adalah
ekspresi (Expr). Karena terakhir adalah pernyataan `if/else` (compound), peta
tidak pernah dirender -> halaman build berisi teks kode saja, tanpa peta.

Perbandingan: 6.1/6.5/6.6 menaruh `m1`/`m2` di LEVEL ATAS -> tampil.

Perbaikan: render eksplisit dengan IPython.display.display() di level atas,
yang tidak tergantung posisi AST.
"""
import sys

import nbformat

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
PATH = r"C:\Users\heker\Downloads\PSD-main\6.3_peta_demo.ipynb"
nb = nbformat.read(PATH, as_version=4)
c = nb.cells[5]
s = c.source

TAIL = """    m.save(OUT_HTML)
    print("tersimpan:", OUT_PNG, "+", OUT_HTML)
    m"""

NEW_TAIL = """    m.save(OUT_HTML)
    print("tersimpan:", OUT_PNG, "+", OUT_HTML)

# --- render peta Folium di halaman build ---
# CATATAN: `m` di atas berada DI DALAM blok else, jadi node AST terakhir sel ini
# adalah pernyataan `if` -- IPython tidak merender ekspresi terakhir yang terbungkus
# blok, sehingga peta tidak pernah muncul di situs. Kita tampilkan eksplisit.
if "m" in globals():
    from IPython.display import display
    display(m)
else:
    print("(peta tidak dibuat: raster/model belum tersedia)")"""

assert TAIL in s, "ekor sel 6.3 berubah -- periksa manual"
assert "display(m)" not in s, "sudah diperbaiki sebelumnya"
c.source = s.replace(TAIL, NEW_TAIL, 1)

nbformat.write(nb, PATH)
nbformat.validate(nbformat.read(PATH, as_version=4))
n = nbformat.read(PATH, as_version=4)
print("6.3 DIPERBARUI.")
print("  display(m):", "display(m)" in n.cells[5].source)
print("  masih ada '    m' polos:", n.cells[5].source.rstrip().endswith("m"))
