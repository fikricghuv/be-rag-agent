from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import shutil
from core.settings import URL_DB_POSTGRES
from database.models.upload_file_model import FileModel

Base = declarative_base()

engine = create_engine(URL_DB_POSTGRES)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_all_pdfs_from_db():
    session = SessionLocal()
    try:
        pdf_records = session.query(FileModel).all()  
        return [{"uuid_file": pdf.uuid_file, "filename": pdf.filename, "content": pdf.content} for pdf in pdf_records]
    finally:
        session.close()

def save_pdfs_locally(directory="resources/pdf_from_postgres"):
    import os

    if os.path.exists(directory):
        if os.listdir(directory): 
            print(f"📁 Folder {directory} tidak kosong. Menghapus isinya...")
            shutil.rmtree(directory) 
            os.makedirs(directory) 
            
        os.makedirs(directory)

    all_pdfs = get_all_pdfs_from_db()

    if not all_pdfs:
        print("Tidak ada file PDF yang ditemukan di database.")
        return

    for pdf in all_pdfs:
        file_path = os.path.join(directory, pdf["filename"])
        with open(file_path, "wb") as f:
            f.write(pdf["content"])
        print(f"File {pdf['filename']} telah disimpan di {file_path}")

if __name__ == "__main__":
    save_pdfs_locally()
