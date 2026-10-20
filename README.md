## 1. Nama aplikasi dan fungsinya

**Tugasku** adalah aplikasi web Learning Management System super sederhana dengan dua peran:

- **Pengajar**: menambah dan menghapus tugas (judul + instruksi teks), serta melihat data siswa dan progres penyelesaian tugas.
- **Siswa**: melihat daftar tugas dan menandai tugas sebagai selesai (tanpa upload file).

Pengguna mendaftar dan login dengan username dan password. Peran dipilih saat registrasi; pendaftaran sebagai pengajar membutuhkan **kode pengajar** (environment variable `TEACHER_CODE`) agar tidak sembarang orang bisa menjadi pengajar. Data pengguna (pengajar dan siswa), tugas, dan status penyelesaian disimpan di database SQLite.

## 2. Bahasa dan framework

- Python 3.14
- Flask 3.1 (web framework), SQLite
- Pengujian: `pytest`
- SAST: Sonarqube

## 3. Cara menjalankan

```bash
# 1. Clone repository dan masuk ke foldernya
git clone https://github.com/Avicennazakiy/DevSecOPS-p5-0110225154-Avicenna-Zakiy-Zuhair.git
cd DevSecOPS-p5-0110225154-Avicenna-Zakiy-Zuhair

# 2. Buat virtual environment dan install dependency
python -m venv .venv
.venv\Scripts\Activate.ps1       # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 3. Set konfigurasi (Windows PowerShell: $env:TEACHER_CODE="...")
export SECRET_KEY="isi-dengan-string-acak-panjang"
export TEACHER_CODE="kode-rahasia-pengajar"

# 4. Jalankan aplikasi
python run.py
```

Buka http://127.0.0.1:5000
Menjalankan unit test:

```bash
python -m pytest --cov=app --cov-report=term-missing --cov-report=xml:coverage.xml
```

## 4. Overview pipeline CI/CD

Project Tugasku menerapkan pipeline DevSecOps menggunakan GitHub Actions untuk mengotomatisasi pengujian aplikasi dan pemeriksaan keamanan kode. Pipeline dipicu ketika terdapat push atau pull_request pada branch main.

Pipeline terdiri dari dua job utama:

Build and Test
Menyiapkan lingkungan Python 3.14, menginstal dependencies, menjalankan automated testing menggunakan pytest, serta menghasilkan laporan code coverage dalam format XML.

SonarQube SAST and Quality Gate
Mengambil laporan coverage, menjalankan Static Application Security Testing (SAST) menggunakan SonarQube, kemudian memeriksa hasil analisis melalui Quality Gate untuk menentukan apakah kriteria kualitas yang dikonfigurasi telah terpenuhi.

Job SonarQube dijalankan setelah job Build and Test berhasil. Jika pengujian gagal, proses analisis SonarQube tidak dilanjutkan. Hasil pemeriksaan dapat dilihat melalui GitHub Actions dan dashboard SonarQube.