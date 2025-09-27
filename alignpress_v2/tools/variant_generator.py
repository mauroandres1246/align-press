"""
VariantGenerator - Generación de variantes de tamaño
Extraído de ConfigDesigner usando Strangler Fig Pattern - Fase 3
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Optional
import logging

from ..config.models import Logo, Style, Variant, Point, Rectangle, create_default_config, AlignPressConfig

logger = logging.getLogger(__name__)


class VariantGenerator:
    """Gestiona la generación automática de variantes de tamaño"""

    # Configuraciones por defecto
    DEFAULT_SIZES = ["XS", "S", "M", "L", "XL", "XXL"]
    DEFAULT_SELECTED = ["S", "M", "L"]
    DEFAULT_SCALE_FACTORS = {
        "XS": 0.85,
        "S": 0.92,
        "M": 1.00,
        "L": 1.08,
        "XL": 1.15,
        "XXL": 1.25
    }

    def __init__(self, parent_window: tk.Tk):
        """
        Inicializar VariantGenerator

        Args:
            parent_window: Ventana padre para diálogos
        """
        self.parent_window = parent_window

    def generate_variants_dialog(self, current_style: Style,
                                current_config: Optional[AlignPressConfig] = None) -> bool:
        """
        Mostrar diálogo para generar variantes y ejecutar generación

        Args:
            current_style: Estilo base para generar variantes
            current_config: Configuración actual (se crea si no existe)

        Returns:
            True si se generaron variantes exitosamente, False si no
        """
        if not current_style:
            messagebox.showwarning("Advertencia", "Crear estilo base primero")
            return False

        # Crear ventana de configuración
        config = self._create_variant_config_dialog()
        if not config:
            return False  # Usuario canceló

        # Generar variantes con la configuración
        return self._generate_variants_with_config(
            current_style, config, current_config
        )

    def _create_variant_config_dialog(self) -> Optional[Dict]:
        """
        Crear diálogo de configuración de variantes

        Returns:
            Diccionario con configuración o None si se cancela
        """
        # Crear ventana modal
        dialog = tk.Toplevel(self.parent_window)
        dialog.title("Generar Variantes de Talla")
        dialog.geometry("450x350")
        dialog.transient(self.parent_window)
        dialog.grab_set()

        # Centrar ventana
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (450 // 2)
        y = (dialog.winfo_screenheight() // 2) - (350 // 2)
        dialog.geometry(f"450x350+{x}+{y}")

        result = {"cancelled": True}

        # Crear UI
        main_frame = ttk.Frame(dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # Sección de selección de tallas
        size_vars = self._create_size_selection_section(main_frame)

        # Separador
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=15)

        # Sección de factores de escala
        scale_vars = self._create_scale_factors_section(main_frame)

        # Botones
        def on_generate():
            config = self._validate_and_extract_config(size_vars, scale_vars)
            if config:
                result.update(config)
                result["cancelled"] = False
                dialog.destroy()

        def on_cancel():
            dialog.destroy()

        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(15, 0))

        ttk.Button(button_frame, text="Cancelar", command=on_cancel).pack(side=tk.RIGHT)
        ttk.Button(button_frame, text="Generar", command=on_generate).pack(side=tk.RIGHT, padx=(0, 10))

        # Esperar a que el diálogo se cierre
        dialog.wait_window()

        return None if result["cancelled"] else result

    def _create_size_selection_section(self, parent: tk.Widget) -> Dict[str, tk.BooleanVar]:
        """
        Crear sección de selección de tallas

        Args:
            parent: Widget padre

        Returns:
            Diccionario de variables booleanas por talla
        """
        ttk.Label(parent, text="🎯 Seleccionar tallas a generar:",
                 font=("Arial", 10, "bold")).pack(anchor=tk.W)

        # Frame para checkboxes en grid
        sizes_frame = ttk.Frame(parent)
        sizes_frame.pack(fill=tk.X, pady=(5, 0))

        size_vars = {}
        for i, size in enumerate(self.DEFAULT_SIZES):
            var = tk.BooleanVar(value=size in self.DEFAULT_SELECTED)
            size_vars[size] = var

            checkbox = ttk.Checkbutton(sizes_frame, text=size, variable=var)
            checkbox.grid(row=i//3, column=i%3, sticky=tk.W, padx=(0, 20), pady=2)

        return size_vars

    def _create_scale_factors_section(self, parent: tk.Widget) -> Dict[str, tk.StringVar]:
        """
        Crear sección de factores de escala

        Args:
            parent: Widget padre

        Returns:
            Diccionario de variables de string por talla
        """
        ttk.Label(parent, text="📏 Factores de escala (relativo a M):",
                 font=("Arial", 10, "bold")).pack(anchor=tk.W)

        # Frame para entradas en grid
        scale_frame = ttk.Frame(parent)
        scale_frame.pack(fill=tk.X, pady=(5, 0))

        scale_vars = {}
        for i, size in enumerate(self.DEFAULT_SIZES):
            row = i // 2
            col = (i % 2) * 2

            ttk.Label(scale_frame, text=f"{size}:").grid(
                row=row, column=col, sticky=tk.W, pady=2
            )

            var = tk.StringVar(value=str(self.DEFAULT_SCALE_FACTORS[size]))
            scale_vars[size] = var

            entry = ttk.Entry(scale_frame, textvariable=var, width=8)
            entry.grid(row=row, column=col+1, padx=(5, 20), pady=2)

        return scale_vars

    def _validate_and_extract_config(self, size_vars: Dict[str, tk.BooleanVar],
                                   scale_vars: Dict[str, tk.StringVar]) -> Optional[Dict]:
        """
        Validar y extraer configuración del diálogo

        Args:
            size_vars: Variables de selección de tallas
            scale_vars: Variables de factores de escala

        Returns:
            Configuración validada o None si hay errores
        """
        selected_sizes = [size for size, var in size_vars.items() if var.get()]

        if not selected_sizes:
            messagebox.showerror("Error", "Selecciona al menos una talla")
            return None

        scale_factors = {}
        for size in selected_sizes:
            try:
                factor = float(scale_vars[size].get())
                if factor <= 0:
                    raise ValueError("Factor debe ser positivo")
                scale_factors[size] = factor
            except ValueError:
                messagebox.showerror("Error", f"Factor de escala inválido para {size}")
                return None

        return {
            "selected_sizes": selected_sizes,
            "scale_factors": scale_factors
        }

    def _generate_variants_with_config(self, base_style: Style, config: Dict,
                                     current_config: Optional[AlignPressConfig]) -> bool:
        """
        Generar variantes con configuración específica

        Args:
            base_style: Estilo base
            config: Configuración de generación
            current_config: Configuración actual

        Returns:
            True si se generó exitosamente, False si no
        """
        try:
            # Inicializar configuración si no existe
            if not current_config:
                current_config = create_default_config()

            # Remover variantes existentes para este estilo
            current_config.library.variants = [
                v for v in current_config.library.variants
                if v.base_style_id != base_style.id
            ]

            # Generar variantes para cada talla seleccionada
            generated_count = 0
            for size in config["selected_sizes"]:
                variant = self._create_size_variant(
                    base_style, size, config["scale_factors"][size]
                )
                current_config.library.variants.append(variant)
                generated_count += 1

            # Mostrar resultado
            messagebox.showinfo(
                "✅ Éxito",
                f"Se generaron {generated_count} variantes de talla\n\n"
                f"📋 Tallas: {', '.join(config['selected_sizes'])}\n"
                f"💾 Guarda la configuración para conservar los cambios"
            )

            logger.info(f"Generated {generated_count} size variants for style {base_style.id}")
            return True

        except Exception as e:
            error_msg = f"Error generando variantes: {str(e)}"
            messagebox.showerror("❌ Error", error_msg)
            logger.error(f"Error generating variants: {e}")
            return False

    def _create_size_variant(self, base_style: Style, size: str, scale_factor: float) -> Variant:
        """
        Crear variante de tamaño específica

        Args:
            base_style: Estilo base
            size: Talla (ej: "L", "XL")
            scale_factor: Factor de escala

        Returns:
            Variante creada
        """
        # Escalar todos los logos
        scaled_logos = []
        for logo in base_style.logos:
            scaled_logo = Logo(
                id=logo.id,
                name=logo.name,
                position_mm=Point(
                    logo.position_mm.x * scale_factor,
                    logo.position_mm.y * scale_factor
                ),
                tolerance_mm=logo.tolerance_mm * scale_factor,
                detector_type=logo.detector_type,
                roi=Rectangle(
                    logo.roi.x * scale_factor,
                    logo.roi.y * scale_factor,
                    logo.roi.width * scale_factor,
                    logo.roi.height * scale_factor
                )
            )
            scaled_logos.append(scaled_logo)

        # Crear variante
        variant = Variant(
            id=f"{base_style.id}_{size.lower()}",
            name=f"{base_style.name} - {size}",
            base_style_id=base_style.id,
            size_category=size.lower(),
            logos=scaled_logos
        )

        return variant

    def get_available_sizes(self) -> List[str]:
        """
        Obtener tallas disponibles

        Returns:
            Lista de tallas disponibles
        """
        return self.DEFAULT_SIZES.copy()

    def get_default_scale_factor(self, size: str) -> float:
        """
        Obtener factor de escala por defecto para una talla

        Args:
            size: Talla

        Returns:
            Factor de escala por defecto
        """
        return self.DEFAULT_SCALE_FACTORS.get(size, 1.0)

    def calculate_scaled_dimensions(self, base_width: float, base_height: float,
                                  scale_factor: float) -> tuple[float, float]:
        """
        Calcular dimensiones escaladas

        Args:
            base_width: Ancho base
            base_height: Alto base
            scale_factor: Factor de escala

        Returns:
            Tuple con (ancho_escalado, alto_escalado)
        """
        return base_width * scale_factor, base_height * scale_factor