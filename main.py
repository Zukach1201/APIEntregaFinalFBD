from fastapi import FastAPI
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
    return {"estado": "API funcionando correctamente...? JAJJA"}
"""
@app.get("/bares")
def get_bares():
    return db["Bares"].find()

@app.post("/bares")
def post_bares(datos: list):
    resultado = db["Bares"].insertMany(datos)
"""
@app.get('/bares/{bar_id}/comentarios')
def get_comentarios(bar_id: int):
    comentarios = db["Bares"].find_one({'_id': bar_id},{'comentarios':1,"_id":0})
    return comentarios['comentarios'] if comentarios and 'comentarios' in comentarios else []

@app.post('/bares/{bar_id}/comentarios')
def post_comentario(bar_id: int, datos: dict):
    # datos['bar_id'] = bar_id // No es necesario agregar bar_id al comentario, ya que se almacenará dentro del documento del bar correspondiente
    datos['fecha']  = datetime.now().isoformat()
    db["Bares"].update_one({'_id': bar_id}, {'$push': {'comentarios': datos}})
    return {'mensaje': 'Comentario guardado'}

@app.get('/bares/{bar_id}/eventos')
def get_eventos(bar_id: int):
    eventos = db["Bares"].find_one({'_id': bar_id}, {'eventos': 1,"_id": 0})
    return eventos['eventos'] if eventos and 'eventos' in eventos else []

@app.post('/bares/{bar_id}/eventos')
def post_evento(bar_id: int, datos: dict): 
    # datos['bar_id'] = bar_id // No es necesario agregar bar_id al evento, ya que se almacenará dentro del documento del bar correspondiente
    datos['fecha_creacion']  = datetime.now().isoformat()
    db["Bares"].update_one({'_id': bar_id}, {'$push': {'eventos': datos}})
    return {'mensaje': 'Evento guardado'}

