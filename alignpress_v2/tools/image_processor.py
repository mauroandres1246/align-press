"""
ImageProcessor - Procesamiento de imágenes y templates
Extraído de ConfigDesigner para seguir principio de responsabilidad única
"""
import cv2
import numpy as np
from PIL import Image, ImageTk
from typing import Dict, Optional, Tuple, Union
import tkinter as tk
from pathlib import Path

from ..config.models import Logo, Style


class ImageProcessor:
    """Gestiona el procesamiento de imágenes, templates y visualización"""

    # Constantes para escalado y visualización
    MAX_CANVAS_WIDTH = 800
    MAX_CANVAS_HEIGHT = 600
    DEFAULT_SCALE = 1.0

    def __init__(self):
        """Inicializar ImageProcessor"""
        self.current_image: Optional[np.ndarray] = None
        self.canvas_scale: float = self.DEFAULT_SCALE
        self.photo_image: Optional[ImageTk.PhotoImage] = None

        # Template management
        self.logo_templates: Dict[str, np.ndarray] = {}
        self.template_references: Dict[str, Dict] = {}
        self.current_template_overlay: Optional[np.ndarray] = None
        self.template_positions: Dict[str, Dict] = {}

    def load_image(self, file_path: str) -> bool:
        """
        Cargar imagen desde archivo

        Args:
            file_path: Ruta del archivo de imagen

        Returns:
            True si se cargó exitosamente, False si no
        """
        try:
            # Limpiar referencias previas para evitar problemas de memoria
            self.photo_image = None

            # Cargar nueva imagen
            self.current_image = cv2.imread(file_path)
            if self.current_image is None:
                raise ValueError("No se pudo cargar la imagen")

            # Validar imagen
            if self.current_image.size == 0:
                raise ValueError("La imagen está vacía")

            return True

        except Exception as e:
            print(f"Error cargando imagen: {e}")
            return False

    def calculate_canvas_scale(self, image_width: int, image_height: int) -> float:
        """
        Calcular escala para ajustar imagen al canvas

        Args:
            image_width: Ancho de la imagen
            image_height: Alto de la imagen

        Returns:
            Factor de escala calculado
        """
        scale_x = self.MAX_CANVAS_WIDTH / image_width
        scale_y = self.MAX_CANVAS_HEIGHT / image_height
        return min(scale_x, scale_y, 1.0)  # No aumentar más allá del tamaño original

    def resize_image_for_display(self, image: np.ndarray, scale: float) -> np.ndarray:
        """
        Redimensionar imagen para visualización

        Args:
            image: Imagen a redimensionar
            scale: Factor de escala

        Returns:
            Imagen redimensionada
        """
        if scale == 1.0:
            return image

        height, width = image.shape[:2]
        new_width = int(width * scale)
        new_height = int(height * scale)

        return cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)

    def convert_cv2_to_pil(self, cv2_image: np.ndarray) -> Image.Image:
        """
        Convertir imagen OpenCV a PIL

        Args:
            cv2_image: Imagen en formato OpenCV (BGR)

        Returns:
            Imagen en formato PIL (RGB)
        """
        # Convertir de BGR a RGB
        rgb_image = cv2.cvtColor(cv2_image, cv2.COLOR_BGR2RGB)
        return Image.fromarray(rgb_image)

    def create_photo_image(self, image: np.ndarray) -> ImageTk.PhotoImage:
        """
        Crear PhotoImage para Tkinter desde imagen OpenCV

        Args:
            image: Imagen en formato OpenCV

        Returns:
            PhotoImage listo para mostrar en Tkinter
        """
        pil_image = self.convert_cv2_to_pil(image)
        return ImageTk.PhotoImage(pil_image)

    def prepare_image_for_canvas(self, image: Optional[np.ndarray] = None) -> Optional[ImageTk.PhotoImage]:
        """
        Preparar imagen para mostrar en canvas

        Args:
            image: Imagen opcional, usa current_image si no se proporciona

        Returns:
            PhotoImage preparado o None si no hay imagen
        """
        if image is None:
            image = self.current_image

        if image is None:
            return None

        # Calcular escala si no está definida
        if self.canvas_scale == self.DEFAULT_SCALE:
            height, width = image.shape[:2]
            self.canvas_scale = self.calculate_canvas_scale(width, height)

        # Redimensionar imagen
        display_image = self.resize_image_for_display(image, self.canvas_scale)

        # Crear PhotoImage
        self.photo_image = self.create_photo_image(display_image)
        return self.photo_image

    def load_template(self, template_path: str, template_id: str) -> bool:
        """
        Cargar template de logo

        Args:
            template_path: Ruta del archivo de template
            template_id: ID único para el template

        Returns:
            True si se cargó exitosamente, False si no
        """
        try:
            template_image = cv2.imread(template_path)
            if template_image is None:
                raise ValueError(f"No se pudo cargar el template: {template_path}")

            self.logo_templates[template_id] = template_image
            self.template_references[template_id] = {
                'path': template_path,
                'original_size': template_image.shape[:2]
            }

            return True

        except Exception as e:
            print(f"Error cargando template {template_id}: {e}")
            return False

    def create_template_overlay(self, template_id: str, position: Tuple[int, int],
                              size: Tuple[int, int]) -> Optional[np.ndarray]:
        """
        Crear overlay de template sobre la imagen actual

        Args:
            template_id: ID del template
            position: Posición (x, y) en píxeles de imagen
            size: Tamaño (width, height) en píxeles

        Returns:
            Imagen con overlay o None si no es posible
        """
        if self.current_image is None or template_id not in self.logo_templates:
            return None

        try:
            # Copiar imagen base
            overlay_image = self.current_image.copy()

            # Obtener template
            template = self.logo_templates[template_id]

            # Redimensionar template al tamaño deseado
            resized_template = cv2.resize(template, size, interpolation=cv2.INTER_AREA)

            # Calcular posición de inserción
            x, y = position
            h, w = resized_template.shape[:2]

            # Verificar que el template cabe en la imagen
            img_h, img_w = overlay_image.shape[:2]
            if x + w > img_w or y + h > img_h or x < 0 or y < 0:
                return None

            # Crear máscara para transparencia (opcional)
            # Por ahora, simplemente copiamos el template
            overlay_image[y:y+h, x:x+w] = resized_template

            return overlay_image

        except Exception as e:
            print(f"Error creando overlay para template {template_id}: {e}")
            return None

    def update_template_position(self, template_id: str, position: Tuple[int, int],
                               size: Tuple[int, int]):
        """
        Actualizar posición de template

        Args:
            template_id: ID del template
            position: Nueva posición (x, y)
            size: Nuevo tamaño (width, height)
        """
        self.template_positions[template_id] = {
            'position': position,
            'size': size
        }

        # Actualizar overlay
        self.current_template_overlay = self.create_template_overlay(
            template_id, position, size
        )

    def get_template_info(self, template_id: str) -> Optional[Dict]:
        """
        Obtener información de un template

        Args:
            template_id: ID del template

        Returns:
            Diccionario con información del template o None
        """
        if template_id in self.template_references:
            info = self.template_references[template_id].copy()
            if template_id in self.template_positions:
                info.update(self.template_positions[template_id])
            return info
        return None

    def convert_pixel_to_mm(self, pixel_coords: Tuple[int, int],
                          mm_per_pixel: float) -> Tuple[float, float]:
        """
        Convertir coordenadas de píxeles a milímetros

        Args:
            pixel_coords: Coordenadas en píxeles (x, y)
            mm_per_pixel: Factor de conversión

        Returns:
            Coordenadas en milímetros (x, y)
        """
        x_px, y_px = pixel_coords
        x_mm = x_px * mm_per_pixel
        y_mm = y_px * mm_per_pixel
        return x_mm, y_mm

    def convert_mm_to_pixel(self, mm_coords: Tuple[float, float],
                          mm_per_pixel: float) -> Tuple[int, int]:
        """
        Convertir coordenadas de milímetros a píxeles

        Args:
            mm_coords: Coordenadas en milímetros (x, y)
            mm_per_pixel: Factor de conversión

        Returns:
            Coordenadas en píxeles (x, y)
        """
        x_mm, y_mm = mm_coords
        x_px = int(x_mm / mm_per_pixel)
        y_px = int(y_mm / mm_per_pixel)
        return x_px, y_px

    def calculate_logo_canvas_position(self, logo: Logo, mm_per_pixel: float) -> Tuple[int, int]:
        """
        Calcular posición de logo en el canvas con escala

        Args:
            logo: Objeto Logo con posición en mm
            mm_per_pixel: Factor de calibración

        Returns:
            Posición en píxeles del canvas (x, y)
        """
        if mm_per_pixel > 0:
            x_px = (logo.position_mm.x / mm_per_pixel) * self.canvas_scale
            y_px = (logo.position_mm.y / mm_per_pixel) * self.canvas_scale
        else:
            # Fallback si no hay calibración
            x_px = logo.position_mm.x * self.canvas_scale
            y_px = logo.position_mm.y * self.canvas_scale

        return int(x_px), int(y_px)

    def calculate_logo_roi_canvas(self, logo: Logo, mm_per_pixel: float) -> Tuple[int, int, int, int]:
        """
        Calcular ROI de logo en el canvas con escala

        Args:
            logo: Objeto Logo con ROI en mm
            mm_per_pixel: Factor de calibración

        Returns:
            ROI en píxeles del canvas (x, y, width, height)
        """
        if mm_per_pixel > 0:
            roi_x = (logo.roi.x / mm_per_pixel) * self.canvas_scale
            roi_y = (logo.roi.y / mm_per_pixel) * self.canvas_scale
            roi_w = (logo.roi.width / mm_per_pixel) * self.canvas_scale
            roi_h = (logo.roi.height / mm_per_pixel) * self.canvas_scale
        else:
            # Fallback si no hay calibración
            roi_x = logo.roi.x * self.canvas_scale
            roi_y = logo.roi.y * self.canvas_scale
            roi_w = logo.roi.width * self.canvas_scale
            roi_h = logo.roi.height * self.canvas_scale

        return int(roi_x), int(roi_y), int(roi_w), int(roi_h)

    def clear_templates(self):
        """Limpiar todos los templates cargados"""
        self.logo_templates.clear()
        self.template_references.clear()
        self.template_positions.clear()
        self.current_template_overlay = None

    def get_image_dimensions(self) -> Optional[Tuple[int, int]]:
        """
        Obtener dimensiones de la imagen actual

        Returns:
            Tuple con (width, height) o None si no hay imagen
        """
        if self.current_image is not None:
            height, width = self.current_image.shape[:2]
            return width, height
        return None

    def reset(self):
        """Reiniciar el procesador de imágenes"""
        self.current_image = None
        self.canvas_scale = self.DEFAULT_SCALE
        self.photo_image = None
        self.clear_templates()