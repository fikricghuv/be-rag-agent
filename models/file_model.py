from pydantic import BaseModel

class FileInfo(BaseModel):
    uuid_file: str
    filename: str

class FileDeleteResponse(BaseModel):
    message: str