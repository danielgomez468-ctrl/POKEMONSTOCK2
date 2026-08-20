import tkinter as tk
from tkinter import messagebox
import threading
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin


# ============================================================
# CONFIGURACIÓN
# ============================================================

INTERVALO = 60  # 1 minuto

ejecutando = False
hilo_monitor = None
contador_comprobaciones = 0

# Productos encontrados en la comprobación anterior
productos_anteriores = {}


# ============================================================
# PALABRAS QUE IDENTIFICAN LA COLECCIÓN
# ============================================================

PALABRAS_COLECCION = [
    "30th anniversary",
    "30th anniversary pokemon",
    "pokemon 30th anniversary",
    "pokemon 30th",
    "30th pokemon",

    "30 aniversario",
    "30 aniversario pokemon",
    "pokemon 30 aniversario",

    "30th celebration",
    "30th celebrations",
    "pokemon 30th celebration",
    "pokemon 30th celebrations",

    "celebraciones 30 aniversario",
    "celebraciones 30th",
    "30 aniversario pokemon tcg",
]


# ============================================================
# TIENDAS
# ============================================================

TIENDAS = [
    {
        "nombre": "POKEMILLON",

        "urls": [
            "https://www.pokemillon.com/collections/eternos-30-aniversario-eternals-30th-anniversary",
            "https://www.pokemillon.com/collections/all/pokemon",
        ],
    },

    {
        "nombre": "TODOHITS",

        "urls": [
            "https://todohits.com/collections/all",
            "https://todohits.com/collections/novedades",
        ],
    },

    {
        "nombre": "POKEBANK",

        "urls": [
            "https://pokebank.es/",
        ],
    },

    {
        "nombre": "SUNNY STORE",

        "urls": [
            "https://sunnystore.es/",
        ],
    },

    {
        "nombre": "UN SOBRE MÁS",

        "urls": [
            "https://unsobremas.com/",
        ],
    },
]


# ============================================================
# CABECERAS
# ============================================================

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/151.0.0.0 Safari/537.36"
    ),

    "Accept": (
        "text/html,application/xhtml+xml,"
        "application/xml;q=0.9,image/avif,"
        "image/webp,*/*;q=0.8"
    ),

    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",

    "Cache-Control": "no-cache",

    "Pragma": "no-cache",
}


# ============================================================
# NORMALIZAR TEXTO
# ============================================================

def normalizar(texto):

    if not texto:
        return ""

    return " ".join(
        texto.lower().split()
    )


# ============================================================
# COMPROBAR SI UN TEXTO ES DE LA COLECCIÓN
# ============================================================

def pertenece_coleccion(texto):

    texto = normalizar(texto)

    for palabra in PALABRAS_COLECCION:

        if palabra in texto:
            return True

    return False


# ============================================================
# EXTRAER NOMBRE DE PRODUCTO
# ============================================================

def obtener_nombre_producto(elemento):

    # Primero intentamos el texto visible
    texto = elemento.get_text(
        " ",
        strip=True
    )

    texto = " ".join(
        texto.split()
    )

    if texto:
        return texto


    # Si no hay texto, probamos atributos
    atributos = [
        "title",
        "aria-label",
        "data-title",
        "data-product-title",
    ]

    for atributo in atributos:

        valor = elemento.get(
            atributo
        )

        if valor:

            return " ".join(
                str(valor).split()
            )

    return ""


# ============================================================
# EXTRAER PRODUCTOS DE UNA PÁGINA
# ============================================================

def extraer_productos(soup, url):

    productos = {}

    # --------------------------------------------------------
    # 1. ENLACES
    # --------------------------------------------------------

    enlaces = soup.find_all(
        "a",
        href=True
    )

    for enlace in enlaces:

        nombre = obtener_nombre_producto(
            enlace
        )

        href = enlace.get(
            "href"
        )

        if not href:
            continue

        url_producto = urljoin(
            url,
            href
        )

        texto_completo = (
            nombre
            + " "
            + href
        )

        if pertenece_coleccion(
            texto_completo
        ):

            if len(nombre) > 2:

                productos[
                    url_producto
                ] = nombre


    # --------------------------------------------------------
    # 2. TÍTULOS
    # --------------------------------------------------------

    for etiqueta in soup.find_all(
        [
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
        ]
    ):

        nombre = obtener_nombre_producto(
            etiqueta
        )

        if pertenece_coleccion(
            nombre
        ):

            if len(nombre) > 2:

                productos[
                    "titulo:" + nombre
                ] = nombre


    # --------------------------------------------------------
    # 3. ATRIBUTOS DE PRODUCTO
    # --------------------------------------------------------

    for etiqueta in soup.find_all(
        True
    ):

        for atributo in [
            "title",
            "aria-label",
            "data-title",
            "data-product-title",
        ]:

            valor = etiqueta.get(
                atributo
            )

            if not valor:
                continue

            valor = " ".join(
                str(valor).split()
            )

            if pertenece_coleccion(
                valor
            ):

                if len(valor) > 2:

                    productos[
                        "atributo:" + valor
                    ] = valor


    # --------------------------------------------------------
    # ELIMINAR RESULTADOS ENORMES
    # --------------------------------------------------------

    resultado = []

    for nombre in productos.values():

        if len(nombre) > 200:
            continue

        if nombre not in resultado:

            resultado.append(
                nombre
            )


    return resultado


# ============================================================
# COMPROBAR UNA URL
# ============================================================

def descargar_pagina(url):

    try:

        respuesta = requests.get(
            url,
            headers=HEADERS,
            timeout=20,
            allow_redirects=True
        )

        if 200 <= respuesta.status_code < 400:

            return respuesta.text, None

        return (
            None,
            "HTTP "
            + str(respuesta.status_code)
        )

    except requests.exceptions.Timeout:

        return None, "TIMEOUT"

    except requests.exceptions.ConnectionError:

        return None, "CONEXIÓN"

    except Exception as error:

        return None, str(error)


# ============================================================
# COMPROBAR TIENDA
# ============================================================

def comprobar_tienda(tienda):

    todos_los_productos = []
    errores = []

    paginas_ok = 0

    for url in tienda["urls"]:

        html, error = descargar_pagina(
            url
        )

        if html is None:

            errores.append(
                url
                + " -> "
                + str(error)
            )

            continue

        paginas_ok += 1

        soup = BeautifulSoup(
            html,
            "html.parser"
        )

        productos = extraer_productos(
            soup,
            url
        )

        for producto in productos:

            if producto not in todos_los_productos:

                todos_los_productos.append(
                    producto
                )


    # --------------------------------------------------------
    # HAY PRODUCTOS PUBLICADOS
    # --------------------------------------------------------

    if todos_los_productos:

        return (
            "PUBLICADO",
            todos_los_productos,
            ""
        )


    # --------------------------------------------------------
    # PÁGINA ACCESIBLE PERO SIN PRODUCTO
    # --------------------------------------------------------

    if paginas_ok > 0:

        return (
            "NO ENCONTRADO",
            [],
            ""
        )


    # --------------------------------------------------------
    # NO PODEMOS ACCEDER
    # --------------------------------------------------------

    if errores:

        return (
            "ERROR",
            [],
            errores[0]
        )


    return (
        "NO ENCONTRADO",
        [],
        ""
    )


# ============================================================
# ACTUALIZAR PANTALLA
# ============================================================

def actualizar_tienda(
    nombre,
    estado,
    productos,
    error
):

    for fila in filas:

        if fila["nombre"] != nombre:
            continue


        # Estado
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

        elif estado == "ERROR":

            fila["estado"].config(
                fg="orange"
            )


        # Productos
        if productos:

            texto = ""

            for producto in productos[:12]:

                texto += (
                    "• "
                    + producto
                    + "\n"
                )

            fila["producto"].config(
                text=texto
            )

        elif error:

            fila["producto"].config(
                text="Error: " + error
            )

        else:

            fila["producto"].config(
                text=""
            )


# ============================================================
# DETECTAR PRODUCTOS NUEVOS
# ============================================================

def detectar_nuevos(
    nombre,
    productos
):

    anteriores = productos_anteriores.get(
        nombre,
        []
    )

    nuevos = []

    for producto in productos:

        if producto not in anteriores:

            nuevos.append(
                producto
            )

    productos_anteriores[
        nombre
    ] = productos

    return nuevos


# ============================================================
# AVISO DE NUEVO PRODUCTO
# ============================================================

def avisar_nuevos(
    nombre,
    nuevos
):

    if not nuevos:
        return


    mensaje = (
        "Tienda:\n"
        + nombre
        + "\n\n"
        "NUEVO PRODUCTO PUBLICADO:\n\n"
    )


    for producto in nuevos[:10]:

        mensaje += (
            "• "
            + producto
            + "\n"
        )


    ventana.bell()


    messagebox.showinfo(
        "NUEVO PRODUCTO 30th ANNIVERSARY",
        mensaje
    )


# ============================================================
# MONITOR
# ============================================================

def monitor():

    global ejecutando
    global contador_comprobaciones


    while ejecutando:

        hora = datetime.now().strftime(
            "%H:%M:%S"
        )


        ventana.after(
            0,
            lambda h=hora:
            ultima_comprobacion.config(
                text=(
                    "Última comprobación: "
                    + h
                )
            )
        )


        # ----------------------------------------------------
        # COMPROBAR TIENDAS
        # ----------------------------------------------------

        for tienda in TIENDAS:

            if not ejecutando:
                break


            nombre = tienda[
                "nombre"
            ]


            estado, productos, error = (
                comprobar_tienda(
                    tienda
                )
            )


            # Detectar nuevos
            nuevos = detectar_nuevos(
                nombre,
                productos
            )


            # Actualizar interfaz
            ventana.after(
                0,
                lambda n=nombre,
                e=estado,
                p=productos,
                er=error:
                actualizar_tienda(
                    n,
                    e,
                    p,
                    er
                )
            )


            # Avisar nuevos productos
            if nuevos:

                ventana.after(
                    0,
                    lambda n=nombre,
                    x=nuevos:
                    avisar_nuevos(
                        n,
                        x
                    )
                )


        # ----------------------------------------------------
        # CONTADOR
        # ----------------------------------------------------

        if ejecutando:

            contador_comprobaciones += 1

            ventana.after(
                0,
                lambda c=contador_comprobaciones:
                contador_label.config(
                    text=(
                        "Comprobaciones realizadas: "
                        + str(c)
                    )
                )
            )


        # ----------------------------------------------------
        # CUENTA ATRÁS
        # ----------------------------------------------------

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
                proxima_comprobacion.config(
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
    global hilo_monitor


    if ejecutando:
        return


    ejecutando = True


    estado_programa.config(
        text="MONITOR ACTIVO",
        fg="green"
    )


    hilo_monitor = threading.Thread(
        target=monitor,
        daemon=True
    )


    hilo_monitor.start()


# ============================================================
# DETENER
# ============================================================

def detener():

    global ejecutando

    ejecutando = False


    estado_programa.config(
        text="MONITOR DETENIDO",
        fg="red"
    )


    proxima_comprobacion.config(
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
    "POKEMONSTOCK - 30th Anniversary"
)

ventana.geometry(
    "1100x800"
)

ventana.resizable(
    False,
    False
)


# ============================================================
# TÍTULO
# ============================================================

titulo = tk.Label(
    ventana,
    text="POKEMONSTOCK",
    font=(
        "Arial",
        30,
        "bold"
    )
)

titulo.pack(
    pady=(25, 5)
)


subtitulo = tk.Label(
    ventana,
    text="Pokémon TCG - 30th Anniversary",
    font=(
        "Arial",
        15
    )
)

subtitulo.pack(
    pady=5
)


descripcion = tk.Label(
    ventana,
    text=(
        "Vigilancia de productos publicados "
        "de la colección 30th Anniversary"
    ),
    font=(
        "Arial",
        12,
        "bold"
    )
)

descripcion.pack(
    pady=(0, 25)
)


# ============================================================
# TABLA
# ============================================================

marco = tk.Frame(
    ventana
)

marco.pack(
    fill="x",
    padx=30
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
    padx=35,
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
    padx=20,
    sticky="nw"
)


# ============================================================
# FILAS
# ============================================================

filas = []


for numero, tienda in enumerate(
    TIENDAS,
    start=1
):

    nombre = tk.Label(
        marco,
        text=tienda["nombre"],
        font=(
            "Arial",
            11
        )
    )

    nombre.grid(
        row=numero,
        column=0,
        sticky="nw",
        pady=15
    )


    estado = tk.Label(
        marco,
        text="SIN COMPROBAR",
        font=(
            "Arial",
            11,
            "bold"
        ),
        fg="gray"
    )

    estado.grid(
        row=numero,
        column=1,
        padx=35,
        sticky="nw",
        pady=15
    )


    producto = tk.Label(
        marco,
        text="",
        font=(
            "Arial",
            9
        ),
        wraplength=650,
        justify="left",
        anchor="w"
    )

    producto.grid(
        row=numero,
        column=2,
        padx=20,
        sticky="nw",
        pady=10
    )


    filas.append(
        {
            "nombre": tienda["nombre"],
            "estado": estado,
            "producto": producto
        }
    )


# ============================================================
# SEPARADOR
# ============================================================

separador = tk.Frame(
    ventana,
    height=2,
    bg="gray"
)

separador.pack(
    fill="x",
    padx=30,
    pady=20
)


# ============================================================
# ESTADO
# ============================================================

estado_programa = tk.Label(
    ventana,
    text="MONITOR DETENIDO",
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


# ============================================================
# ÚLTIMA COMPROBACIÓN
# ============================================================

ultima_comprobacion = tk.Label(
    ventana,
    text="Última comprobación: --:--:--",
    font=("Arial", 10)
)

ultima_comprobacion.pack(
    pady=3
)


# ============================================================
# PRÓXIMA COMPROBACIÓN
# ============================================================

proxima_comprobacion = tk.Label(
    ventana,
    text="Próxima comprobación: detenida",
    font=("Arial", 10)
)

proxima_comprobacion.pack(
    pady=3
)


# ============================================================
# CONTADOR
# ============================================================

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

marco_botones = tk.Frame(
    ventana
)

marco_botones.pack(
    pady=25
)


boton_iniciar = tk.Button(
    marco_botones,
    text="INICIAR",
    font=(
        "Arial",
        12,
        "bold"
    ),
    width=16,
    command=iniciar
)

boton_iniciar.grid(
    row=0,
    column=0,
    padx=10
)


boton_detener = tk.Button(
    marco_botones,
    text="DETENER",
    font=(
        "Arial",
        12,
        "bold"
    ),
    width=16,
    command=detener
)

boton_detener.grid(
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
# EJECUTAR
# ============================================================

ventana.mainloop()
