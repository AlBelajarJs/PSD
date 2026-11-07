# -*- coding: utf-8 -*-
"""Kelas pembungkus XGBoost yang PORTABLE untuk pickle.

XGBoost mewajibkan label kelas 0..n-1, sedangkan dataset kita memakai 1..6.
Kelas ini menggeser label saat `fit` lalu mengembalikannya saat `predict`.

Penting: kelas HARUS berada di modul ini (bukan `__main__` notebook), karena
`joblib.dump` menyimpan nama modul+kelas. Bila didefinisikan di dalam notebook,
hasil pickle adalah `__main__.XGBShift` dan `joblib.load` di proses/notebook lain
(6.3, 6.6, streamlit_jatim.py) akan gagal dengan:
    AttributeError: Can't get attribute 'XGBShift' on <module '__main__'>
"""
import numpy as np
from xgboost import XGBClassifier


class XGBShift(XGBClassifier):
    """XGBoost dengan label digeser 1..6 -> 0..5 saat fit, dikembalikan saat predict."""

    def fit(self, X, y, **kw):
        self._y_off = int(np.min(y))          # offset label asli (biasanya 1)
        return super().fit(X, np.asarray(y) - self._y_off, **kw)

    def predict(self, X):
        return super().predict(X) + getattr(self, "_y_off", 1)

    def predict_proba(self, X):
        # kolom tetap berurutan 0..5 -> setara kelas asli 1..6; pengguna
        # memetakan lewat `classes_`, jadi kembalikan apa adanya.
        return super().predict_proba(X)


def register_alias():
    """Daftarkan kelas ini di __main__ supaya pickle lama ('__main__.XGBShift')
    tetap bisa di-load. Panggil SEBELUM joblib.load()."""
    import __main__
    __main__.XGBShift = XGBShift
    return XGBShift


if __name__ == "__main__":
    print("XGBShift OK:", XGBShift)
