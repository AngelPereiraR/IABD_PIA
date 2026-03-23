from typing import List
from datetime import date
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

@app.get('/clientes', response_model=List[schemas.Cliente])
def read_clientes(db: Session = Depends(get_db)):
    return db.query(models.Cliente).all()

@app.post('/clientes', response_model=schemas.Cliente)
def create_cliente(cliente: schemas.ClienteCreate, db: Session = Depends(get_db)):
    nuevo_cliente = models.Cliente(
        nombre=cliente.nombre,
        email=cliente.email
    )
    db.add(nuevo_cliente)
    db.commit()
    db.refresh(nuevo_cliente)
    return nuevo_cliente

@app.get('/cliente/{id}/pedidos', response_model=List[schemas.PedidoConCliente])
def read_pedidos_by_cliente(id: int, db: Session = Depends(get_db)):
    cliente = db.query(models.Cliente).filter(models.Cliente.id == id).first()
    if cliente is None:
        raise HTTPException(status_code=404, detail='Cliente no encontrado')
    return cliente.pedidos

@app.get('/pedidos', response_model=List[schemas.PedidoConCliente])
def read_pedidos(db: Session = Depends(get_db)):
    return db.query(models.Pedido).all()

@app.post('/pedidos', response_model=schemas.Pedido)
def create_pedido(pedido: schemas.PedidoCreate, db: Session = Depends(get_db)):
    cliente = db.query(models.Cliente).filter(models.Cliente.id == pedido.cliente_id).first()
    if cliente is None:
        raise HTTPException(status_code=404, detail='Cliente no encontrado')
    nuevo_pedido = models.Pedido(fecha=date.today(), cliente_id=pedido.cliente_id)
    db.add(nuevo_pedido)
    db.commit()
    db.refresh(nuevo_pedido)
    return nuevo_pedido

@app.post('/lineas-pedido', response_model=schemas.LineaPedido)
def create_linea_pedido(linea: schemas.LineaPedidoCreate, db: Session = Depends(get_db)):
    pedido = db.query(models.Pedido).filter(models.Pedido.id == linea.pedido_id).first()
    if pedido is None:
        raise HTTPException(status_code=404, detail='Pedido no encontrado')
    producto = db.query(models.Producto).filter(models.Producto.id == linea.producto_id).first()
    if producto is None:
        raise HTTPException(status_code=404, detail='Producto no encontrado')
    nueva_linea = models.LineaPedido(
        pedido_id=linea.pedido_id,
        producto_id=linea.producto_id,
        cantidad=linea.cantidad
    )
    db.add(nueva_linea)
    db.commit()
    db.refresh(nueva_linea)
    return nueva_linea

@app.delete('/pedido/{id}')
def delete_pedido(id: int, db: Session = Depends(get_db)):
    pedido = db.query(models.Pedido).filter(models.Pedido.id == id).first()
    if pedido is None:
        raise HTTPException(status_code=404, detail='Pedido no encontrado')
    db.delete(pedido)
    db.commit()
    return {'detail': f'Pedido {id} eliminado correctamente'}

@app.get('/pedido/{id}', response_model=schemas.PedidoDetalle)
def read_pedido(id: int, db: Session = Depends(get_db)):
    pedido = db.query(models.Pedido).filter(models.Pedido.id == id).first()
    if pedido is None:
        raise HTTPException(status_code=404, detail='Pedido no encontrado')
    return schemas.PedidoDetalle.from_orm_pedido(pedido)

@app.get('/pedido/{id}/total')
def get_total_pedido(id: int, db: Session = Depends(get_db)):
    pedido = db.query(models.Pedido).filter(models.Pedido.id == id).first()
    if pedido is None:
        raise HTTPException(status_code=404, detail='Pedido no encontrado')
    total = sum(linea.cantidad * linea.producto.precio for linea in pedido.lineas_pedido)
    return {'pedido_id': id, 'total': total}

@app.get('/total')
def get_total_value(db: Session = Depends(get_db)):
    total = db.query(func.sum(models.Producto.precio * models.Producto.unidades)).scalar()
    return {'total': total or 0.0}

@app.get('/productos/resumen', response_model=List[schemas.ProductoResumen])
def get_productos_resumen(db: Session = Depends(get_db)):
    productos = db.query(models.Producto).all()
    resumen = []
    for producto in productos:
        veces = len(producto.lineas_pedido)
        unidades = sum(linea.cantidad for linea in producto.lineas_pedido)
        resumen.append(schemas.ProductoResumen(
            nombre=producto.nombre,
            precio=producto.precio,
            veces_en_pedidos=veces,
            unidades_vendidas=unidades
        ))
    return resumen