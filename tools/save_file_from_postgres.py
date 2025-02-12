from sqlalchemy import create_engine, Column, Integer, String, LargeBinary, TIMESTAMP, func
from sqlalchemy.orm import sessionmaker, declarative_base
import shutil
from config.settings import URL_DB_POSTGRES
from models.upload_file_model import FileModel

# ✅ Menggunakan SQLAlchemy 2.0+
Base = declarative_base()

# 📌 Koneksi ke PostgreSQL
engine = create_engine(URL_DB_POSTGRES)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 📌 Fungsi untuk mengambil semua file dari database
def get_all_pdfs_from_db():
    session = SessionLocal()
    try:
        pdf_records = session.query(FileModel).all()  # Ambil semua data dari tabel
        return [{"uuid_file": pdf.uuid_file, "filename": pdf.filename, "content": pdf.content} for pdf in pdf_records]
    finally:
        session.close()

# 📌 Simpan file PDF dari database ke sistem lokal
def save_pdfs_locally(directory="resources/pdf_from_postgres"):
    import os
    
    # Pastikan direktori ada
    if os.path.exists(directory):
        if os.listdir(directory):  # Cek apakah folder tidak kosong
            print(f"📁 Folder {directory} tidak kosong. Menghapus isinya...")
            shutil.rmtree(directory)  # Hapus folder beserta isinya
            os.makedirs(directory)  # Buat ulang folder kosong
    else:
        os.makedirs(directory)

    # Ambil semua PDF dari database
    all_pdfs = get_all_pdfs_from_db()

    if not all_pdfs:
        print("Tidak ada file PDF yang ditemukan di database.")
        return

    # Simpan setiap file ke direktori lokal
    for pdf in all_pdfs:
        file_path = os.path.join(directory, pdf["filename"])
        with open(file_path, "wb") as f:
            f.write(pdf["content"])
        print(f"File {pdf['filename']} telah disimpan di {file_path}")

# 📌 Jalankan fungsi untuk mengambil & menyimpan file PDF
if __name__ == "__main__":
    save_pdfs_locally()
