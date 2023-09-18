from typing import Optional, List
from uuid import UUID, uuid4
from pydantic import BaseModel
from enum import Enum

class Gender(str, Enum):
    male = "male"
    female = "female"

class Role (str, Enum):
    admin = "admin"
    user = "user"
    student = "student"

class User(BaseModel):
    id: Optional[UUID] = uuid4()
    first_name: str
    last_name: str
    middle_name: Optional[str]
    mail: str
    gender: Gender
    roles: List[Role]

class UserUpdateRequest(BaseModel):
    first_name: Optional[str]
    last_name: Optional[str]
    middle_name: Optional[str]
    mail: Optional[str]
    roles: Optional[List[Role]]

class DNSRecordBase(BaseModel):
    name: str  # The name of the DNS record (e.g., subdomain.example.com)
    content: str  # The content of the DNS record (e.g., IP address or hostname)
    ttl: int = 3600  # Time to live (TTL) in seconds (default is 3600 seconds)

class DNSARecordCreate(DNSRecordBase):
    type: str = "A"  # DNS record type (A record for IPv4)

class DNSRecordResponse(BaseModel):
    id: str
    type: str
    name: str
    content: str
    ttl: int

class DNSRecordDelete(BaseModel):
    record_id: str  # The ID of the DNS record to delete