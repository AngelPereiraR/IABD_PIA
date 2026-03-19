from typing import List
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import engine, Base, get_db
import models
import schemas

Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.get('/productos', response_model=List[schemas.Producto])
def read_productos(db: Session = Depends(get_db)):
    productos = db.query(models.Producto).all()
    return productos

@app.get('/producto/{nombre}', response_model=schemas.Producto)
def read_producto_by_name(nombre: str, db: Session = Depends(get_db)):
    producto = db.query(models.Producto).filter(models.Producto.nombre == nombre).first()
    if producto is None:
        raise HTTPException(status_code=404, detail='Producto no encontrado')
    return producto

@app.post('/productos', response_model=schemas.Producto)
def create_product(producto: schemas.ProductoCreate, db: Session = Depends(get_db)):
    nuevo_producto = models.Producto(
        nombre=producto.nombre,
        precio=producto.precio,
        unidades=producto.unidades
    )
    db.add(nuevo_producto)
    db.commit()
    db.refresh(nuevo_producto)
    return nuevo_producto

@app.delete('/producto/{id}')
def delete_product(id: int, db: Session = Depends(get_db)):
    producto = db.query(models.Producto).filter(models.Producto.id == id).first()
    if producto is None:
        raise HTTPException(status_code=404, detail='Producto no encontrado')
    db.delete(producto)
    db.commit()
    return {'detail': 'Producto eliminado correctamente'}

@app.get('/total')
def get_total_value(db: Session = Depends(get_db)):
    total = db.query(func.sum(models.Producto.precio * models.Producto.unidades)).scalar()
    return {'total': total or 0.0}