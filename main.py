from fastapi import FastAPI, HTTPException, Form
from pydantic import BaseModel, HttpUrl
from pymongo import MongoClient
import string
import random
from fastapi.responses import RedirectResponse

# Conexión a la base de datos MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["shortener"]
collection = db["links"]

app = FastAPI()

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
    short_url = f"http://localhost:8000/{short_code}"

    # Guarda el nuevo enlace en la base de datos
    collection.insert_one({"original_url": url, "short_url": short_url, "short_code": short_code})

    return {"short_url": short_url}

# Endpoint para redirigir el enlace corto
@app.get("/{short_code}")
async def redirect_link(short_code: str):
    # Busca el código corto en la base de datos
    link = collection.find_one({"short_code": short_code})
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")

    return {"original_url": link["original_url"]}

