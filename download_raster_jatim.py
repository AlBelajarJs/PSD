"""Download Sentinel-2A Jawa Timur via openEO (Copernicus Data Space Ecosystem).

Fase (jalankan berurutan):
  python download_raster_jatim.py --phase auth      # 1x saja: login device-flow (klik link), simpan refresh token
  python download_raster_jatim.py --phase mean      # ekstraksi mean 6 band per poligon (dengan masking awan SCL)
  python download_raster_jatim.py --phase pixels    # ekstraksi sampel PIKSEL per poligon (masking awan SCL)
                                                    #   -> jatim/features/pixels/pixels_class{N}_p{P}.csv
  python download_raster_jatim.py --phase demo      # download raster komposit ber-awan-masking -> jatim/raster/*.tif

Masking awan (SCL): kelas 3 (cloud shadow), 8 (cloud), 9 (cirrus), 10 (snow), 11 (high-prob cloud)
dijadikan nodata sebelum komposit median, sehingga nilai band tidak lagi terkontaminasi awan.

Butuh: pip install openeo geopandas  (+ akun Copernicus Data Space gratis)
"""

import argparse
import glob
import json
import os

import geopandas as gpd
import numpy as np
import openeo
import pandas as pd
from shapely.geometry import Point

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JATIM_DIR = os.path.join(BASE_DIR, "jatim")
SEED = 42
SAMPLES_GPKG = os.path.join(JATIM_DIR, "training_samples_jawa_timur.gpkg")
FEATURES_DIR = os.path.join(JATIM_DIR, "features")
RASTER_DIR = os.path.join(JATIM_DIR, "raster")

BACKEND = "openeo.dataspace.copernicus.eu"
COLLECTION = "SENTINEL2_L2A"
TEMPORAL_EXTENT = ["2025-08-01", "2025-10-15"]  # musim kemarau Jatim, minim awan
BANDS = ["B02", "B03", "B04", "B08", "B11", "B12"]

# Jendela demo peta: Sidoarjo-Surabaya-Selat Madura (ada 184 poligon sampel, 5 kelas)
DEMO_EXTENT = {"west": 112.60, "south": -7.55, "east": 113.00, "north": -7.05}


def connect(quiet=False):
    conn = openeo.connect(BACKEND)
    try:
        conn.authenticate_oidc_refresh_token()
        if not quiet:
            print("auth: refresh token OK (tanpa login ulang)")
    except Exception as e:
        raise SystemExit(
            f"auth GAGAL ({e}). Jalankan dulu: python download_raster_jatim.py --phase auth"
        )
    return conn


# Koneksi dioptimalkan per-thread: sekali auth dipakai ulang untuk semua attempt
# retry di worker itu (tanpa refresh token berulang tiap kali submit job).
import threading

_TLS = threading.local()


def _get_conn():
    """Koneksi openEO per-thread (cache). Kalau sempat rusak/putus, reset dulu."""
    c = getattr(_TLS, "conn", None)
    if c is None:
        c = connect(quiet=True)
        _TLS.conn = c
    return c


def _reset_conn():
    _TLS.conn = None


# Kata kunci error yang LAYAK dicoba ulang (backoff), bukan langsung menyerah.
# Termasuk error jaringan/DNS sementara yang sering muncul di backend Copernicus.
_RETRY_HINTS = (
    "429", "too many", "timeout", "timed out", "hasil kosong",
    "connection", "name resolution", "getaddrinfo", "max retries",
    "bad gateway", "500", "502", "503", "temporarily", "reset",
    "refused", "ssl", "incomplete read", "newconnectionerror",
    "read timed", "pool", "gateway",
)


def _is_retryable(msg: str) -> bool:
    m = msg.lower()
    return any(h in m for h in _RETRY_HINTS)


def phase_auth(args):
    conn = connect()
    print("Membuka device-flow. Klik link verifikasi yang muncul di bawah,")
    print("masukkan kode user bila diminta, lalu kembali ke sini.")
    conn.authenticate_oidc_device(
        store_refresh_token=True, max_poll_time=args.wait
    )
    print("AUTH OK — refresh token tersimpan, job berikutnya tanpa login ulang.")


def base_cube(conn, mask_clouds=True):
    """Komposit median 6 band. Jika mask_clouds=True, piksel berawan (SCL 3/8/9/10/11)
    dijadikan nodata dulu via `mask`, lalu median dihitung dari sisa piksel bersih."""
    bands = BANDS + (["SCL"] if mask_clouds else [])
    cube = conn.load_collection(
        COLLECTION,
        temporal_extent=TEMPORAL_EXTENT,
        bands=bands,
    )
    if mask_clouds:
        from openeo.processes import between, or_
        scl = cube.band("SCL")

        def _cloud(x):
            # SCL 3 (cloud shadow), 8-9 (cloud), 10 (cirrus), 11 (snow)
            return or_(between(x, 3, 3), between(x, 8, 11))

        cube = cube.mask(scl.apply(_cloud)).filter_bands(BANDS)
    cube = cube.reduce_dimension(dimension="t", reducer="median")
    return cube


def _run_part(task):
    import time
    cid, p, geoms, part_csv, redo = task
    if os.path.exists(part_csv) and not redo:
        return f"[skip] kelas {cid} part {p} sudah ada"
    last = None
    for attempt in range(1, 7):
        try:
            conn = connect()
            cube = base_cube(conn, mask_clouds=not args_no_mask)
            cube = cube.aggregate_spatial(
                reducer="mean",
                geometries={"type": "FeatureCollection", "features": geoms},
            )
            cube.execute_batch(
                title=f"Jatim S2 features kelas {cid} p{p}",
                outputfile=part_csv, out_format="CSV",
            )
            if (not os.path.exists(part_csv)) or os.path.getsize(part_csv) == 0:
                if os.path.exists(part_csv):
                    os.remove(part_csv)
                raise IOError(f"hasil kosong (0 byte): {part_csv}")
            return f"[ok] tersimpan: {part_csv}"
        except Exception as e:
            last = e
            msg = f"{type(e).__name__}: {str(e)[:120]}"
            if "429" in msg or "Too Many" in msg or "timeout" in msg.lower() or "hasil kosong" in msg:
                wait = 30 * attempt
                print(f"[retry {attempt}/6] kelas {cid} part {p} ({msg}) — tunggu {wait}s")
                time.sleep(wait)
            else:
                break
    return f"[GAGAL] kelas {cid} part {p}: {type(last).__name__}: {str(last)[:200]}"


# Variabel global yang diisi phase_features/phase_pixels agar _run_part tahu
# apakah masking awan aktif (bisa dimatikan lewat --no-mask untuk perbandingan).
args_no_mask = False


def phase_features(args):
    from concurrent.futures import ThreadPoolExecutor, as_completed
    global args_no_mask
    args_no_mask = args.no_mask
    os.makedirs(FEATURES_DIR, exist_ok=True)
    g = gpd.read_file(SAMPLES_GPKG, layer="training_samples")
    # Sederhanakan geometri (toleransi ~10 m = ukuran piksel) + bulatkan koordinat:
    # payload process-graph backend dibatasi (~413 di atas ~3 MB), jadi kirim per chunk kecil.
    gs = g.copy()
    gs["geometry"] = (
        g.to_crs("EPSG:32749").geometry.simplify(10).to_crs("EPSG:4326")
    )
    tasks, chunks = [], {}
    for cid in sorted(g["class_id"].unique().tolist()):
        sub = gs[gs["class_id"] == cid].reset_index(drop=True)
        chunks[cid] = []
        for p, start in enumerate(range(0, len(sub), 100)):
            chunk = sub.iloc[start:start + 100]
            part_csv = os.path.join(FEATURES_DIR, f"features_class{cid}_p{p}.csv")
            chunks[cid].append(part_csv)
            geoms = [
                {"type": "Feature", "properties": {"fid": int(i)},
                 "geometry": json.loads(gpd.GeoSeries([geom]).to_json())["features"][0]["geometry"]}
                for i, geom in zip(chunk.index, chunk.geometry)
            ]
            tasks.append((cid, p, geoms, part_csv, args.redo))
    print(f"[info] {len(tasks)} job, {args.workers} worker paralel | masking_awan={not args.no_mask}")
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(_run_part, t): t for t in tasks}
        for f in as_completed(futs):
            try:
                print(f.result())
            except Exception as e:
                t = futs[f]
                print(f"[GAGAL] kelas {t[0]} part {t[1]}: {type(e).__name__}: {str(e)[:200]}")
    for cid, parts in chunks.items():
        done = [p for p in parts if os.path.exists(p)]
        if len(done) != len(parts):
            print(f"[WARN] kelas {cid}: {len(done)}/{len(parts)} part — gabungan ditunda")
            continue
        out_csv = os.path.join(FEATURES_DIR, f"features_class{cid}.csv")
        pd.concat([pd.read_csv(p) for p in parts], ignore_index=True).to_csv(out_csv, index=False)
        print(f"[ok] gabungan kelas {cid}: {out_csv}")


PIXEL_DIR = os.path.join(JATIM_DIR, "features", "pixels")
PIXELS_PER_POLYGON = 30   # titik sampel per poligon (acak, dalam poligon)
POINTS_PER_JOB = 1200     # payload ~150 KB per job (batas backend ~3 MB)


def phase_pixels(args):
    """Sampel piksel per poligon: titik acak di dalam tiap poligon, dibaca lewat
    aggregate_spatial (mean 1 piksel = nilai piksel titik itu). Hasil: banyak baris
    per poligon -> data latih pixel-level, sekaligus poligon yang sebelumnya hilang
    karena nodata total ikut terwakili (titik valid tetap ada)."""
    from concurrent.futures import ThreadPoolExecutor, as_completed
    import time
    global args_no_mask
    args_no_mask = args.no_mask
    os.makedirs(PIXEL_DIR, exist_ok=True)
    rng = np.random.default_rng(SEED)
    g = gpd.read_file(SAMPLES_GPKG, layer="training_samples").reset_index(drop=True)
    gu = g.to_crs("EPSG:32749")

    # titik acak per poligon; poligon kecil tetap dapat kuota penuh (duplikat piksel
    # diperbolehkan — mencerminkan komposisi kelas yang homogen)
    pts, meta = [], []
    pid = 0
    for i, row in gu.iterrows():
        geom = row.geometry
        if geom is None or geom.is_empty:
            continue
        n = PIXELS_PER_POLYGON
        minx, miny, maxx, maxy = geom.bounds
        got = 0
        tries = 0
        while got < n and tries < n * 20:
            tries += 1
            x = rng.uniform(minx, maxx)
            y = rng.uniform(miny, maxy)
            if geom.contains(Point(x, y)):
                pts.append((x, y))
                meta.append({"pid": pid, "poligon": int(i), "class_id": int(row["class_id"])})
                pid += 1
                got += 1
    pm = gpd.GeoDataFrame(
        meta,
        geometry=[Point(x, y) for x, y in pts],
        crs="EPSG:32749",
    ).to_crs("EPSG:4326")
    print(f"[info] {len(pm)} titik dari {pm['poligon'].nunique()} poligon "
          f"| masking_awan={not args.no_mask}")

    jobs = []
    for p, start in enumerate(range(0, len(pm), POINTS_PER_JOB)):
        chunk = pm.iloc[start:start + POINTS_PER_JOB]
        part_csv = os.path.join(PIXEL_DIR, f"pixels_p{p}.csv")
        geoms = [
            {"type": "Feature", "properties": {"pid": int(r["pid"])},
             "geometry": json.loads(gpd.GeoSeries([r.geometry]).to_json())["features"][0]["geometry"]}
            for _, r in chunk.iterrows()
        ]
        jobs.append((p, part_csv, geoms))

    ok = fail = 0
    pending = [(p, part_csv, geoms) for p, part_csv, geoms in jobs]
    # Pass otomatis: kalau ada yang gagal (429/DNS putus), langsung ulangi yang
    # belum ada sampai bersih — maks 3 pass, file sudah jadi selalu di-skip.
    for pass_no in range(1, 4):
        if pass_no > 1 and not pending:
            break
        ok = fail = 0
        failed = []
        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            futs = {ex.submit(_run_pixel_part, part_csv, geoms, args.redo): (p, part_csv)
                    for p, part_csv, geoms in pending}
            for f in as_completed(futs):
                p, part_csv = futs[f]
                try:
                    msg = f.result()
                except Exception as e:
                    msg = f"[GAGAL] {os.path.basename(part_csv)}: {e}"
                print(msg, flush=True)
                if msg.startswith("[ok]") or msg.startswith("[skip]"):
                    ok += 1
                else:
                    fail += 1
                    failed.append((p, part_csv,
                                   next(g for pp, pc, g in jobs if pp == p)))
        print(f"[info] pass {pass_no}: {ok} ok, {fail} gagal", flush=True)
        pending = failed
        if not pending:
            break
        if pass_no < 3:
            print(f"[info] ulangi {len(pending)} bagian gagal (pass {pass_no + 1})...",
                  flush=True)
            time.sleep(15)
    if pending:
        print(f"[WARN] masih {len(pending)} bagian gagal — jalankan ulang fase pixels "
              f"(yang sudah ada tetap di-skip)")
        return
    parts = sorted(glob.glob(os.path.join(PIXEL_DIR, "pixels_p*.csv")))
    rows = []
    for p, part_csv, _geoms in jobs:
        d = pd.read_csv(part_csv)
        # feature_index = posisi fitur (0-based) dalam FeatureCollection job ini;
        # daftar pid dikirim berurutan -> pid = pids[feature_index]
        pids = [g_["properties"]["pid"] for g_ in _geoms]
        d["pid"] = [pids[int(i)] for i in d["feature_index"] if int(i) < len(pids)]
        rows.append(d[["pid"] + BANDS])
    px = pd.concat(rows, ignore_index=True)
    px = px.merge(pm[["pid", "poligon", "class_id"]], on="pid", how="left")
    nan_n = int(px[BANDS].isna().any(axis=1).sum())
    print(f"[info] piksel: {len(px)} baris | NaN (nodata sisa): {nan_n} "
          f"({100 * nan_n / max(len(px), 1):.1f}%)")
    out_csv = os.path.join(FEATURES_DIR, "pixels_all.csv")
    px.to_csv(out_csv, index=False)
    print(f"[ok] gabungan: {out_csv}")


def _run_pixel_part(part_csv, geoms, redo):
    import time
    if os.path.exists(part_csv) and not redo:
        return f"[skip] {os.path.basename(part_csv)} sudah ada"
    last = None
    for attempt in range(1, 9):
        try:
            conn = _get_conn()
            cube = base_cube(conn, mask_clouds=not args_no_mask)
            cube = cube.aggregate_spatial(
                reducer="mean",
                geometries={"type": "FeatureCollection", "features": geoms},
            )
            cube.execute_batch(
                title=f"Jatim S2 pixels p{os.path.basename(part_csv)}",
                outputfile=part_csv, out_format="CSV",
            )
            if (not os.path.exists(part_csv)) or os.path.getsize(part_csv) == 0:
                if os.path.exists(part_csv):
                    os.remove(part_csv)
                raise IOError(f"hasil kosong (0 byte): {part_csv}")
            return f"[ok] tersimpan: {os.path.basename(part_csv)}"
        except SystemExit:
            raise
        except Exception as e:
            last = e
            msg = f"{type(e).__name__}: {str(e)[:120]}"
            if _is_retryable(msg):
                # backoff 5..60s (2x tiap kali, dibatasi) — server Copernicus
                # biasanya pulih <1 menit untuk 429/DNS/putus sesaat
                wait = min(5 * (2 ** (attempt - 1)), 60)
                if any(k in msg.lower() for k in ("connection", "getaddrinfo",
                                                  "name resolution", "max retries")):
                    _reset_conn()  # koneksi/ DNS rusak -> bikin baru di attempt berikutnya
                print(f"[retry {attempt}/8] {os.path.basename(part_csv)} ({msg}) — tunggu {wait}s",
                      flush=True)
                time.sleep(wait)
            else:
                break
    return f"[GAGAL] {os.path.basename(part_csv)}: {type(last).__name__}: {str(last)[:200]}"


def phase_demo(args):
    import time
    os.makedirs(RASTER_DIR, exist_ok=True)
    out_tif = os.path.join(RASTER_DIR, "s2_demo_sidoarjo.tif")
    if os.path.exists(out_tif) and os.path.getsize(out_tif) > 0 and not args.redo:
        print(f"[skip] sudah ada: {out_tif}")
        return
    conn = connect()
    cube = base_cube(conn)
    cube = cube.filter_bbox(**DEMO_EXTENT)
    cube = cube.resample_spatial(resolution=args.res, projection=32749)
    last = None
    for attempt in range(1, 5):
        try:
            print(f"[job] batch demo {DEMO_EXTENT} @ {args.res}m (coba {attempt}/4) ...")
            job = cube.create_job(title="Jatim S2 demo Sidoarjo", out_format="GTiff")
            print("job id:", job.job_id, "- menunggu selesai ...")
            job.start_and_wait()
            assets = job.download_results(RASTER_DIR)
            tifs = [a for a in (assets or []) if str(a).lower().endswith(".tif")]
            if not tifs:
                tifs = [os.path.join(RASTER_DIR, f) for f in os.listdir(RASTER_DIR)
                        if f.lower().endswith(".tif")]
            if not tifs:
                raise IOError("tidak ada aset .tif dari job")
            src = tifs[0] if isinstance(tifs[0], str) else str(tifs[0])
            if os.path.abspath(src) != os.path.abspath(out_tif):
                if os.path.exists(out_tif):
                    os.remove(out_tif)
                os.rename(src, out_tif)
            print(f"[ok] tersimpan: {out_tif}")
            return
        except Exception as e:
            last = e
            print(f"[retry {attempt}/4] {type(e).__name__}: {str(e)[:150]} — tunggu 60s")
            time.sleep(60)
    raise SystemExit(f"demo GAGAL permanen: {last}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", choices=["auth", "features", "pixels", "demo"], required=True)
    ap.add_argument("--wait", type=int, default=1800, help="detik maks menunggu klik auth")
    ap.add_argument("--res", type=int, default=20, help="resolusi meter raster demo")
    ap.add_argument("--redo", action="store_true", help="ulangi job features walau CSV ada")
    ap.add_argument("--workers", type=int, default=5, help="worker paralel fase features")
    ap.add_argument("--no-mask", action="store_true",
                    help="matikan masking awan SCL (untuk eksperimen perbandingan)")
    ns = ap.parse_args()
    {"auth": phase_auth, "features": phase_features,
     "pixels": phase_pixels, "demo": phase_demo}[ns.phase](ns)
