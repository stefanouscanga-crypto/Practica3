import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime, timedelta
from collections import deque

class Paciente:
    """Clase para representar un paciente en la cola"""
    def __init__(self, nombre, telefono, fecha, hora, especialidad, es_emergencia=False):
        self.nombre = nombre
        self.telefono = telefono
        self.fecha = fecha
        self.hora = hora
        self.especialidad = especialidad
        self.es_emergencia = es_emergencia
        self.hora_registro = datetime.now()

class ColaTurnos:
    """Implementación de Cola (Queue) con FIFO para gestión de turnos"""
    def __init__(self):
        # Uso dos colas: una para emergencias y otra para turnos normales
        # Esto mantiene FIFO en cada categoría y prioriza emergencias
        self.cola_emergencias = deque()  # Cola de emergencias (FIFO)
        self.cola_normal = deque()       # Cola normal (FIFO)
    
    def encolar(self, paciente):
        """Agregar paciente al final de la cola correspondiente (enqueue)"""
        if paciente.es_emergencia:
            self.cola_emergencias.append(paciente)  # Al final de cola emergencias
        else:
            self.cola_normal.append(paciente)       # Al final de cola normal
    
    def desencolar(self):
        """Eliminar y retornar el primer paciente de la cola (dequeue)"""
        # Prioridad: primero emergencias, luego normales
        if self.cola_emergencias:
            return self.cola_emergencias.popleft()  # Elimina del frente (FIFO)
        elif self.cola_normal:
            return self.cola_normal.popleft()       # Elimina del frente (FIFO)
        return None
    
    def cancelar_turno(self, nombre_paciente):
        """Cancelar turno por nombre (buscar y eliminar)"""
        nombre_lower = nombre_paciente.lower()
        
        # Buscar en cola de emergencias
        for i, paciente in enumerate(self.cola_emergencias):
            if paciente.nombre.lower() == nombre_lower:
                del self.cola_emergencias[i]
                return True
        
        # Buscar en cola normal
        for i, paciente in enumerate(self.cola_normal):
            if paciente.nombre.lower() == nombre_lower:
                del self.cola_normal[i]
                return True
        
        return False
    
    def buscar_paciente(self, nombre_paciente):
        """Buscar paciente y retornar (paciente, posición_global)"""
        nombre_lower = nombre_paciente.lower()
        posicion = 1
        
        # Buscar en cola de emergencias primero
        for paciente in self.cola_emergencias:
            if paciente.nombre.lower() == nombre_lower:
                return (paciente, posicion)
            posicion += 1
        
        # Buscar en cola normal
        for paciente in self.cola_normal:
            if paciente.nombre.lower() == nombre_lower:
                return (paciente, posicion)
            posicion += 1
        
        return (None, -1)
    
    def obtener_lista_completa(self):
        """Obtener lista completa de pacientes en orden de atención"""
        lista = []
        posicion = 1
        
        # Primero todos los de emergencias (en orden FIFO)
        for paciente in self.cola_emergencias:
            tiempo_espera = datetime.now() - paciente.hora_registro
            minutos = int(tiempo_espera.total_seconds() / 60)
            
            lista.append({
                'posicion': posicion,
                'paciente': paciente.nombre,
                'telefono': paciente.telefono,
                'hora': paciente.hora,
                'especialidad': paciente.especialidad,
                'tipo': 'EMERGENCIA',
                'tiempo_espera': f"{minutos} min"
            })
            posicion += 1
        
        # Luego todos los normales (en orden FIFO)
        for paciente in self.cola_normal:
            tiempo_espera = datetime.now() - paciente.hora_registro
            minutos = int(tiempo_espera.total_seconds() / 60)
            
            lista.append({
                'posicion': posicion,
                'paciente': paciente.nombre,
                'telefono': paciente.telefono,
                'hora': paciente.hora,
                'especialidad': paciente.especialidad,
                'tipo': 'NORMAL',
                'tiempo_espera': f"{minutos} min"
            })
            posicion += 1
        
        return lista
    
    def obtener_estadisticas(self):
        """Calcular estadísticas de las colas"""
        total_emergencias = len(self.cola_emergencias)
        total_normal = len(self.cola_normal)
        total = total_emergencias + total_normal
        
        if total == 0:
            return {
                'total': 0,
                'emergencias': 0,
                'normales': 0,
                'tiempo_promedio': 0
            }
        
        tiempo_total = 0
        
        # Calcular tiempo promedio de todos los pacientes
        for paciente in self.cola_emergencias:
            tiempo = datetime.now() - paciente.hora_registro
            tiempo_total += tiempo.total_seconds() / 60
        
        for paciente in self.cola_normal:
            tiempo = datetime.now() - paciente.hora_registro
            tiempo_total += tiempo.total_seconds() / 60
        
        return {
            'total': total,
            'emergencias': total_emergencias,
            'normales': total_normal,
            'tiempo_promedio': int(tiempo_total / total)
        }
    
    def ver_primero(self):
        """Ver el primer paciente sin eliminarlo (peek)"""
        if self.cola_emergencias:
            return self.cola_emergencias[0]
        elif self.cola_normal:
            return self.cola_normal[0]
        return None
    
    def esta_vacia(self):
        """Verificar si ambas colas están vacías"""
        return len(self.cola_emergencias) == 0 and len(self.cola_normal) == 0
    
    def tamaño(self):
        """Retornar tamaño total de ambas colas"""
        return len(self.cola_emergencias) + len(self.cola_normal)


class GestorTurnosApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Turnos Médicos - Cola FIFO")
        self.root.geometry("1200x800")
        self.root.configure(bg="#f5f5f5")
        
        # Cola principal usando deque (implementación eficiente de cola)
        self.cola_turnos = ColaTurnos()
        
        self.tiempo_por_consulta = 15
        
        self.especialidades = [
            "Medicina General", "Cardiología", "Dermatología", 
            "Neurología", "Pediatría", "Ginecología", "Traumatología"
        ]
        
        self.crear_interfaz()
        self.actualizar_interfaz()
    
    def validar_solo_letras(self, char):
        return (char.isalpha() or char.isspace() or 
                char in "áéíóúüñÁÉÍÓÚÜÑ'-" or char == "")
    
    def validar_solo_numeros(self, char):
        return char.isdigit() or char == ""
    
    def validar_nombre_completo(self, nombre):
        if not nombre.strip():
            return False
        caracteres_validos = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ áéíóúüñÁÉÍÓÚÜÑ'-")
        return all(char in caracteres_validos for char in nombre)
    
    def validar_telefono_completo(self, telefono):
        if not telefono.strip():
            return False
        return telefono.isdigit()
    
    def crear_interfaz(self):
        # Header
        header_frame = tk.Frame(self.root, bg="#E53E3E", height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(header_frame, 
                              text="🏥 SISTEMA DE TURNOS MÉDICOS - COLA FIFO (First In, First Out)", 
                              font=("Segoe UI", 18, "bold"), fg="white", bg="#E53E3E")
        title_label.pack(expand=True)
        
        # Contenedor principal
        main_container = tk.Frame(self.root, bg="#f5f5f5")
        main_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Tres columnas
        self.frame_registro = tk.Frame(main_container, bg="white", relief=tk.FLAT, bd=1)
        self.frame_registro.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        self.frame_lista = tk.Frame(main_container, bg="white", relief=tk.FLAT, bd=1)
        self.frame_lista.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        self.frame_control = tk.Frame(main_container, bg="white", relief=tk.FLAT, bd=1)
        self.frame_control.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        self.crear_seccion_registro()
        self.crear_seccion_lista()
        self.crear_seccion_control()
    
    def crear_seccion_registro(self):
        header_registro = tk.Frame(self.frame_registro, bg="#f8f9fa", height=60)
        header_registro.pack(fill=tk.X, padx=2, pady=2)
        header_registro.pack_propagate(False)
        
        icon_label = tk.Label(header_registro, text="🏥", font=("Segoe UI", 16), bg="#f8f9fa")
        icon_label.pack(side=tk.LEFT, padx=15, pady=15)
        
        title_label = tk.Label(header_registro, text="REGISTRAR EN COLA", 
                              font=("Segoe UI", 12, "bold"), bg="#f8f9fa", fg="#2d3748")
        title_label.pack(side=tk.LEFT, pady=15)
        
        content_frame = tk.Frame(self.frame_registro, bg="white")
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        vcmd_letras = (self.root.register(self.validar_solo_letras), '%S')
        vcmd_numeros = (self.root.register(self.validar_solo_numeros), '%S')
        
        # Nombre
        tk.Label(content_frame, text="👤 Nombre del Paciente:", 
                font=("Segoe UI", 9, "bold"), bg="white", fg="#4a5568").pack(anchor=tk.W, pady=(0, 5))
        self.entry_paciente = tk.Entry(content_frame, font=("Segoe UI", 10), bg="#f7fafc", 
                                      relief=tk.FLAT, bd=5, validate='key', validatecommand=vcmd_letras)
        self.entry_paciente.pack(fill=tk.X, pady=(0, 15), ipady=5)
        
        # Teléfono
        tk.Label(content_frame, text="📞 Teléfono:", 
                font=("Segoe UI", 9, "bold"), bg="white", fg="#4a5568").pack(anchor=tk.W, pady=(0, 5))
        self.entry_telefono = tk.Entry(content_frame, font=("Segoe UI", 10), bg="#f7fafc", 
                                      relief=tk.FLAT, bd=5, validate='key', validatecommand=vcmd_numeros)
        self.entry_telefono.pack(fill=tk.X, pady=(0, 15), ipady=5)
        
        # Fecha
        tk.Label(content_frame, text="📅 Fecha (DD/MM/AAAA):", 
                font=("Segoe UI", 9, "bold"), bg="white", fg="#4a5568").pack(anchor=tk.W, pady=(0, 5))
        self.entry_fecha = tk.Entry(content_frame, font=("Segoe UI", 10), bg="#f7fafc", 
                                   relief=tk.FLAT, bd=5)
        self.entry_fecha.pack(fill=tk.X, pady=(0, 15), ipady=5)
        self.entry_fecha.insert(0, datetime.now().strftime("%d/%m/%Y"))
        
        # Hora
        tk.Label(content_frame, text="🕐 Hora (HH:MM):", 
                font=("Segoe UI", 9, "bold"), bg="white", fg="#4a5568").pack(anchor=tk.W, pady=(0, 5))
        self.entry_hora = tk.Entry(content_frame, font=("Segoe UI", 10), bg="#f7fafc", 
                                  relief=tk.FLAT, bd=5)
        self.entry_hora.pack(fill=tk.X, pady=(0, 15), ipady=5)
        self.entry_hora.insert(0, datetime.now().strftime("%H:%M"))
        
        # Especialidad
        tk.Label(content_frame, text="🏥 Especialidad:", 
                font=("Segoe UI", 9, "bold"), bg="white", fg="#4a5568").pack(anchor=tk.W, pady=(0, 5))
        self.combo_especialidad = ttk.Combobox(content_frame, values=self.especialidades, 
                                              font=("Segoe UI", 10), state="readonly")
        self.combo_especialidad.pack(fill=tk.X, pady=(0, 20), ipady=5)
        
        # Checkbox emergencia
        self.var_emergencia = tk.BooleanVar()
        check_frame = tk.Frame(content_frame, bg="white")
        check_frame.pack(fill=tk.X, pady=(0, 25))
        
        check_emergencia = tk.Checkbutton(check_frame, text="🚨 EMERGENCIA (COLA PRIORITARIA)", 
                                         variable=self.var_emergencia, font=("Segoe UI", 10, "bold"),
                                         bg="white", fg="#E53E3E", selectcolor="white")
        check_emergencia.pack()
        
        # Botones
        btn_registrar = tk.Button(content_frame, text="➕ ENCOLAR PACIENTE", 
                                 command=self.registrar_paciente,
                                 bg="#48BB78", fg="white",
                                 font=("Segoe UI", 11, "bold"), relief=tk.FLAT, 
                                 cursor="hand2", height=2)
        btn_registrar.pack(fill=tk.X, pady=(0, 10))
        
        btn_limpiar = tk.Button(content_frame, text="🗑 LIMPIAR CAMPOS", 
                               command=self.limpiar_campos,
                               bg="#A0AEC0", fg="white",
                               font=("Segoe UI", 11, "bold"), relief=tk.FLAT, 
                               cursor="hand2", height=2)
        btn_limpiar.pack(fill=tk.X, pady=(0, 30))
        
        # Consulta tiempo
        consulta_frame = tk.Frame(content_frame, bg="#f8f9fa", relief=tk.FLAT, bd=1)
        consulta_frame.pack(fill=tk.X, pady=(20, 0))
        
        consulta_header = tk.Label(consulta_frame, text="🔍 CONSULTAR POSICIÓN EN COLA", 
                                  font=("Segoe UI", 11, "bold"), bg="#f8f9fa", fg="#2d3748")
        consulta_header.pack(pady=15)
        
        consulta_content = tk.Frame(consulta_frame, bg="#f8f9fa")
        consulta_content.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        tk.Label(consulta_content, text="Nombre del Paciente:", 
                font=("Segoe UI", 9, "bold"), bg="#f8f9fa", fg="#4a5568").pack(anchor=tk.W, pady=(0, 5))
        self.entry_consultar = tk.Entry(consulta_content, font=("Segoe UI", 10), bg="white", 
                                       relief=tk.FLAT, bd=5, validate='key', validatecommand=vcmd_letras)
        self.entry_consultar.pack(fill=tk.X, pady=(0, 15), ipady=5)
        
        btn_consultar = tk.Button(consulta_content, text="⏱ CONSULTAR TIEMPO", 
                                 command=self.consultar_tiempo_espera,
                                 bg="#4299E1", fg="white",
                                 font=("Segoe UI", 10, "bold"), relief=tk.FLAT, 
                                 cursor="hand2", height=1)
        btn_consultar.pack(fill=tk.X)
    
    def crear_seccion_lista(self):
        header_lista = tk.Frame(self.frame_lista, bg="#f8f9fa", height=60)
        header_lista.pack(fill=tk.X, padx=2, pady=2)
        header_lista.pack_propagate(False)
        
        icon_label = tk.Label(header_lista, text="📋", font=("Segoe UI", 16), bg="#f8f9fa")
        icon_label.pack(side=tk.LEFT, padx=15, pady=15)
        
        title_label = tk.Label(header_lista, text="COLA DE ESPERA (FIFO)", 
                              font=("Segoe UI", 12, "bold"), bg="#f8f9fa", fg="#2d3748")
        title_label.pack(side=tk.LEFT, pady=15)
        
        table_frame = tk.Frame(self.frame_lista, bg="white")
        table_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        columns = ("Pos", "Paciente", "Teléfono", "Hora", "Especialidad", "Tipo", "Tiempo Esp.")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=20)
        
        column_config = {
            "Pos": 50,
            "Paciente": 120, 
            "Teléfono": 100,
            "Hora": 80,
            "Especialidad": 120,
            "Tipo": 80,
            "Tiempo Esp.": 90
        }
        
        for col in columns:
            self.tree.heading(col, text=col, anchor=tk.CENTER)
            self.tree.column(col, width=column_config[col], anchor=tk.CENTER, minwidth=50)
        
        scrollbar_v = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar_v.set)
        
        scrollbar_h = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(xscrollcommand=scrollbar_h.set)
        
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar_v.grid(row=0, column=1, sticky="ns")
        scrollbar_h.grid(row=1, column=0, sticky="ew")
        
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
    
    def crear_seccion_control(self):
        header_control = tk.Frame(self.frame_control, bg="#f8f9fa", height=60)
        header_control.pack(fill=tk.X, padx=2, pady=2)
        header_control.pack_propagate(False)
        
        icon_label = tk.Label(header_control, text="🎛", font=("Segoe UI", 16), bg="#f8f9fa")
        icon_label.pack(side=tk.LEFT, padx=15, pady=15)
        
        title_label = tk.Label(header_control, text="PANEL DE CONTROL", 
                              font=("Segoe UI", 12, "bold"), bg="#f8f9fa", fg="#2d3748")
        title_label.pack(side=tk.LEFT, pady=15)
        
        control_content = tk.Frame(self.frame_control, bg="white")
        control_content.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        btn_llamar = tk.Button(control_content, text="📢 DESENCOLAR (LLAMAR SIGUIENTE)", 
                              command=self.llamar_siguiente_paciente,
                              bg="#E53E3E", fg="white",
                              font=("Segoe UI", 12, "bold"), relief=tk.FLAT, cursor="hand2",
                              height=3)
        btn_llamar.pack(fill=tk.X, pady=(15, 15))
        
        btn_cancelar = tk.Button(control_content, text="❌ CANCELAR TURNO", 
                               command=self.cancelar_turno_seleccionado,
                               bg="#ED8936", fg="white",
                               font=("Segoe UI", 11, "bold"), relief=tk.FLAT, cursor="hand2",
                               height=2)
        btn_cancelar.pack(fill=tk.X, pady=(0, 15))
        
        btn_buscar = tk.Button(control_content, text="🔍 BUSCAR EN COLA", 
                              command=self.buscar_paciente_dialog,
                              bg="#805AD5", fg="white",
                              font=("Segoe UI", 11, "bold"), relief=tk.FLAT, cursor="hand2",
                              height=2)
        btn_buscar.pack(fill=tk.X, pady=(0, 30))
        
        # Estadísticas
        stats_header = tk.Frame(control_content, bg="#edf2f7")
        stats_header.pack(fill=tk.X, pady=(20, 0))
        
        stats_icon = tk.Label(stats_header, text="📊", font=("Segoe UI", 14), bg="#edf2f7")
        stats_icon.pack(side=tk.LEFT, padx=10, pady=10)
        
        stats_title = tk.Label(stats_header, text="ESTADÍSTICAS", 
                              font=("Segoe UI", 11, "bold"), bg="#edf2f7", fg="#2d3748")
        stats_title.pack(side=tk.LEFT, pady=10)
        
        self.stats_container = tk.Frame(control_content, bg="#edf2f7", relief=tk.FLAT, bd=1)
        self.stats_container.pack(fill=tk.X, pady=(0, 20))
        
        self.label_total = tk.Label(self.stats_container, text="Total en cola: 0", 
                                   font=("Segoe UI", 10, "bold"), bg="#edf2f7", fg="#2d3748")
        self.label_total.pack(pady=8)
        
        self.label_emergencias = tk.Label(self.stats_container, text="🚨 Cola Emergencias: 0", 
                                         font=("Segoe UI", 10, "bold"), bg="#edf2f7", fg="#E53E3E")
        self.label_emergencias.pack(pady=3)
        
        self.label_normales = tk.Label(self.stats_container, text="📋 Cola Normal: 0", 
                                      font=("Segoe UI", 10, "bold"), bg="#edf2f7", fg="#48BB78")
        self.label_normales.pack(pady=3)
        
        self.label_tiempo_prom = tk.Label(self.stats_container, text="⏱ Tiempo prom: 0 min", 
                                         font=("Segoe UI", 10, "bold"), bg="#edf2f7", fg="#ED8936")
        self.label_tiempo_prom.pack(pady=8)
        
        # Próximo paciente
        next_header = tk.Frame(control_content, bg="#e6fffa")
        next_header.pack(fill=tk.X, pady=(20, 0))
        
        next_icon = tk.Label(next_header, text="👆", font=("Segoe UI", 14), bg="#e6fffa")
        next_icon.pack(side=tk.LEFT, padx=10, pady=10)
        
        next_title = tk.Label(next_header, text="FRENTE DE LA COLA", 
                             font=("Segoe UI", 11, "bold"), bg="#e6fffa", fg="#2d3748")
        next_title.pack(side=tk.LEFT, pady=10)
        
        self.next_container = tk.Frame(control_content, bg="#e6fffa", relief=tk.FLAT, bd=1)
        self.next_container.pack(fill=tk.X)
        
        self.label_proximo = tk.Label(self.next_container, text="Cola vacía", 
                                     font=("Segoe UI", 10, "bold"), bg="#e6fffa", fg="#38B2AC")
        self.label_proximo.pack(pady=15)
    
    def registrar_paciente(self):
        paciente = self.entry_paciente.get().strip()
        telefono = self.entry_telefono.get().strip()
        fecha = self.entry_fecha.get().strip()
        hora = self.entry_hora.get().strip()
        especialidad = self.combo_especialidad.get()
        es_emergencia = self.var_emergencia.get()
        
        errores = []
        
        if not paciente:
            errores.append("• El nombre del paciente es obligatorio")
        elif not self.validar_nombre_completo(paciente):
            errores.append("• El nombre debe contener solo letras y espacios")
        
        if not telefono:
            errores.append("• El teléfono es obligatorio")
        elif not self.validar_telefono_completo(telefono):
            errores.append("• El teléfono debe contener solo números")
        
        if not especialidad:
            errores.append("• Debe seleccionar una especialidad")
        
        if errores:
            mensaje_error = "❌ ERROR EN REGISTRO\n\nMotivo(s):\n" + "\n".join(errores)
            messagebox.showerror("Error", mensaje_error)
            return
        
        # ENCOLAR: Agregar al final de la cola correspondiente
        nuevo_paciente = Paciente(paciente, telefono, fecha, hora, especialidad, es_emergencia)
        self.cola_turnos.encolar(nuevo_paciente)
        
        tipo = "EMERGENCIA" if es_emergencia else "NORMAL"
        messagebox.showinfo("Paciente Encolado", 
                          f"✅ Paciente agregado a cola {tipo}\n\nNombre: {paciente}\nEspecialidad: {especialidad}\n\nPosición: {self.cola_turnos.tamaño()}")
        
        self.limpiar_campos()
        self.actualizar_interfaz()
    
    def llamar_siguiente_paciente(self):
        # DESENCOLAR: Eliminar del frente de la cola
        paciente = self.cola_turnos.desencolar()
        
        if paciente:
            tipo = "EMERGENCIA" if paciente.es_emergencia else "NORMAL"
            messagebox.showinfo("Desencolando Paciente", 
                              f"📢 SIGUIENTE PACIENTE:\n\n{paciente.nombre}\nTipo: {tipo}\nEspecialidad: {paciente.especialidad}\nTeléfono: {paciente.telefono}")
            self.actualizar_interfaz()
        else:
            messagebox.showwarning("Cola Vacía", "No hay pacientes en la cola")
    
    def cancelar_turno_seleccionado(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Selección", "Seleccione un turno para cancelar")
            return
        
        item_values = self.tree.item(selected_item[0])['values']
        nombre_paciente = item_values[1]
        
        respuesta = messagebox.askyesno("Confirmar", 
                                      f"¿Cancelar turno de {nombre_paciente}?")
        
        if respuesta:
            if self.cola_turnos.cancelar_turno(nombre_paciente):
                messagebox.showinfo("Cancelado", f"Turno de {nombre_paciente} cancelado")
                self.actualizar_interfaz()
            else:
                messagebox.showerror("Error", "No se pudo cancelar")
    
    def buscar_paciente_dialog(self):
        nombre = simpledialog.askstring("Buscar", "Nombre del paciente:")
        
        if nombre:
            paciente, posicion = self.cola_turnos.buscar_paciente(nombre)
            
            if paciente:
                tiempo_espera = datetime.now() - paciente.hora_registro
                minutos = int(tiempo_espera.total_seconds() / 60)
                tiempo_estimado = (posicion - 1) * self.tiempo_por_consulta
                
                tipo = "EMERGENCIA" if paciente.es_emergencia else "NORMAL"
                
                messagebox.showinfo("Encontrado", 
                                  f"Paciente: {paciente.nombre}\n" +
                                  f"Posición en cola: {posicion}\n" +
                                  f"Tipo: {tipo}\n" +
                                  f"Especialidad: {paciente.especialidad}\n" +
                                  f"Tiempo esperando: {minutos} min\n" +
                                  f"Tiempo estimado: {tiempo_estimado} min")
            else:
                messagebox.showwarning("No Encontrado", f"Paciente {nombre} no está en cola")
    
    def consultar_tiempo_espera(self):
        nombre = self.entry_consultar.get().strip()
        
        if not nombre:
            messagebox.showerror("Error", "Ingrese nombre del paciente")
            return
        
        paciente, posicion = self.cola_turnos.buscar_paciente(nombre)
        
        if paciente:
            tiempo_espera = datetime.now() - paciente.hora_registro
            minutos = int(tiempo_espera.total_seconds() / 60)
            tiempo_estimado = (posicion - 1) * self.tiempo_por_consulta
            
            messagebox.showinfo("Tiempo de Espera", 
                              f"Paciente: {paciente.nombre}\n" +
                              f"Posición: {posicion}\n" +
                              f"Esperando: {minutos} min\n" +
                              f"Tiempo estimado: {tiempo_estimado} min")
            
            self.entry_consultar.delete(0, tk.END)
        else:
            messagebox.showwarning("No Encontrado", f"Paciente {nombre} no está en cola")
    
    def limpiar_campos(self):
        self.entry_paciente.delete(0, tk.END)
        self.entry_telefono.delete(0, tk.END)
        self.entry_fecha.delete(0, tk.END)
        self.entry_fecha.insert(0, datetime.now().strftime("%d/%m/%Y"))
        self.entry_hora.delete(0, tk.END)
        self.entry_hora.insert(0, datetime.now().strftime("%H:%M"))
        self.combo_especialidad.set("")
        self.var_emergencia.set(False)
    
    def actualizar_interfaz(self):
        # Limpiar tabla
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Llenar tabla con cola ordenada
        turnos = self.cola_turnos.obtener_lista_completa()
        for turno in turnos:
            tags = ("emergencia",) if turno['tipo'] == "EMERGENCIA" else ("normal",)
            
            self.tree.insert("", "end", values=(
                turno['posicion'],
                turno['paciente'],
                turno['telefono'],
                turno['hora'],
                turno['especialidad'],
                turno['tipo'],
                turno['tiempo_espera']
            ), tags=tags)
        
        self.tree.tag_configure("emergencia", background="#ffebee", foreground="#d32f2f")
        self.tree.tag_configure("normal", background="#f9f9f9", foreground="#333333")
        
        # Actualizar estadísticas
        stats = self.cola_turnos.obtener_estadisticas()
        self.label_total.config(text=f"Total en cola: {stats['total']}")
        self.label_emergencias.config(text=f"🚨 Cola Emergencias: {stats['emergencias']}")
        self.label_normales.config(text=f"📋 Cola Normal: {stats['normales']}")
        self.label_tiempo_prom.config(text=f"⏱ Tiempo prom: {stats['tiempo_promedio']} min")
        
        # Actualizar próximo paciente (frente de la cola)
        proximo = self.cola_turnos.ver_primero()
        if proximo:
            tipo = "🚨 EMERGENCIA" if proximo.es_emergencia else "📋 NORMAL"
            texto = f"{proximo.nombre}\n{tipo}\n{proximo.especialidad}"
            self.label_proximo.config(text=texto, fg="#2d3748")
        else:
            self.label_proximo.config(text="Cola vacía", fg="#38B2AC")


if __name__ == "__main__":
    root = tk.Tk()
    app = GestorTurnosApp(root)
    root.mainloop()


# IMPLEMENTACIÓN DE COLA (QUEUE) CON FIFO
# ========================================
#
# ESTRUCTURA DE DATOS: Cola (Queue)
# - Usa collections.deque para eficiencia O(1) en ambos extremos
# - Dos colas separadas: una para emergencias, otra para turnos normales
# - Cada cola mantiene orden FIFO estricto
#
# OPERACIONES PRINCIPALES:
# 1. ENCOLAR (enqueue): agregar al FINAL de la cola
#    - Tiempo: O(1)
#    - Método: cola.append(elemento)
#
# 2. DESENCOLAR (dequeue): eliminar del FRENTE de la cola
#    - Tiempo: O(1)
#    - Método: cola.popleft()
#
# 3. VER FRENTE (peek): ver primer elemento sin eliminarlo
#    - Tiempo: O(1)
#    - Método: cola[0]
#
# VENTAJAS DE USAR COLA VS LISTA ENLAZADA:
# - Operaciones más eficientes (O(1) garantizado)
# - Código más simple y mantenible
# - Menos propenso a errores de punteros
# - API más clara (append/popleft vs manejar nodos)
#
# PRINCIPIO FIFO:
# "First In, First Out" - El primero en entrar es el primero en salir
# Como una fila en el banco: quien llega primero, es atendido primero
#
# PRIORIDAD DE EMERGENCIAS:
# Se mantiene con dos colas separadas:
# - Cola de emergencias se procesa primero
# - Dentro de cada cola se respeta FIFO estricto
# - Emergencias NO "saltan" a otras emergencias