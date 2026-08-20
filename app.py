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

INTERVALO = 60  # 60 segundos = 1 minuto

ejecutando = False
hilo_monitor = None

contador_comprobaciones = 0

# Guarda los productos encontrados anteriormente
productos_anteriores = {}


# ============================================================
# PALABRAS DE LA COLECCIÓN
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
    "30th anniversary collection",
    "30 aniversario colección",
]


# ============================================================
# TIENDAS
# ============================================================

TIENDAS = [
    {
        "nombre": "POKEMILLON",
        "urls": [
            "https://www.pokemillon.com/collections/eternos-30-aniversario-eternals-30th-anniversary",
            "https://www.pokemillon.com/products/etb-30th",
        ],
    },

    {
        "nombre": "TODOHITS",
        "urls": [
            "https://todohits.com/collections/30th-anniversary",
            "https://todohits.com/",
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
# CABECERAS DEL NAVEGADOR
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

    "Accept-Language": (
        "es-ES,es;q=0.9,en;q=0.8"
    ),

    "Connection": "keep-alive",
}


# ============================================================
# COMPROBAR SI UN TEXTO PERTENECE A LA COLECCIÓN
# ============================================================

def contiene_coleccion(texto):

    texto = texto.lower()

    for palabra in PALABRAS_COLECCION:

        if palabra in texto:
            return True

    return False


# ============================================================
# LIMPIAR TEXTO
# ============================================================

def limpiar_texto(texto):

    texto = " ".join(
        texto.split()
    )

    return texto.strip()


# ============================================================
# BUSCAR PRODUCTOS EN UNA PÁGINA
# ============================================================

def extraer_productos(soup):

    productos = []

    # --------------------------------------------------------
    # 1. Títulos principales
    # --------------------------------------------------------

    etiquetas = soup.find_all(
        [
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
        ]
    )

    for etiqueta in etiquetas:

        texto = limpiar_texto(
            etiqueta.get_text(
                " ",
                strip=True
            )
        )

        if not texto:
            continue

        if contiene_coleccion(texto):

            if texto not in productos:

                productos.append(texto)


    # --------------------------------------------------------
    # 2. Enlaces de productos
    # --------------------------------------------------------

    enlaces = soup.find_all(
        "a",
        href=True
    )

    for enlace in enlaces:

        texto = limpiar_texto(
            enlace.get_text(
                " ",
                strip=True
            )
        )

        if not texto:
            continue

        if contiene_coleccion(texto):

            if texto not in productos:

                productos.append(texto)


    # --------------------------------------------------------
    # 3. Elementos con atributos de producto
    # --------------------------------------------------------

    for etiqueta in soup.find_all(
        True
    ):

        for atributo in [
            "data-title",
            "data-product-title",
            "aria-label",
            "title",
        ]:

            valor = etiqueta.get(
                atributo
            )

            if not valor:
                continue

            valor = limpiar_texto(
                str(valor)
            )

            if contiene_coleccion(
                valor
            ):

                if valor not in productos:

                    productos.append(valor)


    # --------------------------------------------------------
    # Eliminar resultados absurdamente largos
    # --------------------------------------------------------

    productos_limpios = []

    for producto in productos:

        if len(producto) > 250:

            continue

        if producto not in productos_limpios:

            productos_limpios.append(
                producto
            )


    return productos_limpios[:30]


# ============================================================
# COMPROBAR UNA URL
# ============================================================

def comprobar_url(url):

    try:

        respuesta = requests.get(
            url,
            headers=HEADERS,
            timeout=20,
            allow_redirects=True
        )

        if not (
            200
            <= respuesta.status_code
            < 400
        ):

            return None, "HTTP " + str(
                respuesta.status_code
            )


        soup = BeautifulSoup(
            respuesta.text,
            "html.parser"
        )


        return soup, None


    except requests.exceptions.Timeout:

        return None, "TIMEOUT"


    except requests.exceptions.ConnectionError:

        return None, "CONEXIÓN"


    except Exception as error:

        return None, str(error)


# ============================================================
# COMPROBAR UNA TIENDA COMPLETA
# ============================================================

def comprobar_tienda(tienda):

    productos_encontrados = []

    ultimo_error = None

    paginas_comprobadas = 0


    for url in tienda["urls"]:

        soup, error = comprobar_url(
            url
        )


        if soup is None:

            ultimo_error = error

            continue


        paginas_comprobadas += 1


        # ----------------------------------------------------
        # Buscar productos
        # ----------------------------------------------------

        productos = extraer_productos(
            soup
        )


        for producto in productos:

            if producto not in productos_encontrados:

                productos_encontrados.append(
                    producto
                )


        # ----------------------------------------------------
        # Si la página contiene la colección,
        # intentar localizar enlaces relacionados
        # ----------------------------------------------------

        enlaces = soup.find_all(
            "a",
            href=True
        )


        for enlace in enlaces:

            texto = limpiar_texto(
                enlace.get_text(
                    " ",
                    strip=True
                )
            )


            href = enlace.get(
                "href"
            )


            if not href:

                continue


            if (
                contiene_coleccion(texto)
                or contiene_coleccion(href)
            ):

                nombre = texto


                if (
                    nombre
                    and nombre not in productos_encontrados
                ):

                    productos_encontrados.append(
                        nombre
                    )


    # --------------------------------------------------------
    # Resultado
    # --------------------------------------------------------

    if productos_encontrados:

        return (
            "ENCONTRADO",
            productos_encontrados,
            None
        )


    if paginas_comprobadas > 0:

        return (
            "NO ENCONTRADO",
            [],
            None
        )


    return (
        "ERROR",
        [],
        ultimo_error
    )


# ============================================================
# ACTUALIZAR UNA FILA
# ============================================================

def actualizar_estado(
    nombre,
    estado,
    productos,
    error
):

    for fila in filas:

        if fila["nombre"] != nombre:

            continue


        # ----------------------------------------------------
        # Estado
        # ----------------------------------------------------

        fila["estado"].config(
            text=estado
        )


        if estado == "ENCONTRADO":

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


        # ----------------------------------------------------
        # Productos
        # ----------------------------------------------------

        if productos:

            texto_productos = "\n".join(
                "• " + producto
                for producto in productos[:8]
            )

        elif error:

            texto_productos = (
                "Error: " + str(error)
            )

        else:

            texto_productos = ""


        fila["producto"].config(
            text=texto_productos
        )


# ============================================================
# DETECTAR PRODUCTOS NUEVOS
# ============================================================

def detectar_nuevos(
    nombre,
    productos_actuales
):

    anteriores = productos_anteriores.get(
        nombre,
        []
    )


    nuevos = [
        producto
        for producto in productos_actuales
        if producto not in anteriores
    ]


    productos_anteriores[
        nombre
    ] = productos_actuales


    return nuevos


# ============================================================
# AVISAR DE PRODUCTOS NUEVOS
# ============================================================

def avisar_nuevos(
    nombre,
    nuevos
):

    if not nuevos:

        return


    texto = (
        f"Tienda: {nombre}\n\n"
        "Nuevos productos detectados:\n\n"
    )


    for producto in nuevos[:10]:

        texto += (
            "• "
            + producto
            + "\n"
        )


    ventana.bell()


    messagebox.showinfo(
        "NUEVO PRODUCTO 30th ANNIVERSARY",
        texto
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


        # ====================================================
        # COMPROBAR TODAS LAS TIENDAS
        # ====================================================

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


            nuevos = detectar_nuevos(
                nombre,
                productos
            )


            # ------------------------------------------------
            # Actualizar pantalla
            # ------------------------------------------------

            ventana.after(
                0,
                lambda n=nombre,
                e=estado,
                p=productos,
                er=error:
                actualizar_estado(
                    n,
                    e,
                    p,
                    er
                )
            )


            # ------------------------------------------------
            # Avisar nuevos
            # ------------------------------------------------

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


        # ====================================================
        # CONTADOR
        # ====================================================

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
    "1050x780"
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
    text=(
        "Pokémon TCG - "
        "30th Anniversary"
    ),
    font=(
        "Arial",
        15
    )
)

subtitulo.pack(
    pady=(0, 5)
)


descripcion = tk.Label(
    ventana,
    text=(
        "Busca cualquier producto "
        "relacionado con la colección"
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
# CABECERA
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
    sticky="w"
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
    padx=30,
    sticky="w"
)


tk.Label(
    marco,
    text="PRODUCTOS 30th ANNIVERSARY DETECTADOS",
    font=(
        "Arial",
        11,
        "bold"
    )
).grid(
    row=0,
    column=2,
    padx=20,
    sticky="w"
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
        padx=30,
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
        wraplength=550,
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
# ESTADO DEL PROGRAMA
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
    text=(
        "Última comprobación: "
        "--:--:--"
    ),
    font=(
        "Arial",
        10
    )
)


ultima_comprobacion.pack(
    pady=3
)


# ============================================================
# PRÓXIMA COMPROBACIÓN
# ============================================================

proxima_comprobacion = tk.Label(
    ventana,
    text=(
        "Próxima comprobación: "
        "detenida"
    ),
    font=(
        "Arial",
        10
    )
)


proxima_comprobacion.pack(
    pady=3
)


# ============================================================
# CONTADOR
# ============================================================

contador_label = tk.Label(
    ventana,
    text=(
        "Comprobaciones realizadas: 0"
    ),
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
# CERRAR VENTANA
# ============================================================

ventana.protocol(
    "WM_DELETE_WINDOW",
    cerrar
)


# ============================================================
# EJECUTAR
# ============================================================

ventana.mainloop()
