# README - Modelo de Optimización de Rutas / Desvios

Este documento resume la explicación detallada del funcionamiento de los archivos `roads.py` y `model.py`, que conforman el proyecto de optimización.

---

# 1. Archivo: `roads.py`

**Objetivo:**
- Descargar el grafo vial de Medellín.
- Simplificar el grafo.
- Generar caminos alternativos entre pares de nodos (almacén y puntos de venta).
- Guardar los caminos alternativos en un archivo `.pkl`.

## Flujo general:

### 1.1. Descarga del grafo
- Se utiliza `ox.graph_from_place` para obtener las calles de Medellín.
- Se trabaja sobre el tipo `drive`, es decir, calles transitables en vehículo.

### 1.2. Simplificación del grafo
- Se convierte el MultiDiGraph original (que puede tener varios arcos entre dos nodos) a un DiGraph (solo un arco por par).
- Se conserva el arco de menor longitud para simplificar el procesamiento.

### 1.3. Ubicación de nodos de interés
- Para las coordenadas del almacén y puntos de venta, se localiza el nodo más cercano en el grafo.

### 1.4. Generación de caminos alternativos
- Se utiliza `shortest_simple_paths` para encontrar varios caminos simples ordenados por longitud entre cada par.
- Se guarda:
  - Una lista de caminos planeados (`planeados`).
  - Un camino de desvío (`desvio`) (el último de la lista o el mismo si solo hay uno).

### 1.5. Guardado
- Se guarda el diccionario de caminos alternativos en un archivo `.pkl`.


---

# 2. Archivo: `model.py`

**Objetivo:**
- Cargar el grafo simplificado y los caminos alternativos.
- Generar todas las rutas completas posibles combinando ordenes de visita y caminos.
- Calcular los costos robustos de cada ruta considerando desviaciones.
- Formular y resolver un modelo de programación entera con Gurobi.
- Visualizar la solución óptima en un mapa.


## Flujo general:

### 2.1. Carga inicial
- Se cargan:
  - El grafo simplificado de Medellín.
  - El archivo `caminos_alternativos.pkl`.
  - Las ubicaciones de puntos de interés y demandas.

### 2.2. Construcción de rutas completas
- Se generan todas las permutaciones de los clientes.
- Para cada orden de visita, se combinan todas las opciones de caminos alternativos por tramo.

### 2.3. Cálculo de costos de rutas
- Para cada ruta completa:
  - Se calcula la demanda total.
  - Para cada tramo:
    - Se toma el camino planeado.
    - Se genera un camino real alternativo (puede ser desde el pickle o recalculado en tiempo real).
    - Se calculan los arcos comunes y se estima el parámetro \(K_{ij}\) según la longitud de los arcos comunes.
    - Se suma el costo de desviación, considerando probabilidades de accidente, tráfico y clima.

### 2.4. Formulación del modelo de optimización
- Variables binarias \(x_r\) para seleccionar rutas completas.
- Restricciones:
  - Solo se selecciona una ruta completa.
  - La demanda total de la ruta no debe exceder la capacidad del vehículo.
- Objetivo:
  - Minimizar el costo robusto total.

### 2.5. Resolución y extracción de resultados
- Se resuelve el modelo usando Gurobi.
- Se identifica la ruta óptima seleccionada.

### 2.6. Visualización
- Se construye un subgrafo con los tramos utilizados.
- Se dibuja el subgrafo sobre el mapa de Medellín, resaltando los caminos seleccionados y los puntos de interés.


---

# 3. Conceptos clave utilizados

- **MultiDiGraph**: grafo con múltiples arcos entre dos nodos.
- **DiGraph**: grafo dirigido simple, solo un arco entre dos nodos.
- **Kij**: proporción de la longitud del camino planeado que se mantiene en el camino real.
- **shortest_simple_paths**: algoritmo de NetworkX para obtener caminos simples más cortos entre dos nodos.
- **Gurobi**: optimizador matemático usado para resolver el modelo de programación entera.


---

# 4. Estado actual del proyecto

- **roads.py** genera y guarda los caminos correctamente.
- **model.py** construye rutas, calcula costos robustos realistas y resuelve el modelo de optimización.
- Se ha mejorado el cálculo de desviaciones para apegarse más al planteamiento teórico.
- Se permiten alternativas de modelar desviaciones aleatoriamente o recalculándolas en tiempo real.


# Proyecto Final Optimizacion Oscar Diaz y Samuel
© 2025 | Proyecto de Optimización 

