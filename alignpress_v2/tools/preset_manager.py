"""
PresetManager - Manejo centralizado de presets
Extraído de ConfigDesigner para seguir principio de responsabilidad única
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from tkinter import filedialog, messagebox

from ..config.models import Logo, Style, Point, Rectangle


class PresetManager:
    """Gestiona la carga, guardado y validación de presets de configuración"""

    def __init__(self, config_root_path: Path = None):
        """
        Inicializar PresetManager

        Args:
            config_root_path: Ruta base para configuraciones (default: ./configs)
        """
        self.config_root_path = config_root_path or Path("./configs")

    def scan_existing_presets(self) -> Tuple[List[str], List[str], List[str]]:
        """
        Escanear presets existentes en el directorio de configuraciones

        Returns:
            Tuple con listas de (designs, sizes, parts) disponibles
        """
        designs = []
        sizes = []
        parts = []

        if not self.config_root_path.exists():
            return designs, sizes, parts

        try:
            # Escanear designs (directorios de primer nivel)
            for design_dir in self.config_root_path.iterdir():
                if design_dir.is_dir():
                    designs.append(design_dir.name)

                    # Escanear sizes (directorios de segundo nivel)
                    for size_dir in design_dir.iterdir():
                        if size_dir.is_dir() and size_dir.name not in sizes:
                            sizes.append(size_dir.name)

                            # Escanear parts (archivos JSON)
                            for part_file in size_dir.glob("*.json"):
                                part_name = part_file.stem
                                if part_name not in parts:
                                    parts.append(part_name)

        except Exception as e:
            print(f"Error escaneando presets: {e}")

        return sorted(designs), sorted(sizes), sorted(parts)

    def load_preset_file(self) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Abrir diálogo para seleccionar y cargar archivo de preset

        Returns:
            Tuple con (config_data, config_path) o (None, None) si se cancela
        """
        configs_dir = self.config_root_path

        if not configs_dir.exists():
            messagebox.showwarning("Sin Presets", "No hay presets guardados aún.")
            return None, None

        config_path = filedialog.askopenfilename(
            title="Seleccionar Preset",
            initialdir=str(configs_dir),
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

    def extract_preset_metadata(self, config_data: Dict, config_path: str) -> Tuple[str, str, str]:
        """
        Extraer metadatos de diseño/talla/parte desde la ruta del archivo o datos

        Args:
            config_data: Datos de configuración cargados
            config_path: Ruta del archivo de configuración

        Returns:
            Tuple con (design, size, part)
        """
        rel_path = os.path.relpath(config_path, str(self.config_root_path))
        path_parts = rel_path.split(os.sep)

        if len(path_parts) >= 3:
            design = path_parts[0]
            size = path_parts[1]
            part = os.path.splitext(path_parts[2])[0]
        else:
            # Fallback: usar datos del archivo de configuración
            design = config_data.get('design', 'Unknown')
            size = config_data.get('size', 'Unknown')
            part = config_data.get('part', 'Unknown')

        return design, size, part

    def create_logos_from_config(self, config_data: Dict) -> List[Logo]:
        """
        Crear objetos Logo desde datos de configuración

        Args:
            config_data: Datos de configuración con logos

        Returns:
            Lista de objetos Logo creados
        """
        logos = []

        for logo_data in config_data.get('logos', []):
            logo = Logo(
                id=logo_data['id'],
                name=logo_data['name'],
                position_mm=Point(
                    logo_data['position_mm']['x'],
                    logo_data['position_mm']['y']
                ),
                tolerance_mm=logo_data.get('tolerance_mm', 3.0),
                detector_type=logo_data.get('detector_type',
                                         logo_data.get('detector', 'template_matching')),
                roi=Rectangle(
                    logo_data['roi']['x'],
                    logo_data['roi']['y'],
                    logo_data['roi']['width'],
                    logo_data['roi']['height']
                )
            )
            logos.append(logo)

        return logos

    def validate_preset_data(self, design: str, size: str, part: str,
                           style: Optional[Style] = None) -> bool:
        """
        Validar datos de preset antes de guardar

        Args:
            design: Nombre del diseño
            size: Nombre de la talla
            part: Nombre de la parte
            style: Estilo con logos (opcional)

        Returns:
            True si los datos son válidos, False si no
        """
        if not design or not size or not part:
            messagebox.showwarning(
                "Configuración Incompleta",
                "Selecciona Diseño, Talla y Parte para guardar el preset."
            )
            return False

        if not style or not style.logos:
            messagebox.showwarning(
                "Sin Logos",
                "Agrega al menos un logo antes de guardar el preset."
            )
            return False

        return True

    def prepare_preset_config_data(self, design: str, size: str, part: str,
                                 style: Style, mm_per_pixel: float) -> Dict:
        """
        Preparar datos de configuración para guardado

        Args:
            design: Nombre del diseño
            size: Nombre de la talla
            part: Nombre de la parte
            style: Estilo con logos
            mm_per_pixel: Factor de calibración

        Returns:
            Diccionario con datos de configuración preparados
        """
        config_data = {
            "design": design,
            "size": size,
            "part": part,
            "calibration_factor": mm_per_pixel,
            "logos": []
        }

        # Convertir logos a formato de diccionario
        for logo in style.logos:
            logo_data = {
                "id": logo.id,
                "name": logo.name,
                "position_mm": {
                    "x": logo.position_mm.x,
                    "y": logo.position_mm.y
                },
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

    def save_preset(self, design: str, size: str, part: str,
                   style: Style, mm_per_pixel: float) -> bool:
        """
        Guardar preset completo

        Args:
            design: Nombre del diseño
            size: Nombre de la talla
            part: Nombre de la parte
            style: Estilo con logos
            mm_per_pixel: Factor de calibración

        Returns:
            True si se guardó exitosamente, False si no
        """
        # Validar datos
        if not self.validate_preset_data(design, size, part, style):
            return False

        # Crear estructura de directorios
        preset_dir = self.config_root_path / design / size
        preset_dir.mkdir(parents=True, exist_ok=True)

        config_path = preset_dir / f"{part}.json"

        # Verificar si el archivo existe y confirmar sobrescritura
        if config_path.exists():
            if not messagebox.askyesno(
                "Sobrescribir",
                f"El preset {design}/{size}/{part} ya existe.\n\n¿Quieres sobrescribirlo?"
            ):
                return False

        try:
            # Preparar y guardar datos
            config_data = self.prepare_preset_config_data(
                design, size, part, style, mm_per_pixel
            )

            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)

            messagebox.showinfo(
                "Éxito",
                f"Preset guardado correctamente en:\n{config_path}"
            )
            return True

        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar preset: {str(e)}")
            return False

    def get_sizes_for_design(self, design: str) -> List[str]:
        """
        Obtener tallas disponibles para un diseño específico

        Args:
            design: Nombre del diseño

        Returns:
            Lista de tallas disponibles
        """
        if not design:
            return []

        design_path = self.config_root_path / design
        if design_path.exists():
            sizes = [d.name for d in design_path.iterdir() if d.is_dir()]
            return sorted(sizes)
        else:
            # Tallas por defecto para diseños nuevos
            return ["TallaS", "TallaM", "TallaL", "TallaXL"]

    def get_parts_for_design_size(self, design: str, size: str) -> List[str]:
        """
        Obtener partes disponibles para un diseño y talla específicos

        Args:
            design: Nombre del diseño
            size: Nombre de la talla

        Returns:
            Lista de partes disponibles
        """
        if not design or not size:
            return []

        size_path = self.config_root_path / design / size
        if size_path.exists():
            parts = [f.stem for f in size_path.glob("*.json")]
            return sorted(parts)
        else:
            # Partes por defecto
            return ["delantera", "trasera", "manga_izquierda", "manga_derecha"]