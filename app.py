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

PRODUCTO = [
    "30th celebration elite trainer box",
    "30th celebration etb",
    "30th anniversary elite trainer box",
    "30th anniversary etb",
    "etb celebraciones 30 aniversario",
    "elite trainer box 30th",
]

ejecutando = False
hilo_monitor = None

contador_comprobaciones = 0

estados_anteriores = {}


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
    "Accept": (
        "text/html,application/xhtml+xml,"
        "application/xml;q=0.9,image/avif,"
        "image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
}


# =========================================================
# COMPROBAR SI EL PRODUCTO APARECE
# =========================================================

def producto_aparece(texto):

    texto = texto.lower()

    for palabra in PRODUCTO:

        if palabra in texto:
            return True

    if (
        "30th anniversary" in texto
        and "elite trainer box" in texto
    ):
        return True

    if (
        "30th celebration" in texto
        and "elite trainer box" in texto
    ):
        return True

    if (
        "30 aniversario" in texto
        and "elite trainer box" in texto
    ):
        return True

    return False


# =========================================================
# COMPROBAR AGOTADO
# =========================================================

def esta_agotado(texto):

    texto = texto.lower()

    palabras = [
        "agotado",
        "agotada",
        "sold out",
        "out of stock",
        "sin stock",
        "sin existencias",
        "no disponible",
    ]

    for palabra in palabras:

        if palabra in texto:
            return True

    return False


# =========================================================
# COMPROBAR DISPONIBLE
# =========================================================

def esta_disponible(texto):

    texto = texto.lower()

    palabras = [
        "en stock",
        "in stock",
        "disponible",
        "hay existencias",
        "en existencia",
    ]

    for palabra in palabras:

        if palabra in texto:
            return True

    return False


# =========================================================
# COMPROBAR UNA TIENDA
# =========================================================

def comprobar_tienda(tienda):

    try:

        respuesta = requests.get(
            tienda["url"],
            headers=HEADERS,
            timeout=20
        )

        if respuesta.status_code != 200:
            return "ERROR"

        soup = BeautifulSoup(
            respuesta.text,
            "html.parser"
        )

        texto = soup.get_text(
            " ",
            strip=True
        ).lower()

        # Producto no encontrado
        if not producto_aparece(texto):
            return "NO ENCONTRADO"

        # Producto publicado pero agotado
        if esta_agotado(texto):
            return "AGOTADO"

        # Producto publicado y disponible
        if esta_disponible(texto):
            return "EN STOCK"

        # Producto publicado pero no podemos
        # determinar claramente el stock
        return "PUBLICADO"

    except requests.exceptions.Timeout:

        return "ERROR"

    except requests.exceptions.ConnectionError:

        return "ERROR"

    except Exception:

        return "ERROR"


# =========================================================
# ACTUALIZAR ESTADO EN PANTALLA
# =========================================================

def actualizar_estado(nombre, estado):

    for fila in filas:

        if fila["nombre"] == nombre:

            fila["estado"].config(
                text=estado
            )

            if estado == "EN STOCK":

                fila["estado"].config(
                    fg="green"
                )

            elif estado == "AGOTADO":

                fila["estado"].config(
                    fg="red"
                )

            elif estado == "PUBLICADO":

                fila["estado"].config(
                    fg="blue"
                )

            elif estado == "NO ENCONTRADO":

                fila["estado"].config(
                    fg="gray"
                )

            elif estado == "ERROR":

                fila["estado"].config(
                    fg="orange"
                )


# =========================================================
# AVISO DE CAMBIO
# =========================================================

def avisar_cambio(
    nombre,
    estado_anterior,
    estado_nuevo
):

    if estado_anterior is None:
        return

    if estado_anterior == estado_nuevo:
        return

    mensaje = (
        f"{nombre}\n\n"
        f"Estado anterior:\n"
        f"{estado_anterior}\n\n"
        f"Nuevo estado:\n"
        f"{estado_nuevo}"
    )

    ventana.bell()

    messagebox.showwarning(
        "CAMBIO DETECTADO",
        mensaje
    )


# =========================================================
# MONITOR PRINCIPAL
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
                text=f"Última comprobación: {h}"
            )
        )

        # =================================================
        # COMPROBAR LAS 5 TIENDAS
        # =================================================

        for tienda in TIENDAS:

            if not ejecutando:
                break

            nombre = tienda["nombre"]

            estado = comprobar_tienda(
                tienda
            )

            estado_anterior = (
                estados_anteriores.get(nombre)
            )

            estados_anteriores[nombre] = estado

            # Actualizar pantalla
            ventana.after(
                0,
                lambda n=nombre,
                e=estado:
                actualizar_estado(
                    n,
                    e
                )
            )

            # Avisar si cambia
            ventana.after(
                0,
                lambda n=nombre,
                a=estado_anterior,
                e=estado:
                avisar_cambio(
                    n,
                    a,
                    e
                )
            )

        # =================================================
        # SUMAR UNA COMPROBACIÓN COMPLETA
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
        # CUENTA ATRÁS DE 3 SEGUNDOS
        # =================================================

        for segundos in range(
            INTERVALO,
            0,
            -1
        ):

            if not ejecutando:
                break

            texto = (
                f"Próxima comprobación: "
                f"{segundos} segundos"
            )

            ventana.after(
                0,
                lambda t=texto:
                proxima_comprobacion.config(
                    text=t
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
# INTERFAZ
# =========================================================

ventana = tk.Tk()

ventana.title(
    "POKEMONSTOCK"
)

ventana.geometry(
    "750x700"
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
    pady=(0, 10)
)


producto_label = tk.Label(
    ventana,
    text="Elite Trainer Box",
    font=("Arial", 12, "bold")
)

producto_label.pack(
    pady=(0, 25)
)


# =========================================================
# TABLA
# =========================================================

marco = tk.Frame(
    ventana
)

marco.pack(
    fill="x",
    padx=50
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
    padx=150,
    sticky="w"
)


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
        pady=12
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
        padx=150,
        sticky="w"
    )

    filas.append(
        {
            "nombre": tienda["nombre"],
            "estado": estado
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
    padx=50,
    pady=20
)


# =========================================================
# ESTADO DEL MONITOR
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
# ÚLTIMA COMPROBACIÓN
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
# PRÓXIMA COMPROBACIÓN
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
# CERRAR VENTANA
# =========================================================

ventana.protocol(
    "WM_DELETE_WINDOW",
    cerrar
)


# =========================================================
# INICIAR VENTANA
# =========================================================

ventana.mainloop()
