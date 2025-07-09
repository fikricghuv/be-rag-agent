from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class FileInfo(BaseModel):
    """
    Respons model untuk mendapatkan inforamsi file.
    """
    uuid_file: UUID
    filename: str
    uploaded_at: datetime
    status: str

class FileDeletedResponse(BaseModel):
    """
    Respons model untuk konfirmasi penghapusan file.
    """
    message: str

class UploadSuccessResponse(BaseModel):
    """
    Respons model untuk konfirmasi upload file yang sukses.
    """
    message: str
    uuid_file: UUID # Menggunakan tipe UUID untuk konsistensi
    filename: str

class EmbeddingProcessResponse(BaseModel):
    """
    Respons model untuk hasil pemrosesan embedding file.
    """
    message: str
