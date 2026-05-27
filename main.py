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
    return {"estado": "API funcionando correctamente..."}

@app.get("/hoteles")
def get_hoteles():
    return list(db["hoteles"].find({},{'_id':0}))

@app.post("/hoteles")
def post_hoteles(datos: list = Body(...)):
    resultado = db["hoteles" \
    ""].insert_many(datos)
    return {"resultado": "UwU"}

@app.get('/hoteles/{hotel_id}/resenadestacada')
def get_resenadestacada(hotel_id: str):
    destacada = db["hoteles"].find_one({'_id': hotel_id},{"resenaDestacada":1,"_id":0})
    return list(destacada) if destacada else []

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

