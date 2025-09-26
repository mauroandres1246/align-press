"""
Configuration Designer Tool for AlignPress v2

Interactive tool for creating and testing multi-logo garment configurations
"""
from __future__ import annotations

import logging
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import asdict

try:
    import cv2
    import numpy as np
    from PIL import Image, ImageTk, ImageDraw
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    tk = None
    print("Warning: OpenCV, PIL or tkinter not available. GUI tools disabled.")

from ..config.models import (
    Logo, Style, Variant, Point, Rectangle,
    create_default_config, AlignPressConfig
)
from ..config.config_manager import ConfigManager

logger = logging.getLogger(__name__)


class ConfigDesigner:
    """Interactive configuration designer for multi-logo garments"""

    def __init__(self):
        if not CV2_AVAILABLE or tk is None:
            raise ImportError("GUI dependencies not available")

        self.root = tk.Tk()
        self.root.title("AlignPress v2 - Configuration Designer")
        self.root.geometry("1400x900")

        # Current state
        self.current_image: Optional[np.ndarray] = None
        self.current_config: Optional[AlignPressConfig] = None
        self.current_style: Optional[Style] = None
        self.selected_logo: Optional[Logo] = None

        # UI components
        self.image_canvas = None
        self.logo_list = None
        self.property_frame = None

        # Visualization state
        self.canvas_scale = 1.0
        self.roi_rectangles = {}  # logo_id -> rectangle_id
        self.position_markers = {}  # logo_id -> marker_id

        self._setup_ui()
        logger.info("ConfigDesigner initialized")

    def _setup_ui(self):
        """Setup the user interface"""
        # Main layout
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left panel - Image and controls
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Right panel - Configuration
        right_frame = ttk.Frame(main_frame, width=400)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        right_frame.pack_propagate(False)

        self._setup_image_panel(left_frame)
        self._setup_config_panel(right_frame)
        self._setup_menu()

    def _setup_menu(self):
        """Setup menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Archivo", menu=file_menu)
        file_menu.add_command(label="Cargar Imagen", command=self._load_image)
        file_menu.add_command(label="Cargar Configuración", command=self._load_config)
        file_menu.add_separator()
        file_menu.add_command(label="Guardar Configuración", command=self._save_config)
        file_menu.add_command(label="Exportar YAML", command=self._export_yaml)

        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Herramientas", menu=tools_menu)
        tools_menu.add_command(label="Calibrar Escala", command=self._calibrate_scale)
        tools_menu.add_command(label="Generar Variantes", command=self._generate_variants)
        tools_menu.add_command(label="Probar Detección", command=self._test_detection)

    def _setup_image_panel(self, parent):
        """Setup image display panel"""
        # Toolbar
        toolbar = ttk.Frame(parent)
        toolbar.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(toolbar, text="Cargar Imagen",
                  command=self._load_image).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(toolbar, text="Ajustar Zoom",
                  command=self._fit_image).pack(side=tk.LEFT, padx=(0, 10))

        # Canvas with scrollbars
        canvas_frame = ttk.Frame(parent)
        canvas_frame.pack(fill=tk.BOTH, expand=True)

        self.image_canvas = tk.Canvas(canvas_frame, bg="gray")
        v_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.image_canvas.yview)
        h_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL, command=self.image_canvas.xview)

        self.image_canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        self.image_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        # Bind mouse events for interactive editing
        self.image_canvas.bind("<Button-1>", self._on_canvas_click)
        self.image_canvas.bind("<B1-Motion>", self._on_canvas_drag)
        self.image_canvas.bind("<ButtonRelease-1>", self._on_canvas_release)

    def _setup_config_panel(self, parent):
        """Setup configuration panel"""
        # Style information
        style_frame = ttk.LabelFrame(parent, text="Información del Estilo")
        style_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(style_frame, text="ID:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.style_id_var = tk.StringVar()
        ttk.Entry(style_frame, textvariable=self.style_id_var).grid(row=0, column=1, sticky=tk.EW, padx=5, pady=2)

        ttk.Label(style_frame, text="Nombre:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.style_name_var = tk.StringVar()
        ttk.Entry(style_frame, textvariable=self.style_name_var).grid(row=1, column=1, sticky=tk.EW, padx=5, pady=2)

        style_frame.columnconfigure(1, weight=1)

        # Logo list
        logo_frame = ttk.LabelFrame(parent, text="Logos")
        logo_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Logo list with scrollbar
        list_frame = ttk.Frame(logo_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.logo_list = tk.Listbox(list_frame, height=8)
        logo_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.logo_list.yview)
        self.logo_list.configure(yscrollcommand=logo_scrollbar.set)

        self.logo_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        logo_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.logo_list.bind('<<ListboxSelect>>', self._on_logo_select)

        # Logo buttons
        button_frame = ttk.Frame(logo_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=(0, 5))

        ttk.Button(button_frame, text="Agregar Logo",
                  command=self._add_logo).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Eliminar",
                  command=self._remove_logo).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Duplicar",
                  command=self._duplicate_logo).pack(side=tk.LEFT)

        # Logo properties
        self._setup_logo_properties(parent)

    def _setup_logo_properties(self, parent):
        """Setup logo properties panel"""
        self.property_frame = ttk.LabelFrame(parent, text="Propiedades del Logo")
        self.property_frame.pack(fill=tk.X)

        # Logo ID and Name
        ttk.Label(self.property_frame, text="ID:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.logo_id_var = tk.StringVar()
        ttk.Entry(self.property_frame, textvariable=self.logo_id_var).grid(row=0, column=1, sticky=tk.EW, padx=5, pady=2)

        ttk.Label(self.property_frame, text="Nombre:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.logo_name_var = tk.StringVar()
        ttk.Entry(self.property_frame, textvariable=self.logo_name_var).grid(row=1, column=1, sticky=tk.EW, padx=5, pady=2)

        # Position
        ttk.Label(self.property_frame, text="Posición X (mm):").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.pos_x_var = tk.StringVar()
        ttk.Entry(self.property_frame, textvariable=self.pos_x_var).grid(row=2, column=1, sticky=tk.EW, padx=5, pady=2)

        ttk.Label(self.property_frame, text="Posición Y (mm):").grid(row=3, column=0, sticky=tk.W, padx=5, pady=2)
        self.pos_y_var = tk.StringVar()
        ttk.Entry(self.property_frame, textvariable=self.pos_y_var).grid(row=3, column=1, sticky=tk.EW, padx=5, pady=2)

        # Tolerance
        ttk.Label(self.property_frame, text="Tolerancia (mm):").grid(row=4, column=0, sticky=tk.W, padx=5, pady=2)
        self.tolerance_var = tk.StringVar()
        ttk.Entry(self.property_frame, textvariable=self.tolerance_var).grid(row=4, column=1, sticky=tk.EW, padx=5, pady=2)

        # Detector type
        ttk.Label(self.property_frame, text="Detector:").grid(row=5, column=0, sticky=tk.W, padx=5, pady=2)
        self.detector_var = tk.StringVar()
        detector_combo = ttk.Combobox(self.property_frame, textvariable=self.detector_var,
                                     values=["contour", "aruco", "template"])
        detector_combo.grid(row=5, column=1, sticky=tk.EW, padx=5, pady=2)

        self.property_frame.columnconfigure(1, weight=1)

        # Update button
        ttk.Button(self.property_frame, text="Actualizar Logo",
                  command=self._update_logo).grid(row=6, column=0, columnspan=2, pady=10)

    def _load_image(self):
        """Load an image for configuration"""
        if not CV2_AVAILABLE:
            messagebox.showerror("Error", "OpenCV no disponible")
            return

        filename = filedialog.askopenfilename(
            title="Seleccionar imagen",
            filetypes=[
                ("Imágenes", "*.jpg *.jpeg *.png *.bmp"),
                ("Todos los archivos", "*.*")
            ]
        )

        if filename:
            try:
                self.current_image = cv2.imread(filename)
                if self.current_image is None:
                    raise ValueError("No se pudo cargar la imagen")

                self._display_image()
                logger.info(f"Imagen cargada: {filename}")

            except Exception as e:
                messagebox.showerror("Error", f"Error cargando imagen: {e}")

    def _display_image(self):
        """Display current image on canvas"""
        if self.current_image is None:
            return

        # Convert BGR to RGB
        image_rgb = cv2.cvtColor(self.current_image, cv2.COLOR_BGR2RGB)

        # Calculate scale to fit canvas
        canvas_width = self.image_canvas.winfo_width()
        canvas_height = self.image_canvas.winfo_height()

        if canvas_width <= 1 or canvas_height <= 1:
            # Canvas not ready yet
            self.root.after(100, self._display_image)
            return

        img_height, img_width = image_rgb.shape[:2]

        scale_x = canvas_width / img_width
        scale_y = canvas_height / img_height
        self.canvas_scale = min(scale_x, scale_y) * 0.9  # Leave some margin

        # Resize image
        new_width = int(img_width * self.canvas_scale)
        new_height = int(img_height * self.canvas_scale)

        image_resized = cv2.resize(image_rgb, (new_width, new_height))

        # Convert to PIL and then to PhotoImage
        pil_image = Image.fromarray(image_resized)
        self.photo_image = ImageTk.PhotoImage(pil_image)

        # Clear canvas and display image
        self.image_canvas.delete("all")
        self.image_canvas.create_image(
            new_width // 2, new_height // 2,
            image=self.photo_image,
            tags="background"
        )

        # Update canvas scroll region
        self.image_canvas.configure(scrollregion=self.image_canvas.bbox("all"))

        # Redraw logos if any
        self._draw_logos()

    def _draw_logos(self):
        """Draw logo markers and ROIs on canvas"""
        if not self.current_style or not self.current_image.any():
            return

        # Clear existing markers
        for marker_id in self.position_markers.values():
            self.image_canvas.delete(marker_id)
        for rect_id in self.roi_rectangles.values():
            self.image_canvas.delete(rect_id)

        self.position_markers.clear()
        self.roi_rectangles.clear()

        # Draw each logo
        for logo in self.current_style.logos:
            self._draw_single_logo(logo)

    def _draw_single_logo(self, logo: Logo):
        """Draw a single logo marker and ROI"""
        # Convert mm to pixels (mock conversion for now)
        x_px = logo.position_mm.x * self.canvas_scale
        y_px = logo.position_mm.y * self.canvas_scale

        # Draw position marker (crosshair)
        size = 10
        color = "red" if logo == self.selected_logo else "blue"

        # Crosshair lines
        line1 = self.image_canvas.create_line(
            x_px - size, y_px, x_px + size, y_px,
            fill=color, width=2, tags=f"logo_{logo.id}"
        )
        line2 = self.image_canvas.create_line(
            x_px, y_px - size, x_px, y_px + size,
            fill=color, width=2, tags=f"logo_{logo.id}"
        )

        # ROI rectangle
        roi_x = logo.roi.x * self.canvas_scale
        roi_y = logo.roi.y * self.canvas_scale
        roi_w = logo.roi.width * self.canvas_scale
        roi_h = logo.roi.height * self.canvas_scale

        rect = self.image_canvas.create_rectangle(
            roi_x, roi_y, roi_x + roi_w, roi_y + roi_h,
            outline=color, width=1, tags=f"logo_{logo.id}"
        )

        # Text label
        text = self.image_canvas.create_text(
            x_px + 15, y_px - 15,
            text=logo.name, fill=color, font=("Arial", 9),
            tags=f"logo_{logo.id}"
        )

        self.position_markers[logo.id] = [line1, line2, text]
        self.roi_rectangles[logo.id] = rect

    def _on_canvas_click(self, event):
        """Handle canvas click events"""
        if not self.selected_logo:
            return

        # Convert canvas coordinates to image coordinates
        canvas_x = self.image_canvas.canvasx(event.x)
        canvas_y = self.image_canvas.canvasy(event.y)

        # Update logo position
        img_x = canvas_x / self.canvas_scale
        img_y = canvas_y / self.canvas_scale

        self.selected_logo.position_mm = Point(img_x, img_y)

        # Update UI
        self._update_property_fields()
        self._draw_logos()

    def _on_canvas_drag(self, event):
        """Handle canvas drag events"""
        # For now, same as click
        self._on_canvas_click(event)

    def _on_canvas_release(self, event):
        """Handle canvas mouse release"""
        pass

    def _add_logo(self):
        """Add a new logo"""
        if not self.current_style:
            self.current_style = Style(
                id=self.style_id_var.get() or "new_style",
                name=self.style_name_var.get() or "Nuevo Estilo",
                logos=[]
            )

        # Create new logo with default values
        logo_id = f"logo_{len(self.current_style.logos) + 1}"
        new_logo = Logo(
            id=logo_id,
            name=f"Logo {len(self.current_style.logos) + 1}",
            position_mm=Point(100, 100),
            tolerance_mm=3.0,
            detector_type="contour",
            roi=Rectangle(80, 80, 40, 40)
        )

        self.current_style.logos.append(new_logo)
        self._update_logo_list()

        # Select the new logo
        self.logo_list.selection_set(len(self.current_style.logos) - 1)
        self._on_logo_select(None)

    def _remove_logo(self):
        """Remove selected logo"""
        selection = self.logo_list.curselection()
        if not selection or not self.current_style:
            return

        index = selection[0]
        removed_logo = self.current_style.logos.pop(index)

        # Clean up UI references
        if removed_logo.id in self.position_markers:
            for marker_id in self.position_markers[removed_logo.id]:
                self.image_canvas.delete(marker_id)
            del self.position_markers[removed_logo.id]

        if removed_logo.id in self.roi_rectangles:
            self.image_canvas.delete(self.roi_rectangles[removed_logo.id])
            del self.roi_rectangles[removed_logo.id]

        self.selected_logo = None
        self._update_logo_list()
        self._clear_property_fields()

    def _duplicate_logo(self):
        """Duplicate selected logo"""
        selection = self.logo_list.curselection()
        if not selection or not self.current_style:
            return

        index = selection[0]
        original_logo = self.current_style.logos[index]

        # Create duplicate with offset position
        new_logo = Logo(
            id=f"{original_logo.id}_copy",
            name=f"{original_logo.name} (Copia)",
            position_mm=Point(
                original_logo.position_mm.x + 20,
                original_logo.position_mm.y + 20
            ),
            tolerance_mm=original_logo.tolerance_mm,
            detector_type=original_logo.detector_type,
            roi=Rectangle(
                original_logo.roi.x + 20,
                original_logo.roi.y + 20,
                original_logo.roi.width,
                original_logo.roi.height
            )
        )

        self.current_style.logos.append(new_logo)
        self._update_logo_list()
        self._draw_logos()

    def _on_logo_select(self, event):
        """Handle logo selection"""
        selection = self.logo_list.curselection()
        if not selection or not self.current_style:
            self.selected_logo = None
            self._clear_property_fields()
            return

        index = selection[0]
        self.selected_logo = self.current_style.logos[index]
        self._update_property_fields()
        self._draw_logos()  # Redraw to highlight selected logo

    def _update_property_fields(self):
        """Update property fields with selected logo data"""
        if not self.selected_logo:
            return

        self.logo_id_var.set(self.selected_logo.id)
        self.logo_name_var.set(self.selected_logo.name)
        self.pos_x_var.set(str(self.selected_logo.position_mm.x))
        self.pos_y_var.set(str(self.selected_logo.position_mm.y))
        self.tolerance_var.set(str(self.selected_logo.tolerance_mm))
        self.detector_var.set(self.selected_logo.detector_type)

    def _clear_property_fields(self):
        """Clear property fields"""
        self.logo_id_var.set("")
        self.logo_name_var.set("")
        self.pos_x_var.set("")
        self.pos_y_var.set("")
        self.tolerance_var.set("")
        self.detector_var.set("")

    def _update_logo(self):
        """Update selected logo with property field values"""
        if not self.selected_logo:
            return

        try:
            self.selected_logo.id = self.logo_id_var.get()
            self.selected_logo.name = self.logo_name_var.get()
            self.selected_logo.position_mm = Point(
                float(self.pos_x_var.get()),
                float(self.pos_y_var.get())
            )
            self.selected_logo.tolerance_mm = float(self.tolerance_var.get())
            self.selected_logo.detector_type = self.detector_var.get()

            self._update_logo_list()
            self._draw_logos()

        except ValueError as e:
            messagebox.showerror("Error", f"Valores inválidos: {e}")

    def _update_logo_list(self):
        """Update the logo list display"""
        self.logo_list.delete(0, tk.END)

        if self.current_style:
            for i, logo in enumerate(self.current_style.logos):
                self.logo_list.insert(i, f"{logo.id} - {logo.name}")

    def _fit_image(self):
        """Fit image to canvas"""
        if self.current_image is not None:
            self._display_image()

    def _load_config(self):
        """Load configuration from file"""
        filename = filedialog.askopenfilename(
            title="Cargar configuración",
            filetypes=[
                ("YAML files", "*.yaml *.yml"),
                ("JSON files", "*.json"),
                ("Todos los archivos", "*.*")
            ]
        )

        if filename:
            try:
                config_manager = ConfigManager(Path(filename))
                self.current_config = config_manager.load()

                # Load first style if available
                if self.current_config.library.styles:
                    self.current_style = self.current_config.library.styles[0]
                    self.style_id_var.set(self.current_style.id)
                    self.style_name_var.set(self.current_style.name)
                    self._update_logo_list()
                    self._draw_logos()

                messagebox.showinfo("Éxito", "Configuración cargada correctamente")

            except Exception as e:
                messagebox.showerror("Error", f"Error cargando configuración: {e}")

    def _save_config(self):
        """Save current configuration"""
        if not self.current_style:
            messagebox.showwarning("Advertencia", "No hay estilo para guardar")
            return

        filename = filedialog.asksaveasfilename(
            title="Guardar configuración",
            defaultextension=".yaml",
            filetypes=[
                ("YAML files", "*.yaml"),
                ("JSON files", "*.json"),
                ("Todos los archivos", "*.*")
            ]
        )

        if filename:
            try:
                # Update style with current UI values
                self.current_style.id = self.style_id_var.get()
                self.current_style.name = self.style_name_var.get()

                # Create or update config
                if not self.current_config:
                    self.current_config = create_default_config()

                # Update or add style
                existing_style_index = None
                for i, style in enumerate(self.current_config.library.styles):
                    if style.id == self.current_style.id:
                        existing_style_index = i
                        break

                if existing_style_index is not None:
                    self.current_config.library.styles[existing_style_index] = self.current_style
                else:
                    self.current_config.library.styles.append(self.current_style)

                # Save to file
                config_manager = ConfigManager(Path(filename))
                config_manager.save(self.current_config)

                messagebox.showinfo("Éxito", "Configuración guardada correctamente")

            except Exception as e:
                messagebox.showerror("Error", f"Error guardando configuración: {e}")

    def _export_yaml(self):
        """Export current style as YAML"""
        if not self.current_style:
            messagebox.showwarning("Advertencia", "No hay estilo para exportar")
            return

        filename = filedialog.asksaveasfilename(
            title="Exportar YAML",
            defaultextension=".yaml",
            filetypes=[("YAML files", "*.yaml"), ("Todos los archivos", "*.*")]
        )

        if filename:
            try:
                import yaml

                style_dict = asdict(self.current_style)

                with open(filename, 'w', encoding='utf-8') as f:
                    yaml.dump(style_dict, f, default_flow_style=False,
                             allow_unicode=True, indent=2)

                messagebox.showinfo("Éxito", "YAML exportado correctamente")

            except Exception as e:
                messagebox.showerror("Error", f"Error exportando YAML: {e}")

    def _calibrate_scale(self):
        """Calibrate scale using known measurement"""
        # Placeholder for scale calibration
        messagebox.showinfo("Info", "Calibración de escala no implementada aún")

    def _generate_variants(self):
        """Generate size variants"""
        # Placeholder for variant generation
        messagebox.showinfo("Info", "Generación de variantes no implementada aún")

    def _test_detection(self):
        """Test detection with current configuration"""
        # Placeholder for detection testing
        messagebox.showinfo("Info", "Prueba de detección no implementada aún")

    def run(self):
        """Run the configuration designer"""
        self.root.mainloop()


def main():
    """Main entry point for configuration designer"""
    if not CV2_AVAILABLE:
        print("Error: Dependencias de GUI no disponibles")
        print("Instala: pip install opencv-python pillow")
        return

    try:
        app = ConfigDesigner()
        app.run()
    except Exception as e:
        print(f"Error ejecutando Configuration Designer: {e}")


if __name__ == "__main__":
    main()