from fastapi import APIRouter, Depends, status, Path, UploadFile, File
from services.file_service import FileService, get_file_service
from schemas.file_response_schema import FileInfo, FileDeletedResponse, UploadSuccessResponse, EmbeddingProcessResponse
from middleware.token_dependency import verify_access_token
from middleware.auth_client_dependency import get_authenticated_client
from typing import List
import logging
from uuid import UUID
from utils.exception_handler import handle_exceptions

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(tags=["files"])

@router.get("/files", response_model=List[FileInfo])
@handle_exceptions(tag="[FILES]")
async def get_all_files_endpoint(
    file_service: FileService = Depends(get_file_service),
    access_token: str = Depends(verify_access_token),
    client_id: UUID = Depends(get_authenticated_client)
):
    logger.info("[FILES] Fetching all uploaded files.")
    return file_service.fetch_all_files(client_id=client_id)

@router.delete("/files/{uuid_file}", response_model=FileDeletedResponse)
@handle_exceptions(tag="[FILES]")
async def delete_file_endpoint(
    uuid_file: UUID = Path(..., description="UUID of the file to delete"),
    file_service: FileService = Depends(get_file_service),
    access_token: str = Depends(verify_access_token),
    client_id: UUID = Depends(get_authenticated_client) 
):
    logger.info(f"[FILES] Request to delete file UUID: {uuid_file}")
    return file_service.delete_file_from_db(uuid_file=uuid_file, client_id=client_id)

@router.post(
    "/files/upload-file", 
    response_model=List[UploadSuccessResponse],
    status_code=status.HTTP_201_CREATED
)
@handle_exceptions(tag="[FILES]")
async def upload_file_endpoint(
    files: List[UploadFile] = File(..., description="Files to upload"), 
    file_service: FileService = Depends(get_file_service),
    access_token: str = Depends(verify_access_token),
    client_id: UUID = Depends(get_authenticated_client)
):
    logger.info(f"[FILES] Uploading {len(files)} file(s)")
    
    uploaded_files = []
    for file in files:
        file_model = await file_service.save_file(file, client_id)
        uploaded_files.append(
            UploadSuccessResponse(
                message="File uploaded successfully",
                uuid_file=file_model.uuid_file,
                filename=file_model.filename
            )
        )
    return uploaded_files

@router.post("/files/embedding-file", response_model=EmbeddingProcessResponse)
@handle_exceptions(tag="[FILES]")
async def process_embedding_endpoint(
    file_service: FileService = Depends(get_file_service), 
    access_token: str = Depends(verify_access_token),
    client_id: UUID = Depends(get_authenticated_client) 
):
    logger.info("[FILES] Processing file embedding.")
    result = await file_service.process_embedding(client_id=client_id)
    return EmbeddingProcessResponse(**result)
