from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class Address(BaseModel):
    address_id: str = Field(..., description="Unique address identifier")
    user_id: str = Field(..., description="User ID")
    street: str = Field(..., description="Street address")
    city: str = Field(..., description="City")
    state: str = Field(..., description="State/Province")
    postal_code: str = Field(..., description="Postal code")
    country: str = Field(..., description="Country")
    is_default: bool = Field(default=False, description="Is default address")
    created_at: Optional[datetime] = Field(default=None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Update timestamp")

class AddressCreate(BaseModel):
    street: str = Field(..., description="Street address")
    city: str = Field(..., description="City")
    state: str = Field(..., description="State/Province")
    postal_code: str = Field(..., description="Postal code")
    country: str = Field(..., description="Country")
    is_default: bool = Field(default=False, description="Is default address")

class AddressUpdate(BaseModel):
    street: Optional[str] = Field(default=None, description="Street address")
    city: Optional[str] = Field(default=None, description="City")
    state: Optional[str] = Field(default=None, description="State/Province")
    postal_code: Optional[str] = Field(default=None, description="Postal code")
    country: Optional[str] = Field(default=None, description="Country")
    is_default: Optional[bool] = Field(default=None, description="Is default address")

class AddressResponse(BaseModel):
    address_id: str
    user_id: str
    street: str
    city: str
    state: str
    postal_code: str
    country: str
    is_default: bool
    created_at: datetime
    updated_at: datetime

class AddressListResponse(BaseModel):
    addresses: list[AddressResponse]
    count: int
