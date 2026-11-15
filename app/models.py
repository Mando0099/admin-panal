import uuid
from datetime import datetime,timezone
from sqlalchemy import String,Boolean,DateTime,ForeignKey,Integer,BigInteger,Text,UniqueConstraint
from sqlalchemy.orm import Mapped,mapped_column
from app.db import Base
def uid(): return str(uuid.uuid4())
def now(): return datetime.now(timezone.utc)
class User(Base):
    __tablename__="users"
    id:Mapped[str]=mapped_column(String(36),primary_key=True,default=uid)
    email:Mapped[str]=mapped_column(String(255),unique=True,index=True)
    name:Mapped[str]=mapped_column(String(150),default="")
    password_hash:Mapped[str]=mapped_column(String(255))
    role:Mapped[str]=mapped_column(String(30),default="merchant")
    merchant_id:Mapped[str|None]=mapped_column(ForeignKey("merchants.id"),nullable=True)
    active:Mapped[bool]=mapped_column(Boolean,default=True)
class Merchant(Base):
    __tablename__="merchants"
    id:Mapped[str]=mapped_column(String(36),primary_key=True,default=uid)
    code:Mapped[str]=mapped_column(String(40),unique=True,index=True)
    legal_name:Mapped[str]=mapped_column(String(200))
    status:Mapped[str]=mapped_column(String(20),default="pending")
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
class ApiKey(Base):
    __tablename__="api_keys"
    id:Mapped[str]=mapped_column(String(36),primary_key=True,default=uid)
    merchant_id:Mapped[str]=mapped_column(ForeignKey("merchants.id"),index=True)
    prefix:Mapped[str]=mapped_column(String(24),index=True)
    secret_hash:Mapped[str]=mapped_column(String(255))
    active:Mapped[bool]=mapped_column(Boolean,default=True)
class FeePolicy(Base):
    __tablename__="fee_policies"
    id:Mapped[str]=mapped_column(String(36),primary_key=True,default=uid)
    merchant_id:Mapped[str]=mapped_column(ForeignKey("merchants.id"),unique=True)
    platform_bps:Mapped[int]=mapped_column(Integer,default=300)
    gateway_mode:Mapped[str]=mapped_column(String(20),default="merchant")
    gateway_bps:Mapped[int]=mapped_column(Integer,default=0)
    fixed_gateway_minor:Mapped[int]=mapped_column(BigInteger,default=0)
class PaymentOrder(Base):
    __tablename__="payment_orders"
    __table_args__=(UniqueConstraint("merchant_id","order_ref"),)
    id:Mapped[str]=mapped_column(String(36),primary_key=True,default=uid)
    merchant_id:Mapped[str]=mapped_column(ForeignKey("merchants.id"),index=True)
    order_ref:Mapped[str]=mapped_column(String(100))
    amount_minor:Mapped[int]=mapped_column(BigInteger)
    currency:Mapped[str]=mapped_column(String(3))
    status:Mapped[str]=mapped_column(String(30),default="created")
    provider_invoice_id:Mapped[str|None]=mapped_column(String(150),nullable=True,index=True)
    checkout_url:Mapped[str|None]=mapped_column(Text,nullable=True)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
class LedgerAccount(Base):
    __tablename__="ledger_accounts"
    id:Mapped[str]=mapped_column(String(36),primary_key=True,default=uid)
    merchant_id:Mapped[str|None]=mapped_column(ForeignKey("merchants.id"),nullable=True,index=True)
    code:Mapped[str]=mapped_column(String(50))
    currency:Mapped[str]=mapped_column(String(3))
    account_type:Mapped[str]=mapped_column(String(30))
class JournalEntry(Base):
    __tablename__="journal_entries"
    id:Mapped[str]=mapped_column(String(36),primary_key=True,default=uid)
    reference:Mapped[str]=mapped_column(String(150),unique=True)
    currency:Mapped[str]=mapped_column(String(3))
    entry_type:Mapped[str]=mapped_column(String(40))
    status:Mapped[str]=mapped_column(String(20),default="draft")
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
class JournalLine(Base):
    __tablename__="journal_lines"
    id:Mapped[str]=mapped_column(String(36),primary_key=True,default=uid)
    journal_id:Mapped[str]=mapped_column(ForeignKey("journal_entries.id"),index=True)
    account_id:Mapped[str]=mapped_column(ForeignKey("ledger_accounts.id"))
    debit_minor:Mapped[int]=mapped_column(BigInteger,default=0)
    credit_minor:Mapped[int]=mapped_column(BigInteger,default=0)
class Withdrawal(Base):
    __tablename__="withdrawals"
    id:Mapped[str]=mapped_column(String(36),primary_key=True,default=uid)
    merchant_id:Mapped[str]=mapped_column(ForeignKey("merchants.id"),index=True)
    amount_minor:Mapped[int]=mapped_column(BigInteger)
    currency:Mapped[str]=mapped_column(String(3))
    method:Mapped[str]=mapped_column(String(20),default="manual")
    status:Mapped[str]=mapped_column(String(30),default="requested")
    admin_note:Mapped[str]=mapped_column(Text,default="")
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
class WebhookEvent(Base):
    __tablename__="webhook_events"
    id:Mapped[str]=mapped_column(String(36),primary_key=True,default=uid)
    provider_event_id:Mapped[str]=mapped_column(String(150),unique=True)
    payload_text:Mapped[str]=mapped_column(Text)
    processed:Mapped[bool]=mapped_column(Boolean,default=False)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
