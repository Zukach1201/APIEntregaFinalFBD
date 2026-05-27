from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from datetime import datetime
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)


client = MongoClient(os.environ["MONGO_URI"])
db = client[os.environ["MONGO_DB"]]

@app.get("/")
def inicio():
    return {"estado": "API funcionando correctamente... (todo es una mentira del estado)"}

@app.get('/hoteles/{hotel_id}/resenadestacada')
def get_resenadestacada(hotel_id: str):
    # Buscamos las reseñas del hotel, ordenamos por votosUtiles de mayor a menor (-1) y traemos la primera (.limit(1))
    resena_mas_votada = list(db["resenas"].find(
        {'hotelId': hotel_id, 'estado': 'PUBLICADA'},
        {'_id': 0}
    ).sort('votosUtiles', -1).limit(1))

    return resena_mas_votada[0] if resena_mas_votada else None

@app.get('/hoteles/{hotel_id}/resenas')
def get_resenas(hotel_id: str):
    resenas = db["resenas"].find({'hotelId': hotel_id},{"usuarioId":1,"fecha":1,"calificacion":1,"comentario":1,"votosUtiles":1,"_id":0})
    return list(resenas) if resenas else []

@app.post('/hoteles/{hotel_id}/resenas')
def post_resena(hotel_id: str, datos: dict):
    datos['hotelId'] = hotel_id
    datos['fecha']  = datetime.now().isoformat()
    datos['estado'] = 'PUBLICADA' ##confiamos que se publicó correctamente, pero se podría agregar un campo de estado para manejar casos de moderación o errores
    datos['votosUtiles'] = 0
    db["resenas"].insert_one(datos)
    return {'mensaje': 'Reseña guardada correctamente'}

