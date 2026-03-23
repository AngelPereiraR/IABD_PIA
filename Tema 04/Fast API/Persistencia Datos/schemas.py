from pydantic import BaseModel

class ProductoBase(BaseModel):
    nombre: str
    precio: float
    unidades: int

class ProductoCreate(ProductoBase):
    pass

class Producto(ProductoBase):
    id: int

    class Config:
        from_attributes = True

class ClienteCreate(BaseModel):
    nombre: str
    email: str

class Cliente(BaseModel):
    id: int
    nombre: str
    email: str

    class Config:
        from_attributes = True

class ClienteBasico(BaseModel):
    id: int
    nombre: str

    class Config:
        from_attributes = True

class PedidoCreate(BaseModel):
    cliente_id: int

class Pedido(BaseModel):
    id: int
    fecha: object
    cliente_id: int

    class Config:
        from_attributes = True

class PedidoConCliente(BaseModel):
    id: int
    fecha: object
    cliente: ClienteBasico

    class Config:
        from_attributes = True

class LineaPedidoCreate(BaseModel):
    pedido_id: int
    producto_id: int
    cantidad: int

class LineaPedido(BaseModel):
    id: int
    pedido_id: int
    producto_id: int
    cantidad: int

    class Config:
        from_attributes = True

class ProductoBasico(BaseModel):
    id: int
    nombre: str
    precio: float

    class Config:
        from_attributes = True

class LineaPedidoDetalle(BaseModel):
    cantidad: int
    producto: ProductoBasico

    class Config:
        from_attributes = True

class PedidoDetalle(BaseModel):
    id: int
    fecha: object
    cliente: ClienteBasico
    lineas: list[LineaPedidoDetalle]

    class Config:
        from_attributes = True

    @classmethod
    def from_orm_pedido(cls, pedido):
        return cls(
            id=pedido.id,
            fecha=pedido.fecha,
            cliente=pedido.cliente,
            lineas=pedido.lineas_pedido
        )

class ProductoResumen(BaseModel):
    nombre: str
    precio: float
    veces_en_pedidos: int
    unidades_vendidas: int

    class Config:
        from_attributes = True