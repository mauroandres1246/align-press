"""
Configuration Designer Tool for AlignPress v2

Interactive tool for creating and testing multi-logo garment configurations
"""
from __future__ import annotations

import logging
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import asdict

try:
    import cv2
    import numpy as np
    from PIL import Image, ImageTk, ImageDraw
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox, simpledialog
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

# Import new specialized classes - Phase 2 Extract Class Pattern
from .preset_manager import PresetManager
from .image_processor import ImageProcessor
from .ruler_grid_system import RulerGridSystem
from .ui_manager import UIManager

# Import Phase 3 Strangler Fig Pattern classes
from .variant_generator import VariantGenerator
from .template_overlay_manager import TemplateOverlayManager

logger = logging.getLogger(__name__)


class ConfigDesigner:
    """Interactive configuration designer for multi-logo garments"""

    # Constants for refactoring - Phase 1
    MM_TO_INCH = 25.4  # Conversion factor mm to inches
    DEFAULT_DPI = 300  # Default DPI for calculations
    RULER_WIDTH = 40   # Horizontal ruler width in pixels
    RULER_HEIGHT = 30  # Vertical ruler height in pixels
    MIN_RULER_SPACING = 20  # Minimum spacing for rulers
    MIN_GRID_SPACING = 15   # Minimum spacing for grid
    GRID_COLOR = "#DDDDDD"  # Grid line color
    RULER_BG_COLOR = "#F5F5F5"  # Ruler background color
    RULER_BORDER_COLOR = "#999999"  # Ruler border color

    def __init__(self):
        if not CV2_AVAILABLE or tk is None:
            raise ImportError("GUI dependencies not available")

        self.root = tk.Tk()
        self.root.title("AlignPress v2 - Configuration Designer")
        self.root.geometry("1400x900")

        # Core application state
        self.current_config: Optional[AlignPressConfig] = None
        self.current_style: Optional[Style] = None
        self.calibration_data: Optional[Dict] = None
        self.mm_per_pixel: float = 1.0  # Default fallback

        # Hierarchical configuration state
        self.current_design: str = ""  # e.g., "ComunicacionesFutbol"
        self.current_size: str = ""    # e.g., "TallaM"
        self.current_part: str = ""    # e.g., "delantera"

        # Initialize specialized managers - Phase 2 Architecture
        self.preset_manager = PresetManager(Path("./configs"))
        self.image_processor = ImageProcessor()
        self.ui_manager = UIManager(self.root)

        # Initialize Phase 3 Strangler Fig Pattern managers
        self.variant_generator = VariantGenerator(self.root)
        self.template_overlay_manager = TemplateOverlayManager()

        # Logo selection state
        self.selected_logo_index: Optional[int] = None
        self.editing_mode: str = "none"  # "template", "logo", "none"

        # Template interaction state
        self.selected_template_id: Optional[str] = None
        self.dragging_template: bool = False
        self.dragging_logo: bool = False
        self.updating_from_drag: bool = False
        self.drag_start_pos: Optional[tuple] = None

        # Canvas and visualization
        self.image_canvas = None
        self.ruler_grid_system: Optional[RulerGridSystem] = None
        self.roi_rectangles = {}  # logo_id -> rectangle_id
        self.position_markers = {}  # logo_id -> marker_id

        # Image state variables
        self.current_image = None  # Current loaded image
        self.canvas_scale: float = 1.0  # Canvas zoom scale factor

        # Ruler and grid configuration
        self.ruler_spacing_mm: float = 10.0  # Default ruler spacing in mm
        self.grid_spacing_mm: float = 5.0    # Default grid spacing in mm

        # Template system (preserved for compatibility)
        self.template_positions: Dict[str, Dict] = {}

        # UI Components initialization (to avoid AttributeError)
        self.calib_status_label = None
        self.calib_factor_label = None
        self.template_info_label = None
        self.template_size_label = None
        self.template_status_label = None
        self.logo_list = None
        self.design_var = None
        self.size_var = None
        self.part_var = None
        self.design_combo = None
        self.size_combo = None
        self.part_combo = None
        self.save_path_label = None
        self.config_status_label = None

        # Configuration and template system variables
        self.config_root_path = Path("./configs")
        self.logo_templates = {}  # Template cache
        self.template_references = {}  # Template metadata cache

        # Setup UI and register callbacks
        self._setup_ui()
        self._register_ui_callbacks()

        logger.info("ConfigDesigner initialized with new architecture")

    def _register_ui_callbacks(self):
        """Register callbacks for UI events with new architecture"""
        # Image operations
        self.ui_manager.register_callback("load_image", self._load_image)

        # Preset operations
        self.ui_manager.register_callback("load_preset", self._load_preset_with_manager)
        self.ui_manager.register_callback("save_preset", self._save_preset_with_manager)

        # Configuration operations
        self.ui_manager.register_callback("new_config", self._new_configuration)
        self.ui_manager.register_callback("load_config", self._load_config)
        self.ui_manager.register_callback("save_config", self._save_config)

        # Design/Size/Part operations
        self.ui_manager.register_callback("on_design_changed", self._on_design_changed)
        self.ui_manager.register_callback("on_design_typed", self._on_design_typed)
        self.ui_manager.register_callback("on_size_changed", self._on_size_changed)
        self.ui_manager.register_callback("on_size_typed", self._on_size_typed)
        self.ui_manager.register_callback("on_part_changed", self._on_part_changed)
        self.ui_manager.register_callback("on_part_typed", self._on_part_typed)
        self.ui_manager.register_callback("new_design", self._new_design)
        self.ui_manager.register_callback("new_size", self._new_size)
        self.ui_manager.register_callback("new_part", self._new_part)

        # Logo operations
        self.ui_manager.register_callback("on_logo_select", self._on_logo_select)
        self.ui_manager.register_callback("add_logo", self._add_logo_dialog)
        self.ui_manager.register_callback("remove_logo", self._remove_logo)

        # Visual controls
        self.ui_manager.register_callback("toggle_rulers", self._toggle_rulers)
        self.ui_manager.register_callback("toggle_grid", self._toggle_grid)

        # Position controls
        self.ui_manager.register_callback("on_position_changed", self._update_logo_from_position_panel)
        self.ui_manager.register_callback("on_size_changed", self._update_logo_from_position_panel)

        # Tools
        self.ui_manager.register_callback("generate_variants", self._generate_variants_with_generator)
        self.ui_manager.register_callback("export_yaml", self._export_yaml)

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
        self._setup_config_panel_refactored(right_frame)
        self._setup_menu()

    def _setup_menu(self):
        """Setup menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Archivo", menu=file_menu)
        file_menu.add_command(label="Cargar Imagen de Prenda", command=self._load_image)
        file_menu.add_command(label="Cargar Calibración", command=self._load_calibration)
        file_menu.add_separator()
        file_menu.add_command(label="Cargar Configuración", command=self._load_config)
        file_menu.add_command(label="Guardar Configuración", command=self._save_config)
        file_menu.add_separator()
        file_menu.add_command(label="Guardar Configuración Jerárquica", command=self._save_current_configuration)
        file_menu.add_command(label="Exportar YAML", command=self._export_yaml)

        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Herramientas", menu=tools_menu)
        tools_menu.add_command(label="Generar Variantes de Talla", command=self._generate_variants_with_generator)
        tools_menu.add_command(label="Probar Detección", command=self._test_detection)
        tools_menu.add_command(label="Vista Previa de ROIs", command=self._preview_rois)
        tools_menu.add_command(label="Exportar Debug Image", command=self._export_debug_image)

    def _setup_image_panel(self, parent):
        """Setup image display panel"""
        # Toolbar
        toolbar = ttk.Frame(parent)
        toolbar.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(toolbar, text="Cargar Imagen",
                  command=self._load_image).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="Cargar Calibración",
                  command=self._load_calibration).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="Ajustar Zoom",
                  command=self._fit_image).pack(side=tk.LEFT, padx=(0, 5))

        # Visual enhancements controls
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, fill=tk.Y)

        self.rulers_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(toolbar, text="Reglas", variable=self.rulers_var,
                       command=self._toggle_rulers).pack(side=tk.LEFT, padx=(0, 5))

        self.grid_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(toolbar, text="Grid", variable=self.grid_var,
                       command=self._toggle_grid).pack(side=tk.LEFT, padx=(0, 5))

        # Calibration status
        self.calibration_label = ttk.Label(toolbar, text="Sin calibración", foreground="red")
        self.calibration_label.pack(side=tk.RIGHT, padx=(10, 0))

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
        self.image_canvas.bind("<Motion>", self._on_canvas_motion)

        # Tooltip for dimensions
        self.tooltip_label = None

    def _setup_preset_configuration_section(self, parent):
        """
        Setup preset configuration selector section

        Phase 3 Strangler Fig Pattern - Extracted method
        """
        preset_frame = ttk.LabelFrame(parent, text="📋 Configuración de Preset")
        preset_frame.pack(fill=tk.X, pady=(0, 10))

        # Initialize UI variables
        self.design_var = tk.StringVar()
        self.design_combo = ttk.Combobox(preset_frame, textvariable=self.design_var, width=20)

        self.size_var = tk.StringVar()
        self.size_combo = ttk.Combobox(preset_frame, textvariable=self.size_var, width=20)

        self.part_var = tk.StringVar()
        self.part_combo = ttk.Combobox(preset_frame, textvariable=self.part_var, width=20)

        # Design selector with smart dropdown
        self._create_selector_row(preset_frame, 0, "Diseño:", self.design_var, self.design_combo,
                                 "Nuevo", self._new_design, self._on_design_changed, self._on_design_typed)

        # Size selector with smart dropdown
        self._create_selector_row(preset_frame, 1, "Talla:", self.size_var, self.size_combo,
                                 "Nueva", self._new_size, self._on_size_changed, self._on_size_typed)

        # Part selector with smart dropdown
        self._create_selector_row(preset_frame, 2, "Parte:", self.part_var, self.part_combo,
                                 "Nueva", self._new_part, self._on_part_changed, self._on_part_typed)

        # Save path preview with better formatting
        path_frame = ttk.Frame(preset_frame)
        path_frame.pack(fill=tk.X, padx=8, pady=(12, 8))

        self.save_path_label = ttk.Label(path_frame, text="💾 Se guardará en: (selecciona opciones arriba)",
                                       foreground="blue", font=("TkDefaultFont", 8), wraplength=350)
        self.save_path_label.pack(fill=tk.X)

        # Action buttons
        self._create_preset_action_buttons(preset_frame)

        # Configuration status with better spacing
        status_frame = ttk.Frame(preset_frame)
        status_frame.pack(fill=tk.X, padx=8, pady=(5, 8))

        self.config_status_label = ttk.Label(status_frame, text="Estado: Selecciona o crea configuración",
                                           foreground="orange", font=("TkDefaultFont", 8))
        self.config_status_label.pack(fill=tk.X)
        return preset_frame

    def _create_selector_row(self, parent, row, label_text, var, combo, button_text, button_command,
                           select_callback, type_callback):
        """Create a perfectly aligned selector row with fixed positioning"""
        row_frame = ttk.Frame(parent)
        row_frame.pack(fill=tk.X, padx=8, pady=3)

        # Create three sections with fixed proportions
        # Label section - fixed width
        label_frame = ttk.Frame(row_frame, width=80)
        label_frame.pack(side=tk.LEFT, fill=tk.Y)
        label_frame.pack_propagate(False)  # Maintain fixed width

        label = ttk.Label(label_frame, text=label_text, anchor=tk.W)
        label.pack(fill=tk.BOTH, padx=(0, 5))

        # Combobox section - expandable
        combo_frame = ttk.Frame(row_frame)
        combo_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        combo.configure(width=1)  # Minimal width, will expand with frame
        combo.pack(fill=tk.X)

        # Button section - fixed width
        button_frame = ttk.Frame(row_frame, width=90)
        button_frame.pack(side=tk.RIGHT, fill=tk.Y)
        button_frame.pack_propagate(False)  # Maintain fixed width

        button = ttk.Button(button_frame, text=f"+ {button_text}")
        button.configure(command=button_command)
        button.pack(fill=tk.BOTH)

        combo.bind('<<ComboboxSelected>>', select_callback)
        combo.bind('<KeyRelease>', type_callback)

    def _create_preset_action_buttons(self, parent):
        """Create beautifully spaced preset action buttons"""
        action_frame = ttk.Frame(parent)
        action_frame.pack(fill=tk.X, padx=8, pady=(8, 5))

        # Center the buttons with proper spacing
        button_container = ttk.Frame(action_frame)
        button_container.pack(anchor=tk.CENTER)

        ttk.Button(button_container, text="📂 Cargar Preset",
                  command=self._load_preset, width=15).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_container, text="💾 Guardar Preset",
                  command=self._save_preset, width=15).pack(side=tk.LEFT)

    def _setup_calibration_section(self, parent):
        """
        Setup beautifully spaced calibration information section

        Phase 3 Strangler Fig Pattern - Extracted method
        """
        calib_frame = ttk.LabelFrame(parent, text="📏 Calibración")
        calib_frame.pack(fill=tk.X, pady=(0, 10))

        # Status with consistent padding
        self.calib_status_label = ttk.Label(calib_frame, text="Estado: Sin calibrar", foreground="red",
                                          font=("TkDefaultFont", 9))
        self.calib_status_label.pack(fill=tk.X, padx=8, pady=(6, 2))

        # Factor with consistent padding
        self.calib_factor_label = ttk.Label(calib_frame, text="Factor: N/A",
                                          font=("TkDefaultFont", 9))
        self.calib_factor_label.pack(fill=tk.X, padx=8, pady=(2, 6))

        return calib_frame

    def _setup_logo_list_section(self, parent):
        """
        Setup beautifully designed logo list section

        Phase 3 Strangler Fig Pattern - Extracted method
        """
        logo_frame = ttk.LabelFrame(parent, text="📝 Lista de Logos")
        logo_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Logo list with scrollbar - optimized height
        list_frame = ttk.Frame(logo_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=6)

        self.logo_list = tk.Listbox(list_frame, height=6, font=("TkDefaultFont", 9))
        logo_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.logo_list.yview)
        self.logo_list.configure(yscrollcommand=logo_scrollbar.set)

        self.logo_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        logo_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.logo_list.bind('<<ListboxSelect>>', self._on_logo_select)

        # Centered logo control buttons with better spacing
        button_frame = ttk.Frame(logo_frame)
        button_frame.pack(fill=tk.X, padx=8, pady=(6, 8))

        # Center the buttons
        button_container = ttk.Frame(button_frame)
        button_container.pack(anchor=tk.CENTER)

        ttk.Button(button_container, text="➕ Agregar Logo",
                  command=self._add_logo_dialog, width=14).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(button_container, text="➖ Eliminar Logo",
                  command=self._remove_logo, width=14).pack(side=tk.LEFT)

        return logo_frame

    def _setup_config_panel_refactored(self, parent):
        """
        Setup configuration panel using extracted methods

        Phase 3 Strangler Fig Pattern - New implementation
        """
        # Setup each section using extracted methods
        self._setup_preset_configuration_section(parent)
        self._setup_calibration_section(parent)
        self._setup_logo_list_section(parent)

        # Setup template panel
        self._setup_template_panel_refactored(parent)

    def _setup_template_info_section(self, parent):
        """
        Setup template information and instructions section

        Phase 3 Strangler Fig Pattern - Extracted method
        """
        # Clear instruction for template-first workflow
        instruction_label = ttk.Label(parent,
                                     text="Template flotante → Posicionar → Confirmar → Aparece en lista de logos",
                                     foreground="blue")
        instruction_label.pack(fill=tk.X, padx=5, pady=2)

        # Template info and preview
        info_frame = ttk.Frame(parent)
        info_frame.pack(fill=tk.X, padx=5, pady=2)

        self.template_info_label = ttk.Label(info_frame, text="📁 Sin template cargado", foreground="gray")
        self.template_info_label.pack(side=tk.LEFT)

        # Template size info
        self.template_size_label = ttk.Label(info_frame, text="", foreground="blue")
        self.template_size_label.pack(side=tk.RIGHT)

        # Load button
        load_button = ttk.Button(parent, text="📂 Cargar Logo",
                                command=self._load_and_show_template)
        load_button.pack(fill=tk.X, padx=5, pady=5)

        return parent

    def _setup_position_controls_section(self, parent):
        """
        Setup position controls section

        Phase 3 Strangler Fig Pattern - Extracted method
        """
        # Position controls (initially hidden) - works for both templates and logos
        self.position_frame = ttk.LabelFrame(parent, text="📐 Posición y Tamaño")

        # Dynamic editing indicator
        self.editing_indicator = ttk.Label(self.position_frame, text="", foreground="blue", font=("TkDefaultFont", 8))
        self.editing_indicator.pack(fill=tk.X, padx=5, pady=(5, 0))

        # Position fields
        self._create_position_fields(self.position_frame)

        # Size fields
        self._create_size_fields(self.position_frame)

        # Action buttons
        self._create_template_action_buttons(self.position_frame)

        return self.position_frame

    def _create_position_fields(self, parent):
        """Create X/Y position input fields"""
        pos_grid = ttk.Frame(parent)
        pos_grid.pack(fill=tk.X, padx=5, pady=5)

        # X position
        ttk.Label(pos_grid, text="X (mm):").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.pos_x_var = tk.DoubleVar()
        self.pos_x_entry = ttk.Entry(pos_grid, textvariable=self.pos_x_var, width=8)
        self.pos_x_entry.grid(row=0, column=1, padx=(0, 10))
        self.pos_x_var.trace('w', self._on_position_changed)

        # Y position
        ttk.Label(pos_grid, text="Y (mm):").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.pos_y_var = tk.DoubleVar()
        self.pos_y_entry = ttk.Entry(pos_grid, textvariable=self.pos_y_var, width=8)
        self.pos_y_entry.grid(row=0, column=3)
        self.pos_y_var.trace('w', self._on_position_changed)

    def _create_size_fields(self, parent):
        """Create width/height size input fields"""
        size_grid = ttk.Frame(parent)
        size_grid.pack(fill=tk.X, padx=5, pady=5)

        # Width
        ttk.Label(size_grid, text="Ancho (mm):").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.width_var = tk.DoubleVar()
        self.width_entry = ttk.Entry(size_grid, textvariable=self.width_var, width=8)
        self.width_entry.grid(row=0, column=1, padx=(0, 10))
        self.width_var.trace('w', self._on_size_changed)

        # Height
        ttk.Label(size_grid, text="Alto (mm):").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.height_var = tk.DoubleVar()
        self.height_entry = ttk.Entry(size_grid, textvariable=self.height_var, width=8)
        self.height_entry.grid(row=0, column=3)
        self.height_var.trace('w', self._on_size_changed)

    def _create_template_action_buttons(self, parent):
        """Create template action buttons"""
        action_frame = ttk.Frame(parent)
        action_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(action_frame, text="📍 Centrar en Imagen",
                  command=self._center_template).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(action_frame, text="✅ Confirmar Logo",
                  command=self._confirm_logo_at_current_position).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(action_frame, text="❌ Cancelar",
                  command=self._cancel_template).pack(side=tk.LEFT)

    def _setup_template_status_section(self, parent):
        """
        Setup template status section

        Phase 3 Strangler Fig Pattern - Extracted method
        """
        self.template_status_label = ttk.Label(parent, text="", foreground="green")
        self.template_status_label.pack(fill=tk.X, padx=5, pady=2)

        return self.template_status_label

    def _setup_template_panel_refactored(self, parent):
        """
        Setup simplified template panel using extracted methods

        Phase 3 Strangler Fig Pattern - New implementation
        """
        template_frame = ttk.LabelFrame(parent, text="➕ Crear Nuevo Logo")
        template_frame.pack(fill=tk.X, pady=(0, 10))

        # Setup each section using extracted methods
        self._setup_template_info_section(template_frame)
        self._setup_position_controls_section(template_frame)
        self._setup_template_status_section(template_frame)

        # Initialize preset system
        self._initialize_preset_system()

    def _initialize_preset_system(self):
        """Initialize the smart preset system"""
        self._update_design_options()
        self._update_save_path_preview()


    def _update_design_options(self):
        """Update design dropdown with existing designs"""
        designs, _, _ = self.preset_manager.scan_existing_presets()
        self.design_combo['values'] = designs

    def _update_part_options(self):
        """Update part dropdown based on selected design and size"""
        design = self.design_var.get()
        size = self.size_var.get()
        if not design or not size:
            self.part_combo['values'] = []
            return

        configs_dir = os.path.join(os.path.dirname(__file__), "..", "..", "configs")
        size_path = os.path.join(configs_dir, design, size)
        parts = []

        if os.path.exists(size_path):
            for f in os.listdir(size_path):
                if f.endswith('.json'):
                    parts.append(f[:-5])  # Remove .json extension

        # Add common parts if not present
        common_parts = ["delantera", "trasera", "manga_izquierda", "manga_derecha"]
        for part in common_parts:
            if part not in parts:
                parts.append(part)

        self.part_combo['values'] = sorted(parts)

    def _update_save_path_preview(self):
        """Update the save path preview label"""
        design = self.design_var.get()
        size = self.size_var.get()
        part = self.part_var.get()

        if design and size and part:
            path = f"configs/{design}/{size}/{part}.json"
            self.save_path_label.config(text=f"💾 Se guardará en: {path}", foreground="green")
        else:
            missing = []
            if not design: missing.append("Diseño")
            if not size: missing.append("Talla")
            if not part: missing.append("Parte")
            self.save_path_label.config(text=f"💾 Falta seleccionar: {', '.join(missing)}", foreground="orange")

    # New methods for "+ Nuevo" buttons
    def _new_design(self):
        """Create new design"""
        design = simpledialog.askstring("Nuevo Diseño",
                                       "Nombre del nuevo diseño:\n(ej: ComunicacionesFutbol, BarcelonaCamiseta)")
        if design:
            self.design_var.set(design)
            self._update_design_options()
            self._on_design_changed()

    def _new_size(self):
        """Create new size"""
        size = simpledialog.askstring("Nueva Talla",
                                    "Nombre de la nueva talla:\n(ej: TallaS, TallaM, TallaXL)")
        if size:
            self.size_var.set(size)
            self._update_size_options()
            self._on_size_changed()

    def _new_part(self):
        """Create new part"""
        parts = ["delantera", "trasera", "manga_izquierda", "manga_derecha", "cuello", "dobladillo"]

        # Show selection dialog
        part = simpledialog.askstring("Nueva Parte",
                                    f"Nombre de la nueva parte:\n\nComunes: {', '.join(parts[:4])}\nOtras: {', '.join(parts[4:])}\n\nO escribe una personalizada:")
        if part:
            self.part_var.set(part)
            self._update_part_options()
            self._on_part_changed()

    # Event handlers for smart dropdowns
    def _on_design_typed(self, event=None):
        """Handle typing in design field"""
        self._update_save_path_preview()

    def _on_size_changed(self, event=None):
        """Handle size selection change"""
        self._update_part_options()
        self.part_var.set("")  # Clear part when size changes
        self._update_save_path_preview()

    def _on_size_typed(self, event=None):
        """Handle typing in size field"""
        self._update_save_path_preview()

    def _on_part_changed(self, event=None):
        """Handle part selection change"""
        self._update_save_path_preview()

    def _on_part_typed(self, event=None):
        """Handle typing in part field"""
        self._update_save_path_preview()

    def _refresh_preset_dropdowns(self):
        """Refresh dropdown options after loading a preset"""
        # Update design options to include current selection
        self._update_design_options()

        # Update size options for current design
        self._update_size_options()

        # Update part options for current design/size
        self._update_part_options()

        # Update save path preview
        self._update_save_path_preview()

    def _load_preset_file(self):
        """Load and parse preset file data"""
        configs_dir = os.path.join(os.path.dirname(__file__), "..", "..", "configs")

        if not os.path.exists(configs_dir):
            messagebox.showwarning("Sin Presets", "No hay presets guardados aún.")
            return None, None

        config_path = filedialog.askopenfilename(
            title="Seleccionar Preset",
            initialdir=configs_dir,
            filetypes=[("Archivos de configuración", "*.json"), ("Todos los archivos", "*.*")]
        )

        if not config_path:
            return None, None

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            return config_data, config_path
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar preset: {str(e)}")
            return None, None



    def _update_ui_after_preset_load(self, design, size, part, logos_count):
        """Update UI elements after successful preset load"""
        self._update_logo_list()
        self._display_image()

        # Update status
        self.config_status_label.config(
            text=f"✅ Preset cargado: {design}/{size}/{part} ({logos_count} logos)",
            foreground="green"
        )

        messagebox.showinfo("Preset Cargado",
                          f"Preset cargado exitosamente:\n\n" +
                          f"📁 Diseño: {design}\n" +
                          f"📏 Talla: {size}\n" +
                          f"🧩 Parte: {part}\n" +
                          f"🎯 Logos: {logos_count}")

    def _load_preset(self):
        """Interactive preset loading with file browser - Refactored for clarity"""
        # Load preset file data
        config_data, config_path = self._load_preset_file()
        if not config_data or not config_path:
            return

        try:
            # Extract metadata using PresetManager (Phase 3 Migration)
            design, size, part = self.preset_manager.extract_preset_metadata(config_data, config_path)

            # Update UI dropdowns
            self.design_var.set(design)
            self.size_var.set(size)
            self.part_var.set(part)
            self._refresh_preset_dropdowns()

            # Initialize or update style
            if not self.current_style:
                self.current_style = Style(
                    id=f"{design}_{size}_{part}",
                    name=f"{design} {size} {part}",
                    logos=[]
                )

            # Load logos using PresetManager (Phase 3 Migration)
            self.current_style.logos = self.preset_manager.create_logos_from_config(config_data)

            # Load calibration if available
            if 'calibration_factor' in config_data:
                self.mm_per_pixel = config_data['calibration_factor']

            # Initialize config if needed
            from alignpress_v2.config.models import AlignPressConfig, LibraryData
            if not self.current_config:
                self.current_config = AlignPressConfig(library=LibraryData(styles=[]))

            # Ensure the loaded style is in the config
            self.current_config.library.styles = [self.current_style]

            # Update current configuration variables
            self.current_design = design
            self.current_size = size
            self.current_part = part

            # Update UI
            self._update_ui_after_preset_load(design, size, part, len(self.current_style.logos))

        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar preset: {str(e)}")


    def _prepare_preset_config_data(self, design, size, part):
        """Prepare configuration data for saving"""
        config_data = {
            "design": design,
            "size": size,
            "part": part,
            "calibration_factor": self.mm_per_pixel,
            "logos": []
        }

        # Convert logos to dict format
        for logo in self.current_style.logos:
            logo_data = {
                "id": logo.id,
                "name": logo.name,
                "position_mm": {"x": logo.position_mm.x, "y": logo.position_mm.y},
                "roi": {
                    "x": logo.roi.x,
                    "y": logo.roi.y,
                    "width": logo.roi.width,
                    "height": logo.roi.height
                },
                "tolerance_mm": logo.tolerance_mm,
                "detector": logo.detector_type
            }
            config_data["logos"].append(logo_data)

        return config_data

    def _update_ui_after_preset_save(self, design, size, part, config_path):
        """Update UI after successful preset save"""
        # Update dropdowns
        self._update_design_options()
        self._update_size_options()
        self._update_part_options()

        self.config_status_label.config(
            text=f"✅ Preset guardado: {design}/{size}/{part} ({len(self.current_style.logos)} logos)",
            foreground="green"
        )

        messagebox.showinfo("Éxito", f"Preset guardado correctamente en:\n{config_path}")

    def _save_preset(self):
        """Save current configuration as preset - Refactored for clarity"""
        design = self.design_var.get()
        size = self.size_var.get()
        part = self.part_var.get()

        # Validate input data using PresetManager (Phase 3 Migration)
        if not self.preset_manager.validate_preset_data(design, size, part, self.current_style):
            return

        # Create directory structure
        configs_dir = os.path.join(os.path.dirname(__file__), "..", "..", "configs")
        preset_dir = os.path.join(configs_dir, design, size)
        os.makedirs(preset_dir, exist_ok=True)

        config_path = os.path.join(preset_dir, f"{part}.json")

        # Check if file exists and confirm overwrite
        if os.path.exists(config_path):
            if not messagebox.askyesno("Sobrescribir",
                                     f"El preset {design}/{size}/{part} ya existe.\n\n¿Quieres sobrescribirlo?"):
                return

        try:
            # Prepare and save config data
            config_data = self._prepare_preset_config_data(design, size, part)

            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)

            # Update UI after successful save
            self._update_ui_after_preset_save(design, size, part, config_path)

        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar preset: {str(e)}")

    # New methods using specialized managers - Phase 2 Architecture

    def _load_preset_with_manager(self):
        """Load preset using PresetManager"""
        try:
            config_data, config_path = self.preset_manager.load_preset_file()
            if not config_data or not config_path:
                return

            # Extract metadata
            design, size, part = self.preset_manager.extract_preset_metadata(
                config_data, config_path
            )

            # Update UI variables
            self.ui_manager.set_variable_value("design", design)
            self.ui_manager.set_variable_value("size", size)
            self.ui_manager.set_variable_value("part", part)

            # Update current state
            self.current_design = design
            self.current_size = size
            self.current_part = part

            # Create/update style
            if not self.current_style:
                self.current_style = Style(
                    id=f"{design}_{size}_{part}",
                    name=f"{design} {size} {part}",
                    logos=[]
                )

            # Load logos using PresetManager
            self.current_style.logos = self.preset_manager.create_logos_from_config(config_data)

            # Load calibration
            if 'calibration_factor' in config_data:
                self.mm_per_pixel = config_data['calibration_factor']

            # Initialize config if needed
            from ..config.models import AlignPressConfig, LibraryData
            if not self.current_config:
                self.current_config = AlignPressConfig(library=LibraryData(styles=[]))

            self.current_config.library.styles = [self.current_style]

            # Update UI
            self._update_ui_after_preset_load_new(design, size, part, len(self.current_style.logos))

        except Exception as e:
            self.ui_manager.show_error_message("Error", f"Error al cargar preset: {str(e)}")

    def _save_preset_with_manager(self):
        """Save preset using PresetManager"""
        design = self.ui_manager.get_variable_value("design")
        size = self.ui_manager.get_variable_value("size")
        part = self.ui_manager.get_variable_value("part")

        if self.preset_manager.save_preset(design, size, part, self.current_style, self.mm_per_pixel):
            # Update UI after successful save
            self._update_dropdowns_after_save()
            self.ui_manager.update_config_status(
                f"✅ Preset guardado: {design}/{size}/{part} ({len(self.current_style.logos)} logos)",
                "green"
            )

    def _update_ui_after_preset_load_new(self, design: str, size: str, part: str, logos_count: int):
        """Update UI after preset load using new architecture"""
        # Update logo list
        if self.current_style:
            self.ui_manager.update_logo_list(self.current_style.logos)

        # Update image display
        self._display_image_with_processor()

        # Update status
        self.ui_manager.update_config_status(
            f"✅ Preset cargado: {design}/{size}/{part} ({logos_count} logos)",
            "green"
        )

        # Show info message
        self.ui_manager.show_info_message(
            "Preset Cargado",
            f"Preset cargado exitosamente:\n\n"
            f"📁 Diseño: {design}\n"
            f"📏 Talla: {size}\n"
            f"🧩 Parte: {part}\n"
            f"🎯 Logos: {logos_count}"
        )

    def _display_image_with_processor(self):
        """Display image using ImageProcessor"""
        if self.image_processor.current_image is None:
            return

        # Prepare image for display
        photo_image = self.image_processor.prepare_image_for_canvas()
        if photo_image and self.image_canvas:
            # Clear canvas
            self.image_canvas.delete("all")

            # Initialize ruler/grid system if not exists
            if not self.ruler_grid_system:
                self.ruler_grid_system = RulerGridSystem(self.image_canvas)
                self.ruler_grid_system.set_visibility(
                    self.rulers_var.get(),
                    self.grid_var.get()
                )

            # Get canvas dimensions
            canvas_width = photo_image.width()
            canvas_height = photo_image.height()

            # Draw rulers and grid
            self.ruler_grid_system.draw_rulers_and_grid(
                canvas_width, canvas_height,
                self.mm_per_pixel, self.canvas_scale
            )

            # Get ruler offset
            offset_x, offset_y = self.ruler_grid_system.get_ruler_offset()

            # Display image with offset
            self.image_canvas.create_image(
                offset_x, offset_y,
                image=photo_image, anchor="nw"
            )

            # Draw logos
            self._draw_logos_with_processor()

            # Update scroll region
            total_width = canvas_width + offset_x
            total_height = canvas_height + offset_y
            self.ruler_grid_system.adjust_canvas_scroll_region(total_width, total_height)

    def _draw_logos_with_processor(self):
        """Draw logos using ImageProcessor calculations"""
        if not self.current_style or not self.ruler_grid_system:
            return

        # Clear existing markers
        for marker_id in self.position_markers.values():
            if isinstance(marker_id, list):
                for mid in marker_id:
                    self.image_canvas.delete(mid)
            else:
                self.image_canvas.delete(marker_id)

        for rect_id in self.roi_rectangles.values():
            self.image_canvas.delete(rect_id)

        self.position_markers.clear()
        self.roi_rectangles.clear()

        # Draw each logo using ImageProcessor
        for logo in self.current_style.logos:
            self._draw_single_logo_with_processor(logo)

    def _draw_single_logo_with_processor(self, logo: Logo):
        """Draw single logo using ImageProcessor"""
        # Get position and ROI using ImageProcessor
        pos_x, pos_y = self.image_processor.calculate_logo_canvas_position(logo, self.mm_per_pixel)
        roi_x, roi_y, roi_w, roi_h = self.image_processor.calculate_logo_roi_canvas(logo, self.mm_per_pixel)

        # Adjust for ruler offset
        offset_x, offset_y = self.ruler_grid_system.get_ruler_offset()
        pos_x += offset_x
        pos_y += offset_y
        roi_x += offset_x
        roi_y += offset_y

        # Determine if logo is selected
        is_selected = (self.editing_mode == "logo" and
                      self.selected_logo_index is not None and
                      self.current_style and
                      self.selected_logo_index < len(self.current_style.logos) and
                      logo == self.current_style.logos[self.selected_logo_index])

        color = "orange" if is_selected else "blue"
        width = 3 if is_selected else 2
        size = 10

        # Draw crosshair
        line1 = self.image_canvas.create_line(
            pos_x - size, pos_y, pos_x + size, pos_y,
            fill=color, width=width, tags=f"logo_{logo.id}"
        )
        line2 = self.image_canvas.create_line(
            pos_x, pos_y - size, pos_x, pos_y + size,
            fill=color, width=width, tags=f"logo_{logo.id}"
        )

        # Draw ROI rectangle
        rect = self.image_canvas.create_rectangle(
            roi_x, roi_y, roi_x + roi_w, roi_y + roi_h,
            outline=color, width=width, tags=f"logo_{logo.id}"
        )

        # Draw text label
        text = self.image_canvas.create_text(
            pos_x + 15, pos_y - 15,
            text=logo.name, fill=color, font=("Arial", 9),
            tags=f"logo_{logo.id}"
        )

        self.position_markers[logo.id] = [line1, line2, text]
        self.roi_rectangles[logo.id] = rect

    def _toggle_rulers(self):
        """Toggle rulers using RulerGridSystem"""
        if self.ruler_grid_system:
            show_rulers = self.rulers_var.get()
            show_grid = self.grid_var.get()
            self.ruler_grid_system.set_visibility(show_rulers, show_grid)
            self._display_image_with_processor()

    def _toggle_grid(self):
        """Toggle grid using RulerGridSystem"""
        if self.ruler_grid_system:
            show_rulers = self.rulers_var.get()
            show_grid = self.grid_var.get()
            self.ruler_grid_system.set_visibility(show_rulers, show_grid)
            self._display_image_with_processor()

    def _update_dropdowns_after_save(self):
        """Update dropdowns after saving preset"""
        designs, sizes, parts = self.preset_manager.scan_existing_presets()
        self.ui_manager.update_dropdown_values("design_combo", designs)
        self.ui_manager.update_dropdown_values("size_combo", sizes)
        self.ui_manager.update_dropdown_values("part_combo", parts)

    def _generate_variants_with_generator(self):
        """Generate variants using VariantGenerator - Phase 3 Strangler Fig Pattern"""
        success = self.variant_generator.generate_variants_dialog(
            self.current_style, self.current_config
        )
        if success:
            logger.info("Variants generated successfully using new architecture")

    def _load_image(self):
        """Load an image for configuration using ImageProcessor"""
        if not CV2_AVAILABLE:
            self.ui_manager.show_error_message("Error", "OpenCV no disponible")
            return

        filename = filedialog.askopenfilename(
            title="Seleccionar imagen",
            filetypes=[
                ("Imágenes", "*.jpg *.jpeg *.png *.bmp"),
                ("Todos los archivos", "*.*")
            ]
        )

        if filename:
            if self.image_processor.load_image(filename):
                # Copy image reference and scale for compatibility
                self.current_image = self.image_processor.current_image
                self.canvas_scale = getattr(self.image_processor, 'canvas_scale', 1.0)

                # Display image
                self._display_image_with_processor()

                logger.info(f"Imagen cargada: {filename}")
                dimensions = self.image_processor.get_image_dimensions()
                if dimensions:
                    width, height = dimensions
                    self.ui_manager.show_info_message(
                        "Éxito",
                        f"Imagen cargada correctamente\nResolución: {width}x{height}"
                    )
            else:
                self.ui_manager.show_error_message("Error", "No se pudo cargar la imagen")

    def _display_image(self):
        """Display current image on canvas (with template overlay if active)"""
        if self.current_image is None:
            return

        # If template is active, use template overlay method
        if self.selected_template_id:
            self._update_image_with_template_overlay_manager()
        else:
            # Display plain image
            self._display_processed_image(self.current_image)
            # Draw existing logos
            self._draw_logos()

    def _draw_logos(self):
        """Draw logo markers and ROIs on canvas"""
        if not self.current_style or self.current_image is None:
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
        # Convert mm to pixels using calibration data
        if self.mm_per_pixel > 0:
            x_px = (logo.position_mm.x / self.mm_per_pixel) * self.canvas_scale
            y_px = (logo.position_mm.y / self.mm_per_pixel) * self.canvas_scale
        else:
            # Fallback if no calibration
            x_px = logo.position_mm.x * self.canvas_scale
            y_px = logo.position_mm.y * self.canvas_scale

        # Draw position marker (crosshair)
        size = 10
        # Highlight selected logo
        is_selected = (self.editing_mode == "logo" and
                      self.selected_logo_index is not None and
                      self.current_style and
                      self.selected_logo_index < len(self.current_style.logos) and
                      logo == self.current_style.logos[self.selected_logo_index])

        color = "orange" if is_selected else "blue"
        width = 3 if is_selected else 2

        # Crosshair lines
        line1 = self.image_canvas.create_line(
            x_px - size, y_px, x_px + size, y_px,
            fill=color, width=width, tags=f"logo_{logo.id}"
        )
        line2 = self.image_canvas.create_line(
            x_px, y_px - size, x_px, y_px + size,
            fill=color, width=width, tags=f"logo_{logo.id}"
        )

        # ROI rectangle (convert mm to pixels)
        if self.mm_per_pixel > 0:
            roi_x = (logo.roi.x / self.mm_per_pixel) * self.canvas_scale
            roi_y = (logo.roi.y / self.mm_per_pixel) * self.canvas_scale
            roi_w = (logo.roi.width / self.mm_per_pixel) * self.canvas_scale
            roi_h = (logo.roi.height / self.mm_per_pixel) * self.canvas_scale
        else:
            # Fallback if no calibration
            roi_x = logo.roi.x * self.canvas_scale
            roi_y = logo.roi.y * self.canvas_scale
            roi_w = logo.roi.width * self.canvas_scale
            roi_h = logo.roi.height * self.canvas_scale

        rect = self.image_canvas.create_rectangle(
            roi_x, roi_y, roi_x + roi_w, roi_y + roi_h,
            outline=color, width=width, tags=f"logo_{logo.id}"
        )

        # Text label
        text = self.image_canvas.create_text(
            x_px + 15, y_px - 15,
            text=logo.name, fill=color, font=("Arial", 9),
            tags=f"logo_{logo.id}"
        )

        self.position_markers[logo.id] = [line1, line2, text]
        self.roi_rectangles[logo.id] = rect




    def _on_logo_select(self, event=None):
        """Handle logo selection from list - Template-First workflow"""
        selection = self.logo_list.curselection()
        if not selection or not self.current_style:
            self.selected_logo_index = None
            self.editing_mode = "none"
            self.position_frame.pack_forget()
            self.editing_indicator.config(text="💡 Selecciona un logo o carga un template", foreground="gray")
            return

        # Set selected logo index and trigger our new selection handler
        self.selected_logo_index = selection[0]

        # Use our new Template-First selection logic
        self._on_logo_selected()

        # Update unified position panel
        self._update_unified_position_panel()

    def _update_unified_position_panel(self):
        """Update unified position panel with current data"""
        if self.editing_mode == "template" and self.selected_template_id:
            # Update panel for template positioning
            template_info = self.template_positions.get(self.selected_template_id)
            if template_info:
                pos = template_info.get('position', (0, 0))
                size = template_info.get('size', (50, 50))
                self.pos_x_var.set(str(int(pos[0] * self.mm_per_pixel) if self.mm_per_pixel else pos[0]))
                self.pos_y_var.set(str(int(pos[1] * self.mm_per_pixel) if self.mm_per_pixel else pos[1]))
                # Para templates, usar las dimensiones reales calculadas si están disponibles
                if hasattr(self, 'template_size_mm') and self.template_size_mm:
                    self.width_var.set(str(round(self.template_size_mm[0], 1)))
                    self.height_var.set(str(round(self.template_size_mm[1], 1)))
                else:
                    # Fallback para datos antiguos o cuando no hay template_size_mm
                    self.width_var.set(str(int(size[0] * self.mm_per_pixel) if self.mm_per_pixel else size[0]))
                    self.height_var.set(str(int(size[1] * self.mm_per_pixel) if self.mm_per_pixel else size[1]))
        elif self.editing_mode == "logo" and self.selected_logo_index is not None and self.current_style:
            # Update panel for logo editing
            if self.selected_logo_index < len(self.current_style.logos):
                selected_logo = self.current_style.logos[self.selected_logo_index]
                self.pos_x_var.set(str(selected_logo.position_mm.x))
                self.pos_y_var.set(str(selected_logo.position_mm.y))
                self.width_var.set(str(selected_logo.roi.width))
                self.height_var.set(str(selected_logo.roi.height))
        else:
            # Clear panel
            self.pos_x_var.set("")
            self.pos_y_var.set("")
            self.width_var.set("")
            self.height_var.set("")

    def _update_logo_from_position_panel(self):
        """Update selected logo with values from unified position panel"""
        if self.selected_logo_index is None or self.editing_mode != "logo" or not self.current_style:
            return

        if self.selected_logo_index >= len(self.current_style.logos):
            return

        try:
            selected_logo = self.current_style.logos[self.selected_logo_index]
            # Update position from unified panel
            selected_logo.position_mm = Point(
                float(self.pos_x_var.get()),
                float(self.pos_y_var.get())
            )

            # Update ROI size if width/height are available
            if hasattr(self, 'width_var') and hasattr(self, 'height_var'):
                if self.width_var.get() and self.height_var.get():
                    selected_logo.roi.width = float(self.width_var.get())
                    selected_logo.roi.height = float(self.height_var.get())

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
                    # Style info now derived from hierarchical path
                    pass
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
                # Update style with current hierarchical values
                self.current_style.id = f"{self.current_design}_{self.current_size}_{self.current_part}"
                self.current_style.name = f"{self.current_design} {self.current_size} {self.current_part}"

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

    def _load_calibration(self):
        """Load calibration data from JSON file"""
        filename = filedialog.askopenfilename(
            title="Cargar calibración",
            filetypes=[
                ("JSON files", "*.json"),
                ("Todos los archivos", "*.*")
            ]
        )

        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    self.calibration_data = json.load(f)

                # Extract mm/pixel factor
                self.mm_per_pixel = self.calibration_data.get('factor_mm_px', 1.0)

                # Update UI
                self.calibration_label.config(
                    text=f"Calibrado: {self.mm_per_pixel:.4f} mm/px",
                    foreground="green"
                )
                self.calib_status_label.config(
                    text="Estado: Calibrado ✓",
                    foreground="green"
                )
                self.calib_factor_label.config(
                    text=f"Factor: {self.mm_per_pixel:.4f} mm/pixel"
                )

                # Redraw logos with new calibration
                self._draw_logos()

                logger.info(f"Calibración cargada: {self.mm_per_pixel:.4f} mm/pixel")
                messagebox.showinfo("Éxito",
                    f"Calibración cargada correctamente\n"
                    f"Factor: {self.mm_per_pixel:.4f} mm/pixel")

            except Exception as e:
                messagebox.showerror("Error", f"Error cargando calibración: {e}")
                logger.error(f"Error loading calibration: {e}")

    def _preview_rois(self):
        """Show preview of all ROIs"""
        if not self.current_style or self.current_image is None:
            messagebox.showwarning("Advertencia", "Cargar imagen y crear logos primero")
            return

        # Create preview window
        preview_window = tk.Toplevel(self.root)
        preview_window.title("Vista Previa de ROIs")
        preview_window.geometry("800x600")

        # Create canvas for preview
        preview_canvas = tk.Canvas(preview_window, bg="white")
        preview_canvas.pack(fill=tk.BOTH, expand=True)

        # Convert image and draw ROIs
        image_rgb = cv2.cvtColor(self.current_image, cv2.COLOR_BGR2RGB)

        # Scale for preview
        height, width = image_rgb.shape[:2]
        scale = min(750/width, 550/height)

        new_width = int(width * scale)
        new_height = int(height * scale)

        image_preview = cv2.resize(image_rgb, (new_width, new_height))

        # Draw ROIs on preview
        for logo in self.current_style.logos:
            if self.mm_per_pixel > 0:
                # Convert mm to pixels
                roi_x = int(logo.roi.x / self.mm_per_pixel * scale)
                roi_y = int(logo.roi.y / self.mm_per_pixel * scale)
                roi_w = int(logo.roi.width / self.mm_per_pixel * scale)
                roi_h = int(logo.roi.height / self.mm_per_pixel * scale)

                # Draw rectangle
                cv2.rectangle(image_preview,
                            (roi_x, roi_y), (roi_x + roi_w, roi_y + roi_h),
                            (255, 0, 0), 2)

                # Draw text
                cv2.putText(image_preview, logo.name,
                          (roi_x, roi_y - 5), cv2.FONT_HERSHEY_SIMPLEX,
                          0.5, (255, 0, 0), 1)

        # Convert to PhotoImage and display
        pil_preview = Image.fromarray(image_preview)
        photo_preview = ImageTk.PhotoImage(pil_preview)

        preview_canvas.create_image(
            new_width // 2, new_height // 2,
            image=photo_preview
        )

        # Keep reference to avoid garbage collection
        preview_canvas.photo = photo_preview

    def _export_debug_image(self):
        """Export current configuration as debug image"""
        if not self.current_style or self.current_image is None:
            messagebox.showwarning("Advertencia", "Cargar imagen y crear logos primero")
            return

        filename = filedialog.asksaveasfilename(
            title="Exportar imagen de debug",
            defaultextension=".jpg",
            filetypes=[
                ("JPEG files", "*.jpg"),
                ("PNG files", "*.png"),
                ("Todos los archivos", "*.*")
            ]
        )

        if filename:
            try:
                # Create debug image
                debug_image = self.current_image.copy()

                for logo in self.current_style.logos:
                    if self.mm_per_pixel > 0:
                        # Convert mm to pixels
                        roi_x = int(logo.roi.x / self.mm_per_pixel)
                        roi_y = int(logo.roi.y / self.mm_per_pixel)
                        roi_w = int(logo.roi.width / self.mm_per_pixel)
                        roi_h = int(logo.roi.height / self.mm_per_pixel)

                        pos_x = int(logo.position_mm.x / self.mm_per_pixel)
                        pos_y = int(logo.position_mm.y / self.mm_per_pixel)

                        # Draw ROI
                        cv2.rectangle(debug_image,
                                    (roi_x, roi_y), (roi_x + roi_w, roi_y + roi_h),
                                    (0, 255, 0), 2)

                        # Draw position marker
                        cv2.circle(debug_image, (pos_x, pos_y), 5, (0, 0, 255), -1)
                        cv2.circle(debug_image, (pos_x, pos_y), 10, (0, 0, 255), 2)

                        # Draw text
                        cv2.putText(debug_image, logo.name,
                                  (pos_x + 15, pos_y - 15),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

                # Save image
                cv2.imwrite(filename, debug_image)

                messagebox.showinfo("Éxito", f"Imagen de debug guardada: {filename}")
                logger.info(f"Debug image exported: {filename}")

            except Exception as e:
                messagebox.showerror("Error", f"Error exportando imagen: {e}")
                logger.error(f"Error exporting debug image: {e}")


    def _test_detection(self):
        """Test detection with current configuration"""
        if not self.current_style or self.current_image is None:
            messagebox.showwarning("Advertencia", "Cargar imagen y crear configuración primero")
            return

        try:
            # Import detection simulator
            from ..tools.detection_simulator import DetectionSimulator
            from pathlib import Path
            import tempfile
            import os

            # Save current image to temp file
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
                cv2.imwrite(tmp_file.name, self.current_image)
                temp_image_path = Path(tmp_file.name)

            # Create temporary config
            if not self.current_config:
                self.current_config = create_default_config()

            # Update config with current style
            existing_style_index = None
            for i, style in enumerate(self.current_config.library.styles):
                if style.id == self.current_style.id:
                    existing_style_index = i
                    break

            if existing_style_index is not None:
                self.current_config.library.styles[existing_style_index] = self.current_style
            else:
                self.current_config.library.styles.append(self.current_style)

            # Set active style
            self.current_config.active_style_id = self.current_style.id

            # Run simulation
            simulator = DetectionSimulator()

            result = simulator.simulate_garment_detection(
                temp_image_path, self.current_style, self.current_config
            )

            # Show results in new window
            self._show_detection_results(result, temp_image_path)

            # Cleanup
            try:
                os.unlink(temp_image_path)
            except:
                pass

        except ImportError:
            messagebox.showerror("Error", "Detection Simulator no disponible")
        except Exception as e:
            messagebox.showerror("Error", f"Error en prueba de detección: {e}")
            logger.error(f"Error testing detection: {e}")

    def _show_detection_results(self, result: Dict, image_path: Path):
        """Show detection results in popup window"""
        results_window = tk.Toplevel(self.root)
        results_window.title("Resultados de Detección")
        results_window.geometry("600x500")

        main_frame = ttk.Frame(results_window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Results summary
        summary_frame = ttk.LabelFrame(main_frame, text="Resumen")
        summary_frame.pack(fill=tk.X, pady=(0, 10))

        success_status = "✅ ÉXITO" if result.get('overall_success') else "❌ FALLO"
        ttk.Label(summary_frame, text=f"Estado: {success_status}",
                 font=("Arial", 10, "bold")).pack(anchor=tk.W, padx=5, pady=2)

        ttk.Label(summary_frame,
                 text=f"Logos detectados: {result.get('successful_logos', 0)}/{result.get('logo_count', 0)}").pack(anchor=tk.W, padx=5, pady=2)

        ttk.Label(summary_frame,
                 text=f"Tiempo de procesamiento: {result.get('processing_time_ms', 0):.1f}ms").pack(anchor=tk.W, padx=5, pady=2)

        ttk.Label(summary_frame,
                 text=f"Confianza promedio: {result.get('average_confidence', 0):.3f}").pack(anchor=tk.W, padx=5, pady=2)

        # Individual logo results
        if 'logo_results' in result:
            logo_frame = ttk.LabelFrame(main_frame, text="Resultados por Logo")
            logo_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

            # Create scrollable text widget
            text_widget = tk.Text(logo_frame, height=12, wrap=tk.WORD)
            scrollbar = ttk.Scrollbar(logo_frame, orient=tk.VERTICAL, command=text_widget.yview)
            text_widget.configure(yscrollcommand=scrollbar.set)

            text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0), pady=5)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)

            # Add logo results
            for logo_result in result.get('logo_results', []):
                logo_id = logo_result.get('logo_id', 'unknown')
                detected = logo_result.get('detected', False)
                confidence = logo_result.get('confidence', 0.0)
                position = logo_result.get('position_mm', {})

                status = "✅" if detected else "❌"
                text_widget.insert(tk.END, f"{status} {logo_id}:\n")
                text_widget.insert(tk.END, f"   Detectado: {'Sí' if detected else 'No'}\n")
                text_widget.insert(tk.END, f"   Confianza: {confidence:.3f}\n")

                if position:
                    text_widget.insert(tk.END, f"   Posición: ({position.get('x', 0):.1f}, {position.get('y', 0):.1f}) mm\n")

                text_widget.insert(tk.END, "\n")

            text_widget.config(state=tk.DISABLED)

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)

        def show_debug_image():
            """Show debug image if available"""
            try:
                from ..tools.detection_simulator import DetectionSimulator
                simulator = DetectionSimulator()
                debug_path = simulator.create_visual_debug_image(image_path, result)

                if debug_path and debug_path.exists():
                    # Open debug image in new window
                    debug_image = cv2.imread(str(debug_path))
                    if debug_image is not None:
                        self._show_image_popup(debug_image, "Imagen de Debug")
                    else:
                        messagebox.showerror("Error", "No se pudo cargar imagen de debug")
                else:
                    messagebox.showwarning("Advertencia", "No se pudo generar imagen de debug")

            except Exception as e:
                messagebox.showerror("Error", f"Error mostrando debug: {e}")

        ttk.Button(button_frame, text="Ver Debug Image",
                  command=show_debug_image).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Cerrar",
                  command=results_window.destroy).pack(side=tk.RIGHT)

    def _show_image_popup(self, image: np.ndarray, title: str):
        """Show an image in a popup window"""
        popup = tk.Toplevel(self.root)
        popup.title(title)

        # Convert and scale image
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        height, width = image_rgb.shape[:2]

        # Scale to fit screen
        max_width, max_height = 800, 600
        scale = min(max_width/width, max_height/height, 1.0)

        if scale < 1.0:
            new_width = int(width * scale)
            new_height = int(height * scale)
            image_rgb = cv2.resize(image_rgb, (new_width, new_height))

        # Create canvas
        canvas = tk.Canvas(popup, width=image_rgb.shape[1], height=image_rgb.shape[0])
        canvas.pack()

        # Display image
        pil_image = Image.fromarray(image_rgb)
        photo = ImageTk.PhotoImage(pil_image)
        canvas.create_image(0, 0, anchor=tk.NW, image=photo)

        # Keep reference
        popup.photo = photo

    # Hierarchical configuration methods
    def _on_design_changed(self, event=None):
        """Handle design selection change"""
        self.current_design = self.design_var.get()
        self._update_size_options()
        self._update_config_status()

    def _on_size_changed(self, event=None):
        """Handle size selection change"""
        self.current_size = self.size_var.get()
        self._update_part_options()
        self._update_config_status()

    def _on_part_changed(self, event=None):
        """Handle part selection change"""
        self.current_part = self.part_var.get()
        self._update_config_status()
        self._try_load_existing_config()

    def _update_size_options(self):
        """Update size combobox based on selected design"""
        if not self.current_design:
            self.size_combo['values'] = []
            return

        design_path = self.config_root_path / self.current_design
        if design_path.exists():
            sizes = [d.name for d in design_path.iterdir() if d.is_dir()]
            self.size_combo['values'] = sorted(sizes)
        else:
            # Default sizes for new designs
            self.size_combo['values'] = ["TallaS", "TallaM", "TallaL", "TallaXL"]

    def _update_part_options(self):
        """Update part combobox based on selected design/size"""
        # Parts are predefined but could be dynamic in the future
        pass

    def _update_config_status(self):
        """Update configuration status label"""
        if self.current_design and self.current_size and self.current_part:
            config_path = self._get_current_config_path()
            if config_path.exists():
                self.config_status_label.config(
                    text=f"Estado: {self.current_design}/{self.current_size}/{self.current_part} ✓",
                    foreground="green"
                )
            else:
                self.config_status_label.config(
                    text=f"Estado: {self.current_design}/{self.current_size}/{self.current_part} (nuevo)",
                    foreground="blue"
                )
        else:
            self.config_status_label.config(
                text="Estado: Selecciona configuración completa",
                foreground="orange"
            )

    def _get_current_config_path(self) -> Path:
        """Get the current configuration file path"""
        return self.config_root_path / self.current_design / self.current_size / f"{self.current_part}.json"

    def _new_configuration(self):
        """Create a new configuration"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Nueva Configuración")
        dialog.geometry("400x300")  # Increased height
        dialog.transient(self.root)
        dialog.grab_set()

        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (400 // 2)
        y = (dialog.winfo_screenheight() // 2) - (300 // 2)
        dialog.geometry(f"400x300+{x}+{y}")

        # Main frame with padding
        main_frame = ttk.Frame(dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Design name
        ttk.Label(main_frame, text="Nombre del Diseño:").pack(pady=(0, 5))
        design_entry = ttk.Entry(main_frame, width=30)
        design_entry.pack(pady=(0, 15))
        design_entry.focus()  # Focus on first field

        # Size
        ttk.Label(main_frame, text="Talla:").pack(pady=(0, 5))
        size_combo = ttk.Combobox(main_frame, values=["TallaS", "TallaM", "TallaL", "TallaXL"], width=27)
        size_combo.pack(pady=(0, 15))
        size_combo.set("TallaM")  # Default value

        # Part
        ttk.Label(main_frame, text="Parte:").pack(pady=(0, 5))
        part_combo = ttk.Combobox(main_frame, values=["delantera", "trasera", "manga_izquierda", "manga_derecha"], width=27)
        part_combo.pack(pady=(0, 20))
        part_combo.set("delantera")  # Default value

        def create_config():
            design = design_entry.get().strip()
            size = size_combo.get().strip()
            part = part_combo.get().strip()

            if not all([design, size, part]):
                messagebox.showerror("Error", "Todos los campos son obligatorios")
                return

            # Update UI
            self.design_var.set(design)
            self.size_var.set(size)
            self.part_var.set(part)

            # Update internal state
            self.current_design = design
            self.current_size = size
            self.current_part = part

            # Update design options if new
            current_designs = list(self.design_combo['values'])
            if design not in current_designs:
                current_designs.append(design)
                self.design_combo['values'] = sorted(current_designs)

            self._update_config_status()
            dialog.destroy()

        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(button_frame, text="Cancelar",
                  command=dialog.destroy).pack(side=tk.RIGHT, padx=(5, 0))
        create_button = ttk.Button(button_frame, text="Crear", command=create_config)
        create_button.pack(side=tk.RIGHT)

        # Make Create button default
        dialog.bind('<Return>', lambda e: create_config())
        create_button.focus()

    def _load_hierarchy_config(self):
        """Load existing hierarchical configuration"""
        if not self.config_root_path.exists():
            messagebox.showwarning("Advertencia", "No hay configuraciones existentes")
            return

        # Show directory picker or tree view
        initial_dir = str(self.config_root_path)
        filename = filedialog.askopenfilename(
            title="Seleccionar configuración",
            initialdir=initial_dir,
            filetypes=[("JSON files", "*.json"), ("Todos los archivos", "*.*")]
        )

        if filename:
            try:
                config_path = Path(filename)
                rel_path = config_path.relative_to(self.config_root_path)

                # Parse hierarchy from path: design/size/part.json
                parts = rel_path.parts
                if len(parts) >= 3:
                    design = parts[0]
                    size = parts[1]
                    part = parts[2].replace('.json', '')

                    self.design_var.set(design)
                    self.size_var.set(size)
                    self.part_var.set(part)

                    self.current_design = design
                    self.current_size = size
                    self.current_part = part

                    self._load_part_configuration(config_path)
                    self._update_config_status()
                else:
                    messagebox.showerror("Error", "Estructura de archivo no válida")

            except Exception as e:
                messagebox.showerror("Error", f"Error cargando configuración: {e}")

    def _try_load_existing_config(self):
        """Try to load existing configuration for current selection"""
        if not all([self.current_design, self.current_size, self.current_part]):
            return

        config_path = self._get_current_config_path()
        if config_path.exists():
            try:
                self._load_part_configuration(config_path)
            except Exception as e:
                logger.error(f"Error loading existing config: {e}")

    def _load_part_configuration(self, config_path: Path):
        """Load configuration for a specific part"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)

            # Clear current logos
            if self.current_style:
                self.current_style.logos.clear()
            else:
                # Create new style for this part
                self.current_style = Style(
                    id=f"{self.current_design}_{self.current_size}_{self.current_part}",
                    name=f"{self.current_design} {self.current_size} {self.current_part}",
                    logos=[]
                )

            # Load logos from config
            for logo_data in config_data.get('logos', []):
                logo = Logo(
                    id=logo_data['id'],
                    name=logo_data['name'],
                    position_mm=Point(logo_data['position_mm']['x'], logo_data['position_mm']['y']),
                    roi=Rectangle(
                        logo_data['roi']['x'], logo_data['roi']['y'],
                        logo_data['roi']['width'], logo_data['roi']['height']
                    ),
                    tolerance_mm=logo_data.get('tolerance_mm', 5.0),
                    detector_type=logo_data.get('detector_type', 'template_matching')
                )
                self.current_style.logos.append(logo)

            # Update UI
            self._update_logo_list()
            self._draw_logos()

            messagebox.showinfo("Éxito", f"Configuración cargada: {len(self.current_style.logos)} logos")

        except Exception as e:
            messagebox.showerror("Error", f"Error cargando configuración: {e}")

    # Simplified template management
    def _load_and_show_template(self):
        """Load template and show it immediately on the image"""
        if self.current_image is None:
            messagebox.showwarning("Advertencia", "Cargar imagen de prenda primero")
            return

        filename = filedialog.askopenfilename(
            title="Seleccionar template de logo",
            filetypes=[
                ("Imágenes PNG", "*.png"),
                ("Imágenes", "*.jpg *.jpeg *.png *.bmp"),
                ("Todos los archivos", "*.*")
            ]
        )

        if filename:
            try:
                # Try to load template with different modes
                template_image = cv2.imread(filename, cv2.IMREAD_UNCHANGED)
                if template_image is None:
                    # Try with regular color mode
                    template_image = cv2.imread(filename, cv2.IMREAD_COLOR)
                    if template_image is None:
                        raise ValueError("No se pudo cargar el template - formato no soportado")

                # Validate template dimensions
                if len(template_image.shape) < 2:
                    raise ValueError("Template inválido - dimensiones incorrectas")

                # Generate unique template ID
                template_id = f"template_{len(self.logo_templates) + 1}"

                # Store template
                self.logo_templates[template_id] = template_image
                self.template_references[template_id] = {
                    'filename': Path(filename).name,
                    'path': filename,
                    'size': template_image.shape[:2],
                    'channels': template_image.shape[2] if len(template_image.shape) == 3 else 1
                }

                self.selected_template_id = template_id

                # Update UI labels
                template_name = Path(filename).name
                channels_info = f"({template_image.shape[2]} canales)" if len(template_image.shape) == 3 else "(escala de grises)"
                self.template_info_label.config(text=f"📄 {template_name} {channels_info}", foreground="green")
                self.template_status_label.config(text="✅ Template cargado - Ahora arrastra en la imagen", foreground="green")

                # Switch to template editing mode
                self.editing_mode = "template"
                self.selected_logo_index = None

                # Show template immediately in center of image
                self._show_template_on_image()

                # Show position controls
                self.position_frame.pack(fill=tk.X, pady=(5, 0))

            except Exception as e:
                error_msg = f"Error cargando template: {e}"
                logger.error(error_msg)
                messagebox.showerror("Error", error_msg)

                # Reset UI state on error
                self.template_info_label.config(text="❌ Error cargando template", foreground="red")
                self.template_status_label.config(text="", foreground="black")

    def _show_template_on_image(self):
        """Show the loaded template on the image at center position"""
        if not self.selected_template_id or self.current_image is None:
            return

        # Calculate center position
        img_height, img_width = self.current_image.shape[:2]
        center_x = img_width // 2
        center_y = img_height // 2

        # Store template position in image coordinates
        self.template_position = (center_x, center_y)

        # Update the display
        self._update_image_with_template_overlay_manager()

        # Update numeric fields
        self._update_position_fields()

        # Update editing indicator
        template_info = self.template_references[self.selected_template_id]
        self.editing_indicator.config(
            text=f"🎯 Creando nuevo logo: {template_info['filename']}",
            foreground="orange"
        )

        # Update status
        self.template_status_label.config(
            text="🎯 Arrastra el template en la imagen o usa campos numéricos para posicionar",
            foreground="blue"
        )

    def _update_image_with_template_overlay_manager(self):
        """
        Update the canvas display with template overlay using TemplateOverlayManager

        Phase 3 Strangler Fig Pattern - New implementation
        """
        if self.current_image is None:
            return

        try:
            # Check if template overlay is needed
            if not self.selected_template_id or self.selected_template_id not in self.logo_templates:
                # No template selected, just display original image
                self._display_processed_image(self.current_image)
                return

            # Get template image
            template_image = self.logo_templates[self.selected_template_id]

            # Apply template overlay using the specialized manager
            display_image = self.template_overlay_manager.apply_template_overlay(
                base_image=self.current_image.copy(),
                template_id=self.selected_template_id,
                template_image=template_image,
                template_position=self.template_position,
                mm_per_pixel=self.mm_per_pixel,
                template_references=self.template_references
            )

            # Update stored template size from manager
            self.template_size = self.template_overlay_manager.get_template_size()
            self.template_size_mm = self.template_overlay_manager.get_template_size_mm()

            # Display the final image
            self._display_processed_image(display_image)

        except Exception as e:
            logger.error(f"Error updating image with template overlay manager: {e}")
            # Fallback to original image
            self._display_processed_image(self.current_image)

    def _display_processed_image(self, image):
        """Display processed image on canvas"""
        # Convert BGR to RGB
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Calculate scale to fit canvas
        canvas_width = self.image_canvas.winfo_width()
        canvas_height = self.image_canvas.winfo_height()

        if canvas_width <= 1 or canvas_height <= 1:
            # Canvas not ready yet
            self.root.after(100, lambda: self._display_processed_image(image))
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

        # Place the image centered
        self.image_canvas.create_image(
            new_width // 2, new_height // 2,
            image=self.photo_image,
            tags="background"
        )

        # Draw rulers and grid on top
        self._draw_rulers_and_grid(new_width, new_height)

        # Update canvas scroll region
        self.image_canvas.configure(scrollregion=self.image_canvas.bbox("all"))

        # Redraw existing logos
        self._draw_logos()

    def _position_template(self):
        """Enable template positioning mode"""
        if not self.selected_template_id or self.current_image is None:
            messagebox.showwarning("Advertencia", "Cargar template e imagen primero")
            return

        # Enable template positioning mode
        self.template_info_label.config(text="Modo posicionamiento: Click y arrastra en la imagen", foreground="blue")
        messagebox.showinfo("Posicionamiento",
                           "Click en la imagen donde quieres posicionar el logo y arrastra para ajustar el tamaño.\n"
                           "Presiona 'Confirmar Logo' cuando esté en la posición correcta.")

    def _confirm_logo_from_template(self):
        """Confirm logo creation from positioned template"""
        if not self.selected_template_id:
            messagebox.showwarning("Advertencia", "No hay template seleccionado")
            return

        # TODO: Get position from canvas interaction
        # For now, create a centered logo as example
        if self.current_image is not None:
            img_height, img_width = self.current_image.shape[:2]
            template_info = self.template_references[self.selected_template_id]

            # Create logo at center (this would be replaced by actual positioned coordinates)
            center_x_mm = (img_width * self.mm_per_pixel) / 2
            center_y_mm = (img_height * self.mm_per_pixel) / 2

            # Use correct template dimensions
            if self.template_size_mm:
                template_width_mm = self.template_size_mm[0]
                template_height_mm = self.template_size_mm[1]
            else:
                # Fallback con 300 DPI
                template_width_mm = template_info['size'][1] * (25.4 / 300.0)
                template_height_mm = template_info['size'][0] * (25.4 / 300.0)

            # Create new logo
            logo_id = f"logo_{len(self.current_style.logos) + 1}" if self.current_style else "logo_1"

            new_logo = Logo(
                id=logo_id,
                name=f"Logo {template_info['filename']}",
                position_mm=Point(center_x_mm, center_y_mm),
                roi=Rectangle(
                    center_x_mm - template_width_mm/2,
                    center_y_mm - template_height_mm/2,
                    template_width_mm,
                    template_height_mm
                ),
                tolerance_mm=5.0,
                detector_type='template_matching'
            )

            # Add to current style
            if not self.current_style:
                self.current_style = Style(
                    id=f"{self.current_design}_{self.current_size}_{self.current_part}",
                    name=f"{self.current_design} {self.current_size} {self.current_part}",
                    logos=[]
                )

            self.current_style.logos.append(new_logo)

            # Update UI
            self._update_logo_list()
            self._draw_logos()

            messagebox.showinfo("Éxito", f"Logo '{logo_id}' creado desde template")

    # Simplified mouse interaction for template and logo dragging
    def _on_canvas_click(self, event=None):
        """Handle canvas click - start dragging or confirm template/logo"""
        if event is None:
            return
        self.drag_start_pos = (event.x, event.y)

        # Check if we're in logo editing mode and can drag a logo
        if self.editing_mode == "logo" and self.current_style and self.selected_logo_index is not None:
            # Check if clicking on selected logo area for dragging
            logo_center = self._get_logo_canvas_position()
            if logo_center:
                canvas_x, canvas_y = logo_center
                click_distance = ((event.x - canvas_x)**2 + (event.y - canvas_y)**2)**0.5

                # If clicking near logo (within 50 pixels), start dragging
                if click_distance < 50:
                    self.dragging_logo = True
                    self.template_status_label.config(
                        text="🚀 Arrastrando logo...",
                        foreground="orange"
                    )

        elif self.selected_template_id:
            # Check if clicking on template area for dragging
            template_center = self._get_template_canvas_position()
            if template_center:
                canvas_x, canvas_y = template_center
                click_distance = ((event.x - canvas_x)**2 + (event.y - canvas_y)**2)**0.5

                # If clicking near template (within 50 pixels), start dragging
                if click_distance < 50:
                    self.dragging_template = True
                    self.template_status_label.config(
                        text="🚀 Arrastrando template...",
                        foreground="orange"
                    )
                else:
                    # Clicking outside template area - confirm logo creation
                    self._confirm_logo_at_current_position()

    def _on_canvas_drag(self, event=None):
        """Handle canvas drag - move template or logo in real time"""
        if event is None or not self.drag_start_pos:
            return
        # Calculate drag distance
        dx = event.x - self.drag_start_pos[0]
        dy = event.y - self.drag_start_pos[1]
        distance = (dx*dx + dy*dy) ** 0.5

        if distance > 5:  # Minimum drag distance threshold
            self.is_dragging = True

            if self.dragging_logo:
                # Move selected logo to new position
                self._move_logo_to_canvas_position(event.x, event.y)
            elif self.dragging_template:
                # Move template to new position
                self._move_template_to_canvas_position(event.x, event.y)

    def _on_canvas_release(self, event=None):
        """Handle canvas release - stop dragging"""
        if self.dragging_logo:
            self.dragging_logo = False
            selected_logo = self.current_style.logos[self.selected_logo_index]
            self.template_status_label.config(
                text=f"✅ Logo '{selected_logo.name}' reposicionado",
                foreground="green"
            )
        elif self.dragging_template:
            self.dragging_template = False
            self.template_status_label.config(
                text="✅ Template posicionado - Click fuera del template para confirmar",
                foreground="green"
            )

        # Reset drag state
        self.is_dragging = False
        self.drag_start_pos = None

    def _get_template_canvas_position(self):
        """Get template center position in canvas coordinates"""
        if not self.selected_template_id or self.canvas_scale <= 0:
            return None

        # Convert image coordinates to canvas coordinates
        canvas_x = self.template_position[0] * self.canvas_scale
        canvas_y = self.template_position[1] * self.canvas_scale

        return (canvas_x, canvas_y)

    def _get_logo_canvas_position(self):
        """Get selected logo center position in canvas coordinates"""
        if not self.current_style or self.selected_logo_index is None or self.canvas_scale <= 0:
            return None

        if self.selected_logo_index >= len(self.current_style.logos):
            return None

        selected_logo = self.current_style.logos[self.selected_logo_index]

        # Convert mm coordinates to pixel coordinates, then to canvas coordinates
        logo_x_px = selected_logo.position_mm.x / self.mm_per_pixel
        logo_y_px = selected_logo.position_mm.y / self.mm_per_pixel

        canvas_x = logo_x_px * self.canvas_scale
        canvas_y = logo_y_px * self.canvas_scale

        return (canvas_x, canvas_y)

    def _move_logo_to_canvas_position(self, canvas_x, canvas_y):
        """Move selected logo to canvas position and update fields"""
        if not self.current_style or self.selected_logo_index is None:
            return

        if self.selected_logo_index >= len(self.current_style.logos):
            return

        # Convert canvas coordinates to image coordinates
        img_x = int(canvas_x / self.canvas_scale)
        img_y = int(canvas_y / self.canvas_scale)

        # Convert to mm coordinates
        pos_x_mm = img_x * self.mm_per_pixel
        pos_y_mm = img_y * self.mm_per_pixel

        # Update logo position
        selected_logo = self.current_style.logos[self.selected_logo_index]
        selected_logo.position_mm.x = pos_x_mm
        selected_logo.position_mm.y = pos_y_mm

        # Also update ROI center
        selected_logo.roi.x = pos_x_mm - selected_logo.roi.width / 2
        selected_logo.roi.y = pos_y_mm - selected_logo.roi.height / 2

        # Update position fields
        self.updating_from_drag = True
        self.pos_x_var.set(round(pos_x_mm, 2))
        self.pos_y_var.set(round(pos_y_mm, 2))
        self.updating_from_drag = False

        # Update display
        self._display_image()

    def _move_template_to_canvas_position(self, canvas_x, canvas_y):
        """Move template to new position based on canvas coordinates"""
        if self.canvas_scale <= 0:
            return

        # Convert canvas coordinates to image coordinates
        img_x = int(canvas_x / self.canvas_scale)
        img_y = int(canvas_y / self.canvas_scale)

        # Update template position
        self.template_position = (img_x, img_y)

        # Update display
        self._update_image_with_template_overlay_manager()

        # Update position fields in real time
        self._update_position_fields()

    def _confirm_logo_at_current_position(self):
        """Confirm logo creation at current template position"""
        if not self.selected_template_id:
            return

        try:
            template_info = self.template_references[self.selected_template_id]

            # Convert position to mm coordinates
            pos_x_mm = self.template_position[0] * self.mm_per_pixel
            pos_y_mm = self.template_position[1] * self.mm_per_pixel

            # Calculate template size in mm using correct dimensions
            if self.template_size_mm:
                template_width_mm = self.template_size_mm[0]
                template_height_mm = self.template_size_mm[1]
            else:
                # Fallback con 300 DPI
                template_width_mm = self.template_size[0] * (25.4 / 300.0)
                template_height_mm = self.template_size[1] * (25.4 / 300.0)

            # Create new logo
            logo_id = f"logo_{len(self.current_style.logos) + 1}" if self.current_style else "logo_1"
            logo_name = f"Logo {template_info['filename']}"

            new_logo = Logo(
                id=logo_id,
                name=logo_name,
                position_mm=Point(pos_x_mm, pos_y_mm),
                roi=Rectangle(
                    pos_x_mm - template_width_mm/2,
                    pos_y_mm - template_height_mm/2,
                    template_width_mm,
                    template_height_mm
                ),
                tolerance_mm=5.0,
                detector_type='template_matching'
            )

            # Add to current style
            if not self.current_style:
                self.current_style = Style(
                    id=f"{self.current_design}_{self.current_size}_{self.current_part}",
                    name=f"{self.current_design} {self.current_size} {self.current_part}",
                    logos=[]
                )

            self.current_style.logos.append(new_logo)

            # Clear template and update UI
            self._clear_template_overlay()
            self._update_logo_list()
            self._display_image()  # Refresh display without template

            # Switch to "none" editing mode
            self.editing_mode = "none"
            self.selected_logo_index = None

            # Update status
            self.template_status_label.config(
                text=f"✅ Logo '{logo_id}' agregado a la lista!",
                foreground="green"
            )

            # Auto-select the newly created logo in the list
            if self.current_style and self.current_style.logos:
                self.selected_logo_index = len(self.current_style.logos) - 1
                self._on_logo_selected()

            messagebox.showinfo("Logo Creado", f"Logo '{logo_id}' agregado en posición ({pos_x_mm:.1f}, {pos_y_mm:.1f}) mm\n\nAhora aparece en la lista de logos.")

        except Exception as e:
            messagebox.showerror("Error", f"Error creando logo: {e}")

    def _clear_template_overlay(self):
        """Clear template overlay and reset template state"""
        self.selected_template_id = None
        self.current_template_overlay = None
        self.template_position = (0, 0)
        self.dragging_template = False
        self.dragging_logo = False

        # Reset UI
        self.template_info_label.config(text="📁 Sin template cargado", foreground="gray")
        self.template_status_label.config(text="", foreground="black")
        self.editing_indicator.config(text="", foreground="black")

        # Hide position controls
        self.position_frame.pack_forget()

    # Logo selection and editing methods
    def _on_logo_selected(self):
        """Handle logo selection from list"""
        if not self.current_style or self.selected_logo_index is None:
            return

        if self.selected_logo_index >= len(self.current_style.logos):
            return

        # Get selected logo
        selected_logo = self.current_style.logos[self.selected_logo_index]

        # Switch to logo editing mode
        self.editing_mode = "logo"

        # Clear any active template
        if self.selected_template_id:
            self._clear_template_overlay()

        # Show position controls for selected logo
        self.position_frame.pack(fill=tk.X, pady=(5, 0))

        # Update editing indicator
        self.editing_indicator.config(
            text=f"✏️ Editando logo: {selected_logo.name}",
            foreground="green"
        )

        # Update position fields with logo data
        self.updating_from_drag = True
        self.pos_x_var.set(round(selected_logo.position_mm.x, 2))
        self.pos_y_var.set(round(selected_logo.position_mm.y, 2))
        self.width_var.set(round(selected_logo.roi.width, 2))
        self.height_var.set(round(selected_logo.roi.height, 2))
        self.updating_from_drag = False

        # Update UI status
        self.template_status_label.config(
            text=f"📝 Usa los campos numéricos o arrastra el logo en la imagen para modificar posición",
            foreground="blue"
        )

        # Highlight logo in image
        self._highlight_selected_logo()

    def _highlight_selected_logo(self):
        """Highlight the selected logo in the image"""
        self._display_image()  # This will redraw with highlighting

    # Position control methods
    def _update_position_fields(self):
        """Update position fields based on current template position"""
        if not self.updating_from_drag:
            self.updating_from_drag = True

            # Convert to mm coordinates
            pos_x_mm = self.template_position[0] * self.mm_per_pixel
            pos_y_mm = self.template_position[1] * self.mm_per_pixel

            # Update position fields
            self.pos_x_var.set(round(pos_x_mm, 2))
            self.pos_y_var.set(round(pos_y_mm, 2))

            # Update size fields using correct dimensions from template_overlay_manager
            if self.template_size_mm:
                # Usar las dimensiones ya calculadas correctamente por template_overlay_manager
                width_mm, height_mm = self.template_size_mm
                self.width_var.set(round(width_mm, 2))
                self.height_var.set(round(height_mm, 2))
            else:
                # Fallback: calcular con factor por defecto si no hay dimensiones
                width_mm = self.template_size[0] * (25.4 / 300.0)  # Asumir 300 DPI
                height_mm = self.template_size[1] * (25.4 / 300.0)
                self.width_var.set(round(width_mm, 2))
                self.height_var.set(round(height_mm, 2))

            # Update size display
            self.template_size_label.config(text=f"{self.template_size[0]}×{self.template_size[1]}px")

            self.updating_from_drag = False

    def _on_position_changed(self, *args):
        """Handle position field changes - works for both templates and logos"""
        if self.updating_from_drag:
            return

        try:
            # Get values from fields
            pos_x_mm = self.pos_x_var.get()
            pos_y_mm = self.pos_y_var.get()

            if self.editing_mode == "template" and self.selected_template_id:
                # Update template position
                pos_x_img = int(pos_x_mm / self.mm_per_pixel)
                pos_y_img = int(pos_y_mm / self.mm_per_pixel)
                self.template_position = (pos_x_img, pos_y_img)
                self._update_image_with_template_overlay_manager()

            elif self.editing_mode == "logo" and self.selected_logo_index is not None:
                # Update selected logo position
                if self.current_style and self.selected_logo_index < len(self.current_style.logos):
                    logo = self.current_style.logos[self.selected_logo_index]
                    logo.position_mm.x = pos_x_mm
                    logo.position_mm.y = pos_y_mm
                    # Update ROI center as well
                    width = logo.roi.width
                    height = logo.roi.height
                    logo.roi.x = pos_x_mm - width/2
                    logo.roi.y = pos_y_mm - height/2
                    self._display_image()


        except (ValueError, tk.TclError):
            # Ignore invalid input
            pass

    def _on_size_changed(self, *args):
        """Handle size field changes - works for both templates and logos"""
        if self.updating_from_drag:
            return

        try:
            # Get values from fields
            width_mm = self.width_var.get()
            height_mm = self.height_var.get()

            if self.editing_mode == "template" and self.selected_template_id:
                # Convert to pixels
                width_px = int(width_mm / self.mm_per_pixel)
                height_px = int(height_mm / self.mm_per_pixel)

                # Update template size
                self.template_size = (width_px, height_px)
                self.template_size_mm = (width_mm, height_mm)

                # Update display
                self._update_image_with_template_overlay_manager()

                # Update size display
                self.template_size_label.config(text=f"{width_px}×{height_px}px")

            elif self.editing_mode == "logo" and self.selected_logo_index is not None:
                # Update selected logo ROI size
                if self.current_style and self.selected_logo_index < len(self.current_style.logos):
                    logo = self.current_style.logos[self.selected_logo_index]
                    logo.roi.width = width_mm
                    logo.roi.height = height_mm
                    # Re-center ROI around position
                    logo.roi.x = logo.position_mm.x - width_mm/2
                    logo.roi.y = logo.position_mm.y - height_mm/2
                    self._display_image()


        except (ValueError, tk.TclError):
            # Ignore invalid input
            pass

    def _center_template(self):
        """Center template in the image"""
        if not self.selected_template_id or self.current_image is None:
            return

        # Calculate center position
        img_height, img_width = self.current_image.shape[:2]
        center_x = img_width // 2
        center_y = img_height // 2

        # Update template position
        self.template_position = (center_x, center_y)

        # Update display and fields
        self._update_image_with_template_overlay_manager()
        self._update_position_fields()

        self.template_status_label.config(text="📍 Template centrado", foreground="green")

    def _cancel_template(self):
        """Cancel template placement and clear everything"""
        self._clear_template_overlay()
        self.template_status_label.config(text="❌ Template cancelado", foreground="red")

    def _handle_template_placement(self, canvas_x, canvas_y):
        """Handle template placement at canvas coordinates"""
        if not self.selected_template_id:
            return

        # Convert canvas coordinates to image coordinates
        if self.canvas_scale > 0:
            img_x = canvas_x / self.canvas_scale
            img_y = canvas_y / self.canvas_scale

            # Convert to mm coordinates
            pos_x_mm = img_x * self.mm_per_pixel
            pos_y_mm = img_y * self.mm_per_pixel

            template_info = self.template_references[self.selected_template_id]
            # Use correct template dimensions
            if self.template_size_mm:
                template_width_mm = self.template_size_mm[0]
                template_height_mm = self.template_size_mm[1]
            else:
                # Fallback con 300 DPI
                template_width_mm = template_info['size'][1] * (25.4 / 300.0)
                template_height_mm = template_info['size'][0] * (25.4 / 300.0)

            # Update template info to show position
            self.template_info_label.config(
                text=f"Template posicionado en: ({pos_x_mm:.1f}, {pos_y_mm:.1f}) mm",
                foreground="blue"
            )

    def _save_current_configuration(self):
        """Save current configuration to hierarchical structure"""
        if not all([self.current_design, self.current_size, self.current_part]):
            messagebox.showwarning("Advertencia", "Selecciona configuración completa primero")
            return

        if not self.current_style or not self.current_style.logos:
            messagebox.showwarning("Advertencia", "No hay logos para guardar")
            return

        try:
            # Create directory structure
            config_path = self._get_current_config_path()
            config_path.parent.mkdir(parents=True, exist_ok=True)

            # Prepare data
            config_data = {
                'design': self.current_design,
                'size': self.current_size,
                'part': self.current_part,
                'calibration_factor': self.mm_per_pixel,
                'logos': []
            }

            # Add logos
            for logo in self.current_style.logos:
                logo_data = {
                    'id': logo.id,
                    'name': logo.name,
                    'position_mm': {
                        'x': logo.position_mm.x,
                        'y': logo.position_mm.y
                    },
                    'roi': {
                        'x': logo.roi.x,
                        'y': logo.roi.y,
                        'width': logo.roi.width,
                        'height': logo.roi.height
                    },
                    'tolerance_mm': logo.tolerance_mm,
                    'detector_type': logo.detector_type
                }
                config_data['logos'].append(logo_data)

            # Save to file
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)

            messagebox.showinfo("Éxito", f"Configuración guardada en:\n{config_path}")
            logger.info(f"Configuration saved: {config_path}")

        except Exception as e:
            error_msg = f"Error guardando configuración: {e}"
            messagebox.showerror("Error", error_msg)
            logger.error(error_msg)

    def run(self):
        """Run the configuration designer"""
        # Initialize design options from existing configurations
        if self.config_root_path.exists():
            designs = [d.name for d in self.config_root_path.iterdir() if d.is_dir()]
            self.design_combo['values'] = sorted(designs)

        self.root.mainloop()

    def _draw_rulers_and_grid(self, canvas_width, canvas_height):
        """Draw rulers and grid overlay on canvas"""
        if not (self.rulers_var.get() or self.grid_var.get()):
            return

        # Use minimum calibration if not set
        if self.mm_per_pixel <= 0:
            self.mm_per_pixel = 1.0

        # Calculate spacing with minimum limits
        ruler_spacing_px = max(self.MIN_RULER_SPACING, self.ruler_spacing_mm / self.mm_per_pixel * self.canvas_scale)
        grid_spacing_px = max(self.MIN_GRID_SPACING, self.grid_spacing_mm / self.mm_per_pixel * self.canvas_scale)

        # Draw grid first (background)
        if self.grid_var.get():
            self._draw_grid_simple(canvas_width, canvas_height, grid_spacing_px)

        # Draw rulers on top
        if self.rulers_var.get():
            self._draw_rulers_simple(canvas_width, canvas_height, ruler_spacing_px)

    def _draw_grid(self, canvas_width, canvas_height, spacing_px, ruler_width=0, ruler_height=0):
        """Draw grid lines on canvas"""
        # Only draw grid if spacing is reasonable (avoid too dense grids)
        if spacing_px < 5:
            return

        # Vertical grid lines - offset by ruler width
        x = ruler_width + spacing_px
        while x < canvas_width:
            self.image_canvas.create_line(
                x, ruler_height, x, canvas_height,
                fill="#CCCCCC", width=1, tags="grid"
            )
            x += spacing_px

        # Horizontal grid lines - offset by ruler height
        y = ruler_height + spacing_px
        while y < canvas_height:
            self.image_canvas.create_line(
                ruler_width, y, canvas_width, y,
                fill="#CCCCCC", width=1, tags="grid"
            )
            y += spacing_px

    def _draw_rulers(self, canvas_width, canvas_height, spacing_px):
        """Draw rulers with measurements on canvas (legacy function - not used)"""
        pass

    def _draw_grid_simple(self, canvas_width, canvas_height, spacing_px):
        """Simple grid drawing"""
        x = spacing_px
        while x < canvas_width:
            self.image_canvas.create_line(
                x, 0, x, canvas_height,
                fill=self.GRID_COLOR, width=1, tags="grid"
            )
            x += spacing_px

        y = spacing_px
        while y < canvas_height:
            self.image_canvas.create_line(
                0, y, canvas_width, y,
                fill=self.GRID_COLOR, width=1, tags="grid"
            )
            y += spacing_px

    def _draw_rulers_simple(self, canvas_width, canvas_height, spacing_px):
        """Simple rulers drawing"""
        # Top ruler
        self.image_canvas.create_rectangle(
            0, 0, canvas_width, self.RULER_HEIGHT,
            fill=self.RULER_BG_COLOR, outline=self.RULER_BORDER_COLOR, width=1, tags="ruler"
        )

        # Left ruler
        self.image_canvas.create_rectangle(
            0, 0, self.RULER_WIDTH, canvas_height,
            fill=self.RULER_BG_COLOR, outline=self.RULER_BORDER_COLOR, width=1, tags="ruler"
        )

        # Ruler marks - horizontal
        x = 35
        mm = 0
        while x < canvas_width:
            self.image_canvas.create_line(
                x, 0, x, 25,
                fill="#666666", width=1, tags="ruler"
            )
            if mm % 20 == 0:  # Label every 20mm
                self.image_canvas.create_text(
                    x, 12, text=str(mm),
                    font=("Arial", 8), fill="#666666", tags="ruler"
                )
            x += spacing_px
            mm += self.ruler_spacing_mm

        # Ruler marks - vertical
        y = 25
        mm = 0
        while y < canvas_height:
            self.image_canvas.create_line(
                0, y, 35, y,
                fill="#666666", width=1, tags="ruler"
            )
            if mm % 20 == 0:  # Label every 20mm
                self.image_canvas.create_text(
                    17, y, text=str(mm),
                    font=("Arial", 8), fill="#666666", tags="ruler", angle=90
                )
            y += spacing_px
            mm += self.ruler_spacing_mm

    def _toggle_rulers(self):
        """Toggle ruler display"""
        self.show_rulers = self.rulers_var.get()
        if self.current_image is not None:
            self._display_image()

    def _toggle_grid(self):
        """Toggle grid display"""
        self.show_grid = self.grid_var.get()
        if self.current_image is not None:
            self._display_image()

    def _on_canvas_motion(self, event):
        """Handle mouse motion over canvas for tooltip"""
        if self.current_image is None:
            return

        # Convert canvas coordinates to image coordinates
        canvas_x = self.image_canvas.canvasx(event.x)
        canvas_y = self.image_canvas.canvasy(event.y)

        # Convert to real-world coordinates (mm)
        if self.mm_per_pixel > 0 and self.canvas_scale > 0:
            img_x = canvas_x / self.canvas_scale
            img_y = canvas_y / self.canvas_scale
            real_x_mm = img_x * self.mm_per_pixel
            real_y_mm = img_y * self.mm_per_pixel

            # Show coordinates tooltip
            self._show_coordinates_tooltip(event.x, event.y, real_x_mm, real_y_mm)

            # Check if hovering over a logo and show its dimensions
            self._check_logo_hover(real_x_mm, real_y_mm, event.x, event.y)
        else:
            self._hide_tooltip()

    def _show_coordinates_tooltip(self, x, y, real_x_mm, real_y_mm):
        """Show coordinates tooltip"""
        if self.tooltip_label:
            self.tooltip_label.destroy()

        tooltip_text = f"📍 {real_x_mm:.1f}mm, {real_y_mm:.1f}mm"

        self.tooltip_label = tk.Label(
            self.root,
            text=tooltip_text,
            background="lightyellow",
            relief="solid",
            borderwidth=1,
            font=("Arial", 9)
        )

        # Position tooltip near mouse cursor
        self.tooltip_label.place(x=x + 10, y=y + 10)

    def _check_logo_hover(self, real_x_mm, real_y_mm, cursor_x, cursor_y):
        """Check if hovering over a logo and show its dimensions"""
        if not self.current_style:
            return

        for logo in self.current_style.logos:
            # Check if cursor is within logo area
            logo_left = logo.position_mm.x - logo.roi.width * self.mm_per_pixel / 2
            logo_right = logo.position_mm.x + logo.roi.width * self.mm_per_pixel / 2
            logo_top = logo.position_mm.y - logo.roi.height * self.mm_per_pixel / 2
            logo_bottom = logo.position_mm.y + logo.roi.height * self.mm_per_pixel / 2

            if (logo_left <= real_x_mm <= logo_right and
                logo_top <= real_y_mm <= logo_bottom):

                # Show enhanced tooltip with logo info
                if self.tooltip_label:
                    self.tooltip_label.destroy()

                tooltip_text = (f"🏷️ {logo.name}\n"
                              f"📍 Pos: {logo.position_mm.x:.1f}, {logo.position_mm.y:.1f} mm\n"
                              f"📏 ROI: {logo.roi.width:.1f} × {logo.roi.height:.1f} mm\n"
                              f"🎯 Tolerancia: {logo.tolerance_mm:.1f} mm")

                self.tooltip_label = tk.Label(
                    self.root,
                    text=tooltip_text,
                    background="lightblue",
                    relief="solid",
                    borderwidth=1,
                    font=("Arial", 9),
                    justify=tk.LEFT
                )

                self.tooltip_label.place(x=cursor_x + 15, y=cursor_y + 15)
                break

    def _hide_tooltip(self):
        """Hide tooltip"""
        if self.tooltip_label:
            self.tooltip_label.destroy()
            self.tooltip_label = None

    def _add_logo_dialog(self):
        """Add a new logo through dialog"""
        if not self.current_style:
            messagebox.showwarning("Advertencia", "Crear estilo base primero")
            return

        # Simple dialog for logo name
        logo_name = simpledialog.askstring("Nuevo Logo", "Nombre del logo:")
        if not logo_name:
            return

        # Create default logo
        new_logo = Logo(
            id=f"logo_{len(self.current_style.logos) + 1}",
            name=logo_name,
            position_mm=Point(50.0, 50.0),  # Default position
            tolerance_mm=5.0,
            detector_type="template_match",
            roi=Rectangle(40.0, 40.0, 20.0, 20.0)  # Default ROI
        )

        self.current_style.logos.append(new_logo)
        self._update_logo_list()
        messagebox.showinfo("Éxito", f"Logo '{logo_name}' agregado")

    def _remove_logo(self):
        """Remove selected logo"""
        if not self.logo_list or not self.current_style:
            return

        selection = self.logo_list.curselection()
        if not selection:
            messagebox.showwarning("Advertencia", "Selecciona un logo para eliminar")
            return

        index = selection[0]
        logo = self.current_style.logos[index]

        # Confirm deletion
        result = messagebox.askyesno("Confirmar", f"¿Eliminar logo '{logo.name}'?")
        if result:
            self.current_style.logos.pop(index)
            self._update_logo_list()
            messagebox.showinfo("Éxito", f"Logo '{logo.name}' eliminado")

    def _update_logo_list(self):
        """Update the logo list display"""
        if not self.logo_list:
            return

        self.logo_list.delete(0, tk.END)

        if self.current_style:
            for logo in self.current_style.logos:
                display_text = f"{logo.name} ({logo.position_mm.x:.1f}, {logo.position_mm.y:.1f}mm)"
                self.logo_list.insert(tk.END, display_text)


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