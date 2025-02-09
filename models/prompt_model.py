from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String

# Model database
Base = declarative_base()

# Model Prompt
class Prompt(Base):
    __tablename__ = "prompts"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    content = Column(String, nullable=False)
