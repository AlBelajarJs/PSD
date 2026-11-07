# TUGAS: Otomatis Membuat Data Polygon Training 6 Kelas Jawa Timur

Saya sedang mengerjakan klasifikasi penggunaan/penutupan lahan Jawa Timur menggunakan Sentinel-2A.

Saya membutuhkan DATA TRAINING BERBENTUK POLYGON yang setiap polygon-nya memiliki label kelas.

Jangan melakukan digitasi manual.
Jangan membuat label hanya berdasarkan hasil clustering Sentinel-2.
Jangan menggunakan KMeans sebagai ground truth.
Jangan membuat polygon secara asal/random.

Tugasmu adalah mencari, mengunduh/meng-query, memotong, membersihkan, dan menggabungkan sumber data geospasial resmi menjadi satu dataset training.

## TARGET KELAS

Gunakan tepat 6 kelas:

| class_id | class_name |
|---|---|
| 1 | Sawah |
| 2 | Bangunan / Permukiman |
| 3 | Mangrove |
| 4 | Lahan hijau |
| 5 | Laut |
| 6 | Danau |

Output akhir harus memiliki struktur minimal:

geometry
class_id
class_name
source
source_class

Contoh:

POLYGON(...) | 1 | Sawah | Kementan | Sawah
POLYGON(...) | 2 | Bangunan / Permukiman | BIG | Permukiman
POLYGON(...) | 3 | Mangrove | BIG | Mangrove Lebat
...

---

# 1. WILAYAH

Gunakan Jawa Timur sebagai AOI.

Jika belum ada file batas Jawa Timur, cari/download boundary administrasi Jawa Timur dari sumber geospasial yang terpercaya.

Jika sudah tersedia file boundary Jawa Timur di project, gunakan file tersebut.

Semua dataset harus di-clip ke wilayah Jawa Timur.

Gunakan CRS geografis EPSG:4326 untuk dataset akhir, kecuali ada alasan teknis untuk menggunakan CRS lain selama proses.

---

# 2. SUMBER DATA YANG DIUTAMAKAN

Gunakan sumber resmi/open geospatial data.

## KELAS 1 — SAWAH

Gunakan layer Kementerian Pertanian:

https://sig02.pertanian.go.id/server/rest/services/Sawah/LBS2019/MapServer/22

Layer:
sawah_Jawa_Timur

Ambil polygon sawah yang berada di Jawa Timur.

Tambahkan:

class_id = 1
class_name = "Sawah"

---

# 3. KELAS 2 — BANGUNAN / PERMUKIMAN

Prioritaskan data BIG Peta Penggunaan Tanah 50K:

https://kspservices.big.go.id/satupeta/rest/services/PUBLIK/SUMBER_DAYA_ALAM_DAN_LINGKUNGAN/MapServer/5

Gunakan field kategori yang tersedia seperti:

ptnobjname
ptnsbjname
ptnremarks

Cari kategori yang secara jelas berhubungan dengan:

- Permukiman
- Pemukiman
- Perumahan
- Perkampungan
- Kampung
- Perkotaan
- Permukiman perkotaan
- Permukiman perdesaan
- dan kategori lain yang secara semantik memang merupakan kawasan terbangun/permukiman.

JANGAN memasukkan kategori yang tidak jelas sebagai permukiman.

Tambahkan:

class_id = 2
class_name = "Bangunan / Permukiman"

Catatan:
Untuk training Sentinel-2 10 m, kawasan permukiman lebih berguna daripada individual building footprint yang ukurannya terlalu kecil.

---

# 4. KELAS 3 — MANGROVE

Gunakan data BIG Peta Mangrove:

https://kspservices.big.go.id/satupeta/rest/services/PUBLIK/SUMBER_DAYA_ALAM_DAN_LINGKUNGAN/MapServer/57

Gunakan semua kategori yang memang merupakan mangrove, misalnya:

- Mangrove Lebat
- Mangrove Sedang
- Mangrove Jarang

Gabungkan menjadi satu kelas:

class_id = 3
class_name = "Mangrove"

Jangan memasukkan vegetasi pantai biasa sebagai mangrove.

---

# 5. KELAS 4 — LAHAN HIJAU

Gunakan BIG Peta Penggunaan Tanah 50K:

https://kspservices.big.go.id/satupeta/rest/services/PUBLIK/SUMBER_DAYA_ALAM_DAN_LINGKUNGAN/MapServer/5

Cari kategori yang secara jelas merupakan vegetasi/lahan hijau, misalnya:

- Pertanian lahan kering
- Tegalan
- Kebun
- Perkebunan
- Padang rumput
- Savana
- Semak
- Hutan
- Vegetasi lain yang sesuai

Namun:

JANGAN memasukkan:
- Sawah
- Mangrove
- Permukiman
- Laut
- Danau
- Tambak

karena kategori tersebut sudah mempunyai kelas sendiri atau tidak sesuai dengan definisi "lahan hijau".

Sebelum finalisasi, tampilkan daftar unique value kategori sumber yang ditemukan.

Jika terdapat kategori ambigu, JANGAN langsung memasukkannya.
Laporkan kategori tersebut terlebih dahulu.

Tambahkan:

class_id = 4
class_name = "Lahan hijau"

---

# 6. KELAS 5 — LAUT

Gunakan polygon laut/ocean dari Natural Earth 10m:

https://naciscdn.org/naturalearth/10m/physical/ne_10m_ocean.zip

Download dan ekstrak dataset.

Gunakan polygon laut yang berada di sekitar Jawa Timur.

Karena polygon laut tidak selalu berada di dalam polygon administratif Jawa Timur, jangan hanya melakukan clip terhadap batas daratan Jawa Timur.

Gunakan buffer sekitar 20–30 km dari batas Jawa Timur untuk mengambil area laut yang relevan.

Kemudian gunakan area tersebut sebagai training class Laut.

Tambahkan:

class_id = 5
class_name = "Laut"

PENTING:

Hindari polygon yang terlalu dekat dengan garis pantai jika memungkinkan karena piksel Sentinel-2 10 m dapat menjadi mixed pixel.

---

# 7. KELAS 6 — DANAU

Gunakan sumber geospasial yang memiliki polygon dan dapat mengidentifikasi danau.

Prioritas:

BIG Peta Penggunaan Tanah 50K:

https://kspservices.big.go.id/satupeta/rest/services/PUBLIK/SUMBER_DAYA_ALAM_DAN_LINGKUNGAN/MapServer/5

Cari kategori:

- Danau
- Ranu
- Waduk
- Situ
- Telaga

Namun bedakan antara:

DANAU:
Danau
Ranu
Situ
Telaga

dan kategori air lain yang bukan danau.

Jika sumber tersebut tidak cukup lengkap, cari sumber open geospatial lain yang lebih lengkap untuk polygon danau.

Tambahkan:

class_id = 6
class_name = "Danau"

Jika menggunakan waduk sebagai bagian dari kelas 6, catat keputusan tersebut dalam metadata/source_class karena "waduk" secara definisi berbeda dari danau alami.

---

# 8. CARA DOWNLOAD ARC GIS REST

Untuk layer ArcGIS REST, jangan mencoba mengunduh seluruh dataset nasional jika tidak diperlukan.

Gunakan REST API:

.../FeatureServer/... atau .../MapServer/<layer>

Cari endpoint:

/query

Gunakan parameter seperti:

where=1=1
outFields=*
f=geojson

Jika dataset besar, gunakan pagination:

resultOffset
resultRecordCount

atau gunakan spatial filtering/bounding box Jawa Timur.

Jangan mengambil jutaan feature jika hanya membutuhkan Jawa Timur.

---

# 9. PROSES GEOMETRY

Setelah setiap sumber berhasil diperoleh:

1. Baca menjadi GeoDataFrame.
2. Pastikan CRS diketahui.
3. Reproject ke CRS yang konsisten.
4. Fix invalid geometry.
5. Buang geometry kosong.
6. Clip/intersect dengan AOI.
7. Buang polygon dengan luas terlalu kecil.
8. Buang duplicate geometry.
9. Tambahkan class_id.
10. Tambahkan class_name.
11. Tambahkan source.
12. Tambahkan source_class.

Gunakan:

make_valid()

atau metode geometry repair yang sesuai.

Jangan sampai proses gagal hanya karena beberapa geometry invalid.

---

# 10. JANGAN MEMBUAT TRAINING DATA YANG BURUK

Perhatikan:

- Jangan membuat polygon sangat kecil.
- Jangan memasukkan polygon yang jelas merupakan campuran dua kelas.
- Jangan memasukkan garis pantai sebagai training Laut jika terlalu dekat daratan.
- Jangan memasukkan sawah ke Lahan hijau.
- Jangan memasukkan mangrove ke Lahan hijau.
- Jangan memasukkan tambak sebagai Danau.
- Jangan memasukkan sungai sebagai Danau kecuali sumber memang mengklasifikasikannya sebagai danau.
- Jangan memasukkan permukiman ke Lahan hijau.
- Jangan membuat kelas berdasarkan warna RGB saja.

Tujuan dataset ini adalah menjadi referensi training untuk klasifikasi Sentinel-2.

---

# 11. SAMAKAN STRUKTUR

Semua sumber harus digabung menjadi satu GeoPackage:

training_samples_jawa_timur.gpkg

Layer:

training_samples

Kolom:

fid
geometry
class_id
class_name
source
source_class

Contoh:

| class_id | class_name | source |
|---:|---|---|
| 1 | Sawah | Kementan |
| 2 | Bangunan / Permukiman | BIG |
| 3 | Mangrove | BIG |
| 4 | Lahan hijau | BIG |
| 5 | Laut | Natural Earth |
| 6 | Danau | BIG / sumber lain |

---

# 12. JANGAN MEMASUKKAN SEMUA POLYGON SECARA BUTA

Setelah data diperoleh, hitung:

- jumlah polygon setiap kelas
- luas minimum
- luas maksimum
- luas rata-rata
- luas median
- total luas setiap kelas

Tampilkan tabel:

class_id | class_name | jumlah_polygon | total_area | median_area

Jika salah satu kelas mempunyai terlalu banyak polygon dibanding kelas lain, lakukan sampling yang wajar.

Tujuannya bukan membuat dataset sebesar mungkin.

Tujuannya membuat dataset training yang berkualitas.

---

# 13. SAMPLING

Target awal:

sekitar 100–500 polygon per kelas jika sumber memungkinkan.

Jangan memaksa jumlah yang sama jika suatu kelas memang memiliki sedikit polygon.

Jika jumlah polygon sangat besar:

gunakan random sampling dengan random seed tetap, misalnya:

RANDOM_STATE = 42

Tetapi jangan melakukan sampling sebelum geometry dibersihkan.

---

# 14. CEK DISTRIBUSI SPASIAL

Jangan mengambil semua polygon hanya dari satu lokasi.

Jika memungkinkan, pastikan polygon training tersebar di beberapa wilayah Jawa Timur.

Contoh:

Bangkalan
Sampang
Pamekasan
Sumenep
Surabaya
Sidoarjo
Gresik
Lamongan
Tuban
Bojonegoro
Mojokerto
Jombang
Malang
Pasuruan
Probolinggo
Situbondo
Banyuwangi
dll.

Tidak harus semua kabupaten/kota memiliki semua kelas.

Yang penting training sample tidak terkonsentrasi hanya di satu area.

---

# 15. OUTPUT TAMBAHAN

Selain:

training_samples_jawa_timur.gpkg

buat juga:

training_samples_jawa_timur.geojson

dan CSV metadata:

training_samples_summary.csv

Berisi:

class_id
class_name
source
source_class
polygon_count
total_area
mean_area
median_area

---

# 16. LOG PROSES

Buat file:

download_training_log.txt

yang mencatat:

- source yang berhasil diakses
- source yang gagal
- jumlah feature yang didownload
- jumlah feature setelah clip
- jumlah feature setelah cleaning
- jumlah feature akhir
- error jika ada
- kategori sumber yang digunakan untuk setiap kelas

---

# 17. VALIDASI AKHIR

Setelah selesai, tampilkan:

=== TRAINING DATA SUMMARY ===

Class 1 - Sawah
Jumlah polygon: ...

Class 2 - Bangunan / Permukiman
Jumlah polygon: ...

Class 3 - Mangrove
Jumlah polygon: ...

Class 4 - Lahan hijau
Jumlah polygon: ...

Class 5 - Laut
Jumlah polygon: ...

Class 6 - Danau
Jumlah polygon: ...

Kemudian tampilkan:

TOTAL POLYGON: ...

dan:

TOTAL LUAS: ...

---

# 18. BUAT SCRIPT REPRODUCIBLE

Jangan hanya melakukan download manual.

Buat satu script Python:

download_training_data.py

Script harus dapat dijalankan ulang:

python download_training_data.py

dan otomatis:

1. download/query source
2. download boundary
3. clip Jawa Timur
4. cleaning geometry
5. klasifikasi menjadi 6 kelas
6. sampling
7. merge
8. export GeoPackage
9. export GeoJSON
10. export summary
11. export log

Gunakan library yang umum:

geopandas
pandas
requests
shapely
numpy

Jika perlu library lain, jelaskan kenapa.

---

# 19. PENTING: JANGAN BERHENTI KARENA SATU SUMBER GAGAL

Jika satu sumber gagal:

1. coba endpoint alternatif
2. coba query bbox
3. coba GeoJSON
4. coba REST query
5. cari sumber resmi/open alternatif

Tetapi jangan mengganti data dengan pseudo-label Sentinel-2.

Jika benar-benar tidak ada sumber yang dapat digunakan untuk suatu kelas, laporkan:

SOURCE NOT AVAILABLE

dan jangan mengarang data.

---

# 20. HASIL YANG SAYA INGINKAN DARI KAMU

Kerjakan langsung di environment/project saya.

Saya tidak membutuhkan penjelasan panjang terlebih dahulu.

Prioritas:

1. Temukan sumber.
2. Download/query data.
3. Buat script.
4. Jalankan script.
5. Hasilkan GeoPackage.
6. Hasilkan GeoJSON.
7. Tampilkan summary.
8. Beri tahu lokasi file output.

Setelah selesai, berikan saya:

- lokasi script
- lokasi GeoPackage
- lokasi GeoJSON
- lokasi CSV summary
- jumlah polygon tiap kelas
- apakah ada source yang gagal
- kategori sumber apa saja yang dipakai untuk class 2, 4, dan 6

Jangan melakukan digitasi manual.
Jangan menggunakan Sentinel-2 sebagai sumber label.
Jangan membuat pseudo-ground-truth dari clustering.
Gunakan polygon sumber geospasial yang sudah memiliki informasi penggunaan/penutupan lahan.


las	Sumber	Link	Status
1 Sawah	Kementan LBS 2019	https://sig02.pertanian.go.id/server/rest/services/Sawah/LBS2019/MapServer/22	✅ live, layer sawah_Jawa_Timur (kolomnya persis sama kayak di log download kita)
2 Bangunan, 4 Lahan hijau, 6 Danau	BIG SatuPeta	https://kspservices.big.go.id/satupeta/rest/services/PUBLIK/SUMBER_DAYA_ALAM_DAN_LINGKUNGAN/MapServer — layer 5 (Penggunaan Tanah 50K), 52–55 (Danau/Situ/Embung)	✅ live
3 Mangrove	BIG SatuPeta	.../MapServer/57 (Peta Mangrove 1:25.000)	✅ live, ada di daftar layer
5 Laut	Natural Earth 10m	https://naciscdn.org/naturalearth/10m/physical/ne_10m_ocean.zip	dari readme (tidak saya tes download)
Batas Jatim	GADM v4.1	https://gadm.org (level-1 IDN)	dari log
Citra Sentinel-2A	Copernicus Data Space	https://dataspace.copernicus.eu (koleksi SENTINEL2_L2A, via openEO)	✅ dipakai script kita