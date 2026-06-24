from fastapi import APIRouter, HTTPException, status, Query
from app.models import (
    Address, AddressCreate, AddressUpdate, AddressResponse, AddressListResponse
)
from app.db import (
    create_address, get_address, list_addresses, update_address, delete_address
)
import uuid
from datetime import datetime

router = APIRouter(prefix="/v1/addresses", tags=["addresses"])

@router.post("/", response_model=AddressResponse, status_code=status.HTTP_201_CREATED)
async def create_user_address(user_id: str, address_data: AddressCreate):
    """
    Create a new address for a user.
    """
    address_id = str(uuid.uuid4())
    timestamp = datetime.utcnow()
    
    address = Address(
        address_id=address_id,
        user_id=user_id,
        street=address_data.street,
        city=address_data.city,
        state=address_data.state,
        postal_code=address_data.postal_code,
        country=address_data.country,
        is_default=address_data.is_default,
        created_at=timestamp,
        updated_at=timestamp
    )
    
    await create_address(address)
    return AddressResponse(**address.model_dump())

@router.get("/{address_id}", response_model=AddressResponse)
async def get_user_address(user_id: str, address_id: str):
    """
    Retrieve a specific address by ID.
    """
    address = await get_address(user_id, address_id)
    if not address:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Address not found"
        )
    return AddressResponse(**address.model_dump())

@router.get("/", response_model=AddressListResponse)
async def get_user_addresses(user_id: str):
    """
    Retrieve all addresses for a user.
    """
    addresses = await list_addresses(user_id)
    return AddressListResponse(
        addresses=[AddressResponse(**addr.model_dump()) for addr in addresses],
        count=len(addresses)
    )

@router.put("/{address_id}", response_model=AddressResponse)
async def update_user_address(
    user_id: str,
    address_id: str,
    address_data: AddressUpdate
):
    """
    Update an existing address.
    """
    existing = await get_address(user_id, address_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Address not found"
        )
    
    update_dict = address_data.model_dump(exclude_unset=True)
    updated_address = await update_address(user_id, address_id, update_dict)
    
    if not updated_address:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update address"
        )
    
    return AddressResponse(**updated_address.model_dump())

@router.delete("/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_address(user_id: str, address_id: str):
    """
    Delete an address.
    """
    success = await delete_address(user_id, address_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Address not found"
        )
    return None
