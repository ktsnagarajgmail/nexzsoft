from fastapi import FastAPI, Request
from sqlalchemy import create_engine, text
from pydantic import BaseModel
from fastapi.responses import Response
from twilio.twiml.messaging_response import MessagingResponse
from openai import OpenAI
import uuid

# =========================
# CONFIG
# =========================

client = OpenAI(
    api_key="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"
)

DATABASE_URL = "postgresql://postgres:tsaThish27*@localhost:5432/Nexzsoft"

engine = create_engine(DATABASE_URL)

app = FastAPI()

# =========================
# MODELS
# =========================

class TenantCreate(BaseModel):
    clinic_name: str
    whatsapp_number: str

# =========================
# ROUTES
# =========================

@app.get("/")
def home():
    return {"message": "SaaS CRM Backend Running 🚀"}

# =========================
# REGISTER TENANT
# =========================

@app.post("/register")
def register_tenant(tenant: TenantCreate):
    new_api_key = str(uuid.uuid4())

    with engine.connect() as connection:
        query = text("""
            INSERT INTO tenants (clinic_name, whatsapp_number, api_key)
            VALUES (:clinic_name, :whatsapp_number, :api_key)
            RETURNING *
        """)

        result = connection.execute(query, {
            "clinic_name": tenant.clinic_name,
            "whatsapp_number": tenant.whatsapp_number,
            "api_key": new_api_key
        })

        connection.commit()

    return dict(result.fetchone()._mapping)

# =========================
# TWILIO WHATSAPP WEBHOOK
# =========================

@app.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request):
    form_data = await request.form()

    user_number = form_data.get("From")
    business_number = form_data.get("To")
    user_message = form_data.get("Body")

    print("User:", user_number)
    print("Business:", business_number)
    print("Message:", user_message)

    # 🔍 Find tenant by WhatsApp number
    with engine.connect() as connection:
        query = text("""
            SELECT * FROM tenants WHERE whatsapp_number = :number
        """)
        tenant = connection.execute(
            query, {"number": business_number}
        ).fetchone()

    # 🤖 Generate reply
    if not tenant:
        reply = "Clinic not found"
    else:
        tenant_data = dict(tenant._mapping)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": f"You are assistant for {tenant_data['clinic_name']}"
                },
                {
                    "role": "user",
                    "content": user_message
                }
            ]
        )

        reply = response.choices[0].message.content
        
    print("AI Reply:", reply)

    # 📩 Send response back to Twilio
    twilio_response = MessagingResponse()
    twilio_response.message(reply)

    return Response(
        content=str(twilio_response),
        media_type="application/xml"
    )

# =========================
# GET TENANT
# =========================

@app.get("/tenant/{api_key}")
def get_tenant(api_key: str):
    with engine.connect() as connection:
        query = text("""
            SELECT * FROM tenants WHERE api_key = :api_key
        """)
        result = connection.execute(
            query, {"api_key": api_key}
        ).fetchone()

    if result:
        return dict(result._mapping)
    else:
        return {"error": "Tenant not found"}