import flet as ft
import json
import os
from datetime import datetime

def obtener_directorio_datos(page: ft.Page):
    try:
        dir_datos = os.path.join(page.get_upload_dir() if hasattr(page, "get_upload_dir") and page.get_upload_dir() else os.path.expanduser("~"), ".app_planificador")
    except Exception:
        dir_datos = os.path.join(os.path.expanduser("~"), ".app_planificador")
    if not os.path.exists(dir_datos):
        os.makedirs(dir_datos, exist_ok=True)
    return dir_datos

def parse_fecha(fecha_str):
    for fmt in ("%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d"):
        try:
            return datetime.strptime(fecha_str.strip(), fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Formato no válido: {fecha_str}")

class TabActividades(ft.Column):
    def __init__(self, page: ft.Page, nombre_proyecto: str):
        super().__init__(expand=True, spacing=10)
        self.page = page
        self.nombre_proyecto = nombre_proyecto
        self.archivo_json = f"actividades_{self.nombre_proyecto.lower().replace(' ', '_')}.json"
        self.actividades = self.cargar_actividades()
        
        self.txt_nueva = ft.TextField(hint_text="Nueva actividad...", expand=True, dense=True)
        self.txt_fecha = ft.TextField(
            hint_text="DD/MM/YYYY", 
            value=datetime.now().strftime("%d/%m/%Y"), 
            width=130, 
            dense=True
        )
        self.lv_actividades = ft.ListView(expand=True, spacing=10, padding=10)
        
        self.controls = [
            ft.Container(
                content=ft.Row([
                    self.txt_nueva,
                    self.txt_fecha,
                    ft.IconButton(
                        icon=ft.Icons.ADD_CIRCLE, 
                        icon_color=ft.Colors.BLUE_600, 
                        icon_size=32, 
                        on_click=self.agregar_actividad,
                        tooltip="Añadir Actividad"
                    )
                ]),
                padding=10
            ),
            ft.Divider(height=1),
            self.lv_actividades
        ]
        self.actualizar_lista()

    def obtener_ruta_json(self):
        dir_datos = obtener_directorio_datos(self.page)
        return os.path.join(dir_datos, self.archivo_json)

    def cargar_actividades(self):
        try:
            ruta = self.obtener_ruta_json()
            with open(ruta, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def guardar_actividades(self):
        try:
            ruta = self.obtener_ruta_json()
            with open(ruta, "w", encoding="utf-8") as f:
                json.dump(self.actividades, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.page.open(ft.SnackBar(ft.Text(f"Error al guardar: {e}")))

    def agregar_actividad(self, e):
        texto = self.txt_nueva.value.strip()
        fecha_str = self.txt_fecha.value.strip()
        
        if not texto:
            self.page.open(ft.SnackBar(ft.Text("Escribe una descripción para la actividad.")))
            return
            
        try:
            fecha = parse_fecha(fecha_str)
            hoy = datetime.now().date()
            dias_restantes = (fecha - hoy).days
            
            self.actividades.append({
                "texto": texto,
                "completada": False,
                "fecha": fecha.strftime("%d/%m/%Y"),
                "dias_restantes": dias_restantes
            })
            
            self.txt_nueva.value = ""
            self.guardar_actividades()
            self.actualizar_lista()
            self.page.update()
            self.page.open(ft.SnackBar(ft.Text("Actividad añadida correctamente.")))
        except ValueError:
            self.page.open(ft.SnackBar(ft.Text("Formato de fecha inválido (Use DD/MM/YYYY)")))

    def cambiar_estado(self, index, val):
        self.actividades[index]["completada"] = val
        self.guardar_actividades()
        self.actualizar_lista()
        self.page.update()

    def eliminar_actividad(self, index):
        del self.actividades[index]
        self.guardar_actividades()
        self.actualizar_lista()
        self.page.update()

    def editar_actividad(self, index):
        act = self.actividades[index]
        input_edit = ft.TextField(value=act["texto"], expand=True)

        def guardar_edit(e):
            if input_edit.value.strip():
                act["texto"] = input_edit.value.strip()
                self.guardar_actividades()
                self.actualizar_lista()
                dlg.open = False
                self.page.update()

        def cancelar_edit(e):
            dlg.open = False
            self.page.update()

        dlg = ft.AlertDialog(
            title=ft.Text("Editar Descripción"),
            content=input_edit,
            actions=[
                ft.TextButton("Cancelar", on_click=cancelar_edit),
                ft.ElevatedButton("Guardar", on_click=guardar_edit)
            ]
        )
        self.page.open(dlg)

    def actualizar_lista(self):
        self.lv_actividades.controls.clear()
        hoy = datetime.now().date()
        
        for idx, act in enumerate(self.actividades):
            color = ft.Colors.GREEN_600 if act.get("completada") else ft.Colors.BLACK
            subtexto = ""
            
            if act.get("fecha"):
                try:
                    fecha = parse_fecha(act["fecha"])
                    dias = (fecha - hoy).days
                    act["dias_restantes"] = dias
                    
                    if not act.get("completada"):
                        if dias < 0:
                            color = ft.Colors.RED_600
                            subtexto = f"VENCIDA ({abs(dias)}d de retraso) - 📅 {act['fecha']}"
                        elif dias <= 3:
                            color = ft.Colors.RED_500
                            subtexto = f"¡Urgente! Quedan {dias} días - 📅 {act['fecha']}"
                        elif dias <= 7:
                            color = ft.Colors.ORANGE_700
                            subtexto = f"Próxima: Quedan {dias} días - 📅 {act['fecha']}"
                        else:
                            subtexto = f"Quedan {dias} días - 📅 {act['fecha']}"
                    else:
                        subtexto = f"Completada - 📅 {act['fecha']}"
                except Exception:
                    subtexto = "Fecha no válida"
            
            tile = ft.ListTile(
                leading=ft.Checkbox(
                    value=act.get("completada", False), 
                    on_change=lambda e, i=idx: self.cambiar_estado(i, e.control.value)
                ),
                title=ft.Text(
                    act["texto"], 
                    color=color, 
                    weight=ft.FontWeight.BOLD if not act.get("completada") else ft.FontWeight.NORMAL
                ),
                subtitle=ft.Text(subtexto, size=12),
                trailing=ft.Row([
                    ft.IconButton(ft.Icons.EDIT, icon_size=20, on_click=lambda e, i=idx: self.editar_actividad(i)),
                    ft.IconButton(ft.Icons.DELETE, icon_size=20, icon_color=ft.Colors.RED_400, on_click=lambda e, i=idx: self.eliminar_actividad(i))
                ], wrap=False, width=80)
            )
            self.lv_actividades.controls.append(tile)

def main(page: ft.Page):
    page.title = "Planificador Multi-Proyecto"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0

    ruta_config = os.path.join(obtener_directorio_datos(page), "config_proyectos.json")

    def cargar_proyectos():
        try:
            with open(ruta_config, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return ["Trabajo de Grado", "Ingeniería Electrónica", "General"]

    def guardar_proyectos(projs):
        try:
            with open(ruta_config, "w", encoding="utf-8") as f:
                json.dump(projs, f, indent=2, ensure_ascii=False)
        except Exception as e:
            page.open(ft.SnackBar(ft.Text(f"Error al guardar proyectos: {e}")))

    proyectos = cargar_proyectos()
    tabs_control = ft.Tabs(selected_index=0, expand=True)

    def construir_tabs():
        tabs_control.tabs.clear()
        for p in proyectos:
            tabs_control.tabs.append(
                ft.Tab(
                    text=p,
                    icon=ft.Icons.FOLDER,
                    content=TabActividades(page, p)
                )
            )
        page.update()

    def crear_proyecto(e):
        txt_nombre = ft.TextField(hint_text="Nombre del trabajo...")

        def confirmar(e_conf):
            val = txt_nombre.value.strip()
            if val and val not in proyectos:
                proyectos.append(val)
                guardar_proyectos(proyectos)
                construir_tabs()
                dlg.open = False
                page.update()

        def cancelar(e_canc):
            dlg.open = False
            page.update()

        dlg = ft.AlertDialog(
            title=ft.Text("Nuevo Trabajo"),
            content=txt_nombre,
            actions=[
                ft.TextButton("Cancelar", on_click=cancelar),
                ft.ElevatedButton("Crear", on_click=confirmar)
            ]
        )
        page.open(dlg)

    def eliminar_proyecto_actual(e):
        if len(proyectos) <= 1:
            page.open(ft.SnackBar(ft.Text("Debes mantener al menos un trabajo.")))
            return

        idx = tabs_control.selected_index
        nombre = proyectos[idx]

        proyectos.pop(idx)
        guardar_proyectos(proyectos)
        construir_tabs()
        page.open(ft.SnackBar(ft.Text(f"Se eliminó '{nombre}'")))

    page.appbar = ft.AppBar(
        title=ft.Text("Planificador de Actividades"),
        center_title=False,
        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
        actions=[
            ft.IconButton(ft.Icons.CREATE_NEW_FOLDER, tooltip="Nuevo Trabajo", on_click=crear_proyecto),
            ft.IconButton(ft.Icons.DELETE_SWEEP, tooltip="Eliminar Trabajo", on_click=eliminar_proyecto_actual)
        ]
    )

    page.add(tabs_control)
    construir_tabs()

if __name__ == "__main__":
    # Compatibilidad oficial con Flet 1.0+ en Android
    ft.run_async(main)
