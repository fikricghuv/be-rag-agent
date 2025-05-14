# app/api/endpoints/file_routes.py
import logging # Import logging
import uuid # Import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Path, UploadFile, File, Query # Import Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError # Import SQLAlchemyError
# Mengimpor dependency service dan API Key
# Menggunakan service yang sudah digabung (FileService)
from services.file_service import FileService, get_file_service
# Asumsi dependency api_key_auth diimpor dari services.verify_api_key_header
from services.verify_api_key_header import api_key_auth
# Mengimpor Pydantic model respons
# Menggunakan schema yang sudah digabung/diperbaiki
from schemas.file_response_schema import FileInfo, FileDeletedResponse, UploadSuccessResponse, EmbeddingProcessResponse
from typing import List, Dict, Any # Import Dict, Any if needed for EmbeddingProcessResponse (check schema)

# Konfigurasi logging dasar (sesuaikan dengan setup logging aplikasi Anda)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- APIRouter Instance ---
router = APIRouter(
    tags=["files"], # Tag untuk dokumentasi Swagger UI
)

# --- Routes ---

# Endpoint untuk mengambil semua file
# Menerapkan API Key Authentication
@router.get("/files", response_model=List[FileInfo], dependencies=[Depends(api_key_auth)])
async def get_all_files_endpoint(
     # Menggunakan dependency untuk mendapatkan instance service
     file_service: FileService = Depends(get_file_service),
     # current_user: str = Depends(api_key_auth), # Tidak perlu di sini jika sudah di dependencies[]
     # Anda bisa menambahkan pagination di sini jika diperlukan untuk endpoint GET all files
     # offset: int = Query(0, description="Number of items to skip"),
     # limit: int = Query(100, description="Number of items to return per page", le=200),
):
    """
    Endpoint untuk mengambil seluruh file yang telah diunggah.
    Membutuhkan API Key yang valid di header 'X-API-Key'.
    """
    try:
        logger.info("Received request to get all files.")
        # Memanggil metode instance dari service
        # Jika service.fetch_all_files() mendukung pagination, teruskan offset/limit di sini
        files = file_service.fetch_all_files()
        logger.info(f"Returning {len(files)} file entries.")
        # Pydantic dengan orm_mode=True akan mengonversi List[FileModel] menjadi List[FileInfo]
        return files
    # Tangkap SQLAlchemyError secara spesifik
    except SQLAlchemyError as e:
        logger.error(f"Database error in get_all_files_endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal server error occurred while fetching files."
        )
    # Menangkap error tak terduga lainnya yang mungkin terjadi di route layer
    except Exception as e:
        logger.error(f"Unexpected error in get_all_files_endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")


# Endpoint untuk menghapus file berdasarkan UUID
# Menerapkan API Key Authentication
@router.delete("/files/{uuid_file}", response_model=FileDeletedResponse, dependencies=[Depends(api_key_auth)])
async def delete_file_endpoint(
    # Menggunakan Path dan tipe uuid.UUID untuk validasi otomatis
    uuid_file: uuid.UUID = Path(..., description="UUID of the file to delete"),
    # Menggunakan dependency untuk mendapatkan instance service
    file_service: FileService = Depends(get_file_service),
    # current_user: str = Depends(api_key_auth), # Tidak perlu di sini jika sudah di dependencies[]
):
    """
    Endpoint untuk menghapus file dari database berdasarkan UUID.
    Membutuhkan API Key yang valid di header 'X-API-Key'.

    Args:
        uuid_file: UUID dari file yang akan dihapus.
    """
    try:
        logger.info(f"Received request to delete file with UUID: {uuid_file}")
        # Memanggil metode instance dari service
        # Service method akan melempar HTTPException (404 atau 500) jika terjadi error
        result = file_service.delete_file_from_db(uuid_file=uuid_file)

        # Jika service method berhasil dan tidak melempar exception, kembalikan hasilnya
        # Status code default untuk DELETE adalah 200 OK jika ada body, atau 204 No Content jika tidak ada body.
        # Karena kita mengembalikan body dengan pesan sukses, 200 OK (default) sudah tepat.
        logger.info(f"File deletion request successful for UUID: {uuid_file}")
        return result

    # Menangkap HTTPException yang mungkin dilempar oleh service (404, 500)
    except HTTPException as e:
        logger.warning(f"HTTPException raised during file deletion for UUID {uuid_file}: {e.detail}", exc_info=True)
        # Re-raise HTTPException agar ditangani oleh FastAPI
        raise e
    # Menangkap error tak terduga lainnya yang mungkin terjadi di route layer
    except Exception as e:
        logger.error(f"Unexpected error in delete_file_endpoint for UUID {uuid_file}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")

# Endpoint Upload File
# Menerapkan API Key Authentication
@router.post("/files/upload-file", response_model=UploadSuccessResponse, dependencies=[Depends(api_key_auth)], status_code=status.HTTP_201_CREATED)
async def upload_file_endpoint(
    file: UploadFile = File(..., description="File to upload"), # Tambahkan deskripsi
    file_service: FileService = Depends(get_file_service), # Menggunakan service yang sudah digabung
    # current_user: str = Depends(api_key_auth), # Tidak perlu di sini jika sudah di dependencies[]
):
    """
    Endpoint untuk mengunggah file ke server dan menyimpannya di database.
    Membutuhkan API Key yang valid di header 'X-API-Key'.
    """
    try:
        logger.info(f"Received upload request for file: {file.filename}")
        # Memanggil service untuk menyimpan file
        # Service method akan melempar HTTPException 500 jika terjadi error database
        file_model_instance = await file_service.save_file(file) # Menggunakan metode dari service yang digabung

        # Jika service method berhasil dan tidak melempar exception,
        # kembalikan data yang dibutuhkan untuk respons model
        logger.info(f"File upload successful for {file.filename}")
        return UploadSuccessResponse(
            message="File uploaded successfully",
            uuid_file=file_model_instance.uuid_file, # Ambil UUID dari instance model
            filename=file_model_instance.filename # Ambil filename dari instance model
        )

    # Menangkap HTTPException yang mungkin dilempar oleh service (misalnya 500)
    except HTTPException as e:
        logger.warning(f"HTTPException raised during file upload for {file.filename}: {e.detail}", exc_info=True)
        # Re-raise HTTPException agar ditangani oleh FastAPI
        raise e
    # Menangkap error tak terduga lainnya yang mungkin terjadi di route layer
    except Exception as e:
        logger.error(f"Unexpected error in upload_file_endpoint for {file.filename}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")

# Endpoint untuk memproses embedding file
# Menerapkan API Key Authentication
# Mengubah path untuk menerima UUID file
@router.post("/files/embedding-file", response_model=EmbeddingProcessResponse, dependencies=[Depends(api_key_auth)])
async def process_embedding_endpoint(
    file_service: FileService = Depends(get_file_service), # Menggunakan service yang sudah digabung
    # current_user: str = Depends(api_key_auth), # Tidak perlu di sini jika sudah di dependencies[]
):
    """
    Endpoint untuk memproses embedding dari file berdasarkan UUID.
    Membutuhkan API Key yang valid di header 'X-API-Key'.

    Args:
        uuid_file: UUID dari file yang akan diproses embedding-nya.
    """
    logger.info(f"Received request to process embedding.")
    try:
        # Memanggil metode service untuk memproses embedding
        # Service method akan melempar HTTPException (404 atau 500) jika terjadi error
        result = await file_service.process_embedding() # Menggunakan metode dari service yang digabung dan meneruskan UUID

        logger.info(f"Embedding processing request successful.")
        # Mengembalikan hasil dari service, yang sudah sesuai dengan EmbeddingProcessResponse
        # Menggunakan **result untuk unpacking dictionary ke dalam model Pydantic
        return EmbeddingProcessResponse(**result)

    # Menangkap HTTPException yang mungkin dilempar oleh service (404, 500)
    except HTTPException as e:
        logger.warning(f"HTTPException raised during embedding processing: {e.detail}", exc_info=True)
        # Re-raise HTTPException agar ditangani oleh FastAPI
        raise e
    # Menangkap error tak terduga lainnya yang mungkin terjadi di route layer
    except Exception as e:
        logger.error(f"Unexpected error in process_embedding_endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")

