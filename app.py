import tkinter as tk
from tkinter import messagebox
import threading
import time
import requests
from bs4 import BeautifulSoup

INTERVALO = 120  # 2 minutos

# Tiendas que vigilaremos
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

producto_buscado = "30th Celebration Elite Trainer Box"

ejecutando = False
hilo = None


def comprobar_tienda(tienda):
    """
    Comprueba si la página contiene referencias al producto.
    Más adelante sustituiremos estas URL por las fichas exactas
    de la ETB.
    """

    try:
        respuesta = requests.get(
            tienda["url"],
            timeout=20,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 Chrome/151.0 Safari/537.36"
                )
            },
        )

        if respuesta.status_code != 200:
            return "ERROR"

        texto = respuesta.text.lower()

        palabras = [
            "30th celebration",
            "30th anniversary",
            "elite trainer box",
        ]

        encontrado = any(palabra in texto for palabra in palabras)

        if encontrado:
            return "ENCONTRADO"

        return "NO ENCONTRADO"

    except Exception:
        return "ERROR"


def actualizar_estado(tienda, estado):
    for fila in filas:
        if fila["nombre"] == tienda["nombre"]:
            fila["estado"].config(text=estado)

            if estado == "DISPONIBLE":
                fila["estado"].config(fg="green")
            elif estado == "ERROR":
                fila["estado"].config(fg="orange")
            else:
                fila["estado"].config(fg="red")


def comprobar_todas():
    global ejecutando

    while ejecutando:

        hora = time.strftime("%H:%M:%S")

        ventana.after(
            0,
            lambda h=hora: ultima_comprobacion.config(
                text=f"Última comprobación: {h}"
            )
        )

        for tienda in TIENDAS:

            if not ejecutando:
                break

            estado = comprobar_tienda(tienda)

            ventana.after(
                0,
                lambda t=tienda, e=estado: actualizar_estado(t, e)
            )

        for segundos in range(INTERVALO):

            if not ejecutando:
                break

            restante = INTERVALO - segundos

            ventana.after(
                0,
                lambda r=restante: proxima_comprobacion.config(
                    text=f"Próxima comprobación: {r} segundos"
                )
            )

            time.sleep(1)


def iniciar():
    global ejecutando, hilo

    if ejecutando:
        return

    ejecutando = True

    estado_programa.config(
        text="🟢 MONITOR ACTIVO",
        fg="green"
    )

    hilo = threading.Thread(
        target=comprobar_todas,
        daemon=True
    )

    hilo.start()


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


def cerrar_programa():
    global ejecutando

    ejecutando = False
    ventana.destroy()


# -----------------------------
# INTERFAZ
# -----------------------------

ventana = tk.Tk()

ventana.title("POKEMONSTOCK")
ventana.geometry("650x500")
ventana.resizable(False, False)

titulo = tk.Label(
    ventana,
    text="POKEMONSTOCK",
    font=("Arial", 28, "bold")
)

titulo.pack(pady=(20, 5))

subtitulo = tk.Label(
    ventana,
    text="Monitor Pokémon TCG - 30 Aniversario",
    font=("Arial", 13)
)

subtitulo.pack(pady=(0, 20))


marco = tk.Frame(ventana)
marco.pack(fill="x", padx=30)


cabecera_nombre = tk.Label(
    marco,
    text="TIENDA",
    font=("Arial", 11, "bold")
)

cabecera_nombre.grid(row=0, column=0, sticky="w", pady=5)


cabecera_estado = tk.Label(
    marco,
    text="ESTADO",
    font=("Arial", 11, "bold")
)

cabecera_estado.grid(row=0, column=1, sticky="w", padx=100)


filas = []

for i, tienda in enumerate(TIENDAS, start=1):

    nombre = tk.Label(
        marco,
        text=tienda["nombre"],
        font=("Arial", 11)
    )

    nombre.grid(
        row=i,
        column=0,
        sticky="w",
        pady=8
    )

    estado = tk.Label(
        marco,
        text="SIN COMPROBAR",
        font=("Arial", 11, "bold"),
        fg="gray"
    )

    estado.grid(
        row=i,
        column=1,
        sticky="w",
        padx=100
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
    padx=30,
    pady=20
)


estado_programa = tk.Label(
    ventana,
    text="🔴 MONITOR DETENIDO",
    font=("Arial", 14, "bold"),
    fg="red"
)

estado_programa.pack(pady=5)


ultima_comprobacion = tk.Label(
    ventana,
    text="Última comprobación: --:--:--",
    font=("Arial", 10)
)

ultima_comprobacion.pack(pady=3)


proxima_comprobacion = tk.Label(
    ventana,
    text="Próxima comprobación: detenida",
    font=("Arial", 10)
)

proxima_comprobacion.pack(pady=3)


marco_botones = tk.Frame(ventana)
marco_botones.pack(pady=25)


boton_iniciar = tk.Button(
    marco_botones,
    text="▶ INICIAR",
    font=("Arial", 12, "bold"),
    width=15,
    command=iniciar
)

boton_iniciar.grid(
    row=0,
    column=0,
    padx=10
)


boton_detener = tk.Button(
    marco_botones,
    text="■ DETENER",
    font=("Arial", 12, "bold"),
    width=15,
    command=detener
)

boton_detener.grid(
    row=0,
    column=1,
    padx=10
)


ventana.protocol(
    "WM_DELETE_WINDOW",
    cerrar_programa
)

ventana.mainloop()
