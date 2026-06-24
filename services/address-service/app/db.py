import boto3
import os
from datetime import datetime
from app.models import Address
from typing import Optional, List

TABLE_NAME = os.getenv("TABLE_NAME", "retail-platform")

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)

async def create_address(address: Address) -> Address:
    """
    Create a new address in DynamoDB.
    PK: ADDRESS#{user_id}
    SK: {address_id}
    """
    pk = f"ADDRESS#{address.user_id}"
    sk = address.address_id
    
    item = {
        "PK": pk,
        "SK": sk,
        "address_id": address.address_id,
        "user_id": address.user_id,
        "street": address.street,
        "city": address.city,
        "state": address.state,
        "postal_code": address.postal_code,
        "country": address.country,
        "is_default": address.is_default,
        "created_at": address.created_at.isoformat() if address.created_at else datetime.utcnow().isoformat(),
        "updated_at": address.updated_at.isoformat() if address.updated_at else datetime.utcnow().isoformat()
    }
    
    table.put_item(Item=item)
    return address

async def get_address(user_id: str, address_id: str) -> Optional[Address]:
    """
    Retrieve a specific address by user_id and address_id.
    """
    pk = f"ADDRESS#{user_id}"
    sk = address_id
    
    response = table.get_item(Key={"PK": pk, "SK": sk})
    
    if "Item" not in response:
        return None
    
    item = response["Item"]
    return Address(
        address_id=item["address_id"],
        user_id=item["user_id"],
        street=item["street"],
        city=item["city"],
        state=item["state"],
        postal_code=item["postal_code"],
        country=item["country"],
        is_default=item.get("is_default", False),
        created_at=datetime.fromisoformat(item["created_at"]) if "created_at" in item else None,
        updated_at=datetime.fromisoformat(item["updated_at"]) if "updated_at" in item else None
    )

async def list_addresses(user_id: str) -> List[Address]:
    """
    List all addresses for a user.
    """
    pk = f"ADDRESS#{user_id}"
    
    response = table.query(
        KeyConditionExpression="PK = :pk",
        ExpressionAttributeValues={":pk": pk}
    )
    
    addresses = []
    for item in response.get("Items", []):
        addresses.append(Address(
            address_id=item["address_id"],
            user_id=item["user_id"],
            street=item["street"],
            city=item["city"],
            state=item["state"],
            postal_code=item["postal_code"],
            country=item["country"],
            is_default=item.get("is_default", False),
            created_at=datetime.fromisoformat(item["created_at"]) if "created_at" in item else None,
            updated_at=datetime.fromisoformat(item["updated_at"]) if "updated_at" in item else None
        ))
    
    return addresses

async def update_address(user_id: str, address_id: str, update_data: dict) -> Optional[Address]:
    """
    Update an address.
    """
    pk = f"ADDRESS#{user_id}"
    sk = address_id
    
    update_data["updated_at"] = datetime.utcnow().isoformat()
    
    update_expression = "SET " + ", ".join([f"{k} = :{k}" for k in update_data.keys()])
    expression_values = {f":{k}": v for k, v in update_data.items()}
    
    response = table.update_item(
        Key={"PK": pk, "SK": sk},
        UpdateExpression=update_expression,
        ExpressionAttributeValues=expression_values,
        ReturnValues="ALL_NEW"
    )
    
    if "Attributes" not in response:
        return None
    
    item = response["Attributes"]
    return Address(
        address_id=item["address_id"],
        user_id=item["user_id"],
        street=item["street"],
        city=item["city"],
        state=item["state"],
        postal_code=item["postal_code"],
        country=item["country"],
        is_default=item.get("is_default", False),
        created_at=datetime.fromisoformat(item["created_at"]) if "created_at" in item else None,
        updated_at=datetime.fromisoformat(item["updated_at"]) if "updated_at" in item else None
    )

async def delete_address(user_id: str, address_id: str) -> bool:
    """
    Delete an address.
    """
    pk = f"ADDRESS#{user_id}"
    sk = address_id
    
    response = table.delete_item(
        Key={"PK": pk, "SK": sk},
        ReturnValues="ALL_OLD"
    )
    
    return "Attributes" in response
