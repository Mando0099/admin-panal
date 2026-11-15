import hmac,hashlib,json,secrets
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI,Depends,HTTPException,Header,Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel,EmailStr,Field
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db import Base,engine,get_db
from app.models import *
from app.security import *
from app.config import settings
from app.providers.fawaterak import Fawaterak,ProviderNotReady

# تم إضافة مكتبات Alembic لتشغيل الـ Migrations تلقائياً عند البدء
from alembic.config import Config
from alembic import command

app=FastAPI(title="MerchantHub API",version="0.1.0")

_origins=[x.strip() for x in settings.cors_origins.split(",") if x.strip()]
app.add_middleware(CORSMiddleware, allow_origins=_origins or ["*"], allow_credentials=False,
                   allow_methods=["GET","POST","PUT","DELETE","OPTIONS"],
                   allow_headers=["Authorization","Content-Type","X-API-Key"])

Base.metadata.create_all(bind=engine)

class MerchantIn(BaseModel):
    code:str; legal_name:str; owner_email:EmailStr; owner_name:str
    owner_password:str=Field(min_length=12)

class PaymentIn(BaseModel):
    order_ref:str; amount_minor:int=Field(gt=0); currency:str=Field(min_length=3,max_length=3)
    customer_name:str; customer_email:EmailStr; customer_phone:str=""

class FeeIn(BaseModel):
    platform_bps:int=Field(ge=0,le=10000); gateway_mode:str
    gateway_bps:int=Field(ge=0,le=10000); fixed_gateway_minor:int=Field(ge=0)

class WithdrawalIn(BaseModel):
    amount_minor:int=Field(gt=0); currency:str; method:str="manual"

@app.on_event("startup")
def bootstrap():
    # تشغيل هجرات Alembic تلقائياً أول ما السيرفر يقوم
    try:
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
    except Exception as e:
        print(f"Migration error: {e}")

    db=next(get_db())
    try:
        admin_email = settings.admin_email.strip().lower()
        admin = db.query(User).filter(func.lower(User.email) == admin_email).first()
        if not admin:
            db.add(User(email=admin_email, name="Administrator",
                        password_hash=hash_password(settings.admin_password), role="admin"))
            db.commit()
        elif settings.admin_sync_password_on_startup and not verify_password(settings.admin_password, admin.password_hash):
            admin.email = admin_email
            admin.password_hash = hash_password(settings.admin_password)
            admin.role = "admin"
            admin.active = True
            db.commit()
    finally: db.close()

@app.get("/")
def home(): 
    return FileResponse(Path(__file__).resolve().parent.parent / "frontend" / "index.html")

@app.get("/health")
def health():
    return {"ok": True, "service": "MerchantHub API"}

@app.post("/auth/token")
def login(form:OAuth2PasswordRequestForm=Depends(),db:Session=Depends(get_db)):
    email = form.username.strip().lower()
    u = db.query(User).filter(func.lower(User.email) == email).first()
    if not u or not u.active or not verify_password(form.password, u.password_hash):
        raise HTTPException(401, "بيانات البريد الإلكتروني أو كلمة المرور غير صحيحة")
    return {"access_token":token_for(u),"token_type":"bearer","role":u.role}

@app.get("/admin/health")
def admin_health(u:User=Depends(admin_user)): 
    return {"ok":True,"live_provider_enabled":settings.fawaterak_live_enabled}

@app.post("/admin/merchants")
def add_merchant(d:MerchantIn,db:Session=Depends(get_db),admin:User=Depends(admin_user)):
    if db.query(Merchant).filter_by(code=d.code).first(): raise HTTPException(409,"Code exists")
    if db.query(User).filter_by(email=d.owner_email).first(): raise HTTPException(409,"Email exists")
    m=Merchant(code=d.code,legal_name=d.legal_name,status="active"); db.add(m); db.flush()
    db.add(User(email=d.owner_email,name=d.owner_name,password_hash=hash_password(d.owner_password),role="merchant",merchant_id=m.id))
    db.add(FeePolicy(merchant_id=m.id)); db.commit()
    return {"merchant_id":m.id,"code":m.code,"status":m.status}

@app.get("/admin/merchants")
def merchants(db:Session=Depends(get_db),_:User=Depends(admin_user)):
    return [{"id":m.id,"code":m.code,"name":m.legal_name,"status":m.status} for m in db.query(Merchant).all()]

@app.put("/admin/merchants/{mid}/fees")
def fees(mid:str,d:FeeIn,db:Session=Depends(get_db),_:User=Depends(admin_user)):
    if d.gateway_mode not in ("merchant","platform","split"): raise HTTPException(400,"Invalid gateway_mode")
    p=db.query(FeePolicy).filter_by(merchant_id=mid).first()
    if not p: raise HTTPException(404,"Policy not found")
    p.platform_bps=d.platform_bps;p.gateway_mode=d.gateway_mode;p.gateway_bps=d.gateway_bps;p.fixed_gateway_minor=d.fixed_gateway_minor
    db.commit();return {"updated":True}

@app.post("/admin/merchants/{mid}/api-keys")
def api_key(mid:str,db:Session=Depends(get_db),_:User=Depends(admin_user)):
    if not db.get(Merchant,mid): raise HTTPException(404,"Merchant not found")
    secret=secrets.token_urlsafe(32);prefix="mh_"+secrets.token_hex(5)
    db.add(ApiKey(merchant_id=mid,prefix=prefix,secret_hash=hash_password(secret)));db.commit()
    return {"api_key":prefix+"."+secret,"warning":"Shown once. Store securely."}

@app.post("/merchant/payments")
async def payment(d:PaymentIn,db:Session=Depends(get_db),x_api_key:str=Header(default="")):
    mid=api_merchant(x_api_key,db)
    m=db.get(Merchant,mid)
    if not m or m.status!="active": raise HTTPException(403,"Merchant inactive")
    p=PaymentOrder(merchant_id=mid,order_ref=d.order_ref,amount_minor=d.amount_minor,currency=d.currency.upper())
    db.add(p)
    try: db.flush()
    except Exception: db.rollback();raise HTTPException(409,"Duplicate order reference")
    try:
        result=await Fawaterak().create_invoice(d.amount_minor,d.currency.upper(),
            {"name":d.customer_name,"email":d.customer_email,"phone":d.customer_phone},
            {"merchant_id":mid,"order_id":p.id,"order_ref":d.order_ref})
        p.provider_invoice_id=str(result.get("invoice_id") or result.get("id") or "")
        p.checkout_url=result.get("url") or result.get("payment_url");p.status="pending";db.commit()
        return {"order_id":p.id,"status":p.status,"provider":result}
    except ProviderNotReady as e: db.rollback();raise HTTPException(503,str(e))
    except Exception: db.rollback();raise HTTPException(502,"Provider request failed; verify account-specific integration mapping")

@app.get("/merchant/payments")
def my_payments(db:Session=Depends(get_db),u:User=Depends(merchant_user)):
    q=db.query(PaymentOrder)
    if u.role=="merchant": q=q.filter_by(merchant_id=u.merchant_id)
    return [{"id":p.id,"order_ref":p.order_ref,"amount_minor":p.amount_minor,"currency":p.currency,"status":p.status} for p in q.order_by(PaymentOrder.created_at.desc()).limit(500)]

@app.post("/merchant/withdrawals")
def withdraw(d:WithdrawalIn,db:Session=Depends(get_db),u:User=Depends(merchant_user)):
    if u.role!="merchant": raise HTTPException(403,"Merchant only")
    if d.method!="manual": raise HTTPException(501,"Automatic payout requires approved payout API")
    w=Withdrawal(merchant_id=u.merchant_id,amount_minor=d.amount_minor,currency=d.currency.upper(),method="manual")
    db.add(w);db.commit();return {"withdrawal_id":w.id,"status":w.status}

@app.get("/admin/withdrawals")
def all_withdrawals(db:Session=Depends(get_db),_:User=Depends(admin_user)):
    return [{"id":w.id,"merchant_id":w.merchant_id,"amount_minor":w.amount_minor,"currency":w.currency,"status":w.status} for w in db.query(Withdrawal).all()]

@app.post("/admin/withdrawals/{wid}/decision")
def decide(wid:str,decision:str,note:str="",db:Session=Depends(get_db),_:User=Depends(admin_user)):
    w=db.get(Withdrawal,wid)
    if not w: raise HTTPException(404,"Not found")
    if w.status!="requested": raise HTTPException(409,"Already processed")
    if decision not in ("approve","reject"): raise HTTPException(400,"Use approve/reject")
    w.status="approved_manual_transfer" if decision=="approve" else "rejected";w.admin_note=note;db.commit()
    return {"id":wid,"status":w.status}

@app.get("/admin/transactions")
def transactions(db:Session=Depends(get_db),_:User=Depends(admin_user)):
    return [{"id":p.id,"merchant_id":p.merchant_id,"order_ref":p.order_ref,"amount_minor":p.amount_minor,"currency":p.currency,"status":p.status} for p in db.query(PaymentOrder).limit(1000)]

@app.post("/webhooks/fawaterak")
async def webhook(req:Request,db:Session=Depends(get_db),x_provider_signature:str=Header(default="")):
    raw=await req.body()
    if not settings.fawaterak_webhook_secret: raise HTTPException(503,"Webhook secret not configured")
    expected=hmac.new(settings.fawaterak_webhook_secret.encode(),raw,hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected,x_provider_signature): raise HTTPException(401,"Bad signature")
    data=json.loads(raw);event_id=str(data.get("event_id") or data.get("invoice_id") or "")
    if not event_id: raise HTTPException(400,"Missing event ID")
    if db.query(WebhookEvent).filter_by(provider_event_id=event_id).first(): return {"received":True,"duplicate":True}
    db.add(WebhookEvent(provider_event_id=event_id,payload_text=raw.decode(),processed=False));db.commit()
    return {"received":True,"queued_for_verification":True}

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount(
        "/",
        StaticFiles(directory=str(FRONTEND_DIR), html=True),
        name="frontend"
    )
