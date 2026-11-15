import httpx
from app.config import settings
class ProviderNotReady(Exception): pass
class Fawaterak:
    async def create_invoice(self,amount_minor,currency,customer,payload):
        # Verify endpoint auth and exact field mapping against your account docs before live use.
        if not settings.fawaterak_live_enabled or not settings.fawaterak_base_url or not settings.fawaterak_api_token:
            raise ProviderNotReady("Fawaterak live integration is not configured/enabled")
        body={"cartTotal":amount_minor/100,"currency":currency,"customer":customer,"payLoad":payload}
        headers={"Authorization":f"Bearer {settings.fawaterak_api_token}"}
        if settings.fawaterak_vendor_key: headers["Vendor-Key"]=settings.fawaterak_vendor_key
        url=settings.fawaterak_base_url.rstrip("/")+"/"+settings.fawaterak_create_invoice_path.lstrip("/")
        async with httpx.AsyncClient(timeout=25) as client:
            r=await client.post(url,json=body,headers=headers)
            r.raise_for_status()
            return r.json()
