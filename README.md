# Mini LMS (devsecops-p5-[nim])

## 1. Nama aplikasi dan fungsinya

**Mini LMS** adalah aplikasi web Learning Management System super sederhana dengan dua peran:

- **Pengajar**: menambah dan menghapus tugas (judul + instruksi teks), serta melihat data siswa dan progres penyelesaian tugas.
- **Siswa**: melihat daftar tugas dan menandai tugas sebagai selesai (tanpa upload file).

Pengguna mendaftar dan login dengan username dan password. Peran dipilih saat registrasi; pendaftaran sebagai pengajar membutuhkan **kode pengajar** (environment variable `TEACHER_CODE`) agar tidak sembarang orang bisa menjadi pengajar. Data pengguna (pengajar dan siswa), tugas, dan status penyelesaian disimpan di database SQLite.

## 2. Bahasa dan framework

- Python 3.12
- Flask 3.1 (web framework), SQLite (`sqlite3` bawaan Python)
- Pengujian: `unittest` (bawaan Python)
- SAST: Bandit

## 3. Cara menjalankan

```bash
# 1. Clone repository dan masuk ke foldernya
git clone https://github.com/<username>/devsecops-p5-<nim>.git
cd devsecops-p5-<nim>

# 2. Buat virtual environment dan install dependency
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 3. Set konfigurasi (Windows PowerShell: $env:TEACHER_CODE="...")
export SECRET_KEY="isi-dengan-string-acak-panjang"
export TEACHER_CODE="kode-rahasia-pengajar"

# 4. Jalankan aplikasi
python run.py
```

Buka http://127.0.0.1:5000. Database dibuat otomatis di `instance/lms.db`.

Menjalankan unit test:

```bash
python -m unittest discover -s tests -t . -v
```

## 4. Overview pipeline CI/CD

Workflow: `.github/workflows/devsecops.yml` (runner `ubuntu-latest`).
Terpicu pada **push** ke `main` dan **pull request** ke `main`.

| Job | Fungsi | Langkah utama |
|---|---|---|
| `build` | Build dan unit test | install dependency, cek kompilasi (`compileall`), jalankan unit test |
| `sast-scan` (`needs: build`) | SAST dan Quality Gate | jalankan Bandit, simpan laporan JSON sebagai artifact, jalankan Quality Gate |

**Quality Gate** (`scripts/quality_gate.py`): pipeline **gagal** jika Bandit menemukan severity **HIGH** atau **MEDIUM** (batas 0 untuk keduanya; LOW diizinkan). Ambang batas dapat diubah lewat `MAX_HIGH` dan `MAX_MEDIUM` di workflow. Ringkasan hasil juga ditampilkan di halaman summary workflow.

## Struktur proyek

```
app/
  __init__.py   # application factory
  config.py     # konfigurasi dari environment variable
  db.py         # koneksi dan skema SQLite
  security.py   # proteksi CSRF dan header keamanan
  auth.py       # register, login, logout, kontrol akses per peran
  tasks.py      # tugas (tambah, hapus, lihat, tandai selesai) dan data siswa
  templates/    # halaman HTML
  static/       # CSS
tests/          # unit test
scripts/quality_gate.py
run.py
```

## Fitur keamanan yang diterapkan

- Password disimpan sebagai hash (Werkzeug), bukan teks asli
- Semua query SQL memakai parameter (`?`), bukan string formatting
- Otorisasi peran dicek di sisi server; pengajar hanya dapat menghapus tugas miliknya
- Token CSRF pada semua form POST, cookie sesi `HttpOnly` dan `SameSite=Lax`
- Header keamanan (CSP, X-Frame-Options, X-Content-Type-Options)
- Secret dibaca dari environment variable, bukan ditulis di kode

## Keterbatasan yang diketahui

- Belum ada pembatasan percobaan login (rate limiting)
- Belum ada fitur reset password atau verifikasi email
- Semua siswa melihat semua tugas (tidak ada konsep kelas atau mata kuliah)
- Server bawaan Flask hanya untuk pengembangan, bukan produksi
