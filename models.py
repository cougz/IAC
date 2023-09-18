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

class DNSTypes(str, Enum):
    A = "A"
    AAAA = "AAAA"
    NS = "NS"
    MX = "MX"
    CNAME = "CNAME"
    RP = "RP"
    TXT = "TXT"
    SOA = "SOA"
    HINFO = "HINFO"
    SRV = "SRV"
    DANE = "DANE"
    TLSA = "TLSA"
    DS = "DS"
    CAA = "CAA"