# -*- coding: utf-8 -*-
"""Buat raster evaluasi jujur: model dilatih HANYA dari poligon train (6.2 split).

Kenapa terpisah dari 6.6:
  - jatim_best.joblib (6.2) di-refit ke SELURUH data -> bagus untuk deploy
    (Streamlit), TAPI bila dipakai menilai poligon test, angkanya bocor.
  - Skrip ini melatih varian terbaik HANYA pada poligon train, lalu
    mengklasifikasi raster demo -> demo_classified_eval.tif.
  - 6.6 tinggal membaca artefak ini (resumable, aman dari proses terputus).

Keluaran:
  jatim/model/jatim_best_trainonly.joblib
  jatim/model/demo_classified_eval.tif

Pakai: python make_eval_raster.py [--force]
"""
import os
import sys
import time

import joblib
import numpy as np
import pandas as pd
import rasterio
from sklearn.ensemble import (ExtraTreesClassifier,
                              HistGradientBoostingClassifier,
                              RandomForestClassifier)
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
sys.path.insert(0, r"C:\Users\heker\Downloads\PSD-main")
from xgbmod import XGBShift  # noqa: E402

BASE = r"C:\Users\heker\Downloads\PSD-main"
os.chdir(BASE)
RASTER = "jatim/raster/s2_demo_sidoarjo.tif"
MODEL_OUT = "jatim/model/jatim_best_trainonly.joblib"
TIF_OUT = "jatim/model/demo_classified_eval.tif"
BANDS = ["B02", "B03", "B04", "B08", "B11", "B12"]
SEED = 42
CH = 400000
FORCE = "--force" in sys.argv

_t0 = time.time()


def log(msg):
    print(msg, flush=True)
    try:
        with open(os.path.join(BASE, "jatim", "run_nb.log"), "a", encoding="utf-8") as fh:
            fh.write(msg.rstrip("\n") + "\n")
    except Exception:
        pass


# ------------------------------------------------------------------ 1. data
px = pd.read_csv("jatim/model/jatim_dataset_pixel.csv")
FEATS = BANDS + ["NDVI", "NDWI", "NDBI", "NDMI", "EVI", "SAVI"]
X = px[FEATS].to_numpy()
y = px["class_id"].to_numpy().astype(int)
grp = px["poligon"].to_numpy()

uniq = np.unique(grp)
first_y = pd.Series(y).groupby(grp).first().loc[uniq].to_numpy()
u_tr, u_te = train_test_split(uniq, test_size=0.2, random_state=SEED, stratify=first_y)
tr = np.where(np.isin(grp, u_tr))[0]
te = np.where(np.isin(grp, u_te))[0]
assert len(set(u_tr) & set(u_te)) == 0, "BOCOR: poligon train-test beririsan"
log(f"split: train {len(tr)} px / {len(u_tr)} poligon | "
    f"test {len(te)} px / {len(u_te)} poligon")

# ------------------------------------------------------------------ 2. grid
NJ = 2
MODELS = {
    "RandomForest": [
        lambda d: RandomForestClassifier(n_estimators=300, max_depth=25,
                                         min_samples_leaf=1, random_state=SEED, n_jobs=NJ),
        lambda d: RandomForestClassifier(n_estimators=300, random_state=SEED, n_jobs=NJ),
    ],
    "ExtraTrees": [
        lambda d: ExtraTreesClassifier(n_estimators=300, max_depth=25, min_samples_leaf=1,
                                       random_state=SEED, n_jobs=NJ),
        lambda d: ExtraTreesClassifier(n_estimators=300, random_state=SEED, n_jobs=NJ),
    ],
    "HistGradBoost": [
        lambda d: HistGradientBoostingClassifier(max_depth=12, random_state=SEED),
        lambda d: HistGradientBoostingClassifier(random_state=SEED),
        lambda d: HistGradientBoostingClassifier(max_iter=250, learning_rate=0.05,
                                                 max_leaf_nodes=63, min_samples_leaf=30,
                                                 l2_regularization=1.0, random_state=SEED),
    ],
    "XGBoost": [
        lambda d: XGBShift(n_estimators=400, max_depth=8, learning_rate=0.1, subsample=0.9,
                           colsample_bytree=0.9, tree_method="hist", eval_metric="mlogloss",
                           random_state=SEED, n_jobs=NJ),
        lambda d: XGBShift(n_estimators=500, max_depth=8, learning_rate=0.05, subsample=0.8,
                           colsample_bytree=0.8, min_child_weight=3, tree_method="hist",
                           eval_metric="mlogloss", random_state=SEED, n_jobs=NJ),
    ],
    "SVM-RBF": [
        lambda d: make_pipeline(StandardScaler(), SVC(C=1, random_state=SEED)),
        lambda d: make_pipeline(StandardScaler(), SVC(C=10, random_state=SEED)),
    ],
    "LogReg": [
        lambda d: make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000,
                                                                     random_state=SEED)),
    ],
}

cmp_csv = pd.read_csv("jatim/model/jatim_model_compare.csv")
top = cmp_csv.dropna(subset=["test_accuracy"]).sort_values(
    "cv5_f1_macro", ascending=False).iloc[0]
name, var = str(top["model"]), int(top["best_varian"])
log(f"varian terbaik hasil 6.2: {name} var{var} (cv5_f1={top['cv5_f1_macro']:.4f})")

# ------------------------------------------------- 3. latih (hanya poligon train)
if os.path.exists(MODEL_OUT) and not FORCE:
    clf = joblib.load(MODEL_OUT)
    log(f"model train-only sudah ada -- dilewati: {MODEL_OUT}")
else:
    if name == "SVM-RBF":
        rng = np.random.RandomState(SEED)
        cap = 8000
        sidx = np.concatenate([
            rng.choice(np.where(y[tr] == c)[0],
                       size=min(cap // 6, int((y[tr] == c).sum())), replace=False)
            for c in sorted(np.unique(y))])
        rng.shuffle(sidx)
        Xtr, ytr = X[tr][sidx], y[tr][sidx]
    else:
        Xtr, ytr = X[tr], y[tr]
    t = time.time()
    clf = MODELS[name][var](None)
    clf.fit(Xtr, ytr)
    joblib.dump(clf, MODEL_OUT)
    log(f"model train-only tersimpan ({time.time() - t:.0f}s): {MODEL_OUT}")

pv = clf.predict(X[te])
log(f"[jujur] akurasi PIKSEL test (model train-only) = {(pv == y[te]).mean() * 100:.2f}%")

# ------------------------------------------- 4. klasifikasi raster (resumable)
if os.path.exists(TIF_OUT) and not FORCE:
    s = rasterio.open(TIF_OUT)
    a = s.read(1)
    filled = int((a != 255).sum())
    s.close()
    if filled > 0:
        log(f"raster eval sudah ada & terisi ({filled:,} px) -- dilewati: {TIF_OUT}")
        log(f"selesai total {time.time() - _t0:.0f}s")
        raise SystemExit(0)
    os.remove(TIF_OUT)
    log("raster eval lama kosong/rusak -- dibuat ulang")

src = rasterio.open(RASTER)
arr = src.read().astype(float)
nod = src.nodata
h, w = arr.shape[1], arr.shape[2]
B02, B03, B04, B08, B11, B12 = arr
with np.errstate(divide="ignore", invalid="ignore"):
    feats = np.stack([B02, B03, B04, B08, B11, B12,
                      (B08 - B04) / (B08 + B04),
                      (B03 - B08) / (B03 + B08),
                      (B11 - B08) / (B11 + B08),
                      (B08 - B11) / (B08 + B11),
                      2.5 * (B08 - B04) / (B08 + 6 * B04 - 7.5 * B02 + 1),
                      ((B08 - B04) / (B08 + B04 + 0.5)) * 1.5])
flat = feats.reshape(12, -1).T
ok = np.isfinite(flat).all(axis=1)
if nod is not None:
    ok &= ~(arr.reshape(6, -1).T == nod).any(axis=1)
idx = np.where(ok)[0]
log(f"piksel valid: {len(idx):,} / {flat.shape[0]:,}")

out = np.full(flat.shape[0], 255, dtype=np.uint8)

# ---- checkpoint PER CHUNK: server bisa restart kapan saja, jadi hasil chunk
#      yang sudah selesai tidak boleh hilang. Di dalam `idx` semua piksel pasti
#      valid dan di-predict ke 1..6, jadi piksel 255 = chunk belum dikerjakan.
CHK = "jatim/model/eval_out.npy"
if os.path.exists(CHK):
    try:
        _c = np.load(CHK)
        if _c.shape == out.shape:
            out = _c
            log(f"checkpoint ditemukan ({int((out != 255).sum()):,} px sudah jadi) -- dilanjut")
        else:
            log("checkpoint bentuknya beda -- dibuang")
    except Exception as _e:
        log(f"checkpoint rusak ({_e}) -- dibuang")

nchunk = (len(idx) + CH - 1) // CH
done_k = 0
for k, s0 in enumerate(range(0, len(idx), CH)):
    s = idx[s0:s0 + CH]
    if (out[s] != 255).all():
        done_k += 1
        continue                                   # chunk ini sudah dikerjakan
    out[s] = clf.predict(flat[s]).astype(np.uint8)
    # simpan checkpoint atomik (tulis dulu ke .tmp, lalu rename)
    _chk_tmp = CHK.replace(".npy", ".tmp.npy")
    np.save(_chk_tmp, out)
    os.replace(_chk_tmp + ".npy" if os.path.exists(_chk_tmp + ".npy") else _chk_tmp, CHK)
    log(f"  chunk {k + 1}/{nchunk} ({len(s):,} px) "
        f"-> {time.time() - _t0:.0f}s | isi {int((out != 255).sum()):,}")

if done_k:
    log(f"  {done_k} chunk dilewati (sudah ada di checkpoint)")
if (out != 255).sum() < len(idx):
    raise SystemExit(f"GAGAL: baru {int((out != 255).sum()):,}/{len(idx):,} piksel -- "
                     f"jalankan ulang, chunk berikutnya akan lanjut dari checkpoint")

out = out.reshape(h, w)
prof = src.profile.copy()
prof.update(dtype="uint8", nodata=255, count=1)
TMP = TIF_OUT + ".tmp.tif"
with rasterio.open(TMP, "w", **prof) as dst:
    dst.write(out, 1)
src.close()
os.replace(TMP, TIF_OUT)   # atomik: file lama/parcial tidak pernah terbaca
if os.path.exists(CHK):
    os.remove(CHK)          # raster final sudah jadi -> checkpoint tak perlu lagi
log(f"raster eval tersimpan: {TIF_OUT} "
    f"({os.path.getsize(TIF_OUT):,} byte, {int((out != 255).sum()):,} px)")
log(f"selesai total {time.time() - _t0:.0f}s")
