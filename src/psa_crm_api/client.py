from typing import Optional
from .providers.base import PSACRMProvider
from .models import TicketObject, TicketStatusObject


class PSAClient:
    def __init__(self) -> None:
        self.api: PSACRMProvider | None = None
        self.ticket_number: int | None = None
        self.note_id: int | None = None
        self.ticket_object: TicketObject | None = None

    @classmethod
    async def setup(cls, api_client: PSACRMProvider, ticket_number: int) -> "PSAClient":
        instance = cls()
        await instance._setup(api_client=api_client, ticket_number=ticket_number)
        return instance

    async def _setup(self, api_client: PSACRMProvider, ticket_number: int) -> None:
        self.api = api_client
        self.ticket_number = ticket_number

        ticket_info = await self.api.get_ticket(ticket_number=ticket_number)

        self.ticket_object = ticket_info

    async def update_status(self, status_id: int) -> None:
        if self.ticket_number is None or self.api is None or self.ticket_object is None:
            raise RuntimeError('Ticket has not been initialized. Call setup() first.')

        status = await self.api.update_ticket_status(self.ticket_number, status_id)
        self.status = status

    async def add_note(self, note_body: str) -> None:
        if self.ticket_number is None or self.api is None:
            raise RuntimeError('Ticket has not been initialized. Call setup() first.')

        note = await self.api.add_ticket_note(self.ticket_number, note_body)
        self.note_id = note.note_id

    async def update_note(self, note_body: str, note_id: Optional[int] = None, append: bool = True) -> None:
        if self.ticket_number is None or self.api is None:
            raise RuntimeError('Ticket has not been initialized. Call setup() first.')
        
        if note_id is None:
            note_id = self.note_id

        if note_id is None:
            raise ValueError('A note id is required to update an existing ticket note.')
        
        updated_note = await self.api.update_ticket_note(self.ticket_number, note_id, note_body, append)
        self.note_id = updated_note.note_id
    
    @property
    def status(self) -> TicketStatusObject:
        if self.ticket_object is None:
            raise RuntimeError('Ticket has not been initialized. Call setup() first.')
        return self.ticket_object.status
    
    @status.setter
    def status(self, new_stauts: TicketStatusObject):
        if self.ticket_object is None:
            raise RuntimeError('Ticket has not been initialized. Call setup() first.')
        self.ticket_object.status = new_stauts
    
    @property
    def is_open(self) -> bool:
        if self.ticket_object is None:
            raise RuntimeError('Ticket has not been initialized. Call setup() first.')
        return self.ticket_object.is_open
