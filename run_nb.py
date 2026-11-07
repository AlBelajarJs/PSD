# -*- coding: utf-8 -*-
"""Eksekusi notebook bab 6 dengan progres per sel + penyimpanan inkremental.

Pakai: python run_nb.py 6.2_training_model.ipynb [notebook_lain...]

- Progres dicetak per sel (dan ke jatim/run_nb.log) sehingga kelihatan di sel
  mana berjalan/bermasalah.
- Notebook DITULIS ULANG tiap selesai satu sel: bila proses mati di tengah,
  output sel-sel sebelumnya tetap tersimpan (tidak hilang semua).
- Output tersimpan di dalam notebook, sehingga `jupyter-book build`
  (execute_notebooks: off) ikut menampilkannya.
"""
import os
import sys
import time

import nbformat
from nbconvert.preprocessors import ExecutePreprocessor

if len(sys.argv) < 2:
    raise SystemExit(__doc__)

try:
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
except Exception:
    pass

BASE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(BASE, "jatim", "run_nb.log")
os.makedirs(os.path.dirname(LOG), exist_ok=True)
open(LOG, "w", encoding="utf-8").close()   # reset tiap run


def log(msg):
    """Cetak ke stdout DAN ke file log persisten (aman dari shell yang mati)."""
    print(msg, flush=True)
    try:
        with open(LOG, "a", encoding="utf-8") as fh:
            fh.write(msg.rstrip("\n") + "\n")
    except Exception:
        pass


class ProgressPreprocessor(ExecutePreprocessor):
    """ExecutePreprocessor yang mencetak progres + menyimpan notebook tiap sel."""

    def preprocess_cell(self, cell, resources, index):
        t = time.time()
        head = (cell.source.strip().splitlines() or [""])[0][:70]
        log(f"[sel {index + 1}/{self.n_cells}] {head}")
        cell, resources = super().preprocess_cell(cell, resources, index)
        if cell.cell_type == "code":
            for o in cell.get("outputs", []):
                if o.get("output_type") == "stream":
                    txt = "".join(o.get("text", ""))
                    if txt.strip():
                        log(txt.rstrip("\n"))
                elif o.get("output_type") == "error":
                    log(f"  !! ERROR {o.get('ename')}: {o.get('evalue')}")
        log(f"    -> {time.time() - t:.0f}s")
        # simpan segera setelah tiap sel, bukan hanya di akhir
        try:
            nbformat.write(self.book, self.book_path)
        except Exception as e:
            log(f"  (gagal simpan sementara: {e})")
        return cell, resources


for path in sys.argv[1:]:
    t0 = time.time()
    log(f"\n=== {path} ===")
    nb = nbformat.read(path, as_version=4)
    ep = ProgressPreprocessor(timeout=7200, kernel_name="python3")
    ep.n_cells = len(nb.cells)
    ep.book = nb
    ep.book_path = path
    ep.preprocess(nb, {"metadata": {"path": "."}})
    nbformat.write(nb, path)
    log(f"[ok] {path} selesai dalam {time.time() - t0:.0f}s")
