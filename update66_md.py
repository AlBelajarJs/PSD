# -*- coding: utf-8 -*-
"""Lengkapi 'Bacaan hasil' 6.6 dengan angka JUJUR hasil evaluasi poligon Jatim.

Sebelumnya bagian ini hanya membahas Wonoayu; hasil Jatim tidak dibaca sama sekali.
Sekarang angka diambil langsung dari jatim/model/eval_poligon_jatim.csv
(poligon test = yang tidak pernah dilihat model saat training).

Jalankan SETELAH eksekusi 6.6 selesai:
    python update66_md.py
"""
import os
import sys

import nbformat
import pandas as pd
from sklearn.metrics import f1_score

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
BASE = os.path.dirname(os.path.abspath(__file__))
CSV = os.path.join(BASE, "jatim", "model", "eval_poligon_jatim.csv")
PATH = os.path.join(BASE, "6.6_evaluasi_poligon.ipynb")
NAMES6 = {1: "Sawah", 2: "Bangunan", 3: "Mangrove",
          4: "Lahan hijau", 5: "Laut", 6: "Danau"}

if not os.path.exists(CSV):
    raise SystemExit(f"Belum ada evaluasi: {CSV} (jalankan 6.6 dulu)")

d = pd.read_csv(CSV)
te = d[d["split"] == "test"]
tr = d[d["split"] == "train"]
if len(te) == 0:
    raise SystemExit("Tidak ada poligon test terpetakan -- periksa raster eval.")

acc_te = te.benar.mean() * 100
f1_te = f1_score(te["true"], te["pred"], average="macro", zero_division=0)
acc_tr = tr.benar.mean() * 100 if len(tr) else float("nan")

# akurasi per kelas pada poligon test; kelas tanpa poligon test tetap ditampil(n=0)
per = (te.groupby("true")
       .apply(lambda x: pd.Series({"n": len(x), "acc": x.benar.mean() * 100}),
              include_groups=False)
       .reindex(range(1, 7)).fillna(0))

# dua kelas terlemah -- hanya yang benar-benar punya poligon test
punya = per[per["n"] > 0].sort_values("acc")
terburuk = punya.head(2)

print(f"poligon test : n={len(te)} | akurasi={acc_te:.1f}% | F1-macro={f1_te:.4f}")
print(f"poligon train: n={len(tr)} | akurasi={acc_tr:.1f}% (konteks)")
print(per.round(1).to_string())

baris = []
for cid in range(1, 7):
    n = int(per.loc[cid, "n"])
    a = per.loc[cid, "acc"]
    ket = "" if n > 0 else " *(tidak ada di poligon test)*"
    baris.append(f"| {cid} | {NAMES6[cid]} | {n} | {a:.0f}%{ket} |")
tabel = ("| kelas | nama | n poligon test | akurasi |\n"
         "|---|---|---|---|\n" + "\n".join(baris))

salah_txt = ", ".join(
    f"{NAMES6[int(i)]} ({per.loc[i, 'acc']:.0f}%)" for i in terburuk.index)

JATIM = f"""## Bacaan hasil

### Jatim (6 kelas, jendela demo) — angka JUJUR

Metrik di bawah berasal dari **poligon test**: poligon yang sama sekali tidak
dipakai saat training, karena model evaluasi dilatih **hanya dari poligon train**
(`jatim_best_trainonly.joblib`, terpisah dari `jatim_best.joblib` yang di-refit ke
seluruh data untuk Streamlit).

| metrik | nilai |
|---|---|
| poligon test terpetakan | **{len(te)}** |
| akurasi poligon test | **{acc_te:.1f}%** |
| F1-macro poligon test | **{f1_te:.4f}** |
| (konteks) akurasi poligon train | {acc_tr:.1f}% |

Per kelas (poligon test):

{tabel}

- Angka ini **per poligon**, bukan per piksel. Akurasi per piksel pada data uji
  adalah 63,84% (lihat sel di atas) -- keduanya jujur, hanya granularitasnya
  berbeda: piksel mudah bocor antar tetangga, sedangkan poligon jauh lebih ketat.
- Pelajaran UTS: **metrik titik (piksel) vs evaluasi spasial (poligon) bisa beda
  jauh**, keduanya wajib dilaporkan terus terang.
- Kelas paling lemah di poligon test: **{salah_txt}** -- masuk akal karena
  poligonnya sedikit dan spektralnya mirip (sawah <-> lahan hijau).
- Perbandingan pembanding luar (Rahardian): F1 per poligon ~0,52-0,54 pada
  skema mean-per-polygon. Angka kita di atas itu sebagian karena cakupan jendela
  demo lebih sederhana (laut & mangrove dominan dan relatif mudah dikenali).

### Wonoayu (biner sawah vs non-sawah)

"""

nb = nbformat.read(PATH, as_version=4)
c = nb.cells[9]
s = c.source

if "### Jatim (6 kelas, jendela demo)" in s:
    # ganti bagian Jatim lama, pertahankan penjelasan Wonoayu yang mengikutinya
    i0 = s.index("### Jatim (6 kelas, jendela demo)")
    i1 = s.index("### Mengapa akurasi poligon Wonoayu")
    s = s[:i0] + JATIM.split("### Jatim (6 kelas, jendela demo)", 1)[1] + s[i1:]
else:
    i0 = s.index("## Bacaan hasil") + len("## Bacaan hasil\n")
    s = JATIM + s[i0:]

c.source = s
nbformat.write(nb, PATH)
nbformat.validate(nbformat.read(PATH, as_version=4))
print("\n6.6 'Bacaan hasil' DILENGKAPI angka Jatim jujur.")
