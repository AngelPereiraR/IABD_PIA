import os
from typing import List
from datetime import date, datetime, timedelta
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import func
import bcrypt
from jose import jwt
from dotenv import load_dotenv
from database import engine, Base, get_db
import models
import schemas

load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY', 'clave-secreta-super-segura-para-jwt-2026')
ALGORITHM = os.getenv('ALGORITHM', 'HS256')
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', '30'))

def hash_contrasena(contrasena: str) -> str:
    return bcrypt.hashpw(contrasena.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verificar_contrasena(contrasena: str, hash_guardado: str) -> bool:
    return bcrypt.checkpw(contrasena.encode('utf-8'), hash_guardado.encode('utf-8'))

Base.metadata.create_all(bind=engine)

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')

def get_usuario_actual(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get('sub')
        if user_id is None:
            raise ValueError()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Token inválido o expirado',
            headers={'WWW-Authenticate': 'Bearer'},
        )
    usuario = db.query(models.Usuario).filter(models.Usuario.id == int(user_id)).first()
    if usuario is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Usuario no encontrado')
    return usuario

def requiere_administrador(usuario: models.Usuario = Depends(get_usuario_actual)):
    if usuario.rol != 'administrador':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Acceso restringido a administradores',
        )
    return usuario

@app.post('/usuarios', response_model=schemas.UsuarioResponse, status_code=status.HTTP_201_CREATED)
def create_usuario(usuario: schemas.UsuarioCreate, db: Session = Depends(get_db)):
    existente = db.query(models.Usuario).filter(models.Usuario.id_usuario == usuario.id_usuario).first()
    if existente:
        raise HTTPException(status_code=400, detail='El nombre de usuario ya existe')
    
    nuevo = models.Usuario(
        id_usuario=usuario.id_usuario,
        contrasena_hash=hash_contrasena(usuario.contrasena),
        rol=usuario.rol
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo

@app.post('/login', response_model=schemas.Token)
def login(credenciales: schemas.LoginRequest, db: Session = Depends(get_db)):
    usuario = db.query(models.Usuario).filter(models.Usuario.id_usuario == credenciales.id_usuario).first()
    if usuario is None or not verificar_contrasena(credenciales.contrasena, usuario.contrasena_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Credenciales incorrectas',
            headers={'WWW-Authenticate': 'Bearer'},
        )
    expiracion = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        'sub': str(usuario.id),
        'rol': usuario.rol,
        'exp': expiracion,
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return schemas.Token(access_token=token, token_type='bearer')


@app.post('/token', response_model=schemas.Token, include_in_schema=False)
def token_swagger(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Endpoint exclusivo para el flujo OAuth2 de Swagger UI."""
    usuario = db.query(models.Usuario).filter(models.Usuario.id_usuario == form_data.username).first()
    if usuario is None or not verificar_contrasena(form_data.password, usuario.contrasena_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Credenciales incorrectas',
            headers={'WWW-Authenticate': 'Bearer'},
        )
    expiracion = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        'sub': str(usuario.id),
        'rol': usuario.rol,
        'exp': expiracion,
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return schemas.Token(access_token=token, token_type='bearer')


@app.get('/admin/usuarios', response_model=List[schemas.UsuarioResponse])
def listar_usuarios(usuario: models.Usuario = Depends(requiere_administrador), db: Session = Depends(get_db)):
    return db.query(models.Usuario).all()


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