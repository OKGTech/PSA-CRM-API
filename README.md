# PSA CRM API

`psa_crm_api` is a small async Python package for interacting with ticketing providers, with a concrete ConnectWise implementation included.

## Overview

This package exposes a provider abstraction for ticket operations and an async ticket client for working with ticket records and notes.

The current implementation includes:

- `psa_crm_api.providers.base.PSACRMProvider` — abstract base class for ticket provider implementations
- `psa_crm_api.providers.connectwise.ConnectWiseManage` — ConnectWise API provider using `aiohttp`
- `psa_crm_api.PSAClient` — async ticket wrapper for loading ticket details, updating status, and managing notes

## Requirements

- Python 3.9+
- `aiohttp`

## Installation

Install from source in a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

Or install directly:

```bash
python -m pip install .
```

## Usage

Example ConnectWise usage with the provided provider:

```python
import asyncio
from ticket_api.providers.connectwise import CWManageAPI
from ticket_api.client import CWManageTicket

async def main():
    api = ConnectWiseManage(
        base_url='https://api-na.myconnectwise.net/v4_6_release/apis/3.0',
        company_id='your_company_id',
        client_id='your_client_id',
        public_key='your_public_key',
        private_key='your_private_key',
    )

    ticket = await CWManageTicket.setup(api_client=api, ticket_number=12345)
    print('Ticket status:', ticket.ticket_status)
    print('Ticket open:', ticket.is_open)

    await ticket.update_status(5)
    note_id = await ticket.add_note('This is an internal note.')
    await ticket.update_note('Updated note content.', note_id)

if __name__ == '__main__':
    asyncio.run(main())
```

## Package structure

- `src/psa_crm_api/client.py` — client wrapper for ticket operations
- `src/psa_crm_api/providers/base.py` — abstract provider interface
- `src/psa_crm_api/providers/connectwise.py` — ConnectWise provider implementation

## Customization

To add another ticket provider, implement the `PSACRMProvider` abstract methods in a new provider class.

## Development

This project uses `pyproject.toml` for package metadata. To run the package locally during development:

```bash
python -m pip install -e .
```

Then import from `psa_crm_api` in your application code.

## Notes

- The repository is intended for private hosting.
- The ConnectWise provider currently uses ConnectWise authentication via company ID and API key pair.
