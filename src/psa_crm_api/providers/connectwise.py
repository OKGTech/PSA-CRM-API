import aiohttp
import asyncio
from typing import Optional
from .base import PSACRMProvider
from ..models import (
    TicketObject,
    TicketNoteObject,
    ContactObject,
    TicketBoardObject,
    TicketStatusObject,
    CompanyBaseObject,
    ContactBaseObject,
    MemberObject,
    CompanyObject
)

class ConnectWiseManage(PSACRMProvider):
    def __init__(
            self,
            base_url: str,
            company_id: str,
            client_id: str,
            public_key: str,
            private_key: str
        ) -> None:
        self.base_url = base_url.rstrip('/')
        self.company_id = company_id
        self.client_id = client_id
        self.public_key = public_key
        self.private_key = private_key

    def _build_url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def _build_auth(self):
        if self.company_id and self.public_key and self.private_key:
            return aiohttp.BasicAuth(login=f"{self.company_id}+{self.public_key}", password=self.private_key)
        return None

    def _build_headers(self) -> dict:
        return {
            'Accept': 'application/json',
            'clientid': self.client_id,
            'Content-Type': 'application/json',
        }

    @staticmethod
    def _parse_custom_fields(fields: list[dict], _filter: list[str | int] | None = None) -> dict[int | str, str | bool | int | None] | None:
        cf = {
            key: field.get('value')
            for field in fields
            for key in (field['id'], field['caption'])
            if not _filter or field['id'] in _filter or field['caption'] in _filter
        }
        return cf or None

    async def _request_json(
            self,
            method: str,
            path: str,
            *,
            json_body: Optional[dict | list[dict]] = None,
            params: Optional[dict] = None,
        ) -> dict | list[dict] | None:

        request_kwargs = {
            'headers': self._build_headers(),
            'auth': self._build_auth(),
        }

        if json_body is not None:
            request_kwargs['json'] = json_body

        if params is not None:
            request_kwargs['params'] = params

        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(method, self._build_url(path), **request_kwargs) as response:
                    if response.status not in range(200, 203):
                        return None
                    try:
                        return await response.json()
                    except aiohttp.ContentTypeError:
                        return None
        except asyncio.TimeoutError:
            return None

    async def get_member(self, member: int | str) -> MemberObject | None:
        """Get ConnectWise member by member id or username, only active members.

        ### Required Permission.
            | Module | Scope              | Access       |
            |:-------|:-------------------|:-------------|
            | System | Member Maintenance | Inquire > All|

        """

        if not (member_res := await self._request_json(
            'GET',
            f'/system/members/{member}',
            params={'fields': 'id,identifier,firstName,lastName,inactiveFlag,officeExtension,officeEmail'}
        )):
            return

        assert isinstance(member_res, dict)

        if member_res['inactiveFlag']:
            return

        return MemberObject(
            member_id=member_res['id'],
            username=member_res['identifier'],
            name=f"{member_res['firstName']} {member_res['lastName']}",
            email=member_res['officeEmail'],
            extension=member_res['officeExtension'],
        )

    async def get_member_custom_fields(self, member: MemberObject, fields: list[int | str]) -> MemberObject:
        """
        Get custom fields for members.

        Parameters:
            member (MemberObject): Member Object from get_member
            fields (list): List if fields IDs or captions
        
        ### Required Permission.
            | Module | Scope      | Access        |
            |:-------|:-----------|:--------------|
            | System | My Account | Inquire > All |
        """
        if not (member_res := await self._request_json(
            'GET',
            f'/system/myaccount/{member.member_id}',
            params={'fields': 'customFields'}
        )):
            return member

        assert isinstance(member_res, dict)

        member.custom_fields = self._parse_custom_fields(member_res.get('customFields', []), fields)

        return member

    async def get_ticket(self, ticket_number: int) -> TicketObject | None:
        """
        ### Required Permission.
            | Module       | Scope                | Access        |
            |:-------------|:---------------------|:--------------|
            | System       | Member Maintenance   | Inquire > All |
            | Service Desk | Service Ticket       | Inquire > All |
            | Service Desk | Close Service Ticket | Inquire > All |
            | Service Desk | Resource Scheduling  | Inquire > All |
        """
        if not (ticket := await self._request_json(
            'GET',
            f'/service/tickets/{ticket_number}',
            params={'fields': 'id,summary,closedFlag,board,status,company,contact,resources,contactEmailAddress,contactPhoneNumber'},
        )):
            return None

        assert isinstance(ticket, dict), "Invalid response received"

        try:
            ticket_contact = ContactBaseObject(contact_id=ticket['contact']['id'], name=ticket['contact']['name'])
        except KeyError:
            ticket_contact = None    

        try:
            resources = [self.get_member(member) for member in ticket['resources'].split(',')]
            members = await asyncio.gather(*resources)
            resource_list = list(filter(None, members))
        except (KeyError, AttributeError):
            resource_list = None

        
        return TicketObject(
            ticket_id=ticket['id'],
            subject=ticket['summary'],
            company=CompanyBaseObject(
                company_id=ticket['company']['id'],
                name=ticket['company']['name'],
            ),
            contact=ticket_contact,
            board=TicketBoardObject(
                board_id=ticket['board']['id'],
                name=ticket['board']['name'],
            ),
            status=TicketStatusObject(
                status_id=ticket['status']['id'],
                name=ticket['status']['name'],
            ),
            contact_email=ticket.get('contactEmailAddress'),
            contact_phone=ticket.get('contactPhoneNumber'),
            is_open=ticket['closedFlag'] == False,
            resources=resource_list,
        )

    async def update_ticket_status(self, ticket_number: int, status_id: int) -> TicketStatusObject:
        """
        ### Required Permission.
            | Module       | Scope                | Access     |
            |:-------------|:---------------------|:-----------|
            | Service Desk | Service Ticket       | Edit > All |
            | Service Desk | Close Service Ticket | Edit > All |
        """
        status = await self._request_json(
            'PATCH',
            f'/service/tickets/{ticket_number}',
            json_body=[{"op": "replace", "path": "status", "value": {'id': status_id}}],
        )

        assert isinstance(status, dict), "Invalid response received"

        return TicketStatusObject(
            status_id=status['status']['id'],
            name=status['status']['name']
        )
        
    
    async def get_ticket_note(self, ticket_number: int, note_id: int) -> TicketNoteObject | None:
        """
        ### Required Permission.
            | Module       | Scope                | Access        |
            |:-------------|:---------------------|:--------------|
            | Service Desk | Service Ticket       | Inquire > All |
        """
        if not (note := await self._request_json(
            'GET',
            f'/service/tickets/{ticket_number}/notes/{note_id}',
        )):
            return None

        assert isinstance(note, dict), "Invalid response received"

        return TicketNoteObject(
            note_id=note['id'],
            text=note['text']
        )

    async def add_ticket_note(self, ticket_number: int, note_body: str) -> TicketNoteObject:
        """
        ### Required Permission.
            | Module       | Scope                | Access     |
            |:-------------|:---------------------|:-----------|
            | Service Desk | Service Ticket       | Edit > All |
        """
        note = await self._request_json(
            'POST',
            f'/service/tickets/{ticket_number}/notes',
            json_body={
                'internalAnalysisFlag': True,
                'resolutionFlag': False,
                'detailDescriptionFlag': False,
                'customerUpdatedFlag': True,
                'text': note_body,
            },
        )

        assert isinstance(note, dict), "Invalid response received"

        return TicketNoteObject(
            note_id=note['id'],
            text=note['text']
        )

    async def update_ticket_note(self, ticket_number: int, note_id: int, note_body: str, append: bool) -> TicketNoteObject:
        """
        ### Required Permission.
            | Module       | Scope                | Access     |
            |:-------------|:---------------------|:-----------|
            | Service Desk | Service Ticket       | Edit > All |
        """
        if append and (curent_note := await self.get_ticket_note(ticket_number=ticket_number, note_id=note_id)):
            note_body = f"{curent_note.text}\n\n{note_body}"
        
        note = await self._request_json(
            'PATCH',
            f'/service/tickets/{ticket_number}/notes/{note_id}',
            json_body=[{"op": "replace", "path": "text", "value": note_body}],
        )

        assert isinstance(note, dict), "Invalid response received"

        return TicketNoteObject(
            note_id=note['id'],
            text=note['text']
        )
    
    async def get_contact(
            self,
            *,
            phone_number: Optional[str] = None,
            email_address: Optional[str] = None,
            company: bool = False   
        ) -> ContactObject | CompanyBaseObject | None:
        """Get CRM contact by phone_number or email_address

        Args:
            phone_number (str): Phone number to use for the lookup
            email_address (str): Email address to use for the lookup
            company (bool): When using a phone number and no match found, search for a company instead of contact. Defaults to False.

        Returns:
            ContactObject: A ContactObject instance with contact and company info
            CompanyBaseObject: A CompanyBaseObject with company info (when company is True)
            None: If no contact found

        
        ### Required Permission.
            | Module       | Scope                | Access        |
            |:-------------|:---------------------|:--------------|
            | Companies    | Company Maintenance  | Inquire > All |
            | Companies    | Contacts             | Inquire > All |
        """
        if (phone_number == None) == (email_address == None):
            raise TypeError(
                "You must provide either a phone number or an email address, but not both"
            )
        
        lookup_type = 'Email' if email_address else 'Phone'
        lookup_value = email_address or phone_number
        args = {
            'childconditions': f'communicationItems/communicationType="{lookup_type}" AND communicationItems/value="{lookup_value}"'
        }
        if not (contacts := await self._request_json(
            'GET',
            f'/company/contacts',
            params=args
        )):
            return None

        assert isinstance(contacts, list), "Invalid reponse model recieved from CW"

        try:
            contact = contacts[0]
        except IndexError:
            pass
        else:
            return ContactObject(
                contact_id=contact['id'],
                name=f"{contact['firstName']} {contact['lastName']}",
                company=CompanyBaseObject(
                    company_id=contact['company']['id'],
                    name=contact['company']['name']
                )
            )

        if phone_number is None or company == False:
            return
        
        companies = await self._request_json(
            'GET',
            f'/company/companies',
            params={'conditions': f'phoneNumber="{phone_number}"'}
        )

        assert isinstance(companies, list), "Invalid reponse model recieved from CW"

        try:
            res_company = companies[0]
        except IndexError:
            return

        return CompanyBaseObject(
            company_id=res_company['id'],
            name=res_company['name']
        )

    async def get_company(self, company_id: int) -> CompanyObject | None:
        """
        ### Required Permission.
            | Module       | Scope                | Access        |
            |:-------------|:---------------------|:--------------|
            | Companies    | Company Maintenance  | Inquire > All |
        """
        if not (company := await self._request_json(
            'GET',
            f'/company/companies/{company_id}',
            params={'fields': 'id,name,types,customFields'}
        )):
            return None

        assert isinstance(company, dict)

        company_types = [t['name'] for t in company.get('types', [])]
        custom_fields = self._parse_custom_fields(company.get('customFields', []))

        return CompanyObject(
            company_id=company['id'],
            name=company['name'],
            company_type=company_types,
            custom_fields=custom_fields
        )
