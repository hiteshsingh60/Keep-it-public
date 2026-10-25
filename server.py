from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from html import escape
from pathlib import Path
from typing import Annotated, Optional
from datetime import datetime, timezone
from bson import ObjectId
from pydantic import BaseModel, Field, EmailStr, BeforeValidator, ConfigDict

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

from email_service import send_email, EMAIL_FROM_NAME  # noqa: E402

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

client = AsyncIOMotorClient(os.environ['MONGO_URL'])
db = client[os.environ['DB_NAME']]
OWNER_EMAIL = os.environ['OWNER_EMAIL']

app = FastAPI()
api_router = APIRouter(prefix="/api")

PyObjectId = Annotated[str, BeforeValidator(lambda v: str(v) if isinstance(v, ObjectId) else v)]


class BaseDocument(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: Optional[PyObjectId] = Field(default=None, alias="_id")

    def to_mongo(self) -> dict:
        data = self.model_dump(by_alias=True, exclude={"id"})
        return data

    @classmethod
    def from_mongo(cls, doc: dict):
        return cls.model_validate(doc)


class EnquiryIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    company: str = Field(default="", max_length=160)
    email: EmailStr
    phone: str = Field(default="", max_length=30)
    service: str = Field(default="", max_length=80)
    message: str = Field(min_length=5, max_length=3000)


class Enquiry(BaseDocument):
    name: str
    company: str = ""
    email: str
    phone: str = ""
    service: str = ""
    message: str
    email_sent: bool = False
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


def _owner_html(e: Enquiry) -> str:
    rows = [("Name", e.name), ("Company", e.company or "-"), ("Email", e.email),
            ("Phone", e.phone or "-"), ("Service", e.service or "-")]
    cells = "".join(
        f'<tr><td style="padding:6px 12px 6px 0;color:#64748B;font-size:13px">{k}</td>'
        f'<td style="padding:6px 0;color:#0B0F17;font-size:14px">{escape(v)}</td></tr>' for k, v in rows)
    return (
        '<table role="presentation" width="100%" style="font-family:Arial,sans-serif;background:#F7F5F0">'
        '<tr><td style="padding:28px">'
        '<div style="display:inline-block;background:#F5B34A;color:#1F3A6D;font-weight:bold;padding:6px 9px">AE</div>'
        f'<h2 style="color:#1F3A6D;margin:18px 0 6px">New website enquiry</h2>'
        f'<table role="presentation">{cells}</table>'
        f'<p style="color:#0B0F17;font-size:14px;line-height:1.6;white-space:pre-wrap;margin-top:16px">{escape(e.message)}</p>'
        f'<p style="font-size:12px;color:#888;margin-top:24px">Sent by the {escape(EMAIL_FROM_NAME)} website enquiry form.</p>'
        '</td></tr></table>'
    )


def _visitor_html(e: Enquiry) -> str:
    first = escape(e.name.strip().split(" ")[0][:40])
    service = f" regarding <span style=\"color:#F5B34A\">{escape(e.service)}</span>" if e.service else ""
    serif = "Georgia,'Times New Roman',serif"
    sans = "Helvetica,Arial,sans-serif"
    return (
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#07090E;font-family:{sans}">'
        '<tr><td align="center" style="padding:40px 16px">'
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:560px;background:#0D1119;border:1px solid #2a2a22">'
        '<tr><td style="padding:40px 40px 0">'
        '<table role="presentation" cellpadding="0" cellspacing="0"><tr>'
        f'<td style="border:2px solid #F5B34A;padding:6px 10px;color:#F3EEE4;font-weight:bold;font-size:20px;font-family:{sans}">AE</td>'
        f'<td style="padding-left:12px;color:#F3EEE4;font-size:15px;font-weight:bold;line-height:1.15;font-family:{sans}">Avni<br>Enterprises</td>'
        '</tr></table></td></tr>'
        '<tr><td style="padding:36px 40px 0">'
        '<p style="margin:0;color:#F5B34A;font-size:11px;letter-spacing:4px;text-transform:uppercase">Enquiry received</p>'
        f'<h1 style="margin:16px 0 0;color:#F3EEE4;font-family:{serif};font-weight:normal;font-size:34px;line-height:1.15">Thank you, <em style="color:#F5B34A">{first}.</em></h1>'
        '<div style="width:48px;height:1px;background:#F5B34A;margin:24px 0"></div>'
        f'<p style="margin:0;color:#C9CDD4;font-size:15px;line-height:1.7">We have received your enquiry{service}. A member of our team will review your requirements and get back to you shortly with a tailored proposal.</p>'
        '<p style="margin:18px 0 0;color:#C9CDD4;font-size:15px;line-height:1.7">If anything is urgent, you can reach us directly:</p>'
        '</td></tr>'
        '<tr><td style="padding:20px 40px 0">'
        '<table role="presentation" cellpadding="0" cellspacing="0" style="font-size:14px;line-height:2">'
        '<tr><td style="color:#A7ADB8;padding-right:16px">Phone</td><td><a href="tel:+919999724721" style="color:#F3EEE4;text-decoration:none">+91 99997 24721</a> &nbsp;/&nbsp; <a href="tel:+919868750801" style="color:#F3EEE4;text-decoration:none">+91 98687 50801</a></td></tr>'
        f'<tr><td style="color:#A7ADB8;padding-right:16px">Email</td><td><a href="mailto:{escape(OWNER_EMAIL)}" style="color:#F5B34A;text-decoration:none">{escape(OWNER_EMAIL)}</a></td></tr>'
        '</table></td></tr>'
        f'<tr><td style="padding:36px 40px 40px"><p style="margin:0;color:#F3EEE4;font-family:{serif};font-size:18px;font-style:italic">Warm regards,</p>'
        '<p style="margin:4px 0 0;color:#A7ADB8;font-size:13px">Team Avni Enterprises</p></td></tr>'
        '</table>'
        f'<p style="max-width:560px;margin:20px auto 0;color:#7c828c;font-size:11px;line-height:1.6;text-align:center">You are receiving this because an enquiry was submitted with this address on the {escape(EMAIL_FROM_NAME)} website. Facility Management &amp; Administrative Support, Delhi. We never ask for passwords or payment details by email.</p>'
        '</td></tr></table>'
    )


@api_router.get("/")
async def root():
    return {"message": "Avni Enterprises API"}


@api_router.post("/enquiries")
async def create_enquiry(payload: EnquiryIn):
    enquiry = Enquiry(**payload.model_dump())
    result = await db.enquiries.insert_one(enquiry.to_mongo())
    try:
        await send_email(to=OWNER_EMAIL, subject=f"New enquiry from {payload.name[:60]}", html=_owner_html(enquiry), reply_to=str(payload.email))
        await db.enquiries.update_one({"_id": result.inserted_id}, {"$set": {"email_sent": True}})
        enquiry.email_sent = True
    except HTTPException as exc:
        logger.warning(f"Enquiry saved but email failed: {exc.detail}")
    visitor_sent = False
    try:
        await send_email(to=str(payload.email), subject="Thank you for your enquiry | Avni Enterprises", html=_visitor_html(enquiry), reply_to=OWNER_EMAIL)
        visitor_sent = True
        await db.enquiries.update_one({"_id": result.inserted_id}, {"$set": {"visitor_email_sent": True}})
    except HTTPException as exc:
        logger.warning(f"Visitor confirmation failed: {exc.detail}")
    enquiry.id = str(result.inserted_id)
    return {"ok": True, "id": enquiry.id, "email_sent": enquiry.email_sent, "visitor_email_sent": visitor_sent}


app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
