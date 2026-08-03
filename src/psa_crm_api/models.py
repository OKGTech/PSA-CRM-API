from pydantic import BaseModel
from typing import Optional

class CompanyBaseObject(BaseModel):
    company_id: int
    name: str

class ContactBaseObject(BaseModel):
    contact_id: int
    name: str

class ContactObject(ContactBaseObject):
    company: CompanyBaseObject

class TicketStatusObject(BaseModel):
    status_id: int
    name: Optional[str] = None

class TicketObject(BaseModel):
    ticket_id: int
    subject: str
    status: TicketStatusObject
    company: CompanyBaseObject
    contact: Optional[ContactBaseObject] = None    
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    is_open: bool

class TicketNoteObject(BaseModel):
    note_id: int
    text: str