from fastapi import FastAPI
from sqlalchemy import create_engine, text
from pydantic import BaseModel
import uuid

# ✅ Define app FIRST
app = FastAPI()

# ✅ Database config
DATABASE_URL = "postgresql://postgres:YOUR_PASSWORD@localhost:5432/saas_crm"
engine = create_engine(DATABASE_URL)

# ✅ Pydantic model
class TenantCreate(BaseModel):
    clinic_name: str
    whatsapp_number: str

# ✅ Home route
@app.get("/")
def home():
    return {"message": "SaaS CRM Backend Running 🚀"}

# ✅ Register route
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

# ✅ Get tenant route
@app.get("/tenant/{api_key}")
def get_tenant(api_key: str):
    with engine.connect() as connection:
        query = text("SELECT * FROM tenants WHERE api_key = :api_key")

        result = connection.execute(query, {"api_key": api_key}).fetchone()

        if result:
            return dict(result._mapping)
        else:
            return {"error": "Tenant not found"}

# =========================
# IMPORTS
# =========================
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse, Response
from sqlalchemy import create_engine, text
from pydantic import BaseModel
from twilio.twiml.messaging_response import MessagingResponse
from openai import OpenAI
import uuid

# =========================
# INITIAL SETUP
# =========================
app = FastAPI()

# OpenAI Client
client = OpenAI(api_key="YOUR_OPENAI_API_KEY")

# Database Config
DATABASE_URL = "postgresql://postgres:YOUR_PASSWORD@localhost:5432/saas_crm"
engine = create_engine(DATABASE_URL)

# =========================
# MODELS
# =========================
class TenantCreate(BaseModel):
    clinic_name: str
    whatsapp_number: str


# =========================
# ROUTES
# =========================

# Home Route
@app.get("/")
def home():
    return {"message": "SaaS CRM Backend Running 🚀"}


# Register Tenant
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


# WhatsApp Webhook (FINAL CLEAN VERSION)
@app.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request):
    form_data = await request.form()

    user_number = form_data.get("From")
    business_number = form_data.get("To")
    user_message = form_data.get("Body")

    print("User:", user_number)
    print("Business:", business_number)
    print("Message:", user_message)

    # Fetch tenant
    with engine.connect() as connection:
        query = text("""
            SELECT * FROM tenants WHERE whatsapp_number = :number
        """)
        tenant = connection.execute(query, {"number": business_number}).fetchone()

    if not tenant:
        reply = "Clinic not found"
    else:
        tenant_data = dict(tenant._mapping)

        # AI Response
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

    # Twilio XML Response
    twilio_response = MessagingResponse()
    twilio_response.message(reply)

    return Response(
        content=str(twilio_response),
        media_type="application/xml"
    )


# Get Tenant by API Key
@app.get("/tenant/{api_key}")
def get_tenant(api_key: str):
    with engine.connect() as connection:
        query = text("SELECT * FROM tenants WHERE api_key = :api_key")
        result = connection.execute(query, {"api_key": api_key}).fetchone()

    if result:
        return dict(result._mapping)
    else:
        return {"error": "Tenant not found"}


from fastapi import FastAPI, Request
from sqlalchemy import create_engine, text
from pydantic import BaseModel
from fastapi.responses import PlainTextResponse, Response
from twilio.twiml.messaging_response import MessagingResponse
from openai import OpenAI
import uuid

# OpenAI Client
client = OpenAI(
    api_key="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"
)

# Define app FIRST
app = FastAPI()

# Database config
DATABASE_URL = "postgresql://postgres:tsaThish27*@localhost:5432/saas_crm"
engine = create_engine(DATABASE_URL)

# =========================
# MODELS
# =========================
class TenantCreate(BaseModel):
    clinic_name: str
    whatsapp_number: str


class WhatsAppMessage(BaseModel):
    from_number: str
    to_number: str
    message: str


# =========================
# ROUTES
# =========================

@app.get("/")
def home():
    return {"message": "SaaS CRM Backend Running 🚀"}


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
# WEBHOOK VERSION 1
# =========================
@app.post("/webhook/whatsapp")
async def whatsapp_webhook(payload: WhatsAppMessage):
    user_number = payload.from_number
    business_number = payload.to_number
    user_message = payload.message

    with engine.connect() as connection:
        query = text("""
            SELECT * FROM tenants WHERE whatsapp_number = :number
        """)
        tenant = connection.execute(
            query, {"number": business_number}
        ).fetchone()

    if not tenant:
        return {"error": "Clinic not found"}

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
    return {"reply": reply}


# =========================
# WEBHOOK VERSION 2
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

    with engine.connect() as connection:
        query = text("""
            SELECT * FROM tenants WHERE whatsapp_number = :number
        """)
        tenant = connection.execute(
            query, {"number": business_number}
        ).fetchone()

    if not tenant:
        return {"error": "Clinic not found"}

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

    twilio_response = MessagingResponse()
    twilio_response.message(reply)

    return PlainTextResponse(
        str(twilio_response),
        media_type="application/xml"
    )


# =========================
# WEBHOOK VERSION 3
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

    with engine.connect() as connection:
        query = text("""
            SELECT * FROM tenants WHERE whatsapp_number = :number
        """)
        tenant = connection.execute(
            query, {"number": business_number}
        ).fetchone()

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