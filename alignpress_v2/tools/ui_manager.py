"""
UIManager - Manejo centralizado de interfaz de usuario
Extraído de ConfigDesigner para seguir principio de responsabilidad única
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Optional, Callable, Any
from pathlib import Path

from ..config.models import Logo, Style


class UIManager:
    """Gestiona la interfaz de usuario y eventos de widgets"""

    def __init__(self, root: tk.Tk):
        """
        Inicializar UIManager

        Args:
            root: Ventana principal de Tkinter
        """
        self.root = root
        self.widgets: Dict[str, tk.Widget] = {}
        self.variables: Dict[str, tk.Variable] = {}
        self.callbacks: Dict[str, Callable] = {}

        # Estado de la UI
        self.tooltip_label: Optional[tk.Label] = None

    def create_variable(self, name: str, var_type: str = "string", default_value: Any = "") -> tk.Variable:
        """
        Crear variable de Tkinter

        Args:
            name: Nombre de la variable
            var_type: Tipo de variable (string, int, bool, double)
            default_value: Valor por defecto

        Returns:
            Variable de Tkinter creada
        """
        if var_type == "string":
            var = tk.StringVar(value=str(default_value))
        elif var_type == "int":
            var = tk.IntVar(value=int(default_value))
        elif var_type == "bool":
            var = tk.BooleanVar(value=bool(default_value))
        elif var_type == "double":
            var = tk.DoubleVar(value=float(default_value))
        else:
            var = tk.StringVar(value=str(default_value))

        self.variables[name] = var
        return var

    def get_variable(self, name: str) -> Optional[tk.Variable]:
        """
        Obtener variable por nombre

        Args:
            name: Nombre de la variable

        Returns:
            Variable de Tkinter o None si no existe
        """
        return self.variables.get(name)

    def set_variable_value(self, name: str, value: Any):
        """
        Establecer valor de variable

        Args:
            name: Nombre de la variable
            value: Nuevo valor
        """
        if name in self.variables:
            self.variables[name].set(value)

    def get_variable_value(self, name: str) -> Any:
        """
        Obtener valor de variable

        Args:
            name: Nombre de la variable

        Returns:
            Valor de la variable o None si no existe
        """
        if name in self.variables:
            return self.variables[name].get()
        return None

    def register_widget(self, name: str, widget: tk.Widget):
        """
        Registrar widget para acceso posterior

        Args:
            name: Nombre del widget
            widget: Widget de Tkinter
        """
        self.widgets[name] = widget

    def get_widget(self, name: str) -> Optional[tk.Widget]:
        """
        Obtener widget por nombre

        Args:
            name: Nombre del widget

        Returns:
            Widget de Tkinter o None si no existe
        """
        return self.widgets.get(name)

    def register_callback(self, name: str, callback: Callable):
        """
        Registrar callback para eventos

        Args:
            name: Nombre del callback
            callback: Función callback
        """
        self.callbacks[name] = callback

    def trigger_callback(self, name: str, *args, **kwargs):
        """
        Ejecutar callback registrado

        Args:
            name: Nombre del callback
            *args: Argumentos posicionales
            **kwargs: Argumentos nombrados
        """
        if name in self.callbacks:
            self.callbacks[name](*args, **kwargs)

    def setup_menu_bar(self) -> tk.Menu:
        """
        Crear barra de menú

        Returns:
            Barra de menú creada
        """
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # Menú Archivo
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Archivo", menu=file_menu)
        file_menu.add_command(label="Cargar Imagen", command=lambda: self.trigger_callback("load_image"))
        file_menu.add_separator()
        file_menu.add_command(label="Cargar Preset", command=lambda: self.trigger_callback("load_preset"))
        file_menu.add_command(label="Guardar Preset", command=lambda: self.trigger_callback("save_preset"))
        file_menu.add_separator()
        file_menu.add_command(label="Salir", command=self.root.quit)

        # Menú Configuración
        config_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Configuración", menu=config_menu)
        config_menu.add_command(label="Nueva Configuración", command=lambda: self.trigger_callback("new_config"))
        config_menu.add_command(label="Cargar Configuración", command=lambda: self.trigger_callback("load_config"))
        config_menu.add_command(label="Guardar Configuración", command=lambda: self.trigger_callback("save_config"))

        # Menú Herramientas
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Herramientas", menu=tools_menu)
        tools_menu.add_command(label="Generar Variantes", command=lambda: self.trigger_callback("generate_variants"))
        tools_menu.add_command(label="Exportar YAML", command=lambda: self.trigger_callback("export_yaml"))

        self.register_widget("menubar", menubar)
        return menubar

    def create_config_panel(self, parent: tk.Widget) -> tk.Frame:
        """
        Crear panel de configuración

        Args:
            parent: Widget padre

        Returns:
            Frame del panel de configuración
        """
        config_frame = ttk.LabelFrame(parent, text="Configuración de Diseño", padding="10")

        # Variables para dropdowns
        self.create_variable("design", "string", "")
        self.create_variable("size", "string", "")
        self.create_variable("part", "string", "")

        # Diseño
        design_row = ttk.Frame(config_frame)
        design_row.pack(fill="x", pady=2)
        ttk.Label(design_row, text="Diseño:", width=12).pack(side="left")
        design_combo = ttk.Combobox(design_row, textvariable=self.get_variable("design"), width=20)
        design_combo.pack(side="left", padx=(5, 0))
        design_combo.bind('<<ComboboxSelected>>', lambda e: self.trigger_callback("on_design_changed"))
        design_combo.bind('<KeyRelease>', lambda e: self.trigger_callback("on_design_typed"))
        self.register_widget("design_combo", design_combo)

        # Botón Nuevo Diseño
        new_design_btn = ttk.Button(design_row, text="Nuevo",
                                   command=lambda: self.trigger_callback("new_design"))
        new_design_btn.pack(side="left", padx=(5, 0))

        # Talla
        size_row = ttk.Frame(config_frame)
        size_row.pack(fill="x", pady=2)
        ttk.Label(size_row, text="Talla:", width=12).pack(side="left")
        size_combo = ttk.Combobox(size_row, textvariable=self.get_variable("size"), width=20)
        size_combo.pack(side="left", padx=(5, 0))
        size_combo.bind('<<ComboboxSelected>>', lambda e: self.trigger_callback("on_size_changed"))
        size_combo.bind('<KeyRelease>', lambda e: self.trigger_callback("on_size_typed"))
        self.register_widget("size_combo", size_combo)

        # Botón Nueva Talla
        new_size_btn = ttk.Button(size_row, text="Nuevo",
                                 command=lambda: self.trigger_callback("new_size"))
        new_size_btn.pack(side="left", padx=(5, 0))

        # Parte
        part_row = ttk.Frame(config_frame)
        part_row.pack(fill="x", pady=2)
        ttk.Label(part_row, text="Parte:", width=12).pack(side="left")
        part_combo = ttk.Combobox(part_row, textvariable=self.get_variable("part"), width=20)
        part_combo.pack(side="left", padx=(5, 0))
        part_combo.bind('<<ComboboxSelected>>', lambda e: self.trigger_callback("on_part_changed"))
        part_combo.bind('<KeyRelease>', lambda e: self.trigger_callback("on_part_typed"))
        self.register_widget("part_combo", part_combo)

        # Botón Nueva Parte
        new_part_btn = ttk.Button(part_row, text="Nuevo",
                                 command=lambda: self.trigger_callback("new_part"))
        new_part_btn.pack(side="left", padx=(5, 0))

        # Estado de configuración
        status_label = ttk.Label(config_frame, text="Selecciona diseño, talla y parte",
                               foreground="gray")
        status_label.pack(pady=(10, 0))
        self.register_widget("config_status_label", status_label)

        self.register_widget("config_frame", config_frame)
        return config_frame

    def create_logo_panel(self, parent: tk.Widget) -> tk.Frame:
        """
        Crear panel de logos

        Args:
            parent: Widget padre

        Returns:
            Frame del panel de logos
        """
        logo_frame = ttk.LabelFrame(parent, text="Logos", padding="10")

        # Lista de logos
        logo_list = tk.Listbox(logo_frame, height=8)
        logo_list.pack(fill="both", expand=True, pady=(0, 10))
        logo_list.bind('<<ListboxSelect>>', lambda e: self.trigger_callback("on_logo_select"))
        self.register_widget("logo_list", logo_list)

        # Botones de logo
        logo_buttons = ttk.Frame(logo_frame)
        logo_buttons.pack(fill="x")

        add_logo_btn = ttk.Button(logo_buttons, text="Agregar Logo",
                                 command=lambda: self.trigger_callback("add_logo"))
        add_logo_btn.pack(side="left", padx=(0, 5))

        remove_logo_btn = ttk.Button(logo_buttons, text="Eliminar",
                                    command=lambda: self.trigger_callback("remove_logo"))
        remove_logo_btn.pack(side="left")

        self.register_widget("logo_frame", logo_frame)
        return logo_frame

    def create_visual_controls(self, parent: tk.Widget) -> tk.Frame:
        """
        Crear controles visuales (reglas, grid)

        Args:
            parent: Widget padre

        Returns:
            Frame de controles visuales
        """
        visual_frame = ttk.LabelFrame(parent, text="Controles Visuales", padding="10")

        # Variables para checkboxes
        self.create_variable("show_rulers", "bool", True)
        self.create_variable("show_grid", "bool", True)

        # Checkbox para reglas
        rulers_check = ttk.Checkbutton(visual_frame, text="Mostrar Reglas",
                                      variable=self.get_variable("show_rulers"),
                                      command=lambda: self.trigger_callback("toggle_rulers"))
        rulers_check.pack(anchor="w")
        self.register_widget("rulers_check", rulers_check)

        # Checkbox para grid
        grid_check = ttk.Checkbutton(visual_frame, text="Mostrar Grid",
                                    variable=self.get_variable("show_grid"),
                                    command=lambda: self.trigger_callback("toggle_grid"))
        grid_check.pack(anchor="w")
        self.register_widget("grid_check", grid_check)

        self.register_widget("visual_frame", visual_frame)
        return visual_frame

    def create_position_panel(self, parent: tk.Widget) -> tk.Frame:
        """
        Crear panel de posición

        Args:
            parent: Widget padre

        Returns:
            Frame del panel de posición
        """
        position_frame = ttk.LabelFrame(parent, text="Posición y Tamaño", padding="10")

        # Variables para posición
        self.create_variable("pos_x", "string", "")
        self.create_variable("pos_y", "string", "")
        self.create_variable("width", "string", "")
        self.create_variable("height", "string", "")

        # Posición X
        x_row = ttk.Frame(position_frame)
        x_row.pack(fill="x", pady=2)
        ttk.Label(x_row, text="X (mm):", width=8).pack(side="left")
        x_entry = ttk.Entry(x_row, textvariable=self.get_variable("pos_x"), width=10)
        x_entry.pack(side="left", padx=(5, 0))
        x_entry.bind('<KeyRelease>', lambda e: self.trigger_callback("on_position_changed"))

        # Posición Y
        y_row = ttk.Frame(position_frame)
        y_row.pack(fill="x", pady=2)
        ttk.Label(y_row, text="Y (mm):", width=8).pack(side="left")
        y_entry = ttk.Entry(y_row, textvariable=self.get_variable("pos_y"), width=10)
        y_entry.pack(side="left", padx=(5, 0))
        y_entry.bind('<KeyRelease>', lambda e: self.trigger_callback("on_position_changed"))

        # Ancho
        w_row = ttk.Frame(position_frame)
        w_row.pack(fill="x", pady=2)
        ttk.Label(w_row, text="Ancho:", width=8).pack(side="left")
        w_entry = ttk.Entry(w_row, textvariable=self.get_variable("width"), width=10)
        w_entry.pack(side="left", padx=(5, 0))
        w_entry.bind('<KeyRelease>', lambda e: self.trigger_callback("on_size_changed"))

        # Alto
        h_row = ttk.Frame(position_frame)
        h_row.pack(fill="x", pady=2)
        ttk.Label(h_row, text="Alto:", width=8).pack(side="left")
        h_entry = ttk.Entry(h_row, textvariable=self.get_variable("height"), width=10)
        h_entry.pack(side="left", padx=(5, 0))
        h_entry.bind('<KeyRelease>', lambda e: self.trigger_callback("on_size_changed"))

        self.register_widget("position_frame", position_frame)
        return position_frame

    def update_logo_list(self, logos: List[Logo]):
        """
        Actualizar lista de logos

        Args:
            logos: Lista de logos a mostrar
        """
        logo_list = self.get_widget("logo_list")
        if logo_list:
            logo_list.delete(0, tk.END)
            for i, logo in enumerate(logos):
                logo_list.insert(i, f"{logo.id} - {logo.name}")

    def update_config_status(self, message: str, color: str = "black"):
        """
        Actualizar estado de configuración

        Args:
            message: Mensaje a mostrar
            color: Color del texto
        """
        status_label = self.get_widget("config_status_label")
        if status_label:
            status_label.config(text=message, foreground=color)

    def update_dropdown_values(self, widget_name: str, values: List[str]):
        """
        Actualizar valores de dropdown

        Args:
            widget_name: Nombre del widget dropdown
            values: Lista de valores
        """
        widget = self.get_widget(widget_name)
        if widget and hasattr(widget, 'config'):
            widget.config(values=values)

    def show_tooltip(self, x: int, y: int, text: str):
        """
        Mostrar tooltip

        Args:
            x: Posición X
            y: Posición Y
            text: Texto del tooltip
        """
        self.hide_tooltip()  # Limpiar tooltip anterior

        self.tooltip_label = tk.Label(
            self.root,
            text=text,
            background="lightyellow",
            relief="solid",
            borderwidth=1,
            font=("Arial", 9)
        )
        self.tooltip_label.place(x=x + 10, y=y + 10)

    def hide_tooltip(self):
        """Ocultar tooltip"""
        if self.tooltip_label:
            self.tooltip_label.destroy()
            self.tooltip_label = None

    def show_info_message(self, title: str, message: str):
        """
        Mostrar mensaje informativo

        Args:
            title: Título del mensaje
            message: Contenido del mensaje
        """
        messagebox.showinfo(title, message)

    def show_warning_message(self, title: str, message: str):
        """
        Mostrar mensaje de advertencia

        Args:
            title: Título del mensaje
            message: Contenido del mensaje
        """
        messagebox.showwarning(title, message)

    def show_error_message(self, title: str, message: str):
        """
        Mostrar mensaje de error

        Args:
            title: Título del mensaje
            message: Contenido del mensaje
        """
        messagebox.showerror(title, message)

    def ask_yes_no(self, title: str, message: str) -> bool:
        """
        Mostrar diálogo de confirmación

        Args:
            title: Título del diálogo
            message: Mensaje del diálogo

        Returns:
            True si el usuario eligió Sí, False si no
        """
        return messagebox.askyesno(title, message)

    def clear_all_variables(self):
        """Limpiar todas las variables"""
        for var in self.variables.values():
            if isinstance(var, tk.BooleanVar):
                var.set(False)
            elif isinstance(var, (tk.IntVar, tk.DoubleVar)):
                var.set(0)
            else:
                var.set("")

    def get_selected_logo_index(self) -> Optional[int]:
        """
        Obtener índice del logo seleccionado

        Returns:
            Índice del logo seleccionado o None
        """
        logo_list = self.get_widget("logo_list")
        if logo_list:
            selection = logo_list.curselection()
            return selection[0] if selection else None
        return None

    def set_widget_state(self, widget_name: str, state: str):
        """
        Establecer estado de widget

        Args:
            widget_name: Nombre del widget
            state: Estado (normal, disabled, readonly)
        """
        widget = self.get_widget(widget_name)
        if widget and hasattr(widget, 'config'):
            widget.config(state=state)