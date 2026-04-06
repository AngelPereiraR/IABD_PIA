from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Producto(Base):
    __tablename__ = 'productos'

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String)
    precio = Column(Float)
    unidades = Column(Integer)

    lineas_pedido = relationship('LineaPedido', back_populates='producto')

class Cliente(Base):
    __tablename__ = 'clientes'

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String)
    email = Column(String, unique=True)

    pedidos = relationship('Pedido', back_populates='cliente')

class Pedido(Base):
    __tablename__ = 'pedidos'

    id = Column(Integer, primary_key=True, index=True)
    fecha = Column(Date)
    cliente_id = Column(Integer, ForeignKey('clientes.id'))

    cliente = relationship('Cliente', back_populates='pedidos')
    lineas_pedido = relationship('LineaPedido', back_populates='pedido', cascade='all, delete-orphan')

class LineaPedido(Base):
    __tablename__ = 'lineas_pedido'

    id = Column(Integer, primary_key=True, index=True)
    pedido_id = Column(Integer, ForeignKey('pedidos.id'))
    producto_id = Column(Integer, ForeignKey('productos.id'))
    cantidad = Column(Integer)

    pedido = relationship('Pedido', back_populates='lineas_pedido')
    producto = relationship('Producto', back_populates='lineas_pedido')

class Usuario(Base):
    __tablename__ = 'usuarios'

    id = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(String, unique=True, index=True, nullable=False)
    contrasena_hash = Column(String, nullable=False)
    rol = Column(String, nullable=False, default='no administrador')