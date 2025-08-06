# app/utils/save_file_from_postgres_utils.py
from database.models.upload_file_model import FileModel
from core.config_db import config_db
import os

def get_all_pdfs_from_db(filenames: list[str]):
    """Ambil semua PDF dari database berdasarkan list filename."""
    db = next(config_db())
    try:
        pdf_records = (
            db.query(FileModel)
            .filter(FileModel.filename.in_(filenames))
            .all()
        )
        return [
            {
                "uuid_file": pdf.uuid_file,
                "filename": pdf.filename,
                "content": pdf.content
            }
            for pdf in pdf_records
        ]
    finally:
        db.close()

def save_pdfs_locally(filenames: list[str]):
    """Simpan semua file PDF yang ada di DB ke folder lokal."""
    base_dir = "resources/pdf_from_postgres"

    if not os.path.exists(base_dir):
        os.makedirs(base_dir, exist_ok=True)

    all_pdfs = get_all_pdfs_from_db(filenames)

    if not all_pdfs:
        print("Tidak ada file PDF yang ditemukan di database.")
        return
    
    for pdf in all_pdfs:
        file_path = os.path.join(base_dir, pdf["filename"])
        with open(file_path, "wb") as f:
            f.write(pdf["content"])
        print(f"✅ File {pdf['filename']} telah disimpan di {file_path}")

def delete_pdfs_locally(filenames: list[str]):
    """
    Menghapus file PDF di folder lokal hanya jika file tersebut sudah berstatus 'processed' di DB.
    """
    base_dir = "resources/pdf_from_postgres"

    if not os.path.exists(base_dir):
        print("📂 Folder lokal tidak ditemukan.")
        return

    db = next(config_db())
    try:
        
        processed_files = (
            db.query(FileModel)
            .filter(FileModel.filename.in_(filenames), FileModel.status == 'processed')
            .all()
        )

        if not processed_files:
            print("⚠️ Tidak ada file yang berstatus 'processed' untuk dihapus.")
            return

        for file in processed_files:
            file_path = os.path.join(base_dir, file.filename)
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"🗑️ File {file.filename} berhasil dihapus dari lokal.")
            else:
                print(f"⚠️ File {file.filename} tidak ditemukan di folder lokal.")

    finally:
        db.close()