from pydantic import BaseModel

class CompanyBaseObject(BaseModel):
    company_id: int
    name: str

class ContactBaseObject(BaseModel):
    contact_id: int
    name: str

class ContactObject(ContactBaseObject):
    company: CompanyBaseObject

class MemberObject(BaseModel):
    member_id: int
    username: str
    name: str
    email: str
    extension: int
    custom_fields: dict[int | str, str] | None = None

class TicketStatusObject(BaseModel):
    status_id: int
    name: str | None = None

class TicketObject(BaseModel):
    ticket_id: int
    subject: str
    status: TicketStatusObject
    company: CompanyBaseObject
    contact: ContactBaseObject | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    is_open: bool
    resources: list[MemberObject] | None = None

class TicketNoteObject(BaseModel):
    note_id: int
    text: str
