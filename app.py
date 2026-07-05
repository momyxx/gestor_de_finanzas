import streamlit as st
import pandas as pd
import uuid
from datetime import date


CATEGORIAS_BASE = ["Comidas", "Transporte", "Ocio", "Hogar", "Otros"]

ARCHIVO_DATOS = "transacciones.csv"
ARCHIVO_CATEGORIAS = "categorias.csv"

COLUMNAS_TRANSACCION = ["descripcion", "cantidad", "fecha", "categoria", "tipo"]
ANCHOS_COLUMNAS_TABLA = [3, 1.5, 1.5, 1.5, 1.5, 0.6]


class Transaccion:
    def __init__(self, descripcion, cantidad, fecha, categoria, tipo):
        self.id = str(uuid.uuid4())
        self.descripcion = descripcion
        self.cantidad = cantidad
        self.fecha = fecha
        self.categoria = categoria
        self.tipo = tipo

    def es_ingreso(self):
        return self.tipo == "Ingreso"

    def es_gasto(self):
        return self.tipo == "Gasto"

    def to_dict(self):
        return {
            "descripcion": self.descripcion,
            "cantidad": self.cantidad,
            "fecha": self.fecha,
            "categoria": self.categoria,
            "tipo": self.tipo,
        }


class Cartera:
    def __init__(self, transacciones=None):
        if transacciones is None:
            transacciones = []
        self.transacciones = transacciones

    def agregar_transaccion(self, transaccion):
        self.transacciones.append(transaccion)

    def eliminar_transaccion(self, transaccion):
        self.transacciones.remove(transaccion)

    def esta_vacia(self):
        return len(self.transacciones) == 0

    def calcular_resumen(self):
        ingresos = 0
        gastos = 0
        cantidades_gastos = []

        for t in self.transacciones:
            if t.es_ingreso():
                ingresos += t.cantidad
            elif t.es_gasto():
                gastos += t.cantidad
                cantidades_gastos.append(t.cantidad)

        balance = ingresos - gastos

        if cantidades_gastos:
            gasto_promedio = sum(cantidades_gastos) / len(cantidades_gastos)
        else:
            gasto_promedio = 0

        return {
            "ingresos": ingresos,
            "gastos": gastos,
            "balance": balance,
            "gasto_promedio": gasto_promedio,
        }

    def obtener_rango_fechas(self):
        if not self.transacciones:
            return None

        fechas = []
        for t in self.transacciones:
            fechas.append(t.fecha)

        return min(fechas), max(fechas)

    def filtrar(self, categorias_seleccionadas, fecha_desde, fecha_hasta):
        transacciones_filtradas = []

        for t in self.transacciones:
            categoria_coincide = t.categoria in categorias_seleccionadas
            fecha_coincide = fecha_desde <= t.fecha <= fecha_hasta

            if categoria_coincide and fecha_coincide:
                transacciones_filtradas.append(t)

        return Cartera(transacciones_filtradas)

    def tiene_gastos(self):
        for t in self.transacciones:
            if t.es_gasto():
                return True
        return False

    def total_por_categoria(self):
        totales = {}

        for t in self.transacciones:
            if t.es_gasto():
                categoria = t.categoria
                cantidad = t.cantidad
                if categoria in totales:
                    totales[categoria] += cantidad
                else:
                    totales[categoria] = cantidad

        return totales

    def total_por_fecha(self):
        totales = {}

        for t in self.transacciones:
            if t.es_gasto():
                fecha = t.fecha
                cantidad = t.cantidad
                if fecha in totales:
                    totales[fecha] += cantidad
                else:
                    totales[fecha] = cantidad

        return totales

    def to_dataframe(self):
        filas = []
        for t in self.transacciones:
            filas.append(t.to_dict())
        return pd.DataFrame(filas)

    def guardar(self, archivo):
        df = self.to_dataframe()
        df.to_csv(archivo, index=False)

    @staticmethod
    def cargar(archivo):
        try:
            df = pd.read_csv(archivo)
        except (FileNotFoundError, pd.errors.EmptyDataError, pd.errors.ParserError):
            return Cartera([])

        filas = df.to_dict("records")
        transacciones = []

        for fila in filas:
            transaccion = Transaccion(
                descripcion=fila["descripcion"],
                cantidad=float(fila["cantidad"]),
                fecha=date.fromisoformat(str(fila["fecha"])),
                categoria=fila["categoria"],
                tipo=fila["tipo"],
            )
            transacciones.append(transaccion)

        return Cartera(transacciones)


def mostrar_titulos():
    st.title("Tracker de Finanzas Personal")
    st.write("Lleva el control de tus gastos e ingresos de manera simple y visual")
    st.caption("Versión 1.0")


def guardar_categorias():
    df = pd.DataFrame({"categoria": st.session_state.categorias})
    df.to_csv(ARCHIVO_CATEGORIAS, index=False)


def cargar_categorias():
    try:
        df = pd.read_csv(ARCHIVO_CATEGORIAS)
    except (FileNotFoundError, pd.errors.EmptyDataError, pd.errors.ParserError):
        return list(CATEGORIAS_BASE)

    categorias_cargadas = []
    for categoria in df["categoria"]:
        categorias_cargadas.append(categoria)

    return categorias_cargadas


def inicializar_estado():
    if "cartera" not in st.session_state:
        st.session_state.cartera = Cartera.cargar(ARCHIVO_DATOS)

    if "categorias" not in st.session_state:
        st.session_state.categorias = cargar_categorias()


def agregar_categoria_nueva():
    nueva_categoria_limpia = st.session_state.input_nueva_categoria.strip()

    if nueva_categoria_limpia and nueva_categoria_limpia not in st.session_state.categorias:
        st.session_state.categorias.append(nueva_categoria_limpia)

    st.session_state.input_nueva_categoria = ""


def mostrar_formulario():
    with st.form("nueva_transaccion"):
        descripcion = st.text_input("Descripción del gasto o ingreso: ", placeholder="Ej: descripción de la operación")
        cantidad = st.number_input("Cantidad", step=1.0, min_value=0.0, format="%0.2f")
        fecha = st.date_input("Fecha")
        categoria = st.selectbox("Categoría", st.session_state.categorias, index=None, placeholder="")
        tipo_movimiento = st.radio("Tipo", ["Ingreso", "Gasto"], horizontal=True)
        enviado = st.form_submit_button("Enviar")

    if enviado:
        if not descripcion.strip():
            st.error("La descripción no puede estar vacía.")
        elif cantidad <= 0:
            st.error("La cantidad debe ser mayor que 0.")
        elif not categoria:
            st.error("Debes seleccionar una categoría.")
        else:
            transaccion = Transaccion(descripcion.strip(), cantidad, fecha, categoria, tipo_movimiento)
            st.session_state.cartera.agregar_transaccion(transaccion)

            st.success("Transacción agregada con éxito")

    with st.expander("Añadir nueva categoría"):
        st.text_input("Nueva categoría", key="input_nueva_categoria")
        st.button("+ Añadir", on_click=agregar_categoria_nueva)


def importar_csv():
    with st.expander("importar desde CSV"):
        archivo = st.file_uploader("Selecciona un archivo CSV")
        importar = st.button("importar transacciones")

        if importar:
            if archivo is None:
                st.warning("Por favor, sube primero un archivo CSV.")
                return

            if not archivo.name.lower().endswith(".csv"):
                st.error("Solo se permiten archivos CSV. Por favor, sube un archivo con extensión .csv")
                return

            try:
                df = pd.read_csv(archivo)
            except (pd.errors.EmptyDataError, pd.errors.ParserError, UnicodeDecodeError):
                st.error("El archivo no es un CSV válido.")
                return

            columnas_faltantes = []

            for columna in COLUMNAS_TRANSACCION:
                if columna not in df.columns:
                    columnas_faltantes.append(columna)

            if columnas_faltantes:
                st.error(f"El CSV debe contener las columnas: {', '.join(COLUMNAS_TRANSACCION)}")
                return

            filas = df.to_dict("records")
            transacciones_importadas = 0

            for fila in filas:
                transaccion = Transaccion(
                    descripcion=fila["descripcion"],
                    cantidad=float(fila["cantidad"]),
                    fecha=date.fromisoformat(str(fila["fecha"])),
                    categoria=fila["categoria"],
                    tipo=fila["tipo"],
                )
                st.session_state.cartera.agregar_transaccion(transaccion)
                transacciones_importadas += 1

            st.success(f"Se importaron {transacciones_importadas} transacciones con éxito.")


def mostrar_filtros():
    categorias_seleccionadas = st.multiselect("Categorías", st.session_state.categorias, default=st.session_state.categorias)

    rango_fechas = st.session_state.cartera.obtener_rango_fechas()

    if rango_fechas:
        fecha_min, fecha_max = rango_fechas
    else:
        fecha_min = date.today()
        fecha_max = date.today()

    fecha_desde = st.date_input("Desde", value=fecha_min)
    fecha_hasta = st.date_input("Hasta", value=fecha_max)

    return categorias_seleccionadas, fecha_desde, fecha_hasta


def mostrar_transacciones(cartera):
    st.subheader("Transacciones registradas:")

    if not cartera.esta_vacia():
        st.markdown(
            """
            <style>
            div[class*="st-key-fila-"] button {
                opacity: 0;
                transition: opacity 0.15s ease-in-out;
                display: flex;
                align-items: center;
                justify-content: center;
                background-color: transparent;
                padding: 0;
            }
            div[class*="st-key-fila-"] button div[data-testid="stMarkdownContainer"] {
                display: flex;
                align-items: center;
                justify-content: center;
                width: 100%;
                height: 100%;
            }
            div[class*="st-key-fila-"] button p {
                margin: 0;
                padding: 0;
                line-height: 1;
            }
            div[class*="st-key-fila-"]:hover button {
                opacity: 1;
            }
            div[class*="st-key-fila-"] button:hover {
                background-color: #ff4b4b;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

        encabezado = st.columns(ANCHOS_COLUMNAS_TABLA)
        encabezado[0].markdown("**Descripción**")
        encabezado[1].markdown("**Cantidad**")
        encabezado[2].markdown("**Fecha**")
        encabezado[3].markdown("**Categoría**")
        encabezado[4].markdown("**Tipo**")

        for t in cartera.transacciones:
            identificador_fila = getattr(t, "id", None) or id(t)

            with st.container(key=f"fila-{identificador_fila}"):
                fila = st.columns(ANCHOS_COLUMNAS_TABLA)
                fila[0].write(t.descripcion)
                fila[1].write(f"{t.cantidad:.2f}€")
                fila[2].write(t.fecha)
                fila[3].write(t.categoria)
                fila[4].write(t.tipo)

                if fila[5].button("🗑️", key=f"eliminar-{identificador_fila}", help="Eliminar esta transacción"):
                    st.session_state.cartera.eliminar_transaccion(t)

        df = cartera.to_dataframe()
        csv_datos = df.to_csv(index=False)
        st.download_button(
            "Descargar transacciones",
            data=csv_datos,
            file_name="mis_transacciones.csv",
            mime="text/csv",
        )
    else:
        st.info("No hay transacciones registradas.")


def mostrar_resumen(cartera):
    if cartera.esta_vacia():
        st.info("No hay transacciones registradas para mostrar el resumen.")
        return

    resumen = cartera.calcular_resumen()

    fila1_col1, fila1_col2 = st.columns(2)
    fila2_col1, fila2_col2 = st.columns(2)

    with fila1_col1:
        st.metric(label="Ingresos", value=f"{resumen['ingresos']:.2f}€")

    with fila1_col2:
        st.metric(label="Gastos", value=f"{resumen['gastos']:.2f}€")

    with fila2_col1:
        st.metric(label="Balance", value=f"{resumen['balance']:.2f}€")

    with fila2_col2:
        st.metric(label="Gasto promedio", value=f"{resumen['gasto_promedio']:.2f}€")


def mostrar_analisis(cartera):
    if not cartera.tiene_gastos():
        st.info("No hay transacciones de tipo Gasto para mostrar el análisis.")
        return

    total_por_categoria = cartera.total_por_categoria()

    st.subheader("Gastos por categoría")
    df_categoria = pd.DataFrame({
        "categoria": list(total_por_categoria.keys()),
        "total": list(total_por_categoria.values()),
    })
    st.bar_chart(df_categoria, x="categoria", y="total")

    total_por_fecha = cartera.total_por_fecha()
    fechas_ordenadas = sorted(total_por_fecha.keys())
    totales_ordenados = []
    for fecha in fechas_ordenadas:
        totales_ordenados.append(total_por_fecha[fecha])

    st.subheader("Gastos por fecha")
    df_fecha = pd.DataFrame({
        "fecha": fechas_ordenadas,
        "total": totales_ordenados,
    })
    st.line_chart(df_fecha, x="fecha", y="total")


mostrar_titulos()
inicializar_estado()

with st.sidebar:
    mostrar_formulario()
    importar_csv()
    categorias_seleccionadas, fecha_desde, fecha_hasta = mostrar_filtros()

cartera_filtrada = st.session_state.cartera.filtrar(
    categorias_seleccionadas,
    fecha_desde,
    fecha_hasta,
)

tab_resumen, tab_movimientos, tab_analisis = st.tabs(["Resumen", "Movimientos", "Análisis"])

with tab_resumen:
    mostrar_resumen(cartera_filtrada)

with tab_movimientos:
    mostrar_transacciones(cartera_filtrada)

with tab_analisis:
    mostrar_analisis(cartera_filtrada)

st.session_state.cartera.guardar(ARCHIVO_DATOS)
guardar_categorias()
