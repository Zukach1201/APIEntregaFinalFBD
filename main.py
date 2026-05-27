from fastapi import FastAPI, Body, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
import pymongo
from datetime import datetime
import os
import uuid

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

mongo_uri = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
mongo_db = os.environ.get("MONGO_DB", "dann_alpes")
client = MongoClient(mongo_uri)
db = client[mongo_db]

@app.get("/")
def inicio():
    return {"estado": "API funcionando correctamente..."}

@app.get("/hoteles")
def get_hoteles():
    return list(db["hoteles"].find({},{'_id':0}))

@app.get("/usuarios")
def get_usuarios():
    return list(db["usuarios"].find({},{'_id':0}))

@app.post("/hoteles")
def post_hoteles(datos: list = Body(...)):
    if datos:
        db["hoteles"].insert_many(datos)
    return {"resultado": "UwU"}


# RF1 - Crear reseña
@app.post('/hoteles/{hotel_id}/resenas')
def post_resena(hotel_id: str, datos: dict):
    reserva_id = datos.get("reservaId")
    usuario_id = datos.get("usuarioId")
    
    if reserva_id and usuario_id:
        existe = db["resenas"].find_one({
            "reservaId": reserva_id, 
            "usuarioId": usuario_id, 
            "hotelId": hotel_id
        })
        if existe:
            raise HTTPException(status_code=400, detail="El usuario ya ha realizado una reseña para esta reserva.")

    datos['hotelId'] = hotel_id
    datos['fecha'] = datetime.now().isoformat()
    datos['estado'] = 'PUBLICADA' 
    datos['votosUtiles'] = 0
    db["resenas"].insert_one(datos)
    return {'mensaje': 'Reseña creada correctamente', 'resenaId': datos['_id']}

# RF2 - Editar reseña
@app.put('/resenas/{resena_id}')
def put_resena(resena_id: str, datos: dict):
    update_fields = {}
    if "calificacion" in datos:
        update_fields["calificacion"] = datos["calificacion"]
    if "comentario" in datos:
        update_fields["comentario"] = datos["comentario"]
        
    if not update_fields:
        raise HTTPException(status_code=400, detail="No hay datos para actualizar.")
        
    resultado = db["resenas"].update_one(
        {"_id": resena_id},
        {"$set": update_fields}
    )
    if resultado.matched_count == 0:
        raise HTTPException(status_code=404, detail="Reseña no encontrada.")
    return {'mensaje': 'Reseña editada correctamente'}

# RF3 - Eliminar reseña (Cliente)
@app.delete('/resenas/{resena_id}')
def delete_resena(resena_id: str):
    resultado = db["resenas"].update_one(
        {"_id": resena_id},
        {"$set": {"estado": "ELIMINADA"}}
    )
    if resultado.matched_count == 0:
        raise HTTPException(status_code=404, detail="Reseña no encontrada.")
    return {'mensaje': 'Reseña eliminada correctamente'}

# RF4 - Consultar reseñas de un hotel
@app.get('/hoteles/{hotel_id}/resenas')
def get_resenas(hotel_id: str, skip: int = 0, limit: int = 10, sort_by: str = "fecha"):
    query = {'hotelId': hotel_id, 'estado': 'PUBLICADA'}
    
    sort_criteria = [("fecha", pymongo.DESCENDING)]
    if sort_by == "utilidad":
        sort_criteria = [("votosUtiles", pymongo.DESCENDING), ("fecha", pymongo.DESCENDING)]
        
    resenas = list(db["resenas"].find(query, {"_id": 1, "fecha": 1, "calificacion": 1, "comentario": 1, "votosUtiles": 1}).sort(sort_criteria).skip(skip).limit(limit))
    return resenas

# RF5 - Marcar reseña como útil
@app.put('/resenas/{resena_id}/voto-util')
def votar_resena_util(resena_id: str):
    resultado = db["resenas"].update_one(
        {"_id": resena_id},
        {"$inc": {"votosUtiles": 1}}
    )
    if resultado.matched_count == 0:
        raise HTTPException(status_code=404, detail="Reseña no encontrada.")
    return {'mensaje': 'Voto registrado correctamente'}

# RF6 - Consultar historial de reseñas propias
@app.get('/usuarios/{usuario_id}/resenas')
def get_historial_resenas(usuario_id: str, sort_by: str = "fecha"):
    query = {"usuarioId": usuario_id}
    
    sort_criteria = [("fecha", pymongo.DESCENDING)]
    if sort_by == "hotel":
        sort_criteria = [("hotelId", pymongo.ASCENDING), ("fecha", pymongo.DESCENDING)]
        
    resenas = list(db["resenas"].find(query, {
        "_id": 1, "hotelId": 1, "estado": 1, "calificacion": 1, "comentario": 1, "respuestaHotel": 1, "votosUtiles": 1, "fecha": 1
    }).sort(sort_criteria))
    return resenas

# RF7 - Responder reseña
@app.put('/resenas/{resena_id}/respuesta')
def responder_resena(resena_id: str, respuesta: dict = Body(...)):
    texto_respuesta = respuesta.get("respuestaHotel")
    if not texto_respuesta:
        raise HTTPException(status_code=400, detail="El campo respuestaHotel es requerido.")
        
    resultado = db["resenas"].update_one(
        {"_id": resena_id},
        {"$set": {"respuestaHotel": texto_respuesta}}
    )
    if resultado.matched_count == 0:
        raise HTTPException(status_code=404, detail="Reseña no encontrada.")
    return {'mensaje': 'Respuesta registrada correctamente'}

# RF8 - Eliminar reseña (Administrador)
@app.delete('/resenas/{resena_id}/admin')
def delete_resena_admin(resena_id: str):
    resultado = db["resenas"].update_one(
        {"_id": resena_id},
        {"$set": {"estado": "ELIMINADA"}}
    )
    if resultado.matched_count == 0:
        raise HTTPException(status_code=404, detail="Reseña no encontrada.")
    return {'mensaje': 'Reseña eliminada por el administrador.'}

# RF9 - Destacar reseña
@app.put('/hoteles/{hotel_id}/resenadestacada/{resena_id}')
def destacar_resena(hotel_id: str, resena_id: str):
    resena = db["resenas"].find_one({"_id": resena_id, "hotelId": hotel_id, "estado": "PUBLICADA"})
    if not resena:
        raise HTTPException(status_code=404, detail="Reseña no encontrada o no pertenece al hotel especificado.")
        
    resena_destacada = {
        "resenaId": resena["_id"],
        "usuarioId": resena["usuarioId"],
        "calificacion": resena["calificacion"],
        "comentario": resena.get("comentario", ""),
        "fecha": resena["fecha"],
        "votosUtiles": resena.get("votosUtiles", 0)
    }
    
    db["hoteles"].update_one(
        {"_id": hotel_id},
        {"$set": {"resenaDestacada": resena_destacada}}
    )
    return {'mensaje': 'Reseña destacada actualizada correctamente.'}

@app.get('/hoteles/{hotel_id}/resenadestacada') 
def get_resenadestacada(hotel_id: str):
    hotel = db["hoteles"].find_one({'_id': hotel_id},{'resenaDestacada':1,"_id":0})
    return hotel.get('resenaDestacada', {}) if hotel else {}


# ==========================================
# REQUERIMIENTOS DE CONSULTA (RFC1 - RFC3)
# ==========================================

# RFC1 - Top hoteles por calificación
@app.get('/estadisticas/top-hoteles')
def get_top_hoteles(fecha_inicio: str = None, fecha_fin: str = None):
    match_stage = {"estado": "PUBLICADA"}
    
    if fecha_inicio or fecha_fin:
        fecha_query = {}
        if fecha_inicio:
            fecha_query["$gte"] = fecha_inicio
        if fecha_fin:
            fecha_query["$lte"] = fecha_fin
        match_stage["fecha"] = fecha_query
        
    pipeline = [
        {"$match": match_stage},
        {"$group": {
            "_id": "$hotelId",
            "promedioCalificacion": {"$avg": "$calificacion"},
            "totalResenas": {"$sum": 1}
        }},
        {"$sort": {"promedioCalificacion": -1}},
        {"$limit": 10},
        {"$lookup": {
            "from": "hoteles",
            "localField": "_id",
            "foreignField": "_id",
            "as": "infoHotel"
        }},
        {"$unwind": "$infoHotel"},
        {"$project": {
            "hotelId": "$_id",
            "_id": 0,
            "nombre": "$infoHotel.nombre",
            "ubicacion": "$infoHotel.ubicacion",
            "promedioCalificacion": {"$round": ["$promedioCalificacion", 2]},
            "totalResenas": 1
        }}
    ]
    
    resultados = list(db["resenas"].aggregate(pipeline))
    return resultados

# RFC2 - Evolución de la reputación de un hotel en el tiempo
@app.get('/hoteles/{hotel_id}/reputacion')
def get_evolucion_reputacion(hotel_id: str, anio: str):
    pipeline = [
        {"$match": {
            "hotelId": hotel_id,
            "estado": "PUBLICADA",
            "fecha": {"$regex": f"^{anio}"}
        }},
        {"$addFields": {
            "mes": {"$substr": ["$fecha", 5, 2]} 
        }},
        {"$group": {
            "_id": "$mes",
            "promedioCalificacion": {"$avg": "$calificacion"},
            "totalResenas": {"$sum": 1}
        }},
        {"$sort": {"_id": 1}},
        {"$project": {
            "mes": "$_id",
            "_id": 0,
            "promedioCalificacion": {"$round": ["$promedioCalificacion", 2]},
            "totalResenas": 1
        }}
    ]
    
    resultados = list(db["resenas"].aggregate(pipeline))
    return resultados

# RFC3 - Perfil comparativo de hoteles por ciudad
@app.get('/estadisticas/ciudades/{ciudad}/comparativo')
def get_comparativo_ciudad(ciudad: str):
    pipeline = [
        {"$match": {"ubicacion": ciudad}},
        {"$lookup": {
            "from": "resenas",
            "let": {"idHotel": "$_id"},
            "pipeline": [
                {"$match": {
                    "$expr": {"$eq": ["$hotelId", "$$idHotel"]},
                    "estado": "PUBLICADA"
                }}
            ],
            "as": "resenasHotel"
        }},
        {"$project": {
            "_id": 1,
            "nombre": 1,
            "categoria": 1,
            "tieneDestacada": {"$cond": [{"$ifNull": ["$resenaDestacada", False]}, 1, 0]},
            "totalResenas": {"$size": "$resenasHotel"},
            "promedioCalificacion": {"$avg": "$resenasHotel.calificacion"},
            "resenasConRespuesta": {
                "$size": {
                    "$filter": {
                        "input": "$resenasHotel",
                        "as": "r",
                        "cond": {"$ne": [{"$type": "$$r.respuestaHotel"}, "missing"]}
                    }
                }
            }
        }},
        {"$project": {
            "hotelId": "$_id",
            "_id": 0,
            "nombre": 1,
            "categoria": 1,
            "promedioCalificacion": {"$round": [{"$ifNull": ["$promedioCalificacion", 0]}, 2]},
            "totalResenas": 1,
            "porcentajeRespuesta": {
                "$cond": [
                    {"$eq": ["$totalResenas", 0]},
                    0,
                    {"$round": [{"$multiply": [{"$divide": ["$resenasConRespuesta", "$totalResenas"]}, 100]}, 2]}
                ]
            },
            "porcentajeDestacadas": {
                "$cond": [
                    {"$eq": ["$totalResenas", 0]},
                    0,
                    {"$round": [{"$multiply": [{"$divide": ["$tieneDestacada", "$totalResenas"]}, 100]}, 2]}
                ]
            }
        }},
        {"$sort": {"promedioCalificacion": -1}}
    ]
    
    resultados = list(db["hoteles"].aggregate(pipeline))
    return resultados