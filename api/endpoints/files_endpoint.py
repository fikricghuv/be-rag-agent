from fastapi import APIRouter, Depends, HTTPException, status, Path, UploadFile, File, Query
from sqlalchemy.exc import SQLAlchemyError
from services.file_service import FileService, get_file_service
from middleware.verify_api_key_header import api_key_auth
from schemas.file_response_schema import FileInfo, FileDeletedResponse, UploadSuccessResponse, EmbeddingProcessResponse
from middleware.token_dependency import verify_access_token
from typing import List
import uuid
import logging

from utils.exception_handler import handle_exceptions

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(tags=["files"])

@router.get("/files", response_model=List[FileInfo], dependencies=[Depends(api_key_auth)])
@handle_exceptions(tag="[FILES]")
async def get_all_files_endpoint(
     file_service: FileService = Depends(get_file_service),
     access_token: str = Depends(verify_access_token) 
):
    logger.info("[FILES] Fetching all uploaded files.")
    return file_service.fetch_all_files()

@router.delete("/files/{uuid_file}", response_model=FileDeletedResponse, dependencies=[Depends(api_key_auth)])
@handle_exceptions(tag="[FILES]")
async def delete_file_endpoint(
    uuid_file: uuid.UUID = Path(..., description="UUID of the file to delete"),
    file_service: FileService = Depends(get_file_service),
    access_token: str = Depends(verify_access_token) 
):
    logger.info(f"[FILES] Request to delete file UUID: {uuid_file}")
    return file_service.delete_file_from_db(uuid_file=uuid_file)

@router.post("/files/upload-file", response_model=UploadSuccessResponse, dependencies=[Depends(api_key_auth)], status_code=status.HTTP_201_CREATED)
@handle_exceptions(tag="[FILES]")
async def upload_file_endpoint(
    file: UploadFile = File(..., description="File to upload"), 
    file_service: FileService = Depends(get_file_service), 
    access_token: str = Depends(verify_access_token) 
):
    logger.info(f"[FILES] Uploading file: {file.filename}")
    file_model_instance = await file_service.save_file(file)
    return UploadSuccessResponse(
        message="File uploaded successfully",
        uuid_file=file_model_instance.uuid_file,
        filename=file_model_instance.filename
    )

@router.post("/files/embedding-file", response_model=EmbeddingProcessResponse, dependencies=[Depends(api_key_auth)])
@handle_exceptions(tag="[FILES]")
async def process_embedding_endpoint(
    file_service: FileService = Depends(get_file_service), 
    access_token: str = Depends(verify_access_token) 
):
    logger.info("[FILES] Processing file embedding.")
    result = await file_service.process_embedding()
    return EmbeddingProcessResponse(**result)
