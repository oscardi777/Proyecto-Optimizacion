# modelo_optimización.py

import osmnx as ox
import networkx as nx
import pickle
import itertools
import random
import gurobipy as gp
from gurobipy import GRB
import matplotlib.pyplot as plt

# ------------------------
# PARÁMETROS CONFIGURABLES
# ------------------------

# Lugar de trabajo
place = "Medellín, Colombia"
nombre_archivo_caminos = "caminos_alternativos.pkl"

# Coordenadas de almacén y puntos de venta
locations = {
    "A": (6.2410, -75.5795),
    "PV1": (6.2405, -75.5805),
    "PV2": (6.2395, -75.5785),
    "PV3": (6.2420, -75.5800)
}

# Demandas de puntos de venta
demandas = {
    "A": 0,
    "PV1": 2,
    "PV2": 1,
    "PV3": 2  # Asegurándonos que la suma no supere la capacidad
}

# Capacidad máxima del vehículo
CT = 5

# Probabilidades fijas o aleatorias
Pw = 0.1
def Pa(i, j): return random.uniform(0.05, 0.15)
def Pt(i, j): return random.uniform(0.05, 0.15)

# ------------------------
# Cargar grafo y caminos alternativos
# ------------------------

print("Cargando grafo y caminos...")
G = ox.graph_from_place(place, network_type="drive")

# Convertir MultiDiGraph a DiGraph
G_simple = nx.DiGraph()
G_simple.add_nodes_from((n, G.nodes[n]) for n in G.nodes)
for u, v, data in G.edges(data=True):
    if G_simple.has_edge(u, v):
        if data['length'] < G_simple[u][v]['length']:
            G_simple[u][v].update(data)
    else:
        G_simple.add_edge(u, v, **data)
G_simple.graph.update(G.graph)

# Cargar caminos alternativos
with open(nombre_archivo_caminos, "rb") as f:
    caminos_alternativos = pickle.load(f)

nodes = {k: ox.nearest_nodes(G_simple, lon, lat) for k, (lat, lon) in locations.items()}

# ------------------------
# Construir rutas completas posibles
# ------------------------

clientes = [k for k in locations.keys() if k != "A"]
rutas_completas = []

print("Generando rutas completas posibles...")

for perm in itertools.permutations(clientes):
    orden_visita = ["A"] + list(perm) + ["A"]
    
    # Para cada tramo, elegir todas las combinaciones de caminos alternativos
    tramos = [(orden_visita[i], orden_visita[i+1]) for i in range(len(orden_visita)-1)]
    
    opciones_por_tramo = [caminos_alternativos[(i, j)]["planeados"] for (i, j) in tramos]
    
    for seleccion_camino in itertools.product(*opciones_por_tramo):
        rutas_completas.append((orden_visita, seleccion_camino))

print(f"Total de rutas completas generadas: {len(rutas_completas)}")

# ------------------------
# Calcular costos de cada ruta completa
# ------------------------

costos_rutas = {}
demandas_ruta = {}

for idx, (orden_visita, caminos_seleccionados) in enumerate(rutas_completas):
    costo_total = 0
    demanda_total = sum(demandas.get(pv, 0) for pv in orden_visita)
    
    for idx_tramo, path in enumerate(caminos_seleccionados):
    # 1. Obtener los nodos origen y destino del tramo actual
        u = orden_visita[idx_tramo]
        v = orden_visita[idx_tramo + 1]

        # 2. Caminos planeado y real
        path_plan = path
        path_real = caminos_alternativos[(u, v)]["desvio"]

        # 3. Calcular arcos
        arcos_plan = set(zip(path_plan[:-1], path_plan[1:]))
        arcos_real = set(zip(path_real[:-1], path_real[1:]))

        # 4. Arcos en común
        arcos_comunes = arcos_plan.intersection(arcos_real)

        # 5. Calcular Kij
        if len(arcos_plan) > 0:
            kij = sum(G_simple.edges[a, b]['length'] for (a, b) in arcos_comunes) / sum(G_simple.edges[a, b]['length'] for (a, b) in arcos_plan)
        else:
            kij = 0

        # 6. Calcular costo de ese tramo
        costo_total += (1 - kij) + Pa(u, v) + Pt(u, v) + Pw

    costos_rutas[idx] = costo_total
    demandas_ruta[idx] = demanda_total

# ------------------------
# Crear modelo de optimización
# ------------------------

model = gp.Model("RutaRobustaCompleta")

x = model.addVars(costos_rutas.keys(), vtype=GRB.BINARY, name="x")

# Seleccionar una sola ruta
model.addConstr(gp.quicksum(x[r] for r in costos_rutas.keys()) == 1)

# No exceder la capacidad
model.addConstr(gp.quicksum(demandas_ruta[r] * x[r] for r in demandas_ruta.keys()) <= CT)

# Función objetivo
model.setObjective(gp.quicksum(costos_rutas[r] * x[r] for r in costos_rutas.keys()), GRB.MINIMIZE)

model.optimize()

# ------------------------
# Mostrar solución
# ------------------------

if model.status == GRB.OPTIMAL:
    ruta_optima = [r for r in costos_rutas.keys() if x[r].X > 0.5][0]
    orden_visita, caminos_seleccionados = rutas_completas[ruta_optima]
    
    print("\nRuta óptima completa:")
    for idx, tramo in enumerate(caminos_seleccionados):
        print(f"{orden_visita[idx]} → {orden_visita[idx+1]} usando camino {idx+1}")
else:
    print("No se encontró solución óptima.")

# ------------------------
# Visualizar la ruta
# ------------------------

if model.status == GRB.OPTIMAL:
    # 1. Construir lista de arcos usados
    edges_usados = []
    for path in caminos_seleccionados:
        edges_usados += list(zip(path[:-1], path[1:]))

    # 2. Crear subgrafo
    G_sub = G_simple.edge_subgraph(edges_usados).copy()

    # 3. Convertir el subgrafo a MultiDiGraph
    G_sub_plot = nx.MultiDiGraph(G_sub)

    # 4. Dibujar solo la ruta óptima
    fig, ax = ox.plot_graph(
        G_sub_plot,
        node_size=30,
        edge_linewidth=3,
        edge_color="green"
    )

    # 5. Dibujar los puntos especiales encima
    for nombre, node in nodes.items():
        if node in G_sub_plot.nodes:  # Solo si el nodo está en la ruta
            x_coord, y_coord = G_sub_plot.nodes[node]['x'], G_sub_plot.nodes[node]['y']
            ax.plot(x_coord, y_coord, 'o', color='red' if nombre == "A" else 'blue')
            ax.text(x_coord + 2, y_coord + 2, nombre, fontsize=9, color='black')

    plt.title("Ruta óptima recortada")
    plt.show()
