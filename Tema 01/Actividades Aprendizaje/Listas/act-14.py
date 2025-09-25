articulos = []
precios = []
cantidadesVendidas = []
sucursales = ["Cádiz", "Puerto Real", "San Fernando", "Chiclana"]

while len(articulos) < 5:
    articulo = input("Introduce el nombre del artículo: ")
    cantidades = []
    try:
        precio = float(input(f"Introduce el precio de {articulo}: "))
        if precio < 0:
          raise ValueError
        for i in range(len(sucursales)):
            cantidad = int(input(f"Introduce la cantidad vendida de {articulo} en la sucursal {sucursales[i]}: "))
            if cantidad < 0:
              raise ValueError
            cantidades.append(cantidad)
    except ValueError:
        print("Por favor, introduce un valor válido para el precio y las cantidades.")
        continue

    articulos.append(articulo)
    precios.append(precio)
    cantidadesVendidas.append(cantidades)
    
print("\nResumen de ventas:")
for i in range(len(articulos)):
  totalVendido = sum(cantidadesVendidas[i][j] * precios[i] for j in range(len(sucursales)))
  print(f"Artículo: {articulos[i]}, Precio: {precios[i]:.2f}, Total vendido: {totalVendido:.2f}")

totalSucursal2 = sum(cantidadesVendidas[i][j] * precios[i] for i in range(len(articulos)) for j in range(len(sucursales)))
print(f"Sucursal 2: {sucursales[1]}, Total vendido: {totalSucursal2:.2f}")

totalArticulo3Sucursal1 = sum(cantidadesVendidas[2][j] * precios[2] for j in range(len(sucursales)))
print(f"Artículo 3: {articulos[2]}, Sucursal 1: {sucursales[0]}, Total vendido: {totalArticulo3Sucursal1:.2f}")

recaudacionTotalPorSucursal = [sum(cantidadesVendidas[i][j] * precios[i] for i in range(len(articulos))) for j in range(len(sucursales))]
print(f"Recaudación total por sucursal:")
for i in range(len(sucursales)):
  print(f"Sucursal: {sucursales[i]}, Total recaudado: {recaudacionTotalPorSucursal[i]:.2f}")

recaudacionTotalEmpresa = sum(recaudacionTotalPorSucursal)
print(f"Recaudación total de la empresa: {recaudacionTotalEmpresa:.2f}")

sucursalMayor = recaudacionTotalPorSucursal.index(max(recaudacionTotalPorSucursal))
print(f"Sucursal con mayor recaudación: {sucursales[sucursalMayor]} con {recaudacionTotalPorSucursal[sucursalMayor]:.2f}€")