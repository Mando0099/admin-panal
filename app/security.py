from datetime import datetime,timedelta,timezone
from jose import jwt,JWTError
from passlib.context import CryptContext
from fastapi import Depends,HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.config import settings
from app.db import get_db
from app.models import User,ApiKey
pwd=CryptContext(schemes=["bcrypt"],deprecated="auto")
oauth=OAuth2PasswordBearer(tokenUrl="/auth/token")
def hash_password(v): return pwd.hash(v)
def verify_password(v,h): return pwd.verify(v,h)
def token_for(u):
    exp=datetime.now(timezone.utc)+timedelta(minutes=30)
    return jwt.encode({"sub":u.id,"role":u.role,"exp":exp},settings.jwt_secret,algorithm="HS256")
def current_user(token:str=Depends(oauth),db:Session=Depends(get_db)):
    try: data=jwt.decode(token,settings.jwt_secret,algorithms=["HS256"])
    except JWTError: raise HTTPException(401,"Invalid token")
    u=db.get(User,data.get("sub"))
    if not u or not u.active: raise HTTPException(401,"Inactive user")
    return u
def admin_user(u:User=Depends(current_user)):
    if u.role!="admin": raise HTTPException(403,"Admin only")
    return u
def merchant_user(u:User=Depends(current_user)):
    if u.role not in ("merchant","admin"): raise HTTPException(403,"Merchant access only")
    return u
def api_merchant(key:str,db:Session):
    prefix,sep,secret=key.partition(".")
    if not sep: raise HTTPException(401,"Invalid API key")
    row=db.query(ApiKey).filter_by(prefix=prefix,active=True).first()
    if not row or not pwd.verify(secret,row.secret_hash): raise HTTPException(401,"Invalid API key")
    return row.merchant_id
