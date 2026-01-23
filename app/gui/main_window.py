import customtkinter as ctk
from tkinter import filedialog
import os
import threading
import sys  # Necesario para cerrar la app limpiamente

# Importaciones del Core
from app.core.pdf_processor import extraer_texto_pdf
from app.core.parser import analizar_documento
from app.core.file_manager import mover_y_renombrar
from app.utils.logger import registrar_evento
from app.config import DEFAULT_INPUT_DIR, DEFAULT_OUTPUT_DIR


class PDFClassifierApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configuración Ventana
        self.title("Clasificador Inteligente - v2.0")
        self.geometry("950x700")
        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("blue")

        # Variables de estado
        self.input_folder = ctk.StringVar(value=os.path.abspath(DEFAULT_INPUT_DIR))
        self.output_folder = ctk.StringVar(value=os.path.abspath(DEFAULT_OUTPUT_DIR))
        self.is_running = False

        # --- LAYOUT PRINCIPAL (Grid 4 filas) ---
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)  # El log se expande

        # 1. Header
        self.frame_header = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_header.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")

        self.lbl_title = ctk.CTkLabel(self.frame_header, text="⚙️ Panel de Control DAM", font=("Roboto Medium", 24))
        self.lbl_title.pack(side="left")

        self.lbl_version = ctk.CTkLabel(self.frame_header, text="v2.0 Stable", text_color="gray")
        self.lbl_version.pack(side="right", anchor="s")

        # 2. Panel de Control
        self.frame_controls = ctk.CTkFrame(self)
        self.frame_controls.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.frame_controls.grid_columnconfigure(1, weight=1)

        # --- Fila 0: Entrada ---
        lbl_in = ctk.CTkLabel(self.frame_controls, text="Carpeta Origen:", width=100, anchor="w")
        lbl_in.grid(row=0, column=0, padx=15, pady=10)

        entry_in = ctk.CTkEntry(self.frame_controls, textvariable=self.input_folder, state="readonly")
        entry_in.grid(row=0, column=1, padx=5, pady=10, sticky="ew")

        btn_in = ctk.CTkButton(self.frame_controls, text="📂 Buscar", width=80, command=self.select_input)
        btn_in.grid(row=0, column=2, padx=15, pady=10)

        # --- Fila 1: Salida ---
        lbl_out = ctk.CTkLabel(self.frame_controls, text="Carpeta Destino:", width=100, anchor="w")
        lbl_out.grid(row=1, column=0, padx=15, pady=10)

        entry_out = ctk.CTkEntry(self.frame_controls, textvariable=self.output_folder, state="readonly")
        entry_out.grid(row=1, column=1, padx=5, pady=10, sticky="ew")

        btn_out = ctk.CTkButton(self.frame_controls, text="📂 Buscar", width=80, command=self.select_output)
        btn_out.grid(row=1, column=2, padx=15, pady=10)

        # --- Fila 2: Botón de Acción ---
        self.btn_run = ctk.CTkButton(
            self.frame_controls,
            text="▶ INICIAR PROCESAMIENTO",
            font=("Roboto", 16, "bold"),
            fg_color="#2CC985",
            hover_color="#229A65",
            height=40,
            command=self.start_processing_thread
        )
        self.btn_run.grid(row=2, column=0, columnspan=3, padx=20, pady=(10, 20), sticky="ew")

        # 3. Log
        self.textbox_log = ctk.CTkTextbox(self, font=("Consolas", 12))
        self.textbox_log.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")
        self.log_message("Sistema listo v2.0. Esperando archivos...")

        # 4. Footer (Status + Botón Salir)
        self.frame_footer = ctk.CTkFrame(self, height=40)
        self.frame_footer.grid(row=3, column=0, padx=20, pady=20, sticky="ew")
        self.frame_footer.grid_columnconfigure(0, weight=1)

        self.lbl_status = ctk.CTkLabel(self.frame_footer, text="Estado: En espera", anchor="w", text_color="gray")
        self.lbl_status.grid(row=0, column=0, padx=15, pady=5, sticky="ew")

        # Botón Salir (Rojo y alineado a la derecha)
        self.btn_exit = ctk.CTkButton(
            self.frame_footer,
            text="✖ SALIR",
            fg_color="#C0392B",
            hover_color="#E74C3C",
            width=80,
            command=self.cerrar_app
        )
        self.btn_exit.grid(row=0, column=1, padx=15, pady=5)

    # --- FUNCIONES AUXILIARES ---
    def log_message(self, message):
        self.textbox_log.insert("end", f">> {message}\n")
        self.textbox_log.see("end")

    def select_input(self):
        folder = filedialog.askdirectory()
        if folder: self.input_folder.set(folder)

    def select_output(self):
        folder = filedialog.askdirectory()
        if folder: self.output_folder.set(folder)

    def cerrar_app(self):
        """Cierra la aplicación completamente"""
        self.destroy()
        sys.exit()

    # --- LÓGICA DE EJECUCIÓN ---
    def start_processing_thread(self):
        if self.is_running: return
        self.is_running = True
        self.btn_run.configure(state="disabled", text="⏳ PROCESANDO...")
        self.btn_exit.configure(state="disabled")  # No salir mientras procesa
        threading.Thread(target=self.run_processing).start()

    def run_processing(self):
        input_dir = self.input_folder.get()
        base_output_dir = self.output_folder.get()

        if not os.path.exists(input_dir):
            self.log_message(f"❌ Error: Ruta de entrada no existe.")
            self.reset_ui()
            return

        archivos = [f for f in os.listdir(input_dir) if f.lower().endswith(".pdf")]
        total = len(archivos)

        self.log_message(f"📂 Iniciando lote de {total} archivos...")
        procesados = 0
        errores = 0

        for archivo in archivos:
            ruta_completa = os.path.join(input_dir, archivo)
            self.lbl_status.configure(text=f"Procesando: {archivo}...")

            # FASE 1: Leer
            texto, error = extraer_texto_pdf(ruta_completa)
            if error:
                self.log_message(f"⚠️ Fallo lectura {archivo}: {error}")
                errores += 1
                registrar_evento(ruta_completa, {}, "Error Lectura", False)
                continue

            # FASE 2: Analizar
            datos = analizar_documento(texto)

            if datos["proveedor_detectado"]:
                msg = f"✅ {datos['proveedor_detectado']} | Doc: {datos['id_documento']} | Fecha: {datos['fecha_documento']}"
                self.log_message(msg)
            else:
                self.log_message(f"❓ {archivo} -> Proveedor desconocido (Revisión Manual)")

            # FASE 3: Mover
            exito, ruta_final = mover_y_renombrar(ruta_completa, datos, base_output_dir)

            # FASE 4: Log
            registrar_evento(ruta_completa, datos, ruta_final, exito)
            procesados += 1

        self.log_message(f"🏁 FIN. Procesados: {procesados} | Errores lectura: {errores}")
        self.reset_ui()

    def reset_ui(self):
        self.is_running = False
        self.btn_run.configure(state="normal", text="▶ INICIAR PROCESAMIENTO")
        self.btn_exit.configure(state="normal")
        self.lbl_status.configure(text="Estado: Finalizado")