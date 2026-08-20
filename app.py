import tkinter as tk
from tkinter import messagebox
import threading
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime


# =========================================================
# CONFIGURACIÓN
# =========================================================

INTERVALO = 3

ejecutando = False
hilo_monitor = None

contador_comprobaciones = 0

estados_anteriores = {}


# =========================================================
# PALABRAS QUE IDENTIFICAN EL 30 ANIVERSARIO
# =========================================================

PALABRAS_30 = [
    "30th anniversary",
    "30th anniversary pokemon",
    "pokemon 30th",
    "pokemon 30 aniversario",
    "30 aniversario pokemon",
    "30th celebration",
    "30th celebration pokemon",
    "celebration 30th",
    "30 aniversario",
]


# =========================================================
# TIENDAS
# =========================================================

TIENDAS = [
    {
        "nombre": "POKEMILLON",
        "url": "https://www.pokemillon.com/products/etb-30th",
    },
    {
        "nombre": "TODOHITS",
        "url": "https://todohits.com/",
    },
    {
        "nombre": "POKEBANK",
        "url": "https://pokebank.es/",
    },
    {
        "nombre": "SUNNY STORE",
        "url": "https://sunnystore.es/",
    },
    {
        "nombre": "UN SOBRE MÁS",
        "url": "https://unsobremas.com/",
    },
]


# =========================================================
# CABECERAS
# =========================================================

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/151.0 Safari/537.36"
    ),
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
}


# =========================================================
# COMPROBAR SI UNA PÁGINA ES DEL 30 ANIVERSARIO
# =========================================================

def es_30_aniversario(texto):

    texto = texto.lower()

    for palabra in PALABRAS_30:

        if palabra in texto:
            return True

    return False


# =========================================================
# EXTRAER PRODUCTOS RELACIONADOS
# =========================================================

def buscar_productos_30(soup):

    productos = []

    # -----------------------------------------------------
    # Buscar títulos habituales de productos
    # -----------------------------------------------------

    etiquetas = soup.find_all(
        [
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "a",
        ]
    )

    for etiqueta in etiquetas:

        texto = etiqueta.get_text(
            " ",
            strip=True
        )

        if not texto:
            continue

        texto_lower = texto.lower()

        # Comprobamos que tenga referencia al 30 aniversario

        relacionado = False

        for palabra in PALABRAS_30:

            if palabra in texto_lower:

                relacionado = True
                break

        if relacionado:

            # Evitar duplicados

            if texto not in productos:

                productos.append(texto)

    return productos[:10]


# =========================================================
# COMPROBAR TIENDA
# =========================================================

def comprobar_tienda(tienda):

    try:

        respuesta = requests.get(
            tienda["url"],
            headers=HEADERS,
            timeout=15,
            allow_redirects=True
        )

        # -------------------------------------------------
        # Cualquier respuesta HTTP correcta
        # -------------------------------------------------

        if respuesta.status_code < 200 or respuesta.status_code >= 400:

            return "ERROR", []


        # -------------------------------------------------
        # Analizar HTML
        # -------------------------------------------------

        soup = BeautifulSoup(
            respuesta.text,
            "html.parser"
        )


        texto = soup.get_text(
            " ",
            strip=True
        )


        # -------------------------------------------------
        # ¿HAY REFERENCIAS AL 30 ANIVERSARIO?
        # -------------------------------------------------

        if not es_30_aniversario(texto):

            return "NO ENCONTRADO", []


        # -------------------------------------------------
        # BUSCAR NOMBRES DE PRODUCTOS
        # -------------------------------------------------

        productos = buscar_productos_30(
            soup
        )


        # -------------------------------------------------
        # ENCONTRADO
        # -------------------------------------------------

        return "ENCONTRADO", productos


    except requests.exceptions.Timeout:

        return "ERROR", []


    except requests.exceptions.ConnectionError:

        return "ERROR", []


    except Exception:

        return "ERROR", []


# =========================================================
# ACTUALIZAR TIENDA
# =========================================================

def actualizar_estado(
    nombre,
    estado,
    productos
):

    for fila in filas:

        if fila["nombre"] == nombre:

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


            # ------------------------------------------------
            # Mostrar productos
            # ------------------------------------------------

            descripcion = ""

            if productos:

                descripcion = (
                    " | ".join(productos[:3])
                )

            else:

                if estado == "ENCONTRADO":

                    descripcion = (
                        "Producto 30th Anniversary encontrado"
                    )


            fila["producto"].config(
                text=descripcion
            )


# =========================================================
# AVISAR CAMBIO
# =========================================================

def avisar_cambio(
    nombre,
    anterior,
    nuevo
):

    if anterior is None:

        return


    if anterior == nuevo:

        return


    if nuevo == "ENCONTRADO":

        ventana.bell()

        messagebox.showinfo(
            "PRODUCTO 30th ANIVERSARIO",
            (
                f"Se ha encontrado contenido "
                f"del 30 aniversario.\n\n"
                f"Tienda: {nombre}"
            )
        )


# =========================================================
# MONITOR
# =========================================================

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
                    f"Última comprobación: {h}"
                )
            )
        )


        # =================================================
        # COMPROBAR LAS 5 TIENDAS
        # =================================================

        for tienda in TIENDAS:

            if not ejecutando:

                break


            nombre = tienda["nombre"]


            estado, productos = comprobar_tienda(
                tienda
            )


            anterior = (
                estados_anteriores.get(
                    nombre
                )
            )


            estados_anteriores[
                nombre
            ] = estado


            # ------------------------------------------------
            # ACTUALIZAR INTERFAZ
            # ------------------------------------------------

            ventana.after(
                0,
                lambda n=nombre,
                e=estado,
                p=productos:
                actualizar_estado(
                    n,
                    e,
                    p
                )
            )


            # ------------------------------------------------
            # AVISAR SI APARECE
            # ------------------------------------------------

            ventana.after(
                0,
                lambda n=nombre,
                a=anterior,
                e=estado:
                avisar_cambio(
                    n,
                    a,
                    e
                )
            )


        # =================================================
        # CONTADOR
        # =================================================

        if ejecutando:

            contador_comprobaciones += 1


            ventana.after(
                0,
                lambda c=contador_comprobaciones:
                contador_label.config(
                    text=(
                        f"Comprobaciones realizadas: {c}"
                    )
                )
            )


        # =================================================
        # ESPERAR 3 SEGUNDOS
        # =================================================

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
                        f"Próxima comprobación: "
                        f"{s} segundos"
                    )
                )
            )


            time.sleep(1)


# =========================================================
# INICIAR
# =========================================================

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


# =========================================================
# DETENER
# =========================================================

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


# =========================================================
# CERRAR
# =========================================================

def cerrar():

    global ejecutando


    ejecutando = False


    ventana.destroy()


# =========================================================
# VENTANA
# =========================================================

ventana = tk.Tk()


ventana.title(
    "POKEMONSTOCK"
)


ventana.geometry(
    "900x750"
)


ventana.resizable(
    False,
    False
)


# =========================================================
# TÍTULO
# =========================================================

titulo = tk.Label(
    ventana,
    text="POKEMONSTOCK",
    font=("Arial", 30, "bold")
)

titulo.pack(
    pady=(25, 5)
)


subtitulo = tk.Label(
    ventana,
    text="Pokémon TCG - 30th Anniversary",
    font=("Arial", 14)
)

subtitulo.pack(
    pady=(0, 5)
)


producto_label = tk.Label(
    ventana,
    text=(
        "Buscando CUALQUIER PRODUCTO "
        "del 30 aniversario"
    ),
    font=("Arial", 12, "bold")
)

producto_label.pack(
    pady=(0, 25)
)


# =========================================================
# CABECERA TABLA
# =========================================================

marco = tk.Frame(
    ventana
)

marco.pack(
    fill="x",
    padx=35
)


tk.Label(
    marco,
    text="TIENDA",
    font=("Arial", 11, "bold")
).grid(
    row=0,
    column=0,
    sticky="w"
)


tk.Label(
    marco,
    text="ESTADO",
    font=("Arial", 11, "bold")
).grid(
    row=0,
    column=1,
    padx=40,
    sticky="w"
)


tk.Label(
    marco,
    text="PRODUCTO / DESCRIPCIÓN",
    font=("Arial", 11, "bold")
).grid(
    row=0,
    column=2,
    padx=20,
    sticky="w"
)


# =========================================================
# FILAS
# =========================================================

filas = []


for numero, tienda in enumerate(
    TIENDAS,
    start=1
):


    nombre = tk.Label(
        marco,
        text=tienda["nombre"],
        font=("Arial", 11)
    )


    nombre.grid(
        row=numero,
        column=0,
        sticky="w",
        pady=15
    )


    estado = tk.Label(
        marco,
        text="SIN COMPROBAR",
        font=("Arial", 11, "bold"),
        fg="gray"
    )


    estado.grid(
        row=numero,
        column=1,
        padx=40,
        sticky="w"
    )


    producto = tk.Label(
        marco,
        text="",
        font=("Arial", 9),
        wraplength=400,
        justify="left"
    )


    producto.grid(
        row=numero,
        column=2,
        padx=20,
        sticky="w"
    )


    filas.append(
        {
            "nombre": tienda["nombre"],
            "estado": estado,
            "producto": producto
        }
    )


# =========================================================
# SEPARADOR
# =========================================================

separador = tk.Frame(
    ventana,
    height=2,
    bg="gray"
)


separador.pack(
    fill="x",
    padx=35,
    pady=20
)


# =========================================================
# ESTADO
# =========================================================

estado_programa = tk.Label(
    ventana,
    text="MONITOR DETENIDO",
    font=("Arial", 14, "bold"),
    fg="red"
)


estado_programa.pack(
    pady=5
)


# =========================================================
# HORA
# =========================================================

ultima_comprobacion = tk.Label(
    ventana,
    text="Última comprobación: --:--:--",
    font=("Arial", 10)
)


ultima_comprobacion.pack(
    pady=3
)


# =========================================================
# PRÓXIMA
# =========================================================

proxima_comprobacion = tk.Label(
    ventana,
    text="Próxima comprobación: detenida",
    font=("Arial", 10)
)


proxima_comprobacion.pack(
    pady=3
)


# =========================================================
# CONTADOR
# =========================================================

contador_label = tk.Label(
    ventana,
    text="Comprobaciones realizadas: 0",
    font=("Arial", 11, "bold")
)


contador_label.pack(
    pady=5
)


# =========================================================
# BOTONES
# =========================================================

marco_botones = tk.Frame(
    ventana
)


marco_botones.pack(
    pady=25
)


boton_iniciar = tk.Button(
    marco_botones,
    text="INICIAR",
    font=("Arial", 12, "bold"),
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
    font=("Arial", 12, "bold"),
    width=16,
    command=detener
)


boton_detener.grid(
    row=0,
    column=1,
    padx=10
)


# =========================================================
# CERRAR
# =========================================================

ventana.protocol(
    "WM_DELETE_WINDOW",
    cerrar
)


# =========================================================
# EJECUTAR
# =========================================================

ventana.mainloop()
