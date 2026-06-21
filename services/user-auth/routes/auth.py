import os, time, uuid, jwt, bcrypt, boto3
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional

router = APIRouter(tags=["auth"])
TABLE = os.environ.get("DYNAMODB_TABLE", "retail-platform")
ENDPOINT = os.environ.get("DYNAMODB_ENDPOINT")
JWT_SECRET = os.environ.get("JWT_SECRET", "change-me-in-prod")

def table():
    kw = {"region_name": os.environ.get("AWS_DEFAULT_REGION","us-east-1")}
    if ENDPOINT: kw["endpoint_url"] = ENDPOINT
    return boto3.resource("dynamodb", **kw).Table(TABLE)

class RegisterReq(BaseModel):
    email: str
    password: str
    name: str

class LoginReq(BaseModel):
    email: str
    password: str

def _make_token(user_id: str, email: str):
    payload = {"user_id": user_id, "email": email, "exp": int(time.time()) + 86400}
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

@router.post("/auth/register")
def register(req: RegisterReq):
    user_id = str(uuid.uuid4())
    hashed = bcrypt.hashpw(req.password.encode(), bcrypt.gensalt()).decode()
    t = table()
    t.put_item(Item={"PK": f"USER#{user_id}", "SK": "METADATA",
        "GSI1PK": f"EMAIL#{req.email}", "GSI1SK": f"USER#{user_id}",
        "user_id": user_id, "email": req.email, "name": req.name,
        "password_hash": hashed, "created_at": str(int(time.time())), "entity_type": "USER"})
    return {"user_id": user_id, "token": _make_token(user_id, req.email)}

@router.post("/auth/login")
def login(req: LoginReq):
    t = table()
    resp = t.query(IndexName="GSI1",
        KeyConditionExpression="GSI1PK = :e",
        ExpressionAttributeValues={":e": f"EMAIL#{req.email}"})
    items = resp.get("Items", [])
    if not items:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    user = items[0]
    if not bcrypt.checkpw(req.password.encode(), user["password_hash"].encode()):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"token": _make_token(user["user_id"], req.email), "user_id": user["user_id"]}

@router.get("/auth/validate")
def validate(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing token")
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return {"user_id": payload["user_id"], "email": payload["email"], "roles": ["user"]}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
