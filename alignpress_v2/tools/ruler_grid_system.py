"""
RulerGridSystem - Sistema de reglas y grid para medición visual
Extraído de ConfigDesigner para seguir principio de responsabilidad única
"""
import tkinter as tk
from typing import Optional


class RulerGridSystem:
    """Gestiona la visualización de reglas y grid para medición visual"""

    # Constantes para visualización
    RULER_WIDTH = 40           # Ancho de regla vertical en píxeles
    RULER_HEIGHT = 30          # Alto de regla horizontal en píxeles
    MIN_RULER_SPACING = 20     # Espaciado mínimo para reglas
    MIN_GRID_SPACING = 15      # Espaciado mínimo para grid
    GRID_COLOR = "#DDDDDD"     # Color de líneas de grid
    RULER_BG_COLOR = "#F5F5F5" # Color de fondo de reglas
    RULER_BORDER_COLOR = "#999999"  # Color de borde de reglas

    def __init__(self, canvas: tk.Canvas):
        """
        Inicializar sistema de reglas y grid

        Args:
            canvas: Canvas de Tkinter donde dibujar
        """
        self.canvas = canvas
        self.show_rulers = True
        self.show_grid = True
        self.grid_spacing_mm = 10.0     # Espaciado del grid en mm
        self.ruler_spacing_mm = 10.0    # Espaciado de marcas de reglas en mm

    def set_visibility(self, show_rulers: bool, show_grid: bool):
        """
        Configurar visibilidad de reglas y grid

        Args:
            show_rulers: Mostrar reglas
            show_grid: Mostrar grid
        """
        self.show_rulers = show_rulers
        self.show_grid = show_grid

    def set_spacing(self, grid_spacing_mm: float, ruler_spacing_mm: float):
        """
        Configurar espaciado de grid y reglas

        Args:
            grid_spacing_mm: Espaciado del grid en mm
            ruler_spacing_mm: Espaciado de marcas de reglas en mm
        """
        self.grid_spacing_mm = grid_spacing_mm
        self.ruler_spacing_mm = ruler_spacing_mm

    def clear_rulers_and_grid(self):
        """Limpiar todas las reglas y grid del canvas"""
        self.canvas.delete("ruler")
        self.canvas.delete("grid")

    def draw_rulers_and_grid(self, canvas_width: int, canvas_height: int,
                           mm_per_pixel: float, canvas_scale: float):
        """
        Dibujar reglas y grid en el canvas

        Args:
            canvas_width: Ancho del canvas
            canvas_height: Alto del canvas
            mm_per_pixel: Factor de calibración
            canvas_scale: Escala del canvas
        """
        # Limpiar elementos previos
        self.clear_rulers_and_grid()

        # Validar calibración
        if mm_per_pixel <= 0:
            mm_per_pixel = 1.0

        # Calcular espaciado con límites mínimos
        ruler_spacing_px = max(
            self.MIN_RULER_SPACING,
            self.ruler_spacing_mm / mm_per_pixel * canvas_scale
        )
        grid_spacing_px = max(
            self.MIN_GRID_SPACING,
            self.grid_spacing_mm / mm_per_pixel * canvas_scale
        )

        # Dibujar grid primero (fondo)
        if self.show_grid:
            self._draw_grid_simple(canvas_width, canvas_height, grid_spacing_px)

        # Dibujar reglas encima
        if self.show_rulers:
            self._draw_rulers_simple(canvas_width, canvas_height, ruler_spacing_px)

    def _draw_grid_simple(self, canvas_width: int, canvas_height: int, spacing_px: float):
        """
        Dibujar grid simplificado

        Args:
            canvas_width: Ancho del canvas
            canvas_height: Alto del canvas
            spacing_px: Espaciado en píxeles
        """
        # Líneas verticales
        x = spacing_px
        while x < canvas_width:
            self.canvas.create_line(
                x, 0, x, canvas_height,
                fill=self.GRID_COLOR, width=1, tags="grid"
            )
            x += spacing_px

        # Líneas horizontales
        y = spacing_px
        while y < canvas_height:
            self.canvas.create_line(
                0, y, canvas_width, y,
                fill=self.GRID_COLOR, width=1, tags="grid"
            )
            y += spacing_px

    def _draw_rulers_simple(self, canvas_width: int, canvas_height: int, spacing_px: float):
        """
        Dibujar reglas simplificadas

        Args:
            canvas_width: Ancho del canvas
            canvas_height: Alto del canvas
            spacing_px: Espaciado en píxeles
        """
        # Regla horizontal superior
        self.canvas.create_rectangle(
            0, 0, canvas_width, self.RULER_HEIGHT,
            fill=self.RULER_BG_COLOR, outline=self.RULER_BORDER_COLOR,
            width=1, tags="ruler"
        )

        # Regla vertical izquierda
        self.canvas.create_rectangle(
            0, 0, self.RULER_WIDTH, canvas_height,
            fill=self.RULER_BG_COLOR, outline=self.RULER_BORDER_COLOR,
            width=1, tags="ruler"
        )

        # Marcas de regla horizontal
        self._draw_ruler_marks_horizontal(canvas_width, spacing_px)

        # Marcas de regla vertical
        self._draw_ruler_marks_vertical(canvas_height, spacing_px)

    def _draw_ruler_marks_horizontal(self, canvas_width: int, spacing_px: float):
        """
        Dibujar marcas en la regla horizontal

        Args:
            canvas_width: Ancho del canvas
            spacing_px: Espaciado en píxeles
        """
        x = spacing_px
        mm = self.ruler_spacing_mm

        while x < canvas_width:
            # Línea de marca
            self.canvas.create_line(
                x, 0, x, self.RULER_HEIGHT,
                fill=self.RULER_BORDER_COLOR, width=1, tags="ruler"
            )

            # Etiqueta de medida
            if x > self.RULER_WIDTH:  # No solapar con regla vertical
                self.canvas.create_text(
                    x, self.RULER_HEIGHT // 2,
                    text=f"{int(mm)}", font=("Arial", 8),
                    fill="#666666", tags="ruler"
                )

            x += spacing_px
            mm += self.ruler_spacing_mm

    def _draw_ruler_marks_vertical(self, canvas_height: int, spacing_px: float):
        """
        Dibujar marcas en la regla vertical

        Args:
            canvas_height: Alto del canvas
            spacing_px: Espaciado en píxeles
        """
        y = spacing_px
        mm = self.ruler_spacing_mm

        while y < canvas_height:
            # Línea de marca
            self.canvas.create_line(
                0, y, self.RULER_WIDTH, y,
                fill=self.RULER_BORDER_COLOR, width=1, tags="ruler"
            )

            # Etiqueta de medida (rotada)
            if y > self.RULER_HEIGHT:  # No solapar con regla horizontal
                self.canvas.create_text(
                    self.RULER_WIDTH // 2, y,
                    text=f"{int(mm)}", font=("Arial", 8),
                    fill="#666666", tags="ruler", angle=90
                )

            y += spacing_px
            mm += self.ruler_spacing_mm

    def get_ruler_offset(self) -> tuple[int, int]:
        """
        Obtener offset necesario para las reglas

        Returns:
            Tuple con (offset_x, offset_y) en píxeles
        """
        offset_x = self.RULER_WIDTH if self.show_rulers else 0
        offset_y = self.RULER_HEIGHT if self.show_rulers else 0
        return offset_x, offset_y

    def adjust_canvas_scroll_region(self, total_width: int, total_height: int):
        """
        Ajustar región de scroll del canvas para incluir reglas

        Args:
            total_width: Ancho total incluyendo reglas
            total_height: Alto total incluyendo reglas
        """
        self.canvas.configure(scrollregion=(0, 0, total_width, total_height))

    def convert_canvas_to_ruler_coords(self, canvas_x: int, canvas_y: int) -> tuple[int, int]:
        """
        Convertir coordenadas del canvas a coordenadas relativas a las reglas

        Args:
            canvas_x: Coordenada X del canvas
            canvas_y: Coordenada Y del canvas

        Returns:
            Coordenadas ajustadas (x, y)
        """
        offset_x, offset_y = self.get_ruler_offset()
        return canvas_x - offset_x, canvas_y - offset_y

    def convert_ruler_to_canvas_coords(self, ruler_x: int, ruler_y: int) -> tuple[int, int]:
        """
        Convertir coordenadas relativas a las reglas a coordenadas del canvas

        Args:
            ruler_x: Coordenada X relativa a reglas
            ruler_y: Coordenada Y relativa a reglas

        Returns:
            Coordenadas del canvas (x, y)
        """
        offset_x, offset_y = self.get_ruler_offset()
        return ruler_x + offset_x, ruler_y + offset_y

    def is_point_in_ruler_area(self, canvas_x: int, canvas_y: int) -> bool:
        """
        Verificar si un punto está en el área de las reglas

        Args:
            canvas_x: Coordenada X del canvas
            canvas_y: Coordenada Y del canvas

        Returns:
            True si está en área de reglas, False si no
        """
        if not self.show_rulers:
            return False

        # Verificar si está en regla horizontal o vertical
        in_horizontal_ruler = (canvas_y <= self.RULER_HEIGHT)
        in_vertical_ruler = (canvas_x <= self.RULER_WIDTH)

        return in_horizontal_ruler or in_vertical_ruler

    def get_measurement_at_position(self, canvas_x: int, canvas_y: int,
                                  mm_per_pixel: float, canvas_scale: float) -> tuple[float, float]:
        """
        Obtener medida en mm en una posición específica

        Args:
            canvas_x: Coordenada X del canvas
            canvas_y: Coordenada Y del canvas
            mm_per_pixel: Factor de calibración
            canvas_scale: Escala del canvas

        Returns:
            Medidas en mm (x_mm, y_mm)
        """
        # Ajustar por offset de reglas
        ruler_x, ruler_y = self.convert_canvas_to_ruler_coords(canvas_x, canvas_y)

        # Convertir a coordenadas de imagen
        if canvas_scale > 0:
            img_x = ruler_x / canvas_scale
            img_y = ruler_y / canvas_scale
        else:
            img_x = ruler_x
            img_y = ruler_y

        # Convertir a mm
        x_mm = img_x * mm_per_pixel if mm_per_pixel > 0 else img_x
        y_mm = img_y * mm_per_pixel if mm_per_pixel > 0 else img_y

        return x_mm, y_mm

    def create_measurement_tooltip(self, parent: tk.Widget, x: int, y: int,
                                 x_mm: float, y_mm: float) -> tk.Label:
        """
        Crear tooltip con medidas

        Args:
            parent: Widget padre
            x: Posición X del tooltip
            y: Posición Y del tooltip
            x_mm: Medida X en mm
            y_mm: Medida Y en mm

        Returns:
            Label del tooltip
        """
        tooltip_text = f"📍 {x_mm:.1f}mm, {y_mm:.1f}mm"

        tooltip_label = tk.Label(
            parent,
            text=tooltip_text,
            background="lightyellow",
            relief="solid",
            borderwidth=1,
            font=("Arial", 9)
        )

        # Posicionar tooltip cerca del cursor
        tooltip_label.place(x=x + 10, y=y + 10)

        return tooltip_label