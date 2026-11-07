# BAB 1 — BUSINESS UNDERSTANDING

Dokumentasi ini merinci pemahaman bisnis (*Business Understanding*) dalam kerangka metodologi **CRISP-DM** (*Cross-Industry Standard Process for Data Mining*) untuk proyek analisis polutan atmosfer berbasis penginderaan jauh satelit Sentinel-5P di wilayah **Kecamatan Wonoayu, Kabupaten Sidoarjo**.

---

## 1.1 Latar Belakang / Permasalahan

Kualitas udara merupakan indikator fundamental penentu kesehatan lingkungan dan kelangsungan hidup masyarakat. **Kecamatan Wonoayu**, yang terletak di ujung selatan Kabupaten Sidoarjo, Jawa Timur, memiliki posisi geografis dan ekologis yang unik sekaligus rentan:

1. **Karakteristik Wilayah & Koridor Lalu Lintas Industri**: Kecamatan Wonoayu berbatasan langsung dengan Kabupaten Pasuruan dan dilintasi oleh koridor transportasi logistik arteri primer serta aktivitas industri pengolahan. Wilayah ini juga berdekatan dengan kawasan terdampak luapan lumpur Lapindo yang mengalami perubahan tata guna lahan secara masif.
2. **Keterbatasan Stasiun Pemantau Kualitas Udara (SPKU) di Darat**: Stasiun pemantauan kualitas udara terestrial konvensional memerlukan biaya pengadaan dan pemeliharaan instrumen yang sangat tinggi. Akibatnya, stasiun pemantau darat umumnya hanya terkonsentrasi di pusat perkotaan Kabupaten Sidoarjo dan tidak mencakup wilayah sub-urban/rural seperti Kecamatan Wonoayu.
3. **Kebutuhan Pengawasan Spasial Berkelanjutan**: Pemantauan titik tunggal di darat tidak mampu menyajikan resolusi spasial yang merata di seluruh bentang wilayah seluas $\approx 82\text{ km}^2$. 

Oleh karena itu, diperlukan pemanfaatan teknologi penginderaan jauh (*remote sensing*) berbasis satelit **Sentinel-5P TROPOMI** (*Tropospheric Monitoring Instrument*) dari *Copernicus Data Space Ecosystem*. Satelit ini mengorbit bumi secara polar untuk mengukur kolom densitas berbagai gas polutan atmosfer dengan resolusi harian, menjadikannya alternatif terbaik untuk memantau dinamika kualitas udara di Kecamatan Wonoayu secara komprehensif.

> **Rumusan Masalah Utama:**  
> *"Bagaimana memantau, memetakan, dan menganalisis dinamika konsentrasi polutan atmosfer di seluruh wilayah Kecamatan Wonoayu secara berkala selama periode satu tahun penuh tanpa bergantung pada infrastruktur stasiun pemantau darat?"*

---

## 1.2 Tujuan

Proyek sains data ini bertujuan untuk:

1. **Memetakan Konsentrasi Polutan Atmosfer**: Mengumpulkan dan mengolah deret waktu (*time series*) harian konsentrasi 6 polutan udara utama di atas wilayah Kecamatan Wonoayu dari tanggal **31 Agustus 2025 hingga 31 Agustus 2026** (periode 366 hari observasi).
2. **Menganalisis Karakteristik & Dinamika 6 Polutan Utama**:
   - **Nitrogen Dioksida ($\text{NO}_2$)**: Emisi hasil pembakaran bahan bakar kendaraan bermotor dan cerobong industri di sekitar jalur arteri Wonoayu.
   - **Karbon Monoksida ($\text{CO}$)**: Hasil pembakaran hidrokarbon yang tidak sempurna dari sektor transportasi dan pembakaran biomassa.
   - **Formaldehida ($\text{HCHO}$)**: Penanda senyawa organik volatil (*Volatile Organic Compounds* / VOC) yang dilepaskan oleh aktivitas industri kimia dan degradasi vegetasi.
   - **Sulfur Dioksida ($\text{SO}_2$)**: Emisi dari pembakaran batu bara, minyak bumi belerang tinggi, atau proses termal industri.
   - **Ozon Permukaan ($\text{O}_3$)**: Polutan fotokimia sekunder yang terbentuk akibat reaksi fotolisis antara prekursor polutan dengan radiasi sinar matahari.
   - **Metana ($\text{CH}_4$)**: Gas rumah kaca utama yang bersumber dari lahan basah/pertanian sawah, tambak, dan tempat pemrosesan akhir sampah di sekitar wilayah Wonoayu.
3. **Membangun Pipeline Sains Data Terstandar**: Menerapkan tahapan CRISP-DM yang mencakup integrasi database cloud (*Aiven PostgreSQL*), eksplorasi data analitik (*KNIME Analytics Platform*), pembersihan & penanganan nilai hilang (*Interpolasi Linear*), hingga ekstraksi fitur deret waktu (*TSFEL*).

---

## 1.3 Pertanyaan / Kebutuhan Analisis

Untuk memastikan arah analisis terukur dan memberikan wawasan (*actionable insights*) yang aplikatif, kebutuhan analisis dirumuskan ke dalam pertanyaan-pertanyaan kunci berikut:

| No | Kebutuhan Analisis | Pertanyaan Kunci | Luaran yang Diharapkan |
| :-: | :--- | :--- | :--- |
| **1** | **Pola Temporal & Tren Musiman** | Bagaimana variasi konsentrasi polutan harian dan tren musiman (musim kemarau vs. musim hujan) di Kecamatan Wonoayu sepanjang 31 Agustus 2025 – 31 Agustus 2026? | Grafik kurva deret waktu harian dan tren *rolling average* per polutan. |
| **2** | **Kualitas Data & Missing Value** | Berapa proporsi data yang hilang (*missing value*) pada citra satelit Sentinel-5P akibat tutupan awan (*cloud mask*), dan bagaimana strategi imputasi yang mempertahankan kontinuitas sinyal? | Identifikasi 102 nilai *missing* serta pembuktian restorasi deret waktu menggunakan interpolasi linear. |
| **3** | **Deteksi Anomali & Emisi Ekstrem** | Kapan terjadinya peristiwa anomali konsentrasi polutan tertinggi (*peak concentration / outlier*), dan faktor meteorologis atau antropogenik apa yang memicu kondisi tersebut? | Deteksi ambang batas pencilan (*Interquartile Range* / IQR) dan identifikasi tanggal kejadian ekstrem. |
| **4** | **Karakteristik Distribusi Statistik** | Bagaimana bentuk sebaran probabilitas data polutan (apakah simetris atau condong ke kanan / *right-skewed* dengan ekor tebal)? | Metrik deskriptif presisi tinggi: Mean, Deviasi Standar, Kuartil, Skewness, dan Kurtosis. |
| **5** | **Representasi Fitur Deret Waktu** | Fitur-fitur matematika apa saja dari domain statistik, temporal, dan spektral yang paling representatif dalam mencirikan profil polutan di Kecamatan Wonoayu? | Matriks 68 fitur *time series* hasil ekstraksi pustaka TSFEL untuk pemodelan prediktif lanjutan. |

---

> [!NOTE]
> Seluruh prosedur pengumpulan data (*Data Collection*), batas poligon GeoJSON (`wonoayu.geojson`), serta berkas dataset deret waktu tersedia dan dibahas secara mendalam pada **BAB 2 — DATA UNDERSTANDING**.
