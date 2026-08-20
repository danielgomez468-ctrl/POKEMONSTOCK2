import tkinter as tk
from tkinter import messagebox
import threading
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime

INTERVALO = 120

ejecutando = False
hilo_monitor = None

# ==========================================
# PRODUCTO QUE QUEREMOS VIGILAR
# ==========================================

PRODUCTO = "Pokémon TCG 30th Anniversary Elite Trainer Box"


# ==========================================
# TIENDAS
# ==========================================

TIENDAS = [
    {
        "nombre": "Pokemillon",
        "url": "https://www.pokemillon.com/",
    },
    {
        "nombre": "TodoHits",
        "url": "https://todohits.com/",
    },
]


# ==========================================
# COMPROBAR INTERNET / WEB
# ==========================================

def comprobar_tienda(tienda):

    try:

        respuesta = requests.get(
            tienda["url"],
            timeout=20,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 "
                    "(KHTML, like Gecko) "
                    "Chrome/151.0 Safari/537.36"
                )
            },
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

        if (
            "30th anniversary" in texto
            or "30th celebration" in texto
        ):

            return "PRODUCTO ENCONTRADO"

        return "NO ENCONTRADO"

    except Exception:

        return "ERROR"


# ==========================================
# ACTUALIZAR PANTALLA
# ==========================================

def actualizar_tienda(nombre, estado):

    for fila in filas:

        if fila["nombre"] == nombre:

            fila["estado"].config(
                text=estado
            )

            if estado == "PRODUCTO ENCONTRADO":

                fila["estado"].config(
                    fg="green"
                )

            elif estado == "ERROR":

                fila["estado"].config(
                    fg="orange"
                )

            else:

                fila["estado"].config(
                    fg="red"
                )


# ==========================================
# COMPROBAR TODAS LAS TIENDAS
# ==========================================

def monitor():

    global ejecutando

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

        for tienda in TIENDAS:

            if not ejecutando:
                break

            estado = comprobar_tienda(
                tienda
            )

            ventana.after(
                0,
                lambda n=tienda["nombre"],
                e=estado:
                actualizar_tienda(
                    n,
                    e
                )
            )

        # ==================================
        # CUENTA ATRÁS DE 2 MINUTOS
        # ==================================

        for segundos in range(
            INTERVALO,
            0,
            -1
        ):

            if not ejecutando:
                break

            minutos = segundos // 60
            seg = segundos % 60

            texto = (
                f"Próxima comprobación: "
                f"{minutos:02d}:{seg:02d}"
            )

            ventana.after(
                0,
                lambda t=texto:
                proxima_comprobacion.config(
                    text=t
                )
            )

            time.sleep(1)


# ==========================================
# INICIAR
# ==========================================

def iniciar():

    global ejecutando
    global hilo_monitor

    if ejecutando:
        return

    ejecutando = True

    estado_programa.config(
        text="🟢 MONITOR ACTIVO",
        fg="green"
    )

    hilo_monitor = threading.Thread(
        target=monitor,
        daemon=True
    )

    hilo_monitor.start()


# ==========================================
# DETENER
# ==========================================

def detener():

    global ejecutando

    ejecutando = False

    estado_programa.config(
        text="🔴 MONITOR DETENIDO",
        fg="red"
    )

    proxima_comprobacion.config(
        text="Próxima comprobación: detenida"
    )


# ==========================================
# CERRAR
# ==========================================

def cerrar():

    global ejecutando

    ejecutando = False

    ventana.destroy()


# ==========================================
# INTERFAZ
# ==========================================

ventana = tk.Tk()

ventana.title(
    "POKEMONSTOCK"
)

ventana.geometry(
    "700x520"
)

ventana.resizable(
    False,
    False
)


titulo = tk.Label(
    ventana,
    text="POKEMONSTOCK",
    font=("Arial", 28, "bold")
)

titulo.pack(
    pady=(25, 5)
)


subtitulo = tk.Label(
    ventana,
    text="Monitor Pokémon TCG - 30 Aniversario",
    font=("Arial", 13)
)

subtitulo.pack(
    pady=(0, 25)
)


marco = tk.Frame(
    ventana
)

marco.pack(
    fill="x",
    padx=40
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
    padx=100,
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
        pady=10
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
        padx=100,
        sticky="w"
    )


    filas.append(
        {
            "nombre": tienda["nombre"],
            "estado": estado
        }
    )


separador = tk.Frame(
    ventana,
    height=2,
    bg="gray"
)

separador.pack(
    fill="x",
    padx=40,
    pady=20
)


estado_programa = tk.Label(
    ventana,
    text="🔴 MONITOR DETENIDO",
    font=("Arial", 14, "bold"),
    fg="red"
)

estado_programa.pack(
    pady=5
)


ultima_comprobacion = tk.Label(
    ventana,
    text="Última comprobación: --:--:--",
    font=("Arial", 10)
)

ultima_comprobacion.pack(
    pady=3
)


proxima_comprobacion = tk.Label(
    ventana,
    text="Próxima comprobación: detenida",
    font=("Arial", 10)
)

proxima_comprobacion.pack(
    pady=3
)


marco_botones = tk.Frame(
    ventana
)

marco_botones.pack(
    pady=25
)


tk.Button(
    marco_botones,
    text="▶ INICIAR",
    font=("Arial", 12, "bold"),
    width=16,
    command=iniciar
).grid(
    row=0,
    column=0,
    padx=10
)


tk.Button(
    marco_botones,
    text="■ DETENER",
    font=("Arial", 12, "bold"),
    width=16,
    command=detener
).grid(
    row=0,
    column=1,
    padx=10
)


ventana.protocol(
    "WM_DELETE_WINDOW",
    cerrar
)


ventana.mainloop()
