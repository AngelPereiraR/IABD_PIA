from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()


# ── Modelos ──────────────────────────────────────────────────────────────────

class Producto(BaseModel):
    nombre: str
    precio: float
    unidades: int

class ProductoCatalogo(BaseModel):
    nombre: str
    precio: float


# ── Datos iniciales ───────────────────────────────────────────────────────────

# Actividad 5: catálogo con código como clave
catalogoDisponibles: dict[str, ProductoCatalogo] = {
    "P001": ProductoCatalogo(nombre="pan",    precio=1.20),
    "P002": ProductoCatalogo(nombre="leche",  precio=0.95),
    "P003": ProductoCatalogo(nombre="huevos", precio=2.50),
}

# Actividad 2: variable cantidad
cantidad = 10

# Actividad 3 / 4: lista de la compra (usa precios del catálogo)
productosComprados: list[Producto] = [
    Producto(nombre="pan",    precio=1.20, unidades=2),
    Producto(nombre="leche",  precio=0.95, unidades=3),
    Producto(nombre="huevos", precio=2.50, unidades=1),
]


# ── Funciones auxiliares ──────────────────────────────────────────────────────

def calcular_total() -> float:
    return sum(p.precio * p.unidades for p in productosComprados)


# ── Endpoints GET ─────────────────────────────────────────────────────────────

# Actividad 1
@app.get("/")
def raiz():
    return {"mensaje": "Hola hemos creado nuestro primer servidor en IES Fernando Aguilar"}


# Actividad 2
@app.get("/cantidad")
def obtener_cantidad():
    return {"cantidad": cantidad}


# Actividad 3 (actualizada con catálogo de actividad 5)
@app.get("/productos")
def obtener_productos():
    return productosComprados


# Actividad 4
@app.get("/total")
def obtener_total():
    return {"total": calcular_total()}


# Actividad 4.2
@app.get("/producto/{nombre}")
def obtener_producto_por_nombre(nombre: str):
    for p in productosComprados:
        if p.nombre.lower() == nombre.lower():
            return p
    raise HTTPException(status_code=404, detail=f"Producto '{nombre}' no encontrado en la compra")


# Actividad 5: catálogo completo
@app.get("/catalogo")
def obtener_catalogo():
    return catalogoDisponibles


# Actividad 5: buscar por código
@app.get("/catalogo/{codigo}")
def obtener_producto_catalogo(codigo: str):
    producto = catalogoDisponibles.get(codigo)
    if not producto:
        raise HTTPException(status_code=404, detail=f"Código '{codigo}' no existe en el catálogo")
    return {"codigo": codigo, **producto.model_dump()}


# ── Endpoints POST ────────────────────────────────────────────────────────────

# Actividad 4.3 / 6: añadir producto a la compra y descontar unidades del catálogo
@app.post("/add")
def añadir_a_compra(producto: Producto):
    # Buscar en la compra si ya existe
    for p in productosComprados:
        if p.nombre.lower() == producto.nombre.lower():
            p.unidades += producto.unidades
            return {"mensaje": "Unidades actualizadas", "producto": p}

    productosComprados.append(producto)

    # Descontar del catálogo si el nombre coincide con algún producto disponible
    for prod in catalogoDisponibles.values():
        if prod.nombre.lower() == producto.nombre.lower():
            prod.precio = producto.precio  # mantiene precio sincronizado
            break

    return {"mensaje": "Producto añadido a la compra", "producto": producto}


# Actividad 7: añadir producto nuevo al catálogo
@app.post("/catalogo/{codigo}")
def añadir_al_catalogo(codigo: str, producto: ProductoCatalogo):
    if codigo in catalogoDisponibles:
        raise HTTPException(status_code=400, detail=f"El código '{codigo}' ya existe. Usa PUT para modificar.")
    catalogoDisponibles[codigo] = producto
    return {"mensaje": "Producto añadido al catálogo", "codigo": codigo, **producto.model_dump()}


# ── Endpoints PUT ─────────────────────────────────────────────────────────────

# Actividad 8 (modificar): modificar producto del catálogo
@app.put("/catalogo/{codigo}")
def modificar_catalogo(codigo: str, producto: ProductoCatalogo):
    if codigo not in catalogoDisponibles:
        raise HTTPException(status_code=404, detail=f"Código '{codigo}' no existe en el catálogo")
    catalogoDisponibles[codigo] = producto
    return {"mensaje": "Producto actualizado", "codigo": codigo, **producto.model_dump()}


# ── Endpoints DELETE ──────────────────────────────────────────────────────────

# Actividad 4.4: borrar producto de la compra
@app.delete("/producto/{nombre}")
def borrar_de_compra(nombre: str):
    for i, p in enumerate(productosComprados):
        if p.nombre.lower() == nombre.lower():
            productosComprados.pop(i)
            return {"mensaje": f"Producto '{nombre}' eliminado de la compra"}
    raise HTTPException(status_code=404, detail=f"Producto '{nombre}' no encontrado en la compra")


# Actividad 8 (borrar): borrar producto del catálogo
@app.delete("/catalogo/{codigo}")
def borrar_del_catalogo(codigo: str):
    if codigo not in catalogoDisponibles:
        raise HTTPException(status_code=404, detail=f"Código '{codigo}' no existe en el catálogo")
    eliminado = catalogoDisponibles.pop(codigo)
    return {"mensaje": f"Código '{codigo}' eliminado del catálogo", "producto": eliminado}
