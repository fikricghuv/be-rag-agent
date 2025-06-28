# app/api/endpoints/file_routes.py
import logging
import uuid 
from fastapi import APIRouter, Depends, HTTPException, status, Path, UploadFile, File, Query # Import Query
from sqlalchemy.exc import SQLAlchemyError
from services.file_service import FileService, get_file_service
from middleware.verify_api_key_header import api_key_auth
from schemas.file_response_schema import FileInfo, FileDeletedResponse, UploadSuccessResponse, EmbeddingProcessResponse
from typing import List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["files"],
)

@router.get("/files", response_model=List[FileInfo], dependencies=[Depends(api_key_auth)])
async def get_all_files_endpoint(
     file_service: FileService = Depends(get_file_service),
):
    """
    Endpoint untuk mengambil seluruh file yang telah diunggah.
    Membutuhkan API Key yang valid di header 'X-API-Key'.
    """
    try:
        logger.info("Received request to get all files.")
        
        files = file_service.fetch_all_files()
        logger.info(f"Returning {len(files)} file entries.")
        
        return files
    
    except SQLAlchemyError as e:
        logger.error(f"Database error in get_all_files_endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal server error occurred while fetching files."
        )
    
    except Exception as e:
        logger.error(f"Unexpected error in get_all_files_endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")

@router.delete("/files/{uuid_file}", response_model=FileDeletedResponse, dependencies=[Depends(api_key_auth)])
async def delete_file_endpoint(
    uuid_file: uuid.UUID = Path(..., description="UUID of the file to delete"),
    file_service: FileService = Depends(get_file_service),

):
    """
    Endpoint untuk menghapus file dari database berdasarkan UUID.
    Membutuhkan API Key yang valid di header 'X-API-Key'.

    Args:
        uuid_file: UUID dari file yang akan dihapus.
    """
    try:
        logger.info(f"Received request to delete file with UUID: {uuid_file}")
        result = file_service.delete_file_from_db(uuid_file=uuid_file)

        logger.info(f"File deletion request successful for UUID: {uuid_file}")
        
        return result

    except HTTPException as e:
        logger.warning(f"HTTPException raised during file deletion for UUID {uuid_file}: {e.detail}", exc_info=True)
        
        raise e
    
    except Exception as e:
        logger.error(f"Unexpected error in delete_file_endpoint for UUID {uuid_file}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")

@router.post("/files/upload-file", response_model=UploadSuccessResponse, dependencies=[Depends(api_key_auth)], status_code=status.HTTP_201_CREATED)
async def upload_file_endpoint(
    file: UploadFile = File(..., description="File to upload"), 
    file_service: FileService = Depends(get_file_service), 
):
    """
    Endpoint untuk mengunggah file ke server dan menyimpannya di database.
    Membutuhkan API Key yang valid di header 'X-API-Key'.
    """
    try:
        logger.info(f"Received upload request for file: {file.filename}")
        
        file_model_instance = await file_service.save_file(file) 
        logger.info(f"File upload successful for {file.filename}")
        
        return UploadSuccessResponse(
            message="File uploaded successfully",
            uuid_file=file_model_instance.uuid_file, 
            filename=file_model_instance.filename 
        )

    except HTTPException as e:
        logger.warning(f"HTTPException raised during file upload for {file.filename}: {e.detail}", exc_info=True)
        
        raise e
    
    except Exception as e:
        logger.error(f"Unexpected error in upload_file_endpoint for {file.filename}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")

@router.post("/files/embedding-file", response_model=EmbeddingProcessResponse, dependencies=[Depends(api_key_auth)])
async def process_embedding_endpoint(
    file_service: FileService = Depends(get_file_service), 
):
    """
    Endpoint untuk memproses embedding dari file berdasarkan UUID.
    Membutuhkan API Key yang valid di header 'X-API-Key'.

    Args:
        uuid_file: UUID dari file yang akan diproses embedding-nya.
    """
    logger.info(f"Received request to process embedding.")
    try:
        result = await file_service.process_embedding() 

        logger.info(f"Embedding processing request successful.")
        
        return EmbeddingProcessResponse(**result)

    except HTTPException as e:
        logger.warning(f"HTTPException raised during embedding processing: {e.detail}", exc_info=True)
        
        raise e
    
    except Exception as e:
        logger.error(f"Unexpected error in process_embedding_endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")

