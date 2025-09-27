"""
TemplateOverlayManager - Gestión de overlays de templates sobre imágenes
Extraído de ConfigDesigner usando Strangler Fig Pattern - Fase 3
"""
import cv2
import numpy as np
from typing import Dict, Tuple, Optional, Any
import logging

logger = logging.getLogger(__name__)


class TemplateOverlayManager:
    """Gestiona la aplicación de overlays de templates sobre imágenes"""

    # Configuraciones por defecto
    DEFAULT_LOGO_SIZE_MM = (30.0, 30.0)  # Tamaño por defecto de logo en mm
    DEFAULT_OVERLAY_ALPHA = 0.7          # Transparencia del overlay
    MAX_TEMPLATE_RATIO = 0.125           # Máximo 12.5% del tamaño de imagen
    FORCE_300_DPI = True                 # Forzar siempre 300 DPI para logos

    def __init__(self):
        """Inicializar TemplateOverlayManager"""
        self.template_size = None
        self.template_size_mm = None
        self.last_template_id = None
        self.cached_template = None

    def apply_template_overlay(self, base_image: np.ndarray,
                             template_id: str,
                             template_image: np.ndarray,
                             template_position: Tuple[int, int],
                             mm_per_pixel: float = 0.0,
                             template_references: Optional[Dict] = None) -> np.ndarray:
        """
        Aplicar overlay de template sobre imagen base

        Args:
            base_image: Imagen base donde aplicar overlay
            template_id: ID del template
            template_image: Imagen del template
            template_position: Posición (x, y) para centrar el template
            mm_per_pixel: Factor de calibración (opcional)
            template_references: Referencias de tamaño de templates

        Returns:
            Imagen con overlay aplicado
        """
        if base_image is None or template_image is None:
            logger.warning("Base image or template image is None")
            return base_image

        try:
            # Preparar template para overlay
            processed_template = self._prepare_template_for_overlay(
                template_image, template_id, mm_per_pixel, template_references
            )

            # Calcular posición final del template
            final_position = self._calculate_template_position(
                base_image, processed_template, template_position
            )

            # Crear overlay semi-transparente
            return self._create_template_overlay(
                base_image, processed_template, final_position
            )

        except Exception as e:
            logger.error(f"Error applying template overlay: {e}")
            return base_image

    def _prepare_template_for_overlay(self, template_image: np.ndarray,
                                    template_id: str,
                                    mm_per_pixel: float,
                                    template_references: Optional[Dict]) -> np.ndarray:
        """
        Preparar template para overlay (conversión de color y escalado)

        Args:
            template_image: Imagen del template original
            template_id: ID del template
            mm_per_pixel: Factor de calibración
            template_references: Referencias de tamaño

        Returns:
            Template procesado y escalado
        """
        # Convertir a formato BGR estándar
        template_bgr = self._convert_template_to_bgr(template_image)

        # Debug: Log valores de calibración
        logger.info(f"Template sizing - ID: {template_id}, mm_per_pixel: {mm_per_pixel}")

        # Calcular tamaño target
        target_size = self._calculate_target_template_size(
            template_bgr, template_id, mm_per_pixel, template_references
        )

        # Redimensionar template
        if target_size != template_bgr.shape[:2][::-1]:  # (width, height)
            template_bgr = cv2.resize(template_bgr, target_size)

        return template_bgr

    def _convert_template_to_bgr(self, template_image: np.ndarray) -> np.ndarray:
        """
        Convertir template a formato BGR

        Args:
            template_image: Imagen original del template

        Returns:
            Template en formato BGR
        """
        if len(template_image.shape) == 3 and template_image.shape[2] == 4:
            # RGBA/BGRA
            return cv2.cvtColor(template_image, cv2.COLOR_BGRA2BGR)
        elif len(template_image.shape) == 3 and template_image.shape[2] == 3:
            # Ya está en BGR/RGB
            return template_image
        elif len(template_image.shape) == 2:
            # Escala de grises
            return cv2.cvtColor(template_image, cv2.COLOR_GRAY2BGR)
        else:
            # Formato desconocido, intentar usar tal como está
            logger.warning(f"Unknown template format: {template_image.shape}")
            return template_image

    def _calculate_target_template_size(self, template_image: np.ndarray,
                                      template_id: str,
                                      mm_per_pixel: float,
                                      template_references: Optional[Dict]) -> Tuple[int, int]:
        """
        Calcular tamaño target del template

        Prioridad:
        1. Tamaño original del PNG (preservar dimensiones reales)
        2. Tamaño definido en template_references
        3. Fallback a tamaño por defecto

        Args:
            template_image: Imagen del template
            template_id: ID del template
            mm_per_pixel: Factor de calibración
            template_references: Referencias de tamaño

        Returns:
            Tuple con (width, height) en píxeles
        """
        template_height, template_width = template_image.shape[:2]

        # Obtener información del template
        template_info = template_references.get(template_id, {}) if template_references else {}

        # PRIORIDAD 1: Verificar si se debe usar tamaño original
        # Usar configuración específica del template o configuración global
        use_original_size = self.get_template_sizing_mode(template_id)

        if use_original_size:
            # Usar tamaño original del PNG con límites de seguridad
            return self._calculate_size_original_with_limits(
                template_width, template_height, template_info
            )
        elif mm_per_pixel > 0:
            # PRIORIDAD 2: Usar calibración en mm si está configurado
            return self._calculate_size_with_calibration(
                template_id, mm_per_pixel, template_references
            )
        else:
            # PRIORIDAD 3: Fallback a tamaño en píxeles
            return self._calculate_size_pixel_fallback(template_width, template_height)

    def _calculate_size_with_calibration(self, template_id: str,
                                       mm_per_pixel: float,
                                       template_references: Optional[Dict]) -> Tuple[int, int]:
        """
        Calcular tamaño usando calibración en mm

        Args:
            template_id: ID del template
            mm_per_pixel: Factor de calibración
            template_references: Referencias de tamaño

        Returns:
            Tuple con (width, height) en píxeles
        """
        # Obtener información del template
        template_info = template_references.get(template_id, {}) if template_references else {}

        # Si está habilitado FORCE_300_DPI, usar siempre 300 DPI en lugar del mm_per_pixel recibido
        if self.FORCE_300_DPI:
            mm_per_pixel = 25.4 / 300.0
            logger.info(f"Forzando 300 DPI para logo: {mm_per_pixel:.6f} mm/pixel")

        # Usar tamaño definido o por defecto
        if 'size_mm' in template_info:
            target_width_mm, target_height_mm = template_info['size_mm']
        else:
            target_width_mm, target_height_mm = self.DEFAULT_LOGO_SIZE_MM

        # Convertir mm a píxeles
        new_width = int(target_width_mm / mm_per_pixel)
        new_height = int(target_height_mm / mm_per_pixel)

        # Guardar tamaños calculados
        self.template_size = (new_width, new_height)
        self.template_size_mm = (target_width_mm, target_height_mm)

        return new_width, new_height

    def _calculate_size_pixel_fallback(self, template_width: int,
                                     template_height: int) -> Tuple[int, int]:
        """
        Calcular tamaño usando fallback en píxeles - SOLO para casos extremos

        Args:
            template_width: Ancho original del template
            template_height: Alto original del template

        Returns:
            Tuple con (width, height) en píxeles
        """
        # Aumentar límites para permitir logos más grandes por defecto
        max_size = 400  # Aumentado de 100 a 400 píxeles

        if max(template_width, template_height) > max_size:
            scale = max_size / max(template_width, template_height)
            new_width = int(template_width * scale)
            new_height = int(template_height * scale)
        else:
            new_width = template_width
            new_height = template_height

        self.template_size = (new_width, new_height)

        # Calcular tamaño en mm siempre con 300 DPI para consistencia
        mm_per_pixel_300dpi = 25.4 / 300.0
        self.template_size_mm = (new_width * mm_per_pixel_300dpi, new_height * mm_per_pixel_300dpi)

        return new_width, new_height

    def _calculate_size_original_with_limits(self, template_width: int,
                                           template_height: int,
                                           template_info: Dict) -> Tuple[int, int]:
        """
        Calcular tamaño usando dimensiones originales del PNG con límites de seguridad

        Args:
            template_width: Ancho original del template
            template_height: Alto original del template
            template_info: Información del template con configuraciones

        Returns:
            Tuple con (width, height) en píxeles
        """
        # Obtener límites configurables - Permitir logos de alta resolución (hasta 4K)
        max_width = template_info.get('max_width', 4000)   # Límite máximo de ancho - 4K compatible
        max_height = template_info.get('max_height', 4500) # Límite máximo de alto - 4K+ compatible
        max_ratio = template_info.get('max_ratio', 0.9)    # Máximo 90% de la imagen base

        # Usar tamaño original como punto de partida
        new_width = template_width
        new_height = template_height

        # Aplicar límites de seguridad
        if new_width > max_width or new_height > max_height:
            # Redimensionar manteniendo aspecto
            scale_w = max_width / new_width if new_width > max_width else 1.0
            scale_h = max_height / new_height if new_height > max_height else 1.0
            scale = min(scale_w, scale_h)

            new_width = int(new_width * scale)
            new_height = int(new_height * scale)

        # Guardar tamaños calculados
        self.template_size = (new_width, new_height)

        # Calcular tamaño en mm usando el factor de calibración correcto
        # Si no hay calibración específica, asumir 300 DPI (estándar de impresión)
        if 'mm_per_pixel' in template_info and template_info['mm_per_pixel'] > 0:
            mm_per_pixel_for_calc = template_info['mm_per_pixel']
        else:
            # Factor para 300 DPI: 25.4mm / 300dpi = 0.0847 mm/pixel
            mm_per_pixel_for_calc = 25.4 / 300.0

        self.template_size_mm = (new_width * mm_per_pixel_for_calc, new_height * mm_per_pixel_for_calc)

        logger.info(f"Template size calculated: {new_width}x{new_height}px = {self.template_size_mm[0]:.1f}x{self.template_size_mm[1]:.1f}mm")

        return new_width, new_height

    def _calculate_template_position(self, base_image: np.ndarray,
                                   template_image: np.ndarray,
                                   template_position: Tuple[int, int]) -> Tuple[int, int]:
        """
        Calcular posición final del template con bounds checking

        Args:
            base_image: Imagen base
            template_image: Template procesado
            template_position: Posición deseada (centro)

        Returns:
            Posición final (esquina superior izquierda)
        """
        template_height, template_width = template_image.shape[:2]
        base_height, base_width = base_image.shape[:2]

        # Centrar en la posición deseada
        pos_x = template_position[0] - template_width // 2
        pos_y = template_position[1] - template_height // 2

        # Asegurar que el template esté dentro de los límites
        pos_x = max(0, min(pos_x, base_width - template_width))
        pos_y = max(0, min(pos_y, base_height - template_height))

        return pos_x, pos_y

    def _create_template_overlay(self, base_image: np.ndarray,
                               template_image: np.ndarray,
                               position: Tuple[int, int]) -> np.ndarray:
        """
        Crear overlay semi-transparente del template

        Args:
            base_image: Imagen base
            template_image: Template procesado
            position: Posición (x, y) de la esquina superior izquierda

        Returns:
            Imagen con overlay aplicado
        """
        pos_x, pos_y = position
        template_height, template_width = template_image.shape[:2]

        try:
            # Crear copia para overlay
            overlay = base_image.copy()
            template_area = overlay[pos_y:pos_y + template_height,
                                  pos_x:pos_x + template_width]

            # Validar que las áreas coincidan
            if (template_area.shape[:2] == template_image.shape[:2] and
                template_area.shape[2] == template_image.shape[2]):

                # Aplicar blend semi-transparente
                cv2.addWeighted(
                    template_image, self.DEFAULT_OVERLAY_ALPHA,
                    template_area, 1 - self.DEFAULT_OVERLAY_ALPHA,
                    0, template_area
                )
                return overlay
            else:
                logger.warning(
                    f"Template shape mismatch: template={template_image.shape}, "
                    f"area={template_area.shape}"
                )
                return base_image

        except Exception as e:
            logger.error(f"Error creating template overlay: {e}")
            return base_image

    def get_template_size(self) -> Optional[Tuple[int, int]]:
        """
        Obtener último tamaño calculado del template

        Returns:
            Tuple con (width, height) en píxeles o None
        """
        return self.template_size

    def get_template_size_mm(self) -> Optional[Tuple[float, float]]:
        """
        Obtener último tamaño calculado del template en mm

        Returns:
            Tuple con (width_mm, height_mm) o None
        """
        return self.template_size_mm

    def set_overlay_alpha(self, alpha: float):
        """
        Configurar transparencia del overlay

        Args:
            alpha: Valor entre 0.0 (transparente) y 1.0 (opaco)
        """
        self.DEFAULT_OVERLAY_ALPHA = max(0.0, min(1.0, alpha))

    def set_template_sizing_mode(self, use_original_size: bool = True,
                               template_id: str = None):
        """
        Configurar modo de dimensionamiento de templates

        Args:
            use_original_size: True para usar tamaño original del PNG,
                             False para usar tamaño calibrado en mm
            template_id: ID específico del template (opcional)
        """
        if template_id:
            # Configurar para template específico
            if not hasattr(self, 'template_sizing_config'):
                self.template_sizing_config = {}
            self.template_sizing_config[template_id] = {
                'use_original_size': use_original_size
            }
        else:
            # Configurar globalmente
            self.default_use_original_size = use_original_size

    def get_template_sizing_mode(self, template_id: str = None) -> bool:
        """
        Obtener modo de dimensionamiento para un template

        Args:
            template_id: ID del template (opcional)

        Returns:
            True si debe usar tamaño original, False si debe usar calibrado
        """
        if template_id and hasattr(self, 'template_sizing_config'):
            return self.template_sizing_config.get(template_id, {}).get(
                'use_original_size', getattr(self, 'default_use_original_size', True)
            )
        return getattr(self, 'default_use_original_size', True)

    def calculate_template_bounds(self, template_position: Tuple[int, int]) -> Optional[Tuple[int, int, int, int]]:
        """
        Calcular bounds del template en la posición dada

        Args:
            template_position: Posición del centro del template

        Returns:
            Tuple con (x1, y1, x2, y2) o None si no hay template size
        """
        if not self.template_size:
            return None

        width, height = self.template_size
        center_x, center_y = template_position

        x1 = center_x - width // 2
        y1 = center_y - height // 2
        x2 = x1 + width
        y2 = y1 + height

        return x1, y1, x2, y2

    def reset(self):
        """Resetear estado del manager"""
        self.template_size = None
        self.template_size_mm = None
        self.last_template_id = None
        self.cached_template = None