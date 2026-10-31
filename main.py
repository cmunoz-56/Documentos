"""Entrada del Sistema de Clinica Medica, Equipo 2.

Ejecutar: python main.py
Los cuatro modulos originales se conservan sin cambios.
"""

import sqlite3
import sys
from contextlib import closing

import base_datos
import personas
import citas
import consultas
import os


def titulo(texto):
    print("\n" + "=" * 64)
    print(texto.center(64))
    print("=" * 64)


def caratula():
    titulo("SISTEMA DE CLINICA MEDICA")
    print("Universidad Mariano Galvez de Guatemala")
    print("Ingenieria en Sistemas | Algoritmos | Equipo 2 | Seccion B")
    print("\nINTEGRANTES")
    print("  Jose Gabriel Camposeco Santizo       0906 26 16670")
    print("  Christofher Omar Munoz Escobar       0906 26 24748")
    print("  Dafhne Ximena Gabriel Escobar        0906 26 26800")
    print("  Axel Miguel Estrada Garcia           0906 26 11867")
    print("\nOrden sugerido para comenzar:")
    print("  Esp    ecialidad > Medico y paciente > Cita > Consulta")
    print("\nLos datos se guardan automaticamente en clinica.db.")
    print("Ctrl+C cancela una operacion; Ctrl+Z y ENTER cierra en Windows.")
    input("\nPresione ENTER para iniciar...")
    
def menu(titulo_menu, opciones):
    os.system("cls" if os.name == "nt" else "clear")
    """Cada opcion contiene su etiqueta y la funcion original que ejecuta."""
    while True:
        titulo(titulo_menu)
        for numero, (etiqueta, _) in opciones.items():
            print(f"  {numero}. {etiqueta}")
        print("  0. " + ("Salir" if titulo_menu == "MENU PRINCIPAL" else "Volver"))
        try:
            opcion = input("\nSeleccione una opcion: ").strip()
            if opcion == "0":
                return
            if opcion not in opciones:
                print("Opcion incorrecta. Escriba uno de los numeros del menu.")
                continue
            opciones[opcion][1]()
        except KeyboardInterrupt:
            print("\nOperacion interrumpida. Regresando al menu.")
            continue
        except sqlite3.Error as error:
            print("\nNo se pudo completar la operacion con la base de datos:", error)
        except (ValueError, OverflowError) as error:
            print("\nEl dato no es valido o esta fuera del rango permitido:", error)
        # EOFError se propaga hasta main para cerrar incluso desde un submenu.


def seleccionar_registro(tabla, mensaje):
    """Muestra IDs reales antes de pedir una seleccion; no crea registros."""
    # Las tablas son constantes internas, nunca texto introducido por el usuario.
    permitidas = {"pacientes", "medicos"}
    if tabla not in permitidas:
        raise ValueError("Tabla no permitida.")
    with closing(base_datos.conectar()) as conexion:
        filas = conexion.execute(
            f"SELECT id, nombre FROM {tabla} ORDER BY nombre, id"
        ).fetchall()
    if not filas:
        print(f"No hay {tabla}. Registrelos primero en Personas y especialidades.")
        return None
    print(f"\n{tabla.upper()}")
    for fila in filas:
        print(f"  {fila['id']}. {fila['nombre']}")
    ids = {fila["id"] for fila in filas}
    while True:
        texto = input(mensaje + " (0 para volver): ").strip()
        if texto == "0":
            return None
        try:
            numero = citas.validar_id(texto)
            if numero in ids:
                return numero
            print("Seleccione un ID de la lista.")
        except ValueError as error:
            print(error)


def pedir_fecha(mensaje):
    while True:
        try:
            return citas.validar_fecha(input(mensaje).strip())
        except ValueError as error:
            print(error)


def pedir_fecha_hora():
    while True:
        fecha = input("Fecha futura (AAAA-MM-DD): ").strip()
        hora = input("Hora (HH:MM, formato de 24 horas): ").strip()
        try:
            return citas.validar_fecha_hora(fecha, hora)
        except ValueError as error:
            print(error)


def nueva_cita():
    titulo("REGISTRAR CITA")
    paciente = seleccionar_registro("pacientes", "ID del paciente")
    if paciente is None:
        return
    medico = seleccionar_registro("medicos", "ID del medico")
    if medico is None:
        return
    fecha, hora = pedir_fecha_hora()
    cita_id = citas.registrar_cita(paciente, medico, fecha, hora)
    if cita_id is not None:
        print(f"Cita registrada correctamente. ID: {cita_id}")


def todas_las_citas():
    citas.mostrar_citas(citas.consultar_citas())


def agenda_medico():
    medico = seleccionar_registro("medicos", "ID del medico")
    if medico is not None:
        fecha = pedir_fecha("Fecha de la agenda (AAAA-MM-DD): ")
        citas.mostrar_citas(citas.consultar_citas(medico_id=medico, fecha=fecha))


def citas_paciente():
    paciente = seleccionar_registro("pacientes", "ID del paciente")
    if paciente is not None:
        citas.mostrar_citas(citas.consultar_citas(paciente_id=paciente))


def seleccionar_cita():
    pendientes = citas.consultar_citas(estado="Programada")
    citas.mostrar_citas(pendientes)
    if not pendientes:
        return None
    ids = {cita["id"] for cita in pendientes}
    while True:
        texto = input("ID de la cita (0 para volver): ").strip()
        if texto == "0":
            return None
        try:
            numero = citas.validar_id(texto)
            if numero in ids:
                return numero
            print("Seleccione una cita Programada de la lista.")
        except ValueError as error:
            print(error)


def cambiar_cita():
    cita_id = seleccionar_cita()
    if cita_id is not None:
        fecha, hora = pedir_fecha_hora()
        if citas.reprogramar_cita(cita_id, fecha, hora):
            print("Cita reprogramada correctamente.")


def cancelar_cita():
    cita_id = seleccionar_cita()
    if cita_id is None:
        return
    confirmar = input(f"Cancelar cita {cita_id}? Escriba S para confirmar: ").strip().upper()
    if confirmar == "S":
        if citas.cancelar_cita(cita_id):
            print("Cita cancelada correctamente.")
    else:
        print("La cita se conserva.")


def menu_personas():
    menu("PERSONAS Y ESPECIALIDADES", {
        "1": ("Registrar paciente", personas.registrar_paciente),
        "2": ("Consultar pacientes", personas.consultar_pacientes),
        "3": ("Buscar paciente por nombre", personas.buscar_paciente),
        "4": ("Registrar especialidad y costo", personas.registrar_especialidad),
        "5": ("Consultar especialidades", personas.consultar_especialidades),
        "6": ("Registrar medico", personas.registrar_medico),
        "7": ("Consultar medicos", personas.consultar_medicos),
        "8": ("Buscar medico por nombre", personas.buscar_medico),
    })


def menu_citas():
    menu("CITAS Y AGENDA", {
        "1": ("Registrar cita", nueva_cita),
        "2": ("Ver todas las citas", todas_las_citas),
        "3": ("Ver agenda de un medico por fecha", agenda_medico),
        "4": ("Ver citas de un paciente", citas_paciente),
        "5": ("Reprogramar cita", cambiar_cita),
        "6": ("Cancelar cita", cancelar_cita),
    })


def menu_consultas():
    menu("CONSULTAS E INGRESOS", {
        "1": ("Registrar consulta y total a cobrar", consultas.registrar_consulta),
        "2": ("Ver consultas realizadas", consultas.consultar_consultas),
        "3": ("Ver historial de un paciente", consultas.historial_paciente),
        "4": ("Ver ingresos por fechas de las citas", consultas.reporte_ingresos),
        "5": ("Ver citas pendientes", consultas.mostrar_citas_pendientes),
    })


def main():
    """Prepara SQLite una vez y abre la interfaz de consola."""
    try:
        caratula()
        base_datos.crear_tablas()
        menu("MENU PRINCIPAL", {
            "1": ("Personas y especialidades", menu_personas),
            "2": ("Citas y agenda", menu_citas),
            "3": ("Consultas e ingresos", menu_consultas),
        })
    except (EOFError, KeyboardInterrupt):
        print("\nCierre solicitado.")
    except (sqlite3.Error, OSError) as error:
        print("No se pudo iniciar el sistema:", error)
        return 1
    print("\nSistema cerrado. Los registros guardados se conservan.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
