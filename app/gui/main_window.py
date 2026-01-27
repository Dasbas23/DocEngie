import customtkinter as ctk
from tkinter import filedialog
import os
import threading
import sys
import shutil
import time
from app.core.pdf_processor import extraer_texto_pdf
from app.core.parser import analizar_documento
from app.core.file_manager import mover_y_renombrar
from app.core.splitter import dividir_pdf_por_proveedor
from app.utils.logger import registrar_evento
from app.config import DEFAULT_INPUT_DIR, DEFAULT_OUTPUT_DIR, TITULO_APP, VERSION_ACTUAL


# --- CONFIGURACIÓN DE COLORES  ---
COLOR_PRIMARY = "#3B8ED0"  # Azul Caelum
COLOR_SUCCESS = "#2CC985"  # Verde Esmeralda
COLOR_DANGER = "#C0392B"  # Rojo Alizarina
COLOR_CARD_DARK = "#2b2b2b"  # Fondo tarjeta oscuro
COLOR_CARD_LIGHT = "#ebebeb"  # Fondo tarjeta claro
COLOR_OCR_WARNING = "#F39C12"  # Naranja para el aviso de OCR


class PDFClassifierApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configuración Ventana Principal
        self.title(f"{TITULO_APP} - {VERSION_ACTUAL}")
        self.geometry("1000x800")
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        # Variables de estado
        self.input_folder = ctk.StringVar(value=os.path.abspath(DEFAULT_INPUT_DIR))
        self.output_folder = ctk.StringVar(value=os.path.abspath(DEFAULT_OUTPUT_DIR))
        self.is_running = False
        self.usar_ocr = ctk.BooleanVar(value=False)

        # --- LAYOUT PRINCIPAL (GRID) ---
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)  # El log se expandirá


        self.frame_header = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_header.grid(row=0, column=0, padx=25, pady=(20, 10), sticky="ew")

        # Título y Versión
        self.lbl_title = ctk.CTkLabel(
            self.frame_header,
            text=f"🚀 {TITULO_APP}",
            font=("Roboto", 26, "bold")
        )
        self.lbl_title.pack(side="left")

        self.lbl_ver = ctk.CTkLabel(
            self.frame_header,
            text=VERSION_ACTUAL,
            text_color="gray",
            font=("Roboto", 12)
        )
        self.lbl_ver.pack(side="left", padx=(10, 0), pady=(10, 0))

        # Switch de Tema
        self.switch_tema = ctk.CTkSwitch(
            self.frame_header,
            text="Modo Oscuro",
            command=self.cambiar_tema,
            onvalue="Dark",
            offvalue="Light",
            font=("Roboto", 12)
        )
        self.switch_tema.select()
        self.switch_tema.pack(side="right")

        #  PANEL DE CONFIGURACIÓN
        self.frame_config = ctk.CTkFrame(self, fg_color=COLOR_CARD_DARK, corner_radius=15)
        self.frame_config.grid(row=1, column=0, padx=25, pady=10, sticky="ew")
        self.frame_config.grid_columnconfigure(1, weight=1)

        # --- Título Sección ---
        ctk.CTkLabel(self.frame_config, text="CONFIGURACIÓN DE RUTAS", font=("Roboto", 14, "bold"),
                     text_color="silver").grid(row=0, column=0, columnspan=3, sticky="w", padx=20, pady=(15, 10))

        # --- Entrada (Origen) ---
        ctk.CTkLabel(self.frame_config, text="Carpeta Origen:", font=("Roboto", 13)).grid(row=1, column=0, padx=20,
                                                                                            pady=10, sticky="w")

        self.entry_in = ctk.CTkEntry(self.frame_config, textvariable=self.input_folder, height=35, border_width=0,
                                     fg_color="#3a3a3a", text_color="white")
        self.entry_in.grid(row=1, column=1, padx=5, pady=10, sticky="ew")

        # Botón "Examinar..."
        btn_in = ctk.CTkButton(self.frame_config, text="Examinar...", width=100, height=35, fg_color=COLOR_PRIMARY,
                               command=self.select_input)
        btn_in.grid(row=1, column=2, padx=20, pady=10)

        # --- Salida (Destino) ---
        ctk.CTkLabel(self.frame_config, text="Carpeta Destino:", font=("Roboto", 13)).grid(row=2, column=0, padx=20,
                                                                                             pady=10, sticky="w")

        self.entry_out = ctk.CTkEntry(self.frame_config, textvariable=self.output_folder, height=35, border_width=0,
                                      fg_color="#3a3a3a", text_color="white")
        self.entry_out.grid(row=2, column=1, padx=5, pady=10, sticky="ew")

        btn_out = ctk.CTkButton(self.frame_config, text="Examinar...", width=100, height=35, fg_color=COLOR_PRIMARY,
                                command=self.select_output)
        btn_out.grid(row=2, column=2, padx=20, pady=10)

        # --- Opciones Avanzadas (OCR) ---
        ctk.CTkLabel(self.frame_config, text="OPCIONES DE PROCESAMIENTO", font=("Roboto", 14, "bold"),
                     text_color="silver").grid(row=3, column=0, columnspan=3, sticky="w", padx=20, pady=(15, 5))

        self.check_ocr = ctk.CTkCheckBox(
            self.frame_config,
            text="Habilitar OCR Extendido (Lento - Úsalo si los PDFs son imágenes escaneadas)",
            variable=self.usar_ocr,
            onvalue=True, offvalue=False,
            font=("Roboto", 12, "bold"),
            text_color=COLOR_OCR_WARNING,  # Color legible naranja
            hover_color="#9A03FF",
            fg_color="#200065"
        )
        self.check_ocr.grid(row=4, column=0, columnspan=3, sticky="w", padx=20, pady=(5, 20))

        # --- Botón de Acción Principal ---
        self.btn_run = ctk.CTkButton(
            self.frame_config,
            text="▶ INICIAR PROCESAMIENTO",
            font=("Roboto", 16, "bold"),
            fg_color=COLOR_SUCCESS,
            hover_color="#229A65",
            height=45,
            corner_radius=25,
            command=self.start_processing_thread
        )
        self.btn_run.grid(row=5, column=0, columnspan=3, padx=20, pady=(0, 20), sticky="ew")

        # CONSOLA DE REGISTRO (LOG)
        self.frame_log = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_log.grid(row=2, column=0, padx=25, pady=10, sticky="nsew")
        self.frame_log.grid_rowconfigure(1, weight=1)
        self.frame_log.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self.frame_log, text="📟 REGISTRO DE EVENTOS", font=("Roboto", 12, "bold")).grid(row=0, column=0,
                                                                                                     sticky="w",
                                                                                                     pady=(0, 5))

        self.textbox_log = ctk.CTkTextbox(
            self.frame_log,
            font=("Consolas", 12),
            activate_scrollbars=True
        )
        self.textbox_log.grid(row=1, column=0, sticky="nsew")

        # Mensaje inicial
        self.log_message(f"Sistema listo {VERSION_ACTUAL}. Esperando archivos...")

        # FOOTER (Estado sistema + Salir)
        self.frame_footer = ctk.CTkFrame(self, height=60, fg_color="transparent")
        self.frame_footer.grid(row=3, column=0, padx=25, pady=15, sticky="ew")
        self.frame_footer.grid_columnconfigure(0, weight=1)

        # Etiqueta de Estado
        self.lbl_status = ctk.CTkLabel(
            self.frame_footer,
            text="Estado: En espera",
            anchor="w",
            text_color="gray",
            font=("Roboto", 13)
        )
        self.lbl_status.grid(row=0, column=0, sticky="ew")

        # Botón Salir (Estilo V2)
        self.btn_exit = ctk.CTkButton(
            self.frame_footer,
            text="✖ SALIR",
            font=("Roboto", 14, "bold"),
            fg_color=COLOR_DANGER,
            hover_color="#E74C3C",
            height=40,
            width=120,
            corner_radius=20,
            command=self.cerrar_app
        )
        self.btn_exit.grid(row=0, column=1)

    # --- FUNCIONES DE LÓGICA UI ---

    def cambiar_tema(self):
        """ Cambia entre modo claro y oscuro actualizando colores manualmente """
        modo = self.switch_tema.get()
        ctk.set_appearance_mode(modo)

        if modo == "Light":
            self.frame_config.configure(fg_color=COLOR_CARD_LIGHT)
            # Ajuste de colores para modo claro
            self.entry_in.configure(fg_color="white", text_color="black")
            self.entry_out.configure(fg_color="white", text_color="black")
            self.switch_tema.configure(text="Modo Claro")
            # El texto naranja del OCR se lee bien en blanco, pero podemos oscurecerlo un poco
            self.check_ocr.configure(text_color="#D35400")
        else:
            self.frame_config.configure(fg_color=COLOR_CARD_DARK)
            # Ajuste de colores para modo oscuro
            self.entry_in.configure(fg_color="#3a3a3a", text_color="white")
            self.entry_out.configure(fg_color="#3a3a3a", text_color="white")
            self.switch_tema.configure(text="Modo Oscuro")
            self.check_ocr.configure(text_color=COLOR_OCR_WARNING)

    def log_message(self, message):
        """ Escribe en el log y hace autoscroll """
        # Desbloqueamos temporalmente si quisieramos hacerlo read-only estricto,
        # pero por simplicidad de V1 dejamos escribir directo
        self.textbox_log.insert("end", f">> {message}\n")
        self.textbox_log.see("end")

    def select_input(self):
        """ Permite ver archivos en las carpetas de entrada """

        archivo = filedialog.askopenfilename(
            title="Selecciona cualquiera de los archivos PDF dentro de la carpeta",
            filetypes=[("Archivos PDF", "*.pdf"), ("Todos los archivos", "*.*")]
        )
        if archivo:
            #Obtenemos el directorio padre de ese archivo
            folder = os.path.dirname(archivo)
            self.input_folder.set(folder)

            #Escribir en el log que carpeta se ha detectado
            self.log_message(f"📂 Carpeta origen seleccionada: {folder}")

    def select_output(self):
        folder = filedialog.askdirectory()
        if folder:
            self.output_folder.set(folder)

    def cerrar_app(self):
        self.destroy()
        sys.exit()

    # --- HILOS Y PROCESAMIENTO (Lógica V1 + Integración OCR V2) ---

    def start_processing_thread(self):
        if self.is_running: return

        # Validaciones básicas
        if not os.path.exists(self.input_folder.get()):
            self.log_message("❌ Error: La carpeta de origen no existe.")
            return

        self.is_running = True
        self.btn_run.configure(state="disabled", text="⏳ PROCESANDO...", fg_color="#7f8c8d")

        # Iniciar hilo
        threading.Thread(target=self.run_processing, daemon=True).start()

    def run_processing(self):
        input_dir = self.input_folder.get()
        base_output_dir = self.output_folder.get()
        usar_ocr_activo = self.usar_ocr.get()  # Obtenemos estado del Checkbox
        temp_split_dir = os.path.join(base_output_dir, "_TEMP_SPLIT")

        archivos_origen = [f for f in os.listdir(input_dir) if f.lower().endswith(".pdf")]

        self.log_message("━" * 40)
        self.log_message(f"🚀 INICIO DE PROCESO | Archivos: {len(archivos_origen)}")
        if usar_ocr_activo:
            self.log_message(f"👁️ MODO OCR EXTENDIDO: ACTIVADO. Puede tardar unos segundos")
        self.lbl_status.configure(text="Estado: Procesando lotes...")

        procesados_finales = 0
        errores = 0

        # Crear carpeta temporal si no existe
        if not os.path.exists(temp_split_dir):
            os.makedirs(temp_split_dir, exist_ok=True)

        try:
            for archivo in archivos_origen:
                ruta_completa_origen = os.path.join(input_dir, archivo)
                self.lbl_status.configure(text=f"Procesando: {archivo}...")

                # 1. DIVIDIR (SPLITTER)
                try:
                    # Si 'dividir_pdf_por_proveedor' no está importado (fallback), esto fallará controlado
                    if 'dividir_pdf_por_proveedor' in globals():
                        sub_archivos = dividir_pdf_por_proveedor(ruta_completa_origen, temp_split_dir)
                    else:
                        # Fallback simple para pruebas UI sin core
                        sub_archivos = [ruta_completa_origen]
                except Exception as e:
                    self.log_message(f"💥 Error crítico dividiendo {archivo}: {e}")
                    errores += 1
                    continue

                # 2. PROCESAR CADA TROZO
                for sub_ruta in sub_archivos:
                    nombre_sub = os.path.basename(sub_ruta)

                    # A) Leer (Pasamos forzar_ocr si la función lo soporta)
                    try:
                        # Asumiendo que extraer_texto_pdf fue actualizado para aceptar el argumento
                        # Si tu función core no acepta argumentos, elimina 'forzar_ocr=usar_ocr_activo'
                        texto, error = extraer_texto_pdf(sub_ruta, forzar_ocr=usar_ocr_activo)
                    except TypeError:
                        # Si la función del core antigua no acepta el parametro OCR, lo llamamos normal
                        texto, error = extraer_texto_pdf(sub_ruta)

                    if error:
                        self.log_message(f"   ⚠️ Error lectura {nombre_sub}: {error}")
                        errores += 1
                        continue

                    # B) Analizar
                    datos = analizar_documento(texto)

                    if datos.get("proveedor_detectado"):
                        self.log_message(
                            f"   ✅ {datos['proveedor_detectado']} | Doc: {datos.get('id_documento', 'N/A')}")
                    else:
                        self.log_message(f"   ❓ {nombre_sub} -> Desconocido")

                    # C) Mover
                    exito, ruta_final = mover_y_renombrar(sub_ruta, datos, base_output_dir)

                    # D) Registrar
                    registrar_evento(f"{archivo} -> {nombre_sub}", datos, ruta_final, exito)
                    procesados_finales += 1

        except Exception as e:
            self.log_message(f"❌ ERROR GENERAL: {str(e)}")
        finally:
            # Limpieza
            if os.path.exists(temp_split_dir):
                try:
                    shutil.rmtree(temp_split_dir)
                except:
                    pass

            self.reset_ui(procesados_finales, errores)

    def reset_ui(self, procesados=0, errores=0):
        """ Restaura la interfaz al terminar el hilo """
        self.is_running = False

        # Debemos usar after para modificar UI desde hilo de forma segura,
        # aunque CTK suele tolerarlo, es buena práctica o hacerlo directo si no falla.
        self.btn_run.configure(state="normal", text="▶ INICIAR PROCESAMIENTO", fg_color=COLOR_SUCCESS)
        self.btn_exit.configure(state="normal")

        msg_fin = f"🏁 Finalizado. Docs: {procesados} | Errores: {errores}"
        self.lbl_status.configure(text=msg_fin)
        self.log_message(msg_fin)
        self.log_message("━" * 40)


if __name__ == "__main__":
    app = PDFClassifierApp()
    app.mainloop()