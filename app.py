import tkinter as tk
from tkinter import messagebox
import threading
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin

INTERVALO = 3

PRODUCTO = "30th Celebration Elite Trainer Box"

ejecutando = False
hilo_monitor = None


# =========================================================
# TIENDAS
# =========================================================

TIENDAS = [
    {
        "nombre": "POKEMILLON",
        "url": "https://www.pokemillon.com/",
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
# CONFIGURACIÓN DE PETICIONES
# =========================================================

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/151.0 Safari/537.36"
    )
}


# =========================================================
# BUSCAR PRODUCTO EN UNA TIENDA
# =========================================================

def comprobar_tienda(tienda):

    try:

        respuesta = requests.get(
            tienda["url"],
            headers=HEADERS,
            timeout=20
        )

        if respuesta.status_code != 200:
            return "ERROR", tienda["url"]

        soup = BeautifulSoup(
            respuesta.text,
            "html.parser"
        )

        texto = soup.get_text(
            " ",
            strip=True
        ).lower()

        # Palabras relacionadas con el producto
        palabras_producto = [
            "30th celebration",
            "30th anniversary",
            "30 aniversario",
            "celebrations 30",
        ]

        encontrado = False

        for palabra in palabras_producto:

            if palabra in texto:

                encontrado = True
                break

        if not encontrado:

            return "NO ENCONTRADO", tienda["url"]


        # =================================================
        # BUSCAR INDICIOS DE DISPONIBILIDAD
        # =================================================

        palabras_agotado = [
            "agotado",
            "agouté",
            "sold out",
            "sin existencias",
            "sin stock",
            "out of stock",
            "no disponible",
        ]

        palabras_compra = [
            "añadir al carrito",
            "agregar al carrito",
            "add to cart",
            "comprar",
            "buy now",
            "pre-order",
            "preorder",
            "preventa",
        ]


        agotado = False

        for palabra in palabras_agotado:

            if palabra in texto:

                agotado = True
                break


        disponible = False

        for palabra in palabras_compra:

            if palabra in texto:

                disponible = True
                break


        # =================================================
        # RESULTADO
        # =================================================

        if disponible and not agotado:

            return "DISPONIBLE", tienda["url"]

        if agotado:

            return "AGOTADO", tienda["url"]

        return "PRODUCTO ENCONTRADO", tienda["url"]


    except Exception:

        return "ERROR", tienda["url"]


# =========================================================
# ACTUALIZAR ESTADO
# =========================================================

def actualizar_estado(nombre, estado, url):

    for fila in filas:

        if fila["nombre"] == nombre:

            fila["estado"].config(
                text=estado
            )

            if estado == "DISPONIBLE":

                fila["estado"].config(
                    fg="green"
                )

            elif estado == "AGOTADO":

                fila["estado"].config(
                    fg="red"
                )

            elif estado == "ERROR":

                fila["estado"].config(
                    fg="orange"
                )

            elif estado == "PRODUCTO ENCONTRADO":

                fila["estado"].config(
                    fg="blue"
                )

            else:

                fila["estado"].config(
                    fg="gray"
                )


# =========================================================
# MONITOR PRINCIPAL
# =========================================================

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

            estado, url = comprobar_tienda(
                tienda
            )

            ventana.after(
                0,
                lambda n=tienda["nombre"],
                e=estado,
                u=url:
                actualizar_estado(
                    n,
                    e,
                    u
                )
            )

            # =============================================
            # AVISO SI ENCUENTRA DISPONIBILIDAD
            # =============================================

            if estado == "DISPONIBLE":

                ventana.after(
                    0,
                    lambda n=tienda["nombre"]:
                    mostrar_aviso(n)
                )


        # =================================================
        # ESPERA DE 2 MINUTOS
        # =================================================

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


# =========================================================
# AVISO
# =========================================================

def mostrar_aviso(tienda):

    ventana.bell()

    messagebox.showwarning(
        "🚨 STOCK DETECTADO",
        (
            "¡POSIBLE STOCK DETECTADO!\n\n"
            f"Tienda: {tienda}\n\n"
            "Pokémon TCG 30th Celebration\n"
            "Elite Trainer Box"
        )
    )


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
        text="🟢 MONITOR ACTIVO",
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
        text="🔴 MONITOR DETENIDO",
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
    "750x650"
)

ventana.resizable(
    False,
    False
)


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
    pady=(0, 25)
)


producto = tk.Label(
    ventana,
    text="Elite Trainer Box",
    font=("Arial", 12, "bold")
)

producto.pack(
    pady=(0, 20)
)


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
