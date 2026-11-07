# -*- coding: utf-8 -*-
"""Pastikan jatim_best.joblib bisa di-load di proses mana pun.

Kenapa perlu: bila XGBoost jadi model terbaik, 6.2 mendefinisikan kelasnya di
dalam notebook -> pickle mereferensikan `__main__.XGBShift` -> 6.3, 6.6, dan
streamlit_jatim.py gagal saat `joblib.load`.

Skrip ini:
  1. alias `__main__.XGBShift = xgbmod.XGBShift` (memungkinkan pickle lama terbaca)
  2. load model
  3. bila kelasnya berasal dari __main__, dump ulang -> sekarang `xgbmod.XGBShift`
  4. verifikasi load-ulang + predict acak sukses

Jalankan setelah 6.2:  python fix_model_pickle.py
"""
import sys

import joblib
import numpy as np

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
MODEL = r"C:\Users\heker\Downloads\PSD-main\jatim\model\jatim_best.joblib"

# 1) alias dulu, sebelum load apa pun
import xgbmod
xgbmod.register_alias()

# 2) load
clf = joblib.load(MODEL)
mod = type(clf).__module__
print(f"kelas model : {type(clf).__name__} (modul: {mod})")

need_fix = mod == "__main__"
if need_fix:
    # 3) dump ulang dengan kelas milik modul xgbmod -> portable
    clf.__class__ = xgbmod.XGBShift
    joblib.dump(clf, MODEL)
    print("[ok] di-dump ulang -> xgbmod.XGBShift (portable)")

# 4) verifikasi keras: load ulang + prediksi (12 fitur = 6 band + 6 indeks)
clf2 = joblib.load(MODEL)
print(f"reload OK   : {type(clf2).__name__} (modul: {type(clf2).__module__})")

rng = np.random.default_rng(42)
b02, b03, b04, b08, b11, b12 = (rng.integers(200, 6000, size=20).astype(float)
                                for _ in range(6))
X = np.column_stack([
    b02, b03, b04, b08, b11, b12,
    (b08 - b04) / (b08 + b04),
    (b03 - b08) / (b03 + b08),
    (b11 - b08) / (b11 + b08),
    (b08 - b11) / (b08 + b11),
    2.5 * (b08 - b04) / (b08 + 6 * b04 - 7.5 * b02 + 1),
    ((b08 - b04) / (b08 + b04 + 0.5)) * 1.5,
])
assert X.shape[1] == 12, X.shape
pred = clf2.predict(X)
print(f"predict OK  : {sorted(set(map(int, pred)))} (harus di 1..6)")

if not need_fix:
    print("[ok] model sudah portable; tidak ada tindakan.")
else:
    print("[ok] SELESAI -- model aman dibuka 6.3 / 6.6 / streamlit.")
