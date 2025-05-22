fila = [1, 2, 3, 4, 5]
elemento = 3

print("Antes:", fila)

if elemento in fila:
    fila.remove(elemento)
    fila.append(elemento)
else:
    print(f"Elemento {elemento} não está na fila!")

print("Depois:", fila)
