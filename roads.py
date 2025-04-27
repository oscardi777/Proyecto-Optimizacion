# roads.py
# -------------------------------------
# Este script descarga el grafo vial de Medellín,
# lo simplifica y genera múltiples caminos alternativos
# entre cada par de puntos de interés (almacén y puntos de venta).
# Finalmente, guarda los resultados en un archivo .pkl.

import osmnx as ox                   # Para descargar y trabajar con mapas de OpenStreetMap
import networkx as nx                # Para manipulación de grafos y algoritmos de caminos
import pickle                        # Para guardar estructuras de datos en disco
from itertools import islice         # Para limitar la cantidad de elementos extraídos de un iterador

# ------------------------
# PARÁMETROS CONFIGURABLES
# ------------------------

# Nombre de la ciudad o área de la que descargaremos el grafo
place = "Medellín, Colombia"

# Cantidad de caminos alternativos a extraer por cada par de nodos
# Puedes ajustar este valor para obtener más o menos rutas
NUM_CAMINOS_ALTERNATIVOS = 4  # <<<< Cambia este número según tu necesidad

# Coordenadas (latitud, longitud) del almacén y puntos de venta
# Estas coordenadas se usarán para localizar los nodos más cercanos en el grafo
locations = {
    "A":  (6.2410, -75.5795),  # Almacén
    "PV1":(6.2405, -75.5805),  # Punto de venta 1
    "PV2":(6.2395, -75.5785),  # Punto de venta 2
    "PV3":(6.2420, -75.5800)   # Punto de venta 3
}

# ------------------------
# 1. DESCARGA DEL GRAFO
# ------------------------
print("Descargando grafo de", place)
# graph_from_place trae un MultiDiGraph de OSMnx con calles
G = ox.graph_from_place(place, network_type="drive")
print(f"Grafo descargado: {len(G.nodes)} nodos, {len(G.edges)} aristas.")

# ------------------------
# 2. SIMPLIFICACIÓN A DiGraph
# ------------------------
# Convertimos el grafo multiarco (MultiDiGraph) a uno simple (DiGraph)
# para poder usar shortest_simple_paths sin errores.

# Creamos un DiGraph vacío
G_simple = nx.DiGraph()

# 2.1 Copiar nodos con sus atributos (x, y, street_count, etc.)
G_simple.add_nodes_from((n, G.nodes[n]) for n in G.nodes)

# 2.2 Copiar arcos: si hay varios entre u y v, nos quedamos con el de menor 'length'
for u, v, data in G.edges(data=True):
    if G_simple.has_edge(u, v):
        # Si ya existía un arco, comparamos longitudes y guardamos el menor
        if data['length'] < G_simple[u][v]['length']:
            G_simple[u][v].update(data)
    else:
        # Si no existía, lo agregamos directamente
        G_simple.add_edge(u, v, **data)

# 2.3 Copiar atributos globales del grafo (por ejemplo, el CRS)
G_simple.graph.update(G.graph)
print(f"Grafo convertido a DiGraph simple: {len(G_simple.nodes)} nodos, {len(G_simple.edges)} aristas.")

# ------------------------
# 3. LOCALIZAR NODOS DE INTERÉS
# ------------------------
# Para cada ubicación dada (lat, lon), buscamos el nodo más cercano en el grafo
nodes = {
    key: ox.nearest_nodes(G_simple, lon, lat)
    for key, (lat, lon) in locations.items()
}
print("Nodos encontrados para los puntos de interés:", nodes)

# ------------------------
# 4. CÁLCULO DE CAMINOS ALTERNATIVOS
# ------------------------
# Para cada par de puntos de interés (i, j), extraemos los primeros k caminos simples
caminos_alternativos = {}
for i in nodes:
    for j in nodes:
        if i == j:
            continue  # No buscamos caminos de un punto a sí mismo
        origen = nodes[i]
        destino = nodes[j]
        print(f"Buscando caminos de {i} a {j}...")
        try:
            # shortest_simple_paths genera caminos ordenados por longitud
            # islice limita a NUM_CAMINOS_ALTERNATIVOS resultados
            rutas = list(islice(
                nx.shortest_simple_paths(G_simple, origen, destino, weight='length'),
                NUM_CAMINOS_ALTERNATIVOS
            ))
            
            if len(rutas) >= 2:
                caminos_alternativos[(i, j)] = {
                    "planeados": rutas[:-1],  # Todos excepto el último son planeados
                    "desvio": rutas[-1]       # El último camino se guarda como desvío
                }
            elif len(rutas) == 1:
                caminos_alternativos[(i, j)] = {
                    "planeados": rutas,
                    "desvio": rutas[0]  # Si solo hay uno, mismo camino como planeado y desvío
                }
        except Exception as e:
            print(f"Error al encontrar caminos de {i} a {j}: {e}")

# ------------------------
# 5. GUARDAR RESULTADOS
# ------------------------
# Guardamos el diccionario de caminos en un archivo pickle para usarlo luego
nombre_archivo = "caminos_alternativos.pkl"
with open(nombre_archivo, "wb") as f:
    pickle.dump(caminos_alternativos, f)

print(f"\n Caminos guardados en {nombre_archivo}!")