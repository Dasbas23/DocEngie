import customtkinter as ctk
from tkinter import filedialog
import os
import threading

# Importamos nuestro cerebro backend
from app.core.pdf_processor import extraer_texto_pdf
from app.core.parser import analizar_documento
from app.core.file_manager import mover_y_renombrar
from app.utils.logger import registrar_evento
from app.config import DEFAULT_INPUT_DIR


class PDFClassifierApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configuración Ventana
        self.title("Clasificador Inteligente de Albaranes")
        self.geometry("800x600")
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        # Variables
        self.input_folder = ctk.StringVar(value=os.path.abspath(DEFAULT_INPUT_DIR))

        # --- LAYOUT (DISEÑO) ---
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)  # El log se expande

        # 1. Sección Header
        self.lbl_title = ctk.CTkLabel(self, text="Panel de Control DAM", font=("Roboto", 24))
        self.lbl_title.grid(row=0, column=0, pady=20, sticky="ew")

        # 2. Sección Selección Carpeta
        self.frame_top = ctk.CTkFrame(self)
        self.frame_top.grid(row=1, column=0, padx=20, pady=10, sticky="ew")

        self.btn_browse = ctk.CTkButton(self.frame_top, text="Seleccionar Carpeta Entrada",
                                        command=self.seleccionar_carpeta)
        self.btn_browse.grid(row=0, column=0, padx=10, pady=10)

        self.lbl_folder = ctk.CTkLabel(self.frame_top, textvariable=self.input_folder, text_color="gray")
        self.lbl_folder.grid(row=0, column=1, padx=10, sticky="w")

        self.btn_run = ctk.CTkButton(self.frame_top, text="▶ INICIAR CLASIFICACIÓN", fg_color="green",
                                     hover_color="darkgreen", command=self.start_processing_thread)
        self.btn_run.grid(row=0, column=2, padx=10, pady=10)

        # 3. Sección Log (Consola visual)
        self.textbox_log = ctk.CTkTextbox(self, width=760)
        self.textbox_log.grid(row=2, column=0, padx=20, pady=20, sticky="nsew")
        self.log_message("Sistema listo. Esperando órdenes...")

        # 4. Barra de estado
        self.lbl_status = ctk.CTkLabel(self, text="Estado: En espera", anchor="w")
        self.lbl_status.grid(row=3, column=0, padx=20, pady=5, sticky="ew")

    def log_message(self, message):
        """Escribe en la cajita de texto"""
        self.textbox_log.insert("end", f">> {message}\n")
        self.textbox_log.see("end")  # Auto-scroll al final

    def seleccionar_carpeta(self):
        folder = filedialog.askdirectory()
        if folder:
            self.input_folder.set(folder)

    def start_processing_thread(self):
        """Lanza el proceso en segundo plano para no congelar la ventana"""
        self.btn_run.configure(state="disabled")  # Evitar doble click
        thread = threading.Thread(target=self.run_processing)
        thread.start()

    def run_processing(self):
        input_dir = self.input_folder.get()
        if not os.path.exists(input_dir):
            self.log_message(f"❌ Error: La carpeta {input_dir} no existe.")
            self.btn_run.configure(state="normal")
            return

        archivos = [f for f in os.listdir(input_dir) if f.lower().endswith(".pdf")]
        total = len(archivos)

        self.log_message(f"📂 Iniciando escaneo en: {input_dir}")
        self.log_message(f"📄 Archivos PDF encontrados: {total}")

        procesados = 0
        errores = 0

        for archivo in archivos:
            ruta_completa = os.path.join(input_dir, archivo)
            self.lbl_status.configure(text=f"Procesando: {archivo}...")

            # --- FASE 1: LECTURA ---
            texto, error_lectura = extraer_texto_pdf(ruta_completa)

            if error_lectura:
                self.log_message(f"⚠️ Error leyendo {archivo}: {error_lectura}")
                errores += 1
                registrar_evento(ruta_completa, {}, "Error Lectura", False)
                continue

            # --- FASE 2: ANÁLISIS ---
            datos = analizar_documento(texto)

            if datos["proveedor_detectado"]:
                self.log_message(f"✅ {archivo} -> {datos['proveedor_detectado']} (Pedido: {datos['numero_pedido']})")
            else:
                self.log_message(f"❓ {archivo} -> No se identificó proveedor. A revisión manual.")

            # --- FASE 3: ACCIÓN (MOVER) ---
            exito, info_ruta = mover_y_renombrar(ruta_completa, datos)

            # --- FASE 4: LOGGING CSV ---
            registrar_evento(ruta_completa, datos, info_ruta, exito)

            procesados += 1

        self.log_message(f"🏁 FIN DEL PROCESO. Procesados: {procesados} | Errores lectura: {errores}")
        self.lbl_status.configure(text="Estado: Finalizado")
        self.btn_run.configure(state="normal")