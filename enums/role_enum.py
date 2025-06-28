from enum import Enum

class RoleEnum(str, Enum):
    user = "user"
    chatbot = "chatbot"
    admin = "admin"

