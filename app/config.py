from pydantic_settings import BaseSettings, SettingsConfigDict
class Settings(BaseSettings):
    model_config=SettingsConfigDict(env_file=".env",extra="ignore")
    database_url:str="sqlite:///./merchanthub.db"
    jwt_secret:str="CHANGE_ME"
    admin_email:str="admin@example.com"
    admin_password:str="CHANGE_ME"
    admin_sync_password_on_startup:bool=True
    fawaterak_base_url:str=""
    fawaterak_create_invoice_path:str="/api/v2/createInvoiceLink"
    fawaterak_api_token:str=""
    fawaterak_vendor_key:str=""
    fawaterak_webhook_secret:str=""
    fawaterak_live_enabled:bool=False
    cors_origins:str="*"
settings=Settings()
