# -*- coding: utf-8 -*-
"""Laporan perbaikan Bab 6: bandingkan metrik LAMA (backup) vs BARU (hasil retraining).

Jalankan setelah 6.2 selesai:  python report_bab6.py
"""
import os
import sys

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

MODEL_DIR = "jatim/model"
OLD_DIR = "jatim/model_backup"


def load(path, name):
    p = os.path.join(path, name)
    if not os.path.exists(p):
        return None
    return pd.read_csv(p)


old = load(OLD_DIR, "jatim_model_compare.csv")
new = load(MODEL_DIR, "jatim_model_compare.csv")

print("=" * 74)
print("LAPORAN PERBAIKAN BAB 6 — KLASIFIKASI TUTUPAN LAHAN JAWA TIMUR")
print("=" * 74)

# 1) Data
print("\n[1] DATA LATIH")
old_ds = os.path.join(OLD_DIR, "jatim_dataset_12fitur.csv")
new_ds = os.path.join(MODEL_DIR, "jatim_dataset_pixel.csv")
for tag, p in [("sebelum", old_ds), ("sesudah", new_ds)]:
    if os.path.exists(p):
        d = pd.read_csv(p)
        nan = int(d.filter(regex="^(B0|B1|ND|EV|SA)").isna().sum().sum())
        if "poligon" in d.columns:
            # kolom poligon = id poligon asli -> jumlahnya benar
            nkol = f"{d['poligon'].nunique():>4} poligon"
        else:
            # CSV lama TIDAK menyimpan id poligon; feature_index bukan id poligon
            # (hanya 100 nilai unik) -> jangan diklaim sebagai jumlah poligon.
            nkol = "  n/a poligon (id poligon tidak ada di CSV lama)"
        print(f"  {tag:8s}: {len(d):>7,} baris | {nkol} | missing/NaN fitur: {nan}")

# 2) Metrik
print("\n[2] METRIK MODEL (kolom tersedia di tiap versi)")
if old is not None:
    print("  sebelum:", old.round(4).to_dict("records"))
if new is not None:
    print("  sesudah:")
    cols = [c for c in ["model", "varian", "cv5_accuracy", "cv5_f1_macro",
                        "test_accuracy", "test_f1_macro", "accuracy_gap"] if c in new.columns]
    print(new[cols].round(4).to_string(index=False))
    if {"cv5_accuracy", "test_accuracy"}.issubset(new.columns):
        best = new.dropna(subset=["test_accuracy"]).sort_values(
            "cv5_f1_macro", ascending=False).iloc[0]
        print(f"\n  >>> Model terbaik: {best['model']} (varian {int(best['best_varian'])})")
        print(f"      CV 5-lipatan : {best['cv5_accuracy']:.4f} (+-{best['cv5_accuracy_std']:.4f})")
        print(f"      Test (poligon terpisah): {best['test_accuracy']:.4f}")
        print(f"      Gap CV-test  : {abs(best['cv5_accuracy'] - best['test_accuracy']):.4f} "
              f"-> {'TIDAK overfitting' if abs(best['cv5_accuracy'] - best['test_accuracy']) < 0.05 else 'perlu perhatian'}")

# 3) Evaluasi spasial per poligon (bila sudah dijalankan ulang 6.6)
ev = os.path.join(MODEL_DIR, "eval_poligon_jatim.csv")
if os.path.exists(ev):
    d = pd.read_csv(ev)
    te = d[d["split"] == "test"] if "split" in d.columns else pd.DataFrame()
    print(f"\n[3] EVALUASI SPASIAL (peta hasil klasifikasi vs label, {len(d)} poligon)")
    if len(te):
        from sklearn.metrics import f1_score
        f1 = f1_score(te["true"], te["pred"], average="macro", zero_division=0)
        # ANGKA UTAMA: hanya poligon test (tak pernah dilihat model saat training)
        print(f"    >>> POLIGON TEST (jujur): n={len(te)} | akurasi "
              f"{te['benar'].mean() * 100:.1f}% | F1-macro {f1:.4f}")
        print(f"        (pembanding Rahardian: F1 per poligon ~0,52-0,54)")
        if "train" in d["split"].values:
            trn = d[d["split"] == "train"]
            print(f"    konteks poligon train (in-sample): n={len(trn)} | "
                  f"akurasi {trn['benar'].mean() * 100:.1f}%")
        print(f"    seluruh poligon (campur, jangan diklaim): akurasi "
              f"{d['benar'].mean() * 100:.1f}%")
    else:
        print(f"    akurasi poligon: {d['benar'].mean() * 100:.1f}% "
              "(kolom split tidak ada -- belum evaluasi jujur)")

print("\n" + "=" * 74)
