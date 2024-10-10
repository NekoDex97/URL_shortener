import os
from fastapi import FastAPI, HTTPException, Form
from pydantic import BaseModel, HttpUrl
from pymongo import MongoClient
import string
import random
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

DB_URL=os.getenv("DB_URL")
ORIGINS=os.getenv("ORIGINS").split(",")

# Conexión a la base de datos MongoDB
client = MongoClient(DB_URL)
db = client["shortener"]
collection = db["links"]

app = FastAPI(title="URL Shortener")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Función para generar el código corto
def generate_short_code(length=6):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

# Modelo para la creación del enlace
class LinkCreate(BaseModel):
    url: HttpUrl

# Endpoint para acortar un enlace
@app.post("/shorten/")
async def shorten_link(url: str = Form(...)):
    # Verifica si el enlace ya existe en la base de datos
    existing_link = collection.find_one({"original_url": url})
    if existing_link:
        return {"short_url": existing_link["short_url"]}

    # Si no existe, genera un nuevo código corto
    short_code = generate_short_code()
    short_url = f"https://url-shortener-1-qbrq.onrender.com/{short_code}"

    # Guarda el nuevo enlace en la base de datos
    collection.insert_one({"original_url": url, "short_url": short_url, "short_code": short_code})

    return {"short_url": short_url}

# Endpoint para redirigir el enlace corto
@app.get("/get-link/{short_code}")
async def get_original_link(short_code: str):
    link = collection.find_one({"short_code": short_code})
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    return JSONResponse(
            content={"original_url": link["original_url"]},
            headers={"Content-Type": "application/json"}
        )


@app.get("/{short_code}")
async def redirect_link(short_code: str):
    link = collection.find_one({"short_code": short_code})
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    return RedirectResponse(url=link["original_url"])
