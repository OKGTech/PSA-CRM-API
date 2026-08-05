from abc import ABC, abstractmethod
from typing import Optional
from ..models import TicketObject, ContactObject, TicketStatusObject, TicketNoteObject, CompanyBaseObject, MemberObject

class PSACRMProvider(ABC):
    
    @abstractmethod
    async def get_member(self, member: int | str) -> MemberObject | None:
        pass

    @abstractmethod
    async def get_ticket(self, ticket_number: int) -> TicketObject | None:
        pass

    @abstractmethod
    async def update_ticket_status(self, ticket_number: int, status_id: int) -> TicketStatusObject:
        pass

    @abstractmethod
    async def get_ticket_note(self, ticket_number: int, note_id: int) -> TicketNoteObject:
        pass
    
    @abstractmethod
    async def add_ticket_note(self, ticket_number: int, note_body: str) -> TicketNoteObject:
        pass

    @abstractmethod
    async def update_ticket_note(self, ticket_number: int, note_id: int, note_body: str, append: bool) -> TicketNoteObject:
        pass

    @abstractmethod
    async def get_contact(
            self,
            *,
            phone_number: Optional[str] = None,
            email_address: Optional[str] = None,
            company: bool = False   
        ) -> ContactObject | CompanyBaseObject | None:
        pass
