import customtkinter as ctk
from tkinter import filedialog
import os
import threading
import sys
import shutil # Necesario para cerrar la app limpiamente

# Importaciones del Core
from app.core.pdf_processor import extraer_texto_pdf
from app.core.parser import analizar_documento
from app.core.file_manager import mover_y_renombrar
from app.core.splitter import dividir_pdf_por_proveedor
from app.utils.logger import registrar_evento
from app.config import DEFAULT_INPUT_DIR, DEFAULT_OUTPUT_DIR


class PDFClassifierApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configuración Ventana
        self.title("ClassDoc Engine - v2.1 (Splitter)")
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

        self.lbl_title = ctk.CTkLabel(self.frame_header, text="⚙️ ClassDoc Engine", font=("Roboto Medium", 24))
        self.lbl_title.pack(side="left")

        self.lbl_version = ctk.CTkLabel(self.frame_header, text="v2.1 Splitter", text_color="gray")
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
        self.log_message("Sistema listo v2.1. Esperando archivos...")

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
        # Carpeta temporal para los trozos cortados
        temp_split_dir = os.path.join(base_output_dir, "_TEMP_SPLIT")

        if not os.path.exists(input_dir):
            self.log_message(f"❌ Error: Ruta de entrada no existe.")
            self.reset_ui()
            return

        archivos_origen = [f for f in os.listdir(input_dir) if f.lower().endswith(".pdf")]
        total_origen = len(archivos_origen)

        self.log_message(f"📂 Detectados {total_origen} archivos de entrada.")
        self.log_message(f"🔪 Modo Splitter Activo: Analizando multipágina...")

        procesados_finales = 0
        errores = 0

        for archivo in archivos_origen:
            ruta_completa_origen = os.path.join(input_dir, archivo)
            self.lbl_status.configure(text=f"Analizando lote: {archivo}...")

            # 1. DIVIDIR (SPLITTER)
            # Pasamos el archivo por la guillotina. Si es de 1 página, devuelve 1 trozo.
            try:
                sub_archivos = dividir_pdf_por_proveedor(ruta_completa_origen, temp_split_dir)
            except Exception as e:
                self.log_message(f"💥 Error crítico dividiendo {archivo}: {e}")
                errores += 1
                continue

            # 2. PROCESAR CADA TROZO (CLASIFICADOR)
            for sub_ruta in sub_archivos:
                nombre_sub = os.path.basename(sub_ruta)

                # A) Leer
                texto, error = extraer_texto_pdf(sub_ruta)
                if error:
                    self.log_message(f"⚠️ Error lectura sub-archivo {nombre_sub}: {error}")
                    errores += 1
                    continue

                # B) Analizar
                datos = analizar_documento(texto)

                if datos["proveedor_detectado"]:
                    msg = f"   ✅ {datos['proveedor_detectado']} | Doc: {datos['id_documento']}"
                    self.log_message(msg)
                else:
                    self.log_message(f"   ❓ {nombre_sub} -> Proveedor desconocido")

                # C) Mover a destino final
                exito, ruta_final = mover_y_renombrar(sub_ruta, datos, base_output_dir)

                # D) Log
                # Usamos el nombre del archivo original padre para el log, + el trozo
                registrar_evento(f"{archivo} -> {nombre_sub}", datos, ruta_final, exito)
                procesados_finales += 1

        # Limpieza: Borrar carpeta temporal de trozos
        if os.path.exists(temp_split_dir):
            try:
                shutil.rmtree(temp_split_dir)
            except:
                pass

        self.log_message(f"🏁 FIN. Documentos generados: {procesados_finales} | Errores: {errores}")
        self.reset_ui()

    def reset_ui(self):
        self.is_running = False
        self.btn_run.configure(state="normal", text="▶ INICIAR PROCESAMIENTO")
        self.btn_exit.configure(state="normal")
        self.lbl_status.configure(text="Estado: Finalizado")