import shutil, subprocess, math, threading
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

APP_TITLE = "VideoToFrame"
DEFAULT_OUTDIR = "frames_out"

# ASCII Art Banner
BANNER_ASCII = """
░██    ░██ ░██       ░██                       ░██████████           ░██████████                                               
░██    ░██           ░██                           ░██               ░██                                                       
░██    ░██ ░██ ░████████  ░███████   ░███████      ░██     ░███████  ░██        ░██░████  ░██████   ░█████████████   ░███████  
░██    ░██ ░██░██    ░██ ░██    ░██ ░██    ░██     ░██    ░██    ░██ ░█████████ ░███           ░██  ░██   ░██   ░██ ░██    ░██ 
 ░██  ░██  ░██░██    ░██ ░█████████ ░██    ░██     ░██    ░██    ░██ ░██        ░██       ░███████  ░██   ░██   ░██ ░█████████ 
  ░██░██   ░██░██   ░███ ░██        ░██    ░██     ░██    ░██    ░██ ░██        ░██      ░██   ░██  ░██   ░██   ░██ ░██        
   ░███    ░██ ░█████░██  ░███████   ░███████      ░██     ░███████  ░██        ░██       ░█████░██ ░██   ░██   ░██  ░███████  
"""

def have(bin_name: str) -> bool:
    return shutil.which(bin_name) is not None

def run_ffmpeg(cmd: list[str]) -> tuple[int, str]:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True)
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except Exception as e:
        return 1, f"ERROR ejecutando FFmpeg: {e}"

def ffprobe_duration_seconds(path: Path) -> float | None:
    try:
        out = subprocess.check_output(
            ["ffprobe","-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1", str(path)],
            text=True
        ).strip()
        return float(out) if out else None
    except Exception:
        return None

def seconds_to_hhmmss_ms(sec: float) -> str:
    if sec < 0: sec = 0.0
    ms = int(round(sec * 1000))
    h = ms // 3_600_000
    ms %= 3_600_000
    m = ms // 60_000
    ms %= 60_000
    s = ms // 1000
    ms %= 1000
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"

def hhmmss_ms_to_seconds(txt: str) -> float:
    t = txt.strip()
    if not t: return 0.0
    if ":" not in t:
        return float(t)  # segundos como "12.5"
    # HH:MM:SS.mmm
    hh, mm, ss = t.split(":")
    if "." in ss:
        ss_i, ms = ss.split(".")
        ms = ms.ljust(3, "0")[:3]
        total = int(hh)*3600 + int(mm)*60 + int(ss_i) + int(ms)/1000.0
    else:
        total = int(hh)*3600 + int(mm)*60 + int(ss)
    return float(total)

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE); self.geometry("920x700"); self.minsize(900,650)
        self.configure(padx=20, pady=20)
        self._style()

        # Vars
        self.var_input   = tk.StringVar()
        self.var_start   = tk.StringVar()
        self.var_end     = tk.StringVar()
        self.var_duration= tk.StringVar()
        self.var_outdir  = tk.StringVar(value=str(Path(DEFAULT_OUTDIR).resolve()))
        self.var_prefix  = tk.StringVar(value="frame")
        self.var_imgfmt  = tk.StringVar(value="png")
        self.var_q       = tk.StringVar(value="2")
        self.var_use_pts = tk.BooleanVar(value=False)
        self.var_do_cut  = tk.BooleanVar(value=False)
        self.var_cutfile = tk.StringVar(value=str(Path("recorte.mp4").resolve()))
        self.video_seconds = 0.0
        self.extracting = False  # Flag para rastrear si hay una extracción en progreso
        self.current_process = None  # Referencia al proceso actual (si es necesario cancelarlo)

        # Main container
        main_container = ttk.Frame(self, style="Card.TFrame")
        main_container.pack(fill="both", expand=True, padx=0, pady=0)

        # Banner section
        banner_frame = ttk.Frame(main_container, style="Banner.TFrame")
        banner_frame.pack(fill="x", pady=(0, 15))
        
        # ASCII Banner in a Text widget with monospace font
        banner_text = tk.Text(banner_frame, height=10, wrap="none", bg="#1a1f2e", fg="#00d4ff",
                              font=("Courier", 8), relief="flat", borderwidth=0,
                              padx=15, pady=12, cursor="arrow")
        banner_text.pack(fill="both", expand=True)
        banner_text.insert("1.0", BANNER_ASCII + "\n" + " " * 35 + "(VideoToFrame by Alanito)")
        banner_text.config(state="disabled")

        frm = ttk.Frame(main_container, style="Card.TFrame"); frm.pack(fill="both", expand=True)

        r=0
        # Entrada y duración detectada
        ttk.Label(frm, text="Video de entrada", style="Bold.TLabel").grid(row=r, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.var_input).grid(row=r, column=1, columnspan=4, sticky="ew", padx=8)
        ttk.Button(frm, text="Elegir…", command=self.pick_input, style="Accent.TButton").grid(row=r, column=5, sticky="e")
        r+=1

        self.lbl_duration = ttk.Label(frm, text="Duración: –", style="Hint.TLabel")
        self.lbl_duration.grid(row=r, column=0, columnspan=3, sticky="w", pady=(2,8))
        r+=1

        # Sliders Inicio/Final (ms)
        self.start_ms = tk.IntVar(value=0)
        self.end_ms   = tk.IntVar(value=0)

        ttk.Label(frm, text="Inicio (desliza o edita el campo):").grid(row=r, column=0, columnspan=3, sticky="w")
        self.sld_start = ttk.Scale(frm, from_=0, to=0, orient="horizontal", command=self.on_slide_start)
        self.sld_start.grid(row=r, column=3, columnspan=3, sticky="ew", padx=(8,0))
        r+=1

        ttk.Label(frm, text="Final (desliza o edita el campo):").grid(row=r, column=0, columnspan=3, sticky="w")
        self.sld_end = ttk.Scale(frm, from_=0, to=0, orient="horizontal", command=self.on_slide_end)
        self.sld_end.grid(row=r, column=3, columnspan=3, sticky="ew", padx=(8,0))
        r+=1

        # Campos de tiempo (sincronizados)
        ttk.Label(frm, text="Inicio").grid(row=r, column=0, sticky="w")
        e_start = ttk.Entry(frm, width=16, textvariable=self.var_start)
        e_start.grid(row=r, column=1, sticky="w", padx=(0,8))
        e_start.bind("<FocusOut>", lambda _e: self.sync_from_entries())

        ttk.Label(frm, text="Final").grid(row=r, column=2, sticky="w")
        e_end = ttk.Entry(frm, width=16, textvariable=self.var_end)
        e_end.grid(row=r, column=3, sticky="w", padx=(0,8))
        e_end.bind("<FocusOut>", lambda _e: self.sync_from_entries())

        ttk.Label(frm, text="Duración").grid(row=r, column=4, sticky="w")
        e_dur = ttk.Entry(frm, width=12, textvariable=self.var_duration)
        e_dur.grid(row=r, column=5, sticky="w")
        e_dur.bind("<FocusOut>", lambda _e: self.sync_from_entries())
        r+=1

        # Salida y formato
        ttk.Label(frm, text="Carpeta de frames").grid(row=r, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.var_outdir).grid(row=r, column=1, columnspan=4, sticky="ew", padx=8)
        ttk.Button(frm, text="Elegir…", command=self.pick_outdir).grid(row=r, column=5, sticky="e")
        r+=1

        ttk.Label(frm, text="Prefijo").grid(row=r, column=0, sticky="w")
        ttk.Entry(frm, width=12, textvariable=self.var_prefix).grid(row=r, column=1, sticky="w", padx=(0,8))
        ttk.Label(frm, text="Formato").grid(row=r, column=2, sticky="w")
        format_combo = ttk.Combobox(frm, width=10, state="readonly", 
                                   values=["png", "jpg", "jpeg", "webp", "bmp", "tiff", "tif", "gif"], 
                                   textvariable=self.var_imgfmt)
        format_combo.grid(row=r, column=3, sticky="w", padx=(0,8))
        format_combo.bind("<<ComboboxSelected>>", self._on_format_changed)
        ttk.Label(frm, text="Calidad (2–31)", style="Hint.TLabel").grid(row=r, column=4, sticky="w")
        self.q_entry = ttk.Entry(frm, width=6, textvariable=self.var_q)
        self.q_entry.grid(row=r, column=5, sticky="w")
        # Inicializar estado según formato por defecto (png no usa calidad)
        self._on_format_changed()
        r+=1

        # Recorte a archivo + PTS
        ttk.Checkbutton(frm, text="Generar archivo recortado (MP4)", variable=self.var_do_cut, command=self.toggle_cut).grid(row=r, column=0, columnspan=2, sticky="w")
        self.entry_cut = ttk.Entry(frm, textvariable=self.var_cutfile, state="disabled")
        self.entry_cut.grid(row=r, column=2, columnspan=3, sticky="ew", padx=8)
        self.btn_cutfile = ttk.Button(frm, text="Guardar como…", command=self.pick_cutfile, state="disabled")
        self.btn_cutfile.grid(row=r, column=5, sticky="e")
        r+=1

        ttk.Checkbutton(frm, text="Usar PTS en nombre de archivos (timestamps reales)", variable=self.var_use_pts).grid(row=r, column=0, columnspan=3, sticky="w")
        r+=1

        for c in range(0,6): frm.grid_columnconfigure(c, weight=1 if c in (1,2,3) else 0)

        btns = ttk.Frame(frm, style="Card.TFrame"); btns.grid(row=r, column=0, columnspan=6, sticky="ew", pady=(10,6))
        self.btn_extract = ttk.Button(btns, text="Extraer frames", command=self.on_extract, style="Accent.TButton")
        self.btn_extract.pack(side="left")
        ttk.Button(btns, text="Limpiar log", command=self.clear_log).pack(side="right")
        r+=1

        ttk.Label(frm, text="Log", style="Bold.TLabel").grid(row=r, column=0, sticky="w")
        self.txt = tk.Text(frm, height=12, wrap="word", bg="#0a0f14", fg="#00d4ff", 
                          insertbackground="#00d4ff", font=("Consolas", 9),
                          relief="flat", borderwidth=2, highlightthickness=1,
                          highlightbackground="#2d3748", highlightcolor="#00d4ff")
        self.txt.grid(row=r, column=0, columnspan=6, sticky="nsew")
        frm.grid_rowconfigure(r, weight=1)
        self.log("✨ VideoToFrame - Listo. Requiere FFmpeg/FFprobe en PATH.\n")
    
    def _on_format_changed(self, event=None):
        """Actualiza la etiqueta de calidad según el formato seleccionado"""
        fmt = self.var_imgfmt.get().lower()
        # Formatos que soportan calidad con -q:v: jpg, jpeg, webp
        quality_formats = ["jpg", "jpeg", "webp"]
        if fmt in quality_formats:
            self.q_entry.config(state="normal")
        else:
            self.q_entry.config(state="disabled")

    # === Estilo con color (simple, sin libs externas) ===
    def _style(self):
        style = ttk.Style(self)
        try: style.theme_use("clam")
        except: pass
        base_bg = "#0f1419"     # fondo oscuro más profundo
        card_bg = "#1a2332"     # card con tono azulado
        banner_bg = "#1a1f2e"   # fondo banner
        fg     = "#e8f4f8"      # texto principal más brillante
        hint   = "#a8b8c8"      # texto secundario
        accent = "#00d4ff"      # acento cyan brillante
        accent_hover = "#00b8e6"
        secondary = "#7c3aed"   # acento morado
        self.configure(bg=base_bg)
        style.configure(".", background=base_bg, foreground=fg, fieldbackground="#16202d")
        style.configure("Card.TFrame", background=card_bg, relief="flat")
        style.configure("Banner.TFrame", background=banner_bg, relief="flat")
        style.configure("Bold.TLabel", font=("Segoe UI", 10, "bold"), background=card_bg, foreground=accent)
        style.configure("TLabel", background=card_bg, foreground=fg, font=("Segoe UI", 9))
        style.configure("Hint.TLabel", background=card_bg, foreground=hint, font=("Segoe UI", 8))
        style.configure("Credit.TLabel", background=banner_bg, foreground=secondary, font=("Segoe UI", 9, "italic"))
        style.configure("TEntry", fieldbackground="#16202d", foreground=fg, bordercolor="#2d3748", 
                       insertcolor=accent, relief="solid", borderwidth=1)
        style.map("TEntry", bordercolor=[("focus", accent)])
        style.configure("TCombobox", fieldbackground="#16202d", foreground=fg, bordercolor="#2d3748",
                       arrowcolor=accent, relief="solid", borderwidth=1)
        style.map("TCombobox", bordercolor=[("focus", accent)])
        style.configure("TCheckbutton", background=card_bg, foreground=fg, focuscolor=card_bg)
        style.configure("TScale", background=card_bg, troughcolor="#2d3748", bordercolor=card_bg)
        style.configure("TScale.slider", background=accent)
        style.configure("TButton", padding=(10, 6), background="#2d3748", foreground=fg, 
                       bordercolor="#3d4758", relief="solid", borderwidth=1)
        style.map("TButton", background=[("active", "#3d4758")])
        style.configure("Accent.TButton", padding=(12, 8), background=accent, foreground="#0a1419",
                       bordercolor=accent, font=("Segoe UI", 9, "bold"))
        style.map("Accent.TButton", background=[("active", accent_hover)])

    # === Sincronización sliders <-> campos ===
    def on_slide_start(self, _val):
        ms = int(float(self.sld_start.get()))
        end_ms = int(float(self.sld_end.get()))
        if ms >= end_ms:
            end_ms = ms + 10
            self.sld_end.set(end_ms)
        self.var_start.set(seconds_to_hhmmss_ms(ms/1000.0))
        self._update_duration_from_bounds()

    def on_slide_end(self, _val):
        ms = int(float(self.sld_end.get()))
        start_ms = int(float(self.sld_start.get()))
        if ms <= start_ms:
            start_ms = ms - 10 if ms >= 10 else 0
            self.sld_start.set(start_ms)
        self.var_end.set(seconds_to_hhmmss_ms(ms/1000.0))
        self._update_duration_from_bounds()

    def sync_from_entries(self):
        try:
            s = hhmmss_ms_to_seconds(self.var_start.get())
            e = hhmmss_ms_to_seconds(self.var_end.get())
            d = self.var_duration.get().strip()
            if d:
                e = s + hhmmss_ms_to_seconds(d)
            s_ms = max(0, int(round(s*1000)))
            e_ms = max(s_ms+10, int(round(e*1000)))
            max_ms = int(round(self.video_seconds*1000))
            s_ms = min(s_ms, max_ms)
            e_ms = min(e_ms, max_ms)
            self.sld_start.set(s_ms)
            self.sld_end.set(e_ms)
            # Normaliza campos
            self.var_start.set(seconds_to_hhmmss_ms(s_ms/1000))
            self.var_end.set(seconds_to_hhmmss_ms(e_ms/1000))
            self._update_duration_from_bounds()
        except Exception:
            pass

    def _update_duration_from_bounds(self):
        s_ms = int(float(self.sld_start.get()))
        e_ms = int(float(self.sld_end.get()))
        dur = max(0, (e_ms - s_ms)/1000.0)
        self.var_duration.set(seconds_to_hhmmss_ms(dur))

    # === Picks ===
    def pick_input(self):
        # Si hay una extracción en progreso, informar al usuario
        if self.extracting:
            messagebox.showwarning("Extracción en progreso", 
                                 "Hay una extracción en progreso. Por favor espera a que termine antes de cargar un nuevo video.")
            return
        
        p = filedialog.askopenfilename(title="Seleccionar video", filetypes=[("Video","*.*")])
        if not p: return
        
        # Limpiar estado previo
        self.current_process = None
        
        # Cargar nuevo video
        self.var_input.set(p)
        if not have("ffprobe"):
            self.lbl_duration.config(text="Duración: (ffprobe no disponible)")
            return
        
        # Obtener duración del video en thread separado para no bloquear la UI
        def load_video_duration():
            try:
                secs = ffprobe_duration_seconds(Path(p)) or 0.0
                self.after(0, lambda: self._update_video_info(secs))
            except Exception as e:
                self.after(0, lambda: self.lbl_duration.config(text=f"Duración: Error al leer video"))
        
        self.lbl_duration.config(text="Duración: Cargando...")
        thread = threading.Thread(target=load_video_duration, daemon=True)
        thread.start()
    
    def _update_video_info(self, secs: float):
        """Actualiza la información del video en el hilo principal"""
        self.video_seconds = secs
        max_ms = max(10, int(math.ceil(secs*1000)))
        self.sld_start.configure(from_=0, to=max_ms)
        self.sld_end.configure(from_=0, to=max_ms)
        self.sld_start.set(0)
        self.sld_end.set(min(max_ms, 5000))
        self.var_start.set("00:00:00.000")
        self.var_end.set(seconds_to_hhmmss_ms(min(secs, 5.0)))
        self._update_duration_from_bounds()
        self.lbl_duration.config(text=f"Duración: {seconds_to_hhmmss_ms(secs)}")

    def pick_outdir(self):
        p = filedialog.askdirectory(title="Seleccionar carpeta de salida")
        if p: self.var_outdir.set(p)

    def pick_cutfile(self):
        p = filedialog.asksaveasfilename(title="Guardar video recortado como", defaultextension=".mp4",
                                         filetypes=[("MP4","*.mp4"),("Todos","*.*")])
        if p: self.var_cutfile.set(p)

    # === Utilidades UI ===
    def toggle_cut(self):
        st = "normal" if self.var_do_cut.get() else "disabled"
        self.entry_cut.configure(state=st); self.btn_cutfile.configure(state=st)

    def log(self, text: str):
        self.txt.insert("end", text); self.txt.see("end")

    def clear_log(self):
        self.txt.delete("1.0", "end")

    # === Acción principal ===
    def on_extract(self):
        if self.extracting:
            messagebox.showwarning("En progreso", "Ya hay una extracción en progreso. Por favor espera.")
            return
        
        if not have("ffmpeg") or not have("ffprobe"):
            messagebox.showerror("Dependencias", "Se requieren ffmpeg y ffprobe en el PATH.")
            return
        
        inp = Path(self.var_input.get().strip())
        if not inp.exists():
            messagebox.showerror("Entrada", "Selecciona un archivo de video válido.")
            return

        # calcula tiempo desde sliders (preciso por ms)
        s_ms = int(float(self.sld_start.get())); e_ms = int(float(self.sld_end.get()))
        s = seconds_to_hhmmss_ms(s_ms/1000.0); e = seconds_to_hhmmss_ms(e_ms/1000.0)

        outdir = Path(self.var_outdir.get().strip() or DEFAULT_OUTDIR); outdir.mkdir(parents=True, exist_ok=True)
        prefix = self.var_prefix.get().strip() or "frame"
        imgfmt = (self.var_imgfmt.get() or "png").lower()
        # Formatos soportados
        supported_formats = ["png", "jpg", "jpeg", "webp", "bmp", "tiff", "tif", "gif"]
        if imgfmt not in supported_formats:
            messagebox.showerror("Formato", f"Formato inválido. Formatos soportados: {', '.join(supported_formats)}")
            return

        # Validar calidad antes de iniciar thread
        if imgfmt in ("jpg", "jpeg", "webp"):
            try:
                q = int((self.var_q.get() or "2").strip())
                if not (2<=q<=31): raise ValueError()
            except ValueError:
                messagebox.showerror("Calidad","Proporciona un entero entre 2 y 31.")
                return

        # Deshabilitar botón y marcar como extrayendo
        self.extracting = True
        self.btn_extract.config(state="disabled", text="Extrayendo...")
        
        # Ejecutar extracción en thread separado
        thread = threading.Thread(target=self._extract_worker, args=(inp, s, e, outdir, prefix, imgfmt), daemon=True)
        thread.start()

    def _extract_worker(self, inp: Path, s: str, e: str, outdir: Path, prefix: str, imgfmt: str):
        """Ejecuta la extracción en un thread separado"""
        try:
            # (Opcional) recorte a MP4 con precisión por cuadro
            if self.var_do_cut.get():
                cutpath = Path(self.var_cutfile.get().strip() or "recorte.mp4")
                cut_cmd = ["ffmpeg","-hide_banner","-loglevel","error","-i",str(inp), "-ss", s, "-to", e,
                           "-c:v","libx264","-crf","18","-preset","veryfast","-c:a","aac","-b:a","192k", str(cutpath)]
                self.after(0, lambda: self.log("[INFO] Cortando fragmento de video…\n"))
                rc,out = run_ffmpeg(cut_cmd)
                self.after(0, lambda: self.log(out+"\n"))
                if rc!=0:
                    self.after(0, lambda: self.log("[ERROR] Falló el recorte.\n"))
                    return
                self.after(0, lambda: self.log(f"[OK] Recorte: {cutpath}\n"))

            # Extracción de frames nativos (sin cambiar FPS)
            # Normalizar extensiones
            ext_map = {"jpeg": "jpg", "tif": "tiff"}
            ext = ext_map.get(imgfmt, imgfmt)
            pattern = str((outdir / f"{prefix}_%06d.{ext}").resolve())
            extract_cmd = ["ffmpeg","-hide_banner","-loglevel","error","-i",str(inp), "-ss", s, "-to", e, "-vsync","0"]
            if self.var_use_pts.get(): extract_cmd += ["-frame_pts","1"]
            
            # Configuración de calidad según formato
            if imgfmt in ("jpg", "jpeg"):
                q = int((self.var_q.get() or "2").strip())
                extract_cmd += ["-q:v", str(q)]
            elif imgfmt == "webp":
                q = int((self.var_q.get() or "2").strip())
                webp_quality = int(100 - ((q - 2) * (70 / 29)))
                if webp_quality < 0: webp_quality = 0
                if webp_quality > 100: webp_quality = 100
                extract_cmd += ["-quality", str(webp_quality)]
            elif imgfmt == "gif":
                extract_cmd += ["-pix_fmt", "rgb24"]
            # BMP, TIFF son sin pérdida
            
            extract_cmd += [pattern]

            self.after(0, lambda: self.log(f"[INFO] Extrayendo frames nativos en formato {imgfmt.upper()}…\n"))
            rc,out = run_ffmpeg(extract_cmd)
            self.after(0, lambda: self.log(out+"\n"))
            if rc!=0:
                self.after(0, lambda: self.log("[ERROR] Falló la extracción de frames.\n"))
            else:
                self.after(0, lambda: self.log(f"[✅] Frames extraídos exitosamente en: {outdir.resolve()}\n"))
                self.after(0, lambda: messagebox.showinfo("✨ Completado", f"Frames en formato {imgfmt.upper()} guardados en:\n{outdir.resolve()}"))
        except Exception as e:
            self.after(0, lambda: self.log(f"[ERROR] Error inesperado: {e}\n"))
        finally:
            # Restaurar estado
            self.after(0, self._extraction_done)

    def _extraction_done(self):
        """Restaura el estado de la UI después de la extracción"""
        self.extracting = False
        self.current_process = None
        self.btn_extract.config(state="normal", text="Extraer frames")

if __name__ == "__main__":
    app = App()
    app.mainloop()