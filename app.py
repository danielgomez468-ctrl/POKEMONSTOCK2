import tkinter as tk
from tkinter import messagebox
import requests
from bs4 import BeautifulSoup
import threading
import time
from datetime import datetime


# ============================================================
# CONFIGURACIÓN
# ============================================================

INTERVALO = 60

ejecutando = False
hilo = None
contador = 0

productos_conocidos = {
    "POKEMILLON": set(),
    "TODOHITS": set()
}


# ============================================================
# PÁGINAS QUE VAMOS A VIGILAR
# ============================================================

TIENDAS = {

    "POKEMILLON": [
        "https://www.pokemillon.com/collections/eternos-30-aniversario-eternals-30th-anniversary"
    ],

    "TODOHITS": [
        "https://todohits.com/collections/all"
    ]

}


# ============================================================
# PALABRAS QUE IDENTIFICAN EL 30 ANIVERSARIO
# ============================================================

PALABRAS = [
    "30th anniversary",
    "30th anniversary pokemon",
    "pokemon 30th anniversary",
    "30th celebration",
    "30th celebrations",
    "30 aniversario",
    "30 aniversario pokemon",
    "pokemon 30 aniversario",
    "celebraciones 30 aniversario",
    "celebraciones 30th",
    "30th"
]


# ============================================================
# CABECERAS
# ============================================================

HEADERS = {
    "User-Agent":
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/151.0.0.0 Safari/537.36",

    "Accept":
        "text/html,application/xhtml+xml,"
        "application/xml;q=0.9,image/avif,"
        "image/webp,*/*;q=0.8",

    "Accept-Language":
        "es-ES,es;q=0.9,en;q=0.8"
}


# ============================================================
# COMPROBAR SI EL TEXTO ES DEL 30 ANIVERSARIO
# ============================================================

def es_30_aniversario(texto):

    if not texto:
        return False

    texto = texto.lower()

    for palabra in PALABRAS:

        if palabra in texto:
            return True

    return False


# ============================================================
# LIMPIAR TEXTO
# ============================================================

def limpiar(texto):

    if not texto:
        return ""

    return " ".join(
        texto.split()
    ).strip()


# ============================================================
# DESCARGAR PÁGINA
# ============================================================

def descargar(url):

    try:

        respuesta = requests.get(
            url,
            headers=HEADERS,
            timeout=20
        )

        if respuesta.status_code != 200:

            return None, (
                "HTTP "
                + str(respuesta.status_code)
            )

        return respuesta.text, None

    except requests.exceptions.Timeout:

        return None, "TIMEOUT"

    except requests.exceptions.ConnectionError:

        return None, "CONEXIÓN"

    except Exception as e:

        return None, str(e)


# ============================================================
# EXTRAER PRODUCTOS
# ============================================================

def buscar_productos(html):

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    productos = set()


    # --------------------------------------------------------
    # SHOPIFY: PRODUCT GRID
    # --------------------------------------------------------

    selectores = [

        ".product-card",

        ".card-wrapper",

        ".product-grid-item",

        ".grid-product",

        ".product-item",

        ".product-card-wrapper",

        "[class*='product-card']",

        "[class*='product-item']",

        "[class*='product-grid']"

    ]


    elementos = []

    for selector in selectores:

        encontrados = soup.select(
            selector
        )

        elementos.extend(
            encontrados
        )


    # --------------------------------------------------------
    # ANALIZAR CADA PRODUCTO
    # --------------------------------------------------------

    for elemento in elementos:

        texto = limpiar(
            elemento.get_text(
                " ",
                strip=True
            )
        )


        if not texto:
            continue


        if es_30_aniversario(
            texto
        ):

            # Intentar obtener título
            titulo = None


            for selector in [
                "h1",
                "h2",
                "h3",
                "h4",
                ".card__heading",
                ".product-title",
                ".product-card__title",
                "[class*='title']"
            ]:

                encontrado = elemento.select_one(
                    selector
                )

                if encontrado:

                    titulo = limpiar(
                        encontrado.get_text(
                            " ",
                            strip=True
                        )
                    )

                    if titulo:
                        break


            if titulo:

                productos.add(
                    titulo
                )

            else:

                # Si no encontramos título,
                # usamos una versión corta
                if len(texto) <= 200:

                    productos.add(
                        texto
                    )


    # --------------------------------------------------------
    # SEGUNDA BÚSQUEDA:
    # ENLACES DE PRODUCTOS
    # --------------------------------------------------------

    for enlace in soup.find_all(
        "a",
        href=True
    ):

        texto = limpiar(
            enlace.get_text(
                " ",
                strip=True
            )
        )

        href = enlace.get(
            "href",
            ""
        )


        # Solo consideramos enlaces
        # que parezcan productos

        parece_producto = (
            "/products/" in href
            or "/product/" in href
        )


        if not parece_producto:
            continue


        if es_30_aniversario(
            texto
        ):

            if texto:

                if len(texto) <= 200:

                    productos.add(
                        texto
                    )


    return productos


# ============================================================
# COMPROBAR TIENDA
# ============================================================

def comprobar_tienda(
    nombre,
    urls
):

    productos = set()

    errores = []


    for url in urls:

        html, error = descargar(
            url
        )


        if html is None:

            errores.append(
                error
            )

            continue


        encontrados = buscar_productos(
            html
        )


        productos.update(
            encontrados
        )


    # --------------------------------------------------------
    # RESULTADO
    # --------------------------------------------------------

    if productos:

        return (
            "PUBLICADO",
            productos,
            ""
        )


    if errores:

        return (
            "ERROR",
            set(),
            errores[0]
        )


    return (
        "NO ENCONTRADO",
        set(),
        ""
    )


# ============================================================
# ACTUALIZAR FILA
# ============================================================

def actualizar_fila(
    nombre,
    estado,
    productos,
    error
):

    for fila in filas:

        if fila["nombre"] != nombre:
            continue


        fila["estado"].config(
            text=estado
        )


        if estado == "PUBLICADO":

            fila["estado"].config(
                fg="green"
            )

        elif estado == "NO ENCONTRADO":

            fila["estado"].config(
                fg="gray"
            )

        else:

            fila["estado"].config(
                fg="orange"
            )


        if productos:

            lista = sorted(
                productos
            )


            texto = ""

            for producto in lista[:15]:

                texto += (
                    "• "
                    + producto
                    + "\n"
                )


            if len(lista) > 15:

                texto += (
                    "\n... y "
                    + str(
                        len(lista) - 15
                    )
                    + " productos más"
                )


            fila["productos"].config(
                text=texto
            )


        elif error:

            fila["productos"].config(
                text=(
                    "Error de consulta: "
                    + error
                )
            )

        else:

            fila["productos"].config(
                text="Sin productos detectados"
            )


# ============================================================
# MOSTRAR NUEVOS PRODUCTOS
# ============================================================

def mostrar_nuevos(
    tienda,
    nuevos
):

    if not nuevos:
        return


    mensaje = (
        "🚨 NUEVO PRODUCTO PUBLICADO\n\n"
        + tienda
        + "\n\n"
    )


    for producto in sorted(
        nuevos
    ):

        mensaje += (
            "• "
            + producto
            + "\n"
        )


    ventana.bell()


    messagebox.showinfo(
        "POKEMONSTOCK - NUEVO PRODUCTO",
        mensaje
    )


# ============================================================
# CICLO DE MONITORIZACIÓN
# ============================================================

def monitor():

    global contador
    global ejecutando


    while ejecutando:

        hora = datetime.now().strftime(
            "%H:%M:%S"
        )


        ventana.after(
            0,
            lambda h=hora:
            ultima.config(
                text=(
                    "Última comprobación: "
                    + h
                )
            )
        )


        # ====================================================
        # COMPROBAR LAS DOS TIENDAS
        # ====================================================

        for nombre, urls in TIENDAS.items():

            if not ejecutando:
                break


            estado, productos, error = (
                comprobar_tienda(
                    nombre,
                    urls
                )
            )


            # ------------------------------------------------
            # DETECTAR NUEVOS
            # ------------------------------------------------

            anteriores = productos_conocidos[
                nombre
            ]


            # La primera comprobación solamente
            # establece la referencia inicial.
            if contador == 0:

                nuevos = set()

            else:

                nuevos = (
                    productos
                    - anteriores
                )


            productos_conocidos[
                nombre
            ] = set(productos)


            # ------------------------------------------------
            # ACTUALIZAR INTERFAZ
            # ------------------------------------------------

            ventana.after(
                0,
                lambda n=nombre,
                e=estado,
                p=productos,
                er=error:
                actualizar_fila(
                    n,
                    e,
                    p,
                    er
                )
            )


            # ------------------------------------------------
            # AVISAR NUEVOS
            # ------------------------------------------------

            if nuevos:

                ventana.after(
                    0,
                    lambda n=nombre,
                    x=nuevos:
                    mostrar_nuevos(
                        n,
                        x
                    )
                )


        # ====================================================
        # CONTADOR
        # ====================================================

        contador += 1


        ventana.after(
            0,
            lambda c=contador:
            contador_label.config(
                text=(
                    "Comprobaciones realizadas: "
                    + str(c)
                )
            )
        )


        # ====================================================
        # CUENTA ATRÁS
        # ====================================================

        for segundos in range(
            INTERVALO,
            0,
            -1
        ):

            if not ejecutando:
                break


            ventana.after(
                0,
                lambda s=segundos:
                proxima.config(
                    text=(
                        "Próxima comprobación: "
                        + str(s)
                        + " segundos"
                    )
                )
            )


            time.sleep(1)


# ============================================================
# INICIAR
# ============================================================

def iniciar():

    global ejecutando
    global hilo


    if ejecutando:
        return


    ejecutando = True


    estado_programa.config(
        text="🟢 MONITOR ACTIVO",
        fg="green"
    )


    hilo = threading.Thread(
        target=monitor,
        daemon=True
    )


    hilo.start()


# ============================================================
# DETENER
# ============================================================

def detener():

    global ejecutando

    ejecutando = False


    estado_programa.config(
        text="🔴 MONITOR DETENIDO",
        fg="red"
    )


    proxima.config(
        text="Próxima comprobación: detenida"
    )


# ============================================================
# CERRAR
# ============================================================

def cerrar():

    global ejecutando

    ejecutando = False

    ventana.destroy()


# ============================================================
# INTERFAZ
# ============================================================

ventana = tk.Tk()

ventana.title(
    "POKEMONSTOCK - Pokémon 30th Anniversary"
)

ventana.geometry(
    "1100x700"
)

ventana.resizable(
    False,
    False
)


# ============================================================
# TÍTULO
# ============================================================

tk.Label(
    ventana,
    text="POKEMONSTOCK",
    font=(
        "Arial",
        30,
        "bold"
    )
).pack(
    pady=(25, 5)
)


tk.Label(
    ventana,
    text=(
        "Pokémon TCG · 30th Anniversary"
    ),
    font=(
        "Arial",
        16
    )
).pack(
    pady=5
)


tk.Label(
    ventana,
    text=(
        "Solo detecta productos publicados "
        "de la colección"
    ),
    font=(
        "Arial",
        11,
        "bold"
    )
).pack(
    pady=(0, 25)
)


# ============================================================
# CABECERA
# ============================================================

marco = tk.Frame(
    ventana
)

marco.pack(
    padx=30,
    fill="x"
)


tk.Label(
    marco,
    text="TIENDA",
    font=(
        "Arial",
        11,
        "bold"
    )
).grid(
    row=0,
    column=0,
    sticky="nw"
)


tk.Label(
    marco,
    text="ESTADO",
    font=(
        "Arial",
        11,
        "bold"
    )
).grid(
    row=0,
    column=1,
    padx=40,
    sticky="nw"
)


tk.Label(
    marco,
    text="PRODUCTOS PUBLICADOS",
    font=(
        "Arial",
        11,
        "bold"
    )
).grid(
    row=0,
    column=2,
    sticky="nw"
)


# ============================================================
# FILAS
# ============================================================

filas = []


for numero, nombre in enumerate(
    TIENDAS.keys(),
    start=1
):

    etiqueta_nombre = tk.Label(
        marco,
        text=nombre,
        font=(
            "Arial",
            12,
            "bold"
        )
    )


    etiqueta_nombre.grid(
        row=numero,
        column=0,
        sticky="nw",
        pady=20
    )


    etiqueta_estado = tk.Label(
        marco,
        text="SIN COMPROBAR",
        font=(
            "Arial",
            11,
            "bold"
        ),
        fg="gray"
    )


    etiqueta_estado.grid(
        row=numero,
        column=1,
        padx=40,
        sticky="nw",
        pady=20
    )


    etiqueta_productos = tk.Label(
        marco,
        text="",
        font=(
            "Arial",
            9
        ),
        justify="left",
        anchor="w",
        wraplength=650
    )


    etiqueta_productos.grid(
        row=numero,
        column=2,
        sticky="nw",
        pady=15
    )


    filas.append(
        {
            "nombre": nombre,
            "estado": etiqueta_estado,
            "productos": etiqueta_productos
        }
    )


# ============================================================
# SEPARADOR
# ============================================================

tk.Frame(
    ventana,
    height=2,
    bg="gray"
).pack(
    fill="x",
    padx=30,
    pady=15
)


# ============================================================
# INFORMACIÓN
# ============================================================

estado_programa = tk.Label(
    ventana,
    text="🔴 MONITOR DETENIDO",
    font=(
        "Arial",
        14,
        "bold"
    ),
    fg="red"
)

estado_programa.pack(
    pady=5
)


ultima = tk.Label(
    ventana,
    text="Última comprobación: --:--:--",
    font=(
        "Arial",
        10
    )
)

ultima.pack(
    pady=2
)


proxima = tk.Label(
    ventana,
    text="Próxima comprobación: detenida",
    font=(
        "Arial",
        10
    )
)

proxima.pack(
    pady=2
)


contador_label = tk.Label(
    ventana,
    text="Comprobaciones realizadas: 0",
    font=(
        "Arial",
        11,
        "bold"
    )
)

contador_label.pack(
    pady=5
)


# ============================================================
# BOTONES
# ============================================================

botones = tk.Frame(
    ventana
)

botones.pack(
    pady=20
)


tk.Button(
    botones,
    text="▶ INICIAR",
    font=(
        "Arial",
        12,
        "bold"
    ),
    width=16,
    command=iniciar
).grid(
    row=0,
    column=0,
    padx=10
)


tk.Button(
    botones,
    text="⛔ DETENER",
    font=(
        "Arial",
        12,
        "bold"
    ),
    width=16,
    command=detener
).grid(
    row=0,
    column=1,
    padx=10
)


# ============================================================
# CERRAR
# ============================================================

ventana.protocol(
    "WM_DELETE_WINDOW",
    cerrar
)


# ============================================================
# ARRANCAR
# ============================================================

ventana.mainloop()
