"""Modulo de consultas medicas del Proyecto 2 (consola + SQLite).

Se integra con base_datos.py y las tablas pacientes, medicos,
especialidades, citas y consultas.
"""

import math
import sqlite3
from datetime import date
from base_datos import conectar, crear_tablas


def abrir_conexion():
    """Conecta con la misma base de datos del resto del proyecto."""
    conexion = conectar()
    conexion.row_factory = sqlite3.Row
    conexion.execute("PRAGMA foreign_keys = ON")
    return conexion


def leer_id(mensaje):
    while True:
        try:
            numero = int(input(mensaje).strip())
            if numero > 0:
                return numero
            print("ERROR: el ID debe ser mayor que cero.")
        except ValueError:
            print("ERROR: escriba un numero entero valido.")


def leer_texto(mensaje):
    while True:
        texto = input(mensaje).strip()
        if 0 < len(texto) <= 1000:
            return texto
        print("ERROR: escriba texto (maximo 1000 caracteres).")


def leer_fecha(mensaje):
    while True:
        texto = input(mensaje).strip()
        try:
            fecha = date.fromisoformat(texto)
            if fecha.isoformat() == texto:
                return texto
        except ValueError:
            pass
        print("ERROR: use una fecha real en formato AAAA-MM-DD.")


def mostrar_citas_pendientes():
    """Muestra las citas que aun pueden convertirse en consultas."""
    conexion = None
    try:
        conexion = abrir_conexion()
        citas = conexion.execute("""
            SELECT c.id, c.fecha, c.hora, p.nombre AS paciente,
                   m.nombre AS medico, e.nombre AS especialidad, e.costo
            FROM citas AS c
            JOIN pacientes AS p ON p.id = c.paciente_id
            JOIN medicos AS m ON m.id = c.medico_id
            JOIN especialidades AS e ON e.id = m.especialidad_id
            WHERE c.estado = 'Programada'
            ORDER BY c.fecha, c.hora, c.id
        """).fetchall()
        print("\n========== CITAS PENDIENTES ==========")
        if not citas:
            print("No hay citas programadas para atender.")
            return False
        for cita in citas:
            print(f"ID: {cita['id']} | {cita['fecha']} {cita['hora']} | "
                  f"Paciente: {cita['paciente']} | Medico: {cita['medico']} | "
                  f"Especialidad: {cita['especialidad']} | "
                  f"Costo: Q{cita['costo']:.2f}")
        return True
    except sqlite3.Error as error:
        print("ERROR al consultar citas:", error)
        return False
    finally:
        if conexion is not None:
            conexion.close()


def registrar_consulta():
    """Registra diagnostico/tratamiento, cobra y marca la cita Atendida."""
    if not mostrar_citas_pendientes():
        return

    cita_id = leer_id("ID de la cita que desea atender: ")
    diagnostico = leer_texto("Diagnostico: ")
    tratamiento = leer_texto("Tratamiento: ")

    conexion = None
    try:
        conexion = abrir_conexion()
        # Una sola transaccion: no guardar parcialmente la atencion.
        conexion.execute("BEGIN IMMEDIATE")
        cita = conexion.execute("""
            SELECT c.id, c.estado, e.costo, p.nombre AS paciente
            FROM citas AS c
            JOIN pacientes AS p ON p.id = c.paciente_id
            JOIN medicos AS m ON m.id = c.medico_id
            JOIN especialidades AS e ON e.id = m.especialidad_id
            WHERE c.id = ?
        """, (cita_id,)).fetchone()

        if cita is None:
            print("ERROR: la cita no existe o sus datos no son validos.")
            return
        if cita["estado"] != "Programada":
            print(f"ERROR: la cita esta en estado {cita['estado']}.")
            return

        registrada = conexion.execute(
            "SELECT id FROM consultas WHERE cita_id = ?", (cita_id,)
        ).fetchone()
        if registrada:
            print("ERROR: esta cita ya tiene una consulta registrada.")
            return

        costo = float(cita["costo"])
        if not math.isfinite(costo) or costo < 0:
            print("ERROR: el costo de la especialidad no es valido.")
            return
        total = round(costo, 2)

        conexion.execute("""
            INSERT INTO consultas (cita_id, diagnostico, tratamiento, total)
            VALUES (?, ?, ?, ?)
        """, (cita_id, diagnostico, tratamiento, total))
        actualizado = conexion.execute("""
            UPDATE citas SET estado = 'Atendida'
            WHERE id = ? AND estado = 'Programada'
        """, (cita_id,))
        if actualizado.rowcount != 1:
            print("ERROR: no fue posible actualizar el estado de la cita.")
            return

        conexion.commit()
        print(f"\nEXITO: consulta de {cita['paciente']} registrada.")
        print("Estado de la cita: Atendida")
        print(f"Total a cobrar: Q{total:.2f}")
    except (sqlite3.Error, ValueError, TypeError, OverflowError) as error:
        print("ERROR: no se pudo registrar la consulta:", error)
    finally:
        if conexion is not None:
            conexion.close()  # Si no hubo commit, SQLite revierte los cambios.


def consultar_consultas():
    conexion = None
    try:
        conexion = abrir_conexion()
        filas = conexion.execute("""
            SELECT q.id, c.fecha, c.hora, p.nombre AS paciente,
                   m.nombre AS medico, q.diagnostico, q.tratamiento, q.total
            FROM consultas AS q
            JOIN citas AS c ON c.id = q.cita_id
            JOIN pacientes AS p ON p.id = c.paciente_id
            JOIN medicos AS m ON m.id = c.medico_id
            ORDER BY c.fecha DESC, c.hora DESC, q.id DESC
        """).fetchall()
        print("\n========== CONSULTAS REALIZADAS ==========")
        if not filas:
            print("No hay consultas registradas.")
        for fila in filas:
            print(f"\nConsulta: {fila['id']} | {fila['fecha']} {fila['hora']}")
            print(f"Paciente: {fila['paciente']} | Medico: {fila['medico']}")
            print(f"Diagnostico: {fila['diagnostico']}")
            print(f"Tratamiento: {fila['tratamiento']}")
            print(f"Cobrado: Q{fila['total']:.2f}")
        print(f"\nTotal de consultas: {len(filas)}")
    except sqlite3.Error as error:
        print("ERROR al consultar las atenciones:", error)
    finally:
        if conexion is not None:
            conexion.close()


def historial_paciente():
    paciente_id = leer_id("ID del paciente: ")
    conexion = None
    try:
        conexion = abrir_conexion()
        paciente = conexion.execute(
            "SELECT nombre FROM pacientes WHERE id = ?", (paciente_id,)
        ).fetchone()
        if paciente is None:
            print("ERROR: no existe un paciente con ese ID.")
            return
        filas = conexion.execute("""
            SELECT c.fecha, c.hora, m.nombre AS medico,
                   e.nombre AS especialidad, q.diagnostico,
                   q.tratamiento, q.total
            FROM consultas AS q
            JOIN citas AS c ON c.id = q.cita_id
            JOIN medicos AS m ON m.id = c.medico_id
            JOIN especialidades AS e ON e.id = m.especialidad_id
            WHERE c.paciente_id = ?
            ORDER BY c.fecha DESC, c.hora DESC, q.id DESC
        """, (paciente_id,)).fetchall()
        print(f"\n========== HISTORIAL DE {paciente['nombre']} ==========")
        if not filas:
            print("El paciente no tiene consultas registradas.")
        for fila in filas:
            print(f"\nFecha: {fila['fecha']} {fila['hora']}")
            print(f"Medico: {fila['medico']} | Especialidad: {fila['especialidad']}")
            print(f"Diagnostico: {fila['diagnostico']}")
            print(f"Tratamiento: {fila['tratamiento']}")
            print(f"Total: Q{fila['total']:.2f}")
        print(f"\nTotal de atenciones: {len(filas)}")
    except sqlite3.Error as error:
        print("ERROR al obtener el historial:", error)
    finally:
        if conexion is not None:
            conexion.close()


def reporte_ingresos():
    print("\n========== INGRESOS POR PERIODO ==========")
    inicio = leer_fecha("Desde (AAAA-MM-DD): ")
    fin = leer_fecha("Hasta (AAAA-MM-DD): ")
    if inicio > fin:
        print("ERROR: la fecha inicial no puede ser posterior a la final.")
        return
    conexion = None
    try:
        conexion = abrir_conexion()
        resumen = conexion.execute("""
            SELECT COUNT(*) AS cantidad, COALESCE(SUM(q.total), 0) AS ingresos
            FROM consultas AS q
            JOIN citas AS c ON c.id = q.cita_id
            WHERE c.fecha BETWEEN ? AND ? AND c.estado = 'Atendida'
        """, (inicio, fin)).fetchone()
        print(f"Periodo: {inicio} al {fin}")
        print(f"Consultas atendidas: {resumen['cantidad']}")
        print(f"Ingresos totales: Q{resumen['ingresos']:.2f}")
    except sqlite3.Error as error:
        print("ERROR al generar el reporte:", error)
    finally:
        if conexion is not None:
            conexion.close()


def menu():
    """Menu independiente para probar el modulo antes de integrarlo."""
    try:
        crear_tablas()
    except sqlite3.Error as error:
        print("ERROR al preparar la base de datos:", error)
        return

    opciones = {
        "1": registrar_consulta,
        "2": consultar_consultas,
        "3": historial_paciente,
        "4": reporte_ingresos,
        "5": mostrar_citas_pendientes,
    }
    while True:
        print("""
========== MODULO DE CONSULTAS ==========
1. Registrar una consulta
2. Ver consultas realizadas
3. Ver historial de un paciente
4. Reporte de ingresos por fechas
5. Ver citas pendientes
6. Regresar / salir
=========================================
""")
        opcion = input("Seleccione una opcion (1-6): ").strip()
        if opcion == "6":
            print("Regresando del modulo de consultas.")
            break
        accion = opciones.get(opcion)
        if accion is None:
            print("ERROR: seleccione una opcion del 1 al 6.")
            continue
        try:
            accion()
        except (EOFError, KeyboardInterrupt):
            print("\nOperacion interrumpida.")
            break
        input("\nPresione ENTER para continuar...")


if __name__ == "__main__":
    try:
        menu()
    except (EOFError, KeyboardInterrupt):
        print("\nModulo cerrado.")
