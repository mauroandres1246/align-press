"""
Visual Calibration Tool for AlignPress v2

Interactive tool for calibrating platens using chessboard or ArUco patterns
"""
from __future__ import annotations

import logging
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
from datetime import datetime
import json

try:
    import cv2
    import numpy as np
    from PIL import Image, ImageTk, ImageDraw, ImageFont
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("Warning: OpenCV/PIL not available. Calibration tool disabled.")

from ..config.models import CalibrationData, CameraSettings
from ..config.config_manager import ConfigManager

logger = logging.getLogger(__name__)


class CalibrationTool:
    """Visual calibration tool for platen/camera calibration"""

    def __init__(self):
        if not CV2_AVAILABLE:
            raise ImportError("OpenCV and PIL are required for calibration tool")

        self.root = tk.Tk()
        self.root.title("AlignPress v2 - Visual Calibration Tool")
        self.root.geometry("1200x800")

        # Calibration state
        self.current_image: Optional[np.ndarray] = None
        self.image_path: Optional[Path] = None
        self.calibration_result: Optional[CalibrationData] = None

        # Pattern detection settings
        self.pattern_type = tk.StringVar(value="chessboard")
        self.chessboard_size = [7, 7]  # Internal corners
        self.square_size_mm = tk.DoubleVar(value=25.0)
        self.aruco_dict_name = tk.StringVar(value="DICT_6X6_250")
        self.aruco_marker_size_mm = tk.DoubleVar(value=20.0)

        # UI components
        self.image_canvas = None
        self.result_text = None
        self.photo_image = None

        # Detection results
        self.detected_corners = None
        self.detected_pattern = None

        self._setup_ui()
        logger.info("CalibrationTool initialized")

    def _setup_ui(self):
        """Setup the user interface"""
        # Main layout
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left panel - Image and canvas
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Right panel - Controls
        right_frame = ttk.Frame(main_frame, width=350)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        right_frame.pack_propagate(False)

        self._setup_image_panel(left_frame)
        self._setup_controls_panel(right_frame)
        self._setup_menu()

    def _setup_menu(self):
        """Setup menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Archivo", menu=file_menu)
        file_menu.add_command(label="Cargar Imagen", command=self._load_image)
        file_menu.add_separator()
        file_menu.add_command(label="Guardar Calibración", command=self._save_calibration)
        file_menu.add_command(label="Cargar Calibración", command=self._load_calibration)
        file_menu.add_separator()
        file_menu.add_command(label="Exportar Reporte", command=self._export_report)

    def _setup_image_panel(self, parent):
        """Setup image display panel"""
        # Toolbar
        toolbar = ttk.Frame(parent)
        toolbar.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(toolbar, text="Cargar Imagen de Plancha",
                  command=self._load_image).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(toolbar, text="Detectar Patrón",
                  command=self._detect_pattern).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(toolbar, text="Calcular Calibración",
                  command=self._calculate_calibration).pack(side=tk.LEFT)

        # Canvas with scrollbars
        canvas_frame = ttk.Frame(parent)
        canvas_frame.pack(fill=tk.BOTH, expand=True)

        self.image_canvas = tk.Canvas(canvas_frame, bg="gray90")
        v_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.image_canvas.yview)
        h_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL, command=self.image_canvas.xview)

        self.image_canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        self.image_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

    def _setup_controls_panel(self, parent):
        """Setup controls panel"""
        # Pattern type selection
        pattern_frame = ttk.LabelFrame(parent, text="Tipo de Patrón")
        pattern_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Radiobutton(pattern_frame, text="Chessboard (Tablero)",
                       variable=self.pattern_type, value="chessboard",
                       command=self._on_pattern_changed).pack(anchor=tk.W, padx=5, pady=2)
        ttk.Radiobutton(pattern_frame, text="ArUco Markers",
                       variable=self.pattern_type, value="aruco",
                       command=self._on_pattern_changed).pack(anchor=tk.W, padx=5, pady=2)

        # Chessboard settings
        self.chessboard_frame = ttk.LabelFrame(parent, text="Configuración Chessboard")
        self.chessboard_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(self.chessboard_frame, text="Esquinas internas (ancho):").pack(anchor=tk.W, padx=5)
        self.chess_width_var = tk.IntVar(value=7)
        ttk.Spinbox(self.chessboard_frame, from_=3, to=20, textvariable=self.chess_width_var,
                   width=10).pack(anchor=tk.W, padx=5, pady=2)

        ttk.Label(self.chessboard_frame, text="Esquinas internas (alto):").pack(anchor=tk.W, padx=5)
        self.chess_height_var = tk.IntVar(value=7)
        ttk.Spinbox(self.chessboard_frame, from_=3, to=20, textvariable=self.chess_height_var,
                   width=10).pack(anchor=tk.W, padx=5, pady=2)

        ttk.Label(self.chessboard_frame, text="Tamaño cuadro (mm):").pack(anchor=tk.W, padx=5)
        ttk.Entry(self.chessboard_frame, textvariable=self.square_size_mm,
                 width=10).pack(anchor=tk.W, padx=5, pady=2)

        # ArUco settings
        self.aruco_frame = ttk.LabelFrame(parent, text="Configuración ArUco")
        self.aruco_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(self.aruco_frame, text="Diccionario:").pack(anchor=tk.W, padx=5)
        aruco_dict_combo = ttk.Combobox(self.aruco_frame, textvariable=self.aruco_dict_name,
                                       values=["DICT_4X4_50", "DICT_4X4_100", "DICT_4X4_250",
                                              "DICT_5X5_50", "DICT_5X5_100", "DICT_5X5_250",
                                              "DICT_6X6_50", "DICT_6X6_100", "DICT_6X6_250"],
                                       width=15)
        aruco_dict_combo.pack(anchor=tk.W, padx=5, pady=2)

        ttk.Label(self.aruco_frame, text="Tamaño marcador (mm):").pack(anchor=tk.W, padx=5)
        ttk.Entry(self.aruco_frame, textvariable=self.aruco_marker_size_mm,
                 width=10).pack(anchor=tk.W, padx=5, pady=2)

        # Results display
        results_frame = ttk.LabelFrame(parent, text="Resultados de Calibración")
        results_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Scrollable text widget
        text_frame = ttk.Frame(results_frame)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.result_text = tk.Text(text_frame, height=15, width=40, wrap=tk.WORD)
        result_scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.result_text.yview)
        self.result_text.configure(yscrollcommand=result_scrollbar.set)

        self.result_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        result_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Action buttons
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(button_frame, text="Guardar Calibración",
                  command=self._save_calibration).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Usar en Configuración",
                  command=self._use_calibration).pack(side=tk.LEFT)

        # Initialize pattern settings
        self._on_pattern_changed()

    def _on_pattern_changed(self):
        """Handle pattern type change"""
        pattern = self.pattern_type.get()

        if pattern == "chessboard":
            # Show chessboard frame, hide aruco frame
            self.chessboard_frame.pack(fill=tk.X, pady=(0, 10), before=self.aruco_frame)
            self.aruco_frame.pack_forget()
        else:
            # Show aruco frame, hide chessboard frame
            self.aruco_frame.pack(fill=tk.X, pady=(0, 10), before=self.chessboard_frame)
            self.chessboard_frame.pack_forget()

    def _load_image(self):
        """Load calibration image"""
        filename = filedialog.askopenfilename(
            title="Seleccionar imagen de calibración",
            filetypes=[
                ("Imágenes", "*.jpg *.jpeg *.png *.bmp"),
                ("Todos los archivos", "*.*")
            ]
        )

        if filename:
            try:
                self.image_path = Path(filename)
                self.current_image = cv2.imread(filename)

                if self.current_image is None:
                    raise ValueError("No se pudo cargar la imagen")

                self._display_image()
                self._log_result(f"✅ Imagen cargada: {self.image_path.name}")
                self._log_result(f"   Resolución: {self.current_image.shape[1]}x{self.current_image.shape[0]}")

                # Reset detection results
                self.detected_corners = None
                self.detected_pattern = None
                self.calibration_result = None

            except Exception as e:
                messagebox.showerror("Error", f"Error cargando imagen: {e}")
                logger.error(f"Error loading image: {e}")

    def _display_image(self, overlay_results: bool = True):
        """Display current image on canvas with optional overlay"""
        if self.current_image is None:
            return

        # Convert BGR to RGB
        image_rgb = cv2.cvtColor(self.current_image, cv2.COLOR_BGR2RGB)

        # Create PIL image for display
        pil_image = Image.fromarray(image_rgb)

        # Add overlay if we have detection results
        if overlay_results and self.detected_corners is not None:
            pil_image = self._draw_detection_overlay(pil_image)

        # Calculate display size (fit to canvas with max size limit)
        canvas_width = self.image_canvas.winfo_width()
        canvas_height = self.image_canvas.winfo_height()

        if canvas_width <= 1 or canvas_height <= 1:
            # Canvas not ready yet, try again later
            self.root.after(100, lambda: self._display_image(overlay_results))
            return

        # Scale image to fit canvas
        img_width, img_height = pil_image.size
        max_size = min(800, canvas_width - 20, canvas_height - 20)

        if max(img_width, img_height) > max_size:
            scale = max_size / max(img_width, img_height)
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)
            pil_image = pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Convert to PhotoImage
        self.photo_image = ImageTk.PhotoImage(pil_image)

        # Clear canvas and display image
        self.image_canvas.delete("all")
        self.image_canvas.create_image(
            pil_image.size[0] // 2, pil_image.size[1] // 2,
            image=self.photo_image
        )

        # Update canvas scroll region
        self.image_canvas.configure(scrollregion=self.image_canvas.bbox("all"))

    def _draw_detection_overlay(self, pil_image: Image.Image) -> Image.Image:
        """Draw detection results overlay on PIL image"""
        draw = ImageDraw.Draw(pil_image)

        try:
            # Try to load a font
            font = ImageFont.truetype("arial.ttf", 16)
        except:
            font = ImageFont.load_default()

        pattern_type = self.pattern_type.get()

        if pattern_type == "chessboard" and self.detected_corners is not None:
            # Draw chessboard corners
            corners = self.detected_corners.reshape(-1, 2)

            # Draw corner points
            for corner in corners:
                x, y = int(corner[0]), int(corner[1])
                draw.ellipse([x-3, y-3, x+3, y+3], fill='red', outline='darkred')

            # Draw corner connections (grid lines)
            width, height = self.chess_width_var.get(), self.chess_height_var.get()

            # Horizontal lines
            for row in range(height):
                for col in range(width - 1):
                    start_idx = row * width + col
                    end_idx = row * width + col + 1
                    if start_idx < len(corners) and end_idx < len(corners):
                        start_point = corners[start_idx]
                        end_point = corners[end_idx]
                        draw.line([
                            int(start_point[0]), int(start_point[1]),
                            int(end_point[0]), int(end_point[1])
                        ], fill='blue', width=2)

            # Vertical lines
            for col in range(width):
                for row in range(height - 1):
                    start_idx = row * width + col
                    end_idx = (row + 1) * width + col
                    if start_idx < len(corners) and end_idx < len(corners):
                        start_point = corners[start_idx]
                        end_point = corners[end_idx]
                        draw.line([
                            int(start_point[0]), int(start_point[1]),
                            int(end_point[0]), int(end_point[1])
                        ], fill='blue', width=2)

            # Add info text
            draw.text((10, 10), f"Chessboard detectado: {len(corners)} esquinas",
                     fill='green', font=font)

        elif pattern_type == "aruco" and self.detected_pattern is not None:
            # Draw ArUco markers
            corners, ids, _ = self.detected_pattern

            if len(corners) > 0:
                for i, corner in enumerate(corners):
                    corner = corner.reshape(-1, 2)

                    # Draw marker outline
                    points = [(int(p[0]), int(p[1])) for p in corner]
                    draw.polygon(points, outline='red', width=3)

                    # Draw marker ID
                    center_x = int(np.mean(corner[:, 0]))
                    center_y = int(np.mean(corner[:, 1]))
                    draw.text((center_x-10, center_y-8), str(ids[i][0]),
                             fill='red', font=font)

                # Add info text
                draw.text((10, 10), f"ArUco detectados: {len(corners)} marcadores",
                         fill='green', font=font)

        return pil_image

    def _detect_pattern(self):
        """Detect calibration pattern in current image"""
        if self.current_image is None:
            messagebox.showwarning("Advertencia", "Primero carga una imagen")
            return

        try:
            pattern_type = self.pattern_type.get()

            if pattern_type == "chessboard":
                success = self._detect_chessboard()
            else:
                success = self._detect_aruco()

            if success:
                self._display_image(overlay_results=True)
                self._log_result("✅ Patrón detectado exitosamente")
            else:
                self._log_result("❌ No se pudo detectar el patrón")
                self._log_result("   Verifica que el patrón sea visible y esté bien iluminado")

        except Exception as e:
            messagebox.showerror("Error", f"Error detectando patrón: {e}")
            logger.error(f"Error detecting pattern: {e}")

    def _detect_chessboard(self) -> bool:
        """Detect chessboard pattern with improved robustness"""
        # Convert to grayscale
        gray = cv2.cvtColor(self.current_image, cv2.COLOR_BGR2GRAY)

        # Pattern size
        pattern_size = (self.chess_width_var.get(), self.chess_height_var.get())

        # Try multiple detection strategies
        detection_flags = [
            cv2.CALIB_CB_ADAPTIVE_THRESH + cv2.CALIB_CB_NORMALIZE_IMAGE,
            cv2.CALIB_CB_ADAPTIVE_THRESH + cv2.CALIB_CB_NORMALIZE_IMAGE + cv2.CALIB_CB_FAST_CHECK,
            cv2.CALIB_CB_ADAPTIVE_THRESH,
            cv2.CALIB_CB_NORMALIZE_IMAGE,
            None  # Default flags
        ]

        found = False
        corners = None

        # Preprocess image to improve detection
        processed_images = [gray]

        # Try with enhanced contrast
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)
        processed_images.append(enhanced)

        # Try with gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        processed_images.append(blurred)

        # Try different pattern sizes in case of misconfiguration
        pattern_sizes = [
            pattern_size,
            (pattern_size[0] + 1, pattern_size[1]),
            (pattern_size[0], pattern_size[1] + 1),
            (pattern_size[0] + 1, pattern_size[1] + 1),
            (pattern_size[0] - 1, pattern_size[1]) if pattern_size[0] > 3 else pattern_size,
            (pattern_size[0], pattern_size[1] - 1) if pattern_size[1] > 3 else pattern_size
        ]

        self._log_result(f"🔍 Intentando detectar patrón {pattern_size} con múltiples estrategias...")

        for img_idx, processed_img in enumerate(processed_images):
            for size_idx, test_pattern_size in enumerate(pattern_sizes):
                for flag_idx, flags in enumerate(detection_flags):
                    try:
                        if flags is None:
                            found, corners = cv2.findChessboardCorners(processed_img, test_pattern_size)
                        else:
                            found, corners = cv2.findChessboardCorners(processed_img, test_pattern_size, flags)

                        if found:
                            self._log_result(f"✅ Patrón detectado con imagen {img_idx}, tamaño {test_pattern_size}, flags {flag_idx}")
                            break
                    except Exception as e:
                        continue

                if found:
                    break
            if found:
                break

        if found:
            # Refine corner positions
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
            try:
                corners = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
                self._log_result(f"🎯 Esquinas refinadas: {len(corners)} puntos detectados")
            except Exception as e:
                self._log_result(f"⚠️ No se pudieron refinar las esquinas: {e}")

            self.detected_corners = corners
            self.detected_pattern = None

            # Update pattern size if different was detected
            if test_pattern_size != pattern_size:
                self.chess_width_var.set(test_pattern_size[0])
                self.chess_height_var.set(test_pattern_size[1])
                self._log_result(f"📐 Tamaño del patrón ajustado a: {test_pattern_size}")

            return True

        self._log_result("❌ No se pudo detectar el chessboard con ninguna estrategia")
        self._log_result("💡 Sugerencias:")
        self._log_result("   - Verifica que el patrón sea un chessboard válido")
        self._log_result("   - Asegúrate de que esté bien iluminado y enfocado")
        self._log_result("   - Prueba diferentes tamaños de patrón en la configuración")
        self._log_result("   - El patrón debe ocupar al menos 1/4 de la imagen")

        return False

    def _detect_aruco(self) -> bool:
        """Detect ArUco markers with improved compatibility"""
        try:
            # Get ArUco dictionary - handle both old and new OpenCV versions
            dict_name = self.aruco_dict_name.get()

            try:
                # New OpenCV 4.7+ method
                aruco_dict = getattr(cv2.aruco, dict_name)
                dictionary = cv2.aruco.getPredefinedDictionary(aruco_dict)
                parameters = cv2.aruco.DetectorParameters()

                self._log_result(f"🔍 Usando detección ArUco moderna para {dict_name}")

            except AttributeError:
                # Fallback to older OpenCV method
                aruco_dict = getattr(cv2.aruco, dict_name)
                dictionary = cv2.aruco.Dictionary_get(aruco_dict)
                parameters = cv2.aruco.DetectorParameters_create()

                self._log_result(f"🔍 Usando detección ArUco clásica para {dict_name}")

            # Convert to grayscale for better detection
            if len(self.current_image.shape) == 3:
                gray = cv2.cvtColor(self.current_image, cv2.COLOR_BGR2GRAY)
            else:
                gray = self.current_image

            # Detect markers
            corners, ids, rejected = cv2.aruco.detectMarkers(
                gray, dictionary, parameters=parameters
            )

            if len(corners) > 0:
                self.detected_pattern = (corners, ids, rejected)
                self.detected_corners = None
                self._log_result(f"✅ {len(corners)} marcadores ArUco detectados")

                # Log detected marker IDs
                if ids is not None:
                    marker_ids = [str(id[0]) for id in ids]
                    self._log_result(f"🏷️ IDs detectados: {', '.join(marker_ids)}")

                return True
            else:
                self._log_result("❌ No se detectaron marcadores ArUco")
                self._log_result("💡 Sugerencias:")
                self._log_result("   - Verifica que los marcadores sean del diccionario correcto")
                self._log_result("   - Asegúrate de que estén bien enfocados y visibles")
                self._log_result("   - Prueba con diferentes diccionarios ArUco")
                self._log_result("   - Los marcadores deben tener buen contraste")

                return False

        except Exception as e:
            self._log_result(f"❌ Error en detección ArUco: {e}")
            logger.error(f"ArUco detection error: {e}")
            return False

    def _calculate_calibration(self):
        """Calculate calibration from detected pattern"""
        if self.detected_corners is None and self.detected_pattern is None:
            messagebox.showwarning("Advertencia", "Primero detecta un patrón")
            return

        try:
            pattern_type = self.pattern_type.get()

            if pattern_type == "chessboard":
                calibration = self._calculate_chessboard_calibration()
            else:
                calibration = self._calculate_aruco_calibration()

            if calibration:
                self.calibration_result = calibration
                self._display_calibration_results()
                self._log_result("✅ Calibración calculada exitosamente")
            else:
                self._log_result("❌ Error calculando calibración")

        except Exception as e:
            messagebox.showerror("Error", f"Error calculando calibración: {e}")
            logger.error(f"Error calculating calibration: {e}")

    def _calculate_chessboard_calibration(self) -> Optional[CalibrationData]:
        """Calculate calibration from chessboard"""
        if self.detected_corners is None:
            return None

        corners = self.detected_corners.reshape(-1, 2)
        square_size = self.square_size_mm.get()

        # Calculate mm/pixel ratio using adjacent corners
        # Take first row of corners for horizontal measurement
        width = self.chess_width_var.get()

        if len(corners) >= width:
            # Get distance between first two corners in first row
            corner1 = corners[0]
            corner2 = corners[1]

            pixel_distance = np.linalg.norm(corner2 - corner1)
            mm_per_pixel = square_size / pixel_distance

            return CalibrationData(
                factor_mm_px=mm_per_pixel,
                timestamp=datetime.now(),
                method="chessboard_visual_tool",
                pattern_type="chessboard",
                pattern_size=(self.chess_width_var.get(), self.chess_height_var.get())
            )

        return None

    def _calculate_aruco_calibration(self) -> Optional[CalibrationData]:
        """Calculate calibration from ArUco markers"""
        if self.detected_pattern is None:
            return None

        corners, ids, _ = self.detected_pattern
        marker_size = self.aruco_marker_size_mm.get()

        if len(corners) > 0:
            # Use first marker for calibration
            marker_corners = corners[0].reshape(-1, 2)

            # Calculate marker side length in pixels
            side_distances = []
            for i in range(4):
                p1 = marker_corners[i]
                p2 = marker_corners[(i + 1) % 4]
                distance = np.linalg.norm(p2 - p1)
                side_distances.append(distance)

            avg_pixel_distance = np.mean(side_distances)
            mm_per_pixel = marker_size / avg_pixel_distance

            return CalibrationData(
                factor_mm_px=mm_per_pixel,
                timestamp=datetime.now(),
                method="aruco_visual_tool",
                pattern_type="aruco",
                pattern_size=(len(corners),)  # Number of markers detected
            )

        return None

    def _display_calibration_results(self):
        """Display calibration results in the text widget"""
        if not self.calibration_result:
            return

        result = self.calibration_result

        results_text = f"""
🎯 RESULTADOS DE CALIBRACIÓN

📏 Factor de conversión: {result.factor_mm_px:.6f} mm/pixel
📅 Fecha: {result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
🔧 Método: {result.method}
📐 Tipo de patrón: {result.pattern_type}
📊 Tamaño del patrón: {result.pattern_size}

💡 INTERPRETACIÓN:
- Cada pixel en la imagen representa {result.factor_mm_px:.3f} mm en la realidad
- Una distancia de 10 mm equivale a {10/result.factor_mm_px:.1f} pixels
- Una distancia de 100 pixels equivale a {100*result.factor_mm_px:.1f} mm

✅ CALIDAD DE CALIBRACIÓN:
"""

        # Add quality assessment
        if 0.1 <= result.factor_mm_px <= 0.5:
            results_text += "🟢 Excelente - Factor típico para cámaras de plancha\n"
        elif 0.05 <= result.factor_mm_px <= 0.8:
            results_text += "🟡 Buena - Factor razonable\n"
        else:
            results_text += "🔴 Revisar - Factor inusual, verificar patrón\n"

        results_text += f"""
📸 INFORMACIÓN DE IMAGEN:
- Archivo: {self.image_path.name if self.image_path else 'N/A'}
- Resolución: {self.current_image.shape[1]}x{self.current_image.shape[0]} pixels
- Área cubierta: {self.current_image.shape[1]*result.factor_mm_px:.1f} x {self.current_image.shape[0]*result.factor_mm_px:.1f} mm
"""

        self._log_result(results_text)

    def _log_result(self, message: str):
        """Log message to results text widget"""
        self.result_text.insert(tk.END, message + "\n")
        self.result_text.see(tk.END)

    def _save_calibration(self):
        """Save calibration to file"""
        if not self.calibration_result:
            messagebox.showwarning("Advertencia", "No hay calibración para guardar")
            return

        filename = filedialog.asksaveasfilename(
            title="Guardar calibración",
            defaultextension=".json",
            filetypes=[
                ("JSON files", "*.json"),
                ("YAML files", "*.yaml"),
                ("Todos los archivos", "*.*")
            ]
        )

        if filename:
            try:
                # Convert to dictionary with proper type conversion
                calibration_dict = {
                    "factor_mm_px": float(self.calibration_result.factor_mm_px),
                    "timestamp": self.calibration_result.timestamp.isoformat(),
                    "method": self.calibration_result.method,
                    "pattern_type": self.calibration_result.pattern_type,
                    "pattern_size": list(self.calibration_result.pattern_size),
                    "source_image": str(self.image_path) if self.image_path else None,
                    "image_resolution": [int(self.current_image.shape[1]), int(self.current_image.shape[0])] if self.current_image is not None else None
                }

                # Save as JSON
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(calibration_dict, f, indent=2, ensure_ascii=False)

                messagebox.showinfo("Éxito", f"Calibración guardada en:\n{filename}")
                self._log_result(f"✅ Calibración guardada: {Path(filename).name}")

            except Exception as e:
                messagebox.showerror("Error", f"Error guardando calibración: {e}")
                logger.error(f"Error saving calibration: {e}")

    def _load_calibration(self):
        """Load calibration from file"""
        filename = filedialog.askopenfilename(
            title="Cargar calibración",
            filetypes=[
                ("JSON files", "*.json"),
                ("YAML files", "*.yaml"),
                ("Todos los archivos", "*.*")
            ]
        )

        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    calibration_dict = json.load(f)

                # Create CalibrationData object
                self.calibration_result = CalibrationData(
                    factor_mm_px=calibration_dict["factor_mm_px"],
                    timestamp=datetime.fromisoformat(calibration_dict["timestamp"]),
                    method=calibration_dict["method"],
                    pattern_type=calibration_dict.get("pattern_type", "unknown"),
                    pattern_size=tuple(calibration_dict.get("pattern_size", []))
                )

                self._display_calibration_results()
                messagebox.showinfo("Éxito", "Calibración cargada exitosamente")

            except Exception as e:
                messagebox.showerror("Error", f"Error cargando calibración: {e}")
                logger.error(f"Error loading calibration: {e}")

    def _use_calibration(self):
        """Use calibration in a new configuration"""
        if not self.calibration_result:
            messagebox.showwarning("Advertencia", "No hay calibración disponible")
            return

        # Show dialog to create configuration with this calibration
        result = messagebox.askyesno(
            "Usar Calibración",
            "¿Quieres crear una nueva configuración usando esta calibración?\n\n"
            f"Factor: {self.calibration_result.factor_mm_px:.6f} mm/pixel"
        )

        if result:
            try:
                # Launch Configuration Designer with this calibration
                from .config_designer import ConfigDesigner

                config_designer = ConfigDesigner()

                # Set calibration (this would need to be implemented in ConfigDesigner)
                # config_designer.set_calibration(self.calibration_result)

                messagebox.showinfo("Info",
                    "Se abrirá el Configuration Designer.\n"
                    "Puedes usar la calibración guardada para configurar logos.")

                config_designer.run()

            except Exception as e:
                messagebox.showerror("Error", f"Error abriendo Configuration Designer: {e}")
                logger.error(f"Error opening config designer: {e}")

    def _export_report(self):
        """Export calibration report"""
        if not self.calibration_result:
            messagebox.showwarning("Advertencia", "No hay calibración para exportar")
            return

        filename = filedialog.asksaveasfilename(
            title="Exportar reporte de calibración",
            defaultextension=".txt",
            filetypes=[
                ("Text files", "*.txt"),
                ("Todos los archivos", "*.*")
            ]
        )

        if filename:
            try:
                report_content = self._generate_calibration_report()

                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(report_content)

                messagebox.showinfo("Éxito", f"Reporte exportado a:\n{filename}")

            except Exception as e:
                messagebox.showerror("Error", f"Error exportando reporte: {e}")

    def _generate_calibration_report(self) -> str:
        """Generate detailed calibration report"""
        if not self.calibration_result:
            return "No calibration data available"

        result = self.calibration_result
        timestamp_str = result.timestamp.strftime('%Y-%m-%d %H:%M:%S')

        report = f"""
ALIGNPRESS v2 - REPORTE DE CALIBRACIÓN
=====================================

INFORMACIÓN GENERAL:
- Fecha de calibración: {timestamp_str}
- Método utilizado: {result.method}
- Tipo de patrón: {result.pattern_type}
- Tamaño del patrón: {result.pattern_size}

RESULTADOS:
- Factor de conversión: {result.factor_mm_px:.6f} mm/pixel
- Factor inverso: {1/result.factor_mm_px:.2f} pixels/mm

IMAGEN FUENTE:
- Archivo: {self.image_path.name if self.image_path else 'N/A'}
- Ruta: {self.image_path if self.image_path else 'N/A'}
"""

        if self.current_image is not None:
            report += f"""- Resolución: {self.current_image.shape[1]}x{self.current_image.shape[0]} pixels
- Área cubierta: {self.current_image.shape[1]*result.factor_mm_px:.1f} x {self.current_image.shape[0]*result.factor_mm_px:.1f} mm
"""

        report += f"""
EJEMPLOS DE CONVERSIÓN:
- 10 mm = {10/result.factor_mm_px:.1f} pixels
- 25 mm = {25/result.factor_mm_px:.1f} pixels
- 50 mm = {50/result.factor_mm_px:.1f} pixels
- 100 mm = {100/result.factor_mm_px:.1f} pixels

- 10 pixels = {10*result.factor_mm_px:.2f} mm
- 50 pixels = {50*result.factor_mm_px:.2f} mm
- 100 pixels = {100*result.factor_mm_px:.2f} mm
- 200 pixels = {200*result.factor_mm_px:.2f} mm

NOTAS DE USO:
- Usar este factor en configuraciones de AlignPress v2
- Válido para la distancia y iluminación de calibración
- Recalibrar si cambia la configuración de cámara o distancia

Generado por AlignPress v2 Calibration Tool
"""

        return report

    def run(self):
        """Run the calibration tool"""
        self.root.mainloop()


def main():
    """Main entry point for calibration tool"""
    if not CV2_AVAILABLE:
        print("Error: OpenCV y PIL son requeridos para la herramienta de calibración")
        print("Instala: pip install opencv-python pillow")
        return

    try:
        app = CalibrationTool()
        app.run()
    except Exception as e:
        print(f"Error ejecutando herramienta de calibración: {e}")


if __name__ == "__main__":
    main()