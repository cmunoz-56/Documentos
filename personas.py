import math
import sqlite3
from base_datos import conectar, crear_tablas, RUTA_BD


# VALIDACIONES

def leer_nombre(mensaje):
    while True:
        nombre = input(mensaje).strip()

        if nombre and all(c.isalpha() or c.isspace() for c in nombre):
            return nombre

        print("ERROR: solo se permiten letras y espacios.")


def leer_telefono():
    while True:
        telefono = input("Telefono (8 digitos): ").strip()

        if telefono.isascii() and telefono.isdigit() and len(telefono) == 8:
            return telefono

        print("ERROR: el telefono debe tener exactamente 8 digitos.")


def leer_entero(mensaje):
    while True:
        try:
            numero = int(input(mensaje).strip())

            if numero > 0:
                return numero

            print("ERROR: el numero debe ser mayor que cero.")

        except ValueError:
            print("ERROR: ingresa un numero entero valido.")


def leer_precio():
    while True:
        try:
            precio = float(input("Precio de la consulta en Q: ").strip())

            if math.isfinite(precio) and precio >= 0:
                return precio

            print("ERROR: el precio debe ser mayor o igual a cero.")

        except ValueError:
            print("ERROR: ingresa un precio valido.")


# OPERACIONES CON LA BASE DE DATOS

def guardar(sql, datos, mensaje):
    conexion = conectar()

    try:
        conexion.execute(sql, datos)
        conexion.commit()
        print("\nEXITO:", mensaje)
        return True

    except sqlite3.IntegrityError as error:
        conexion.rollback()
        print("\nERROR: el registro viola una regla de la base de datos.")
        print("Detalle:", error)
        return False

    except sqlite3.Error as error:
        conexion.rollback()
        print("\nERROR al guardar:", error)
        return False

    finally:
        conexion.close()


def consultar(sql, datos=()):
    conexion = conectar()

    try:
        return conexion.execute(sql, datos).fetchall()

    finally:
        conexion.close()


def mostrar_total(cantidad, tipo):
    print(f"\nTotal de {tipo}: {cantidad}")


# OPCION 1: REGISTRAR PACIENTE

def registrar_paciente():
    print("\n========== REGISTRAR PACIENTE ==========")

    nombre = leer_nombre("Nombre completo del paciente: ")
    telefono = leer_telefono()

    guardar(
        "INSERT INTO pacientes (nombre, telefono) VALUES (?, ?)",
        (nombre, telefono),
        f"Paciente '{nombre}' registrado correctamente."
    )


# OPCION 2: CONSULTAR PACIENTES

def consultar_pacientes():
    print("\n========== CONSULTAR PACIENTES ==========")
    print("Base de datos:", RUTA_BD.resolve())

    pacientes = consultar(
        "SELECT id, nombre, telefono FROM pacientes ORDER BY id"
    )

    if not pacientes:
        print("No hay pacientes registrados.")
        return

    for paciente in pacientes:
        telefono = paciente["telefono"] or "No registrado"

        print(
            f"ID: {paciente['id']} | "
            f"Nombre: {paciente['nombre']} | "
            f"Telefono: {telefono}"
        )

    mostrar_total(len(pacientes), "pacientes")


# OPCION 3: BUSCAR PACIENTE

def buscar_paciente():
    print("\n========== BUSCAR PACIENTE ==========")

    busqueda = input("Ingrese el nombre del paciente: ").strip()

    if not busqueda:
        print("ERROR: debes escribir un nombre para buscar.")
        return

    pacientes = consultar(
        """
        SELECT id, nombre, telefono
        FROM pacientes
        WHERE nombre LIKE ?
        ORDER BY nombre
        """,
        (f"%{busqueda}%",)
    )

    if not pacientes:
        print(f"No se encontraron pacientes con el nombre '{busqueda}'.")
        return

    for paciente in pacientes:
        telefono = paciente["telefono"] or "No registrado"

        print(
            f"ID: {paciente['id']} | "
            f"Nombre: {paciente['nombre']} | "
            f"Telefono: {telefono}"
        )

    mostrar_total(len(pacientes), "coincidencias")


# OPCION 4: REGISTRAR ESPECIALIDAD

def registrar_especialidad():
    print("\n========== REGISTRAR ESPECIALIDAD ==========")

    nombre = leer_nombre("Nombre de la especialidad: ")
    costo = leer_precio()

    guardar(
        "INSERT INTO especialidades (nombre, costo) VALUES (?, ?)",
        (nombre, costo),
        f"Especialidad '{nombre}' registrada correctamente "
        f"con un costo de Q{costo:.2f}."
    )


# OPCION 5: CONSULTAR ESPECIALIDADES

def consultar_especialidades():
    print("\n========== CONSULTAR ESPECIALIDADES ==========")

    especialidades = consultar(
        "SELECT id, nombre, costo FROM especialidades ORDER BY id"
    )

    if not especialidades:
        print("No hay especialidades registradas.")
        return

    for especialidad in especialidades:
        print(
            f"ID: {especialidad['id']} | "
            f"Especialidad: {especialidad['nombre']} | "
            f"Costo: Q{especialidad['costo']:.2f}"
        )

    mostrar_total(len(especialidades), "especialidades")


# OPCION 6: REGISTRAR MEDICO

def registrar_medico():
    print("\n========== REGISTRAR MEDICO ==========")

    especialidades = consultar(
        "SELECT id, nombre FROM especialidades ORDER BY nombre"
    )

    if not especialidades:
        print("No puedes registrar un medico todavía.")
        print("Primero registra una especialidad con la opcion 4.")
        return

    print("\nEspecialidades disponibles:")

    for especialidad in especialidades:
        print(
            f"ID: {especialidad['id']} | "
            f"Nombre: {especialidad['nombre']}"
        )

    ids_validos = [e["id"] for e in especialidades]

    while True:
        especialidad_id = leer_entero("ID de la especialidad: ")

        if especialidad_id in ids_validos:
            break

        print("ERROR: selecciona un ID de la lista.")

    nombre = leer_nombre("Nombre completo del medico: ")

    guardar(
        "INSERT INTO medicos (nombre, especialidad_id) VALUES (?, ?)",
        (nombre, especialidad_id),
        f"Medico '{nombre}' registrado correctamente."
    )


# OPCION 7: CONSULTAR MEDICOS

def consultar_medicos():
    print("\n========== CONSULTAR MEDICOS ==========")

    medicos = consultar(
        """
        SELECT m.id, m.nombre, e.nombre AS especialidad, e.costo
        FROM medicos AS m
        JOIN especialidades AS e ON e.id = m.especialidad_id
        ORDER BY m.id
        """
    )

    if not medicos:
        print("No hay medicos registrados con una especialidad valida.")
        return

    for medico in medicos:
        print(
            f"ID: {medico['id']} | "
            f"Medico: {medico['nombre']} | "
            f"Especialidad: {medico['especialidad']} | "
            f"Costo: Q{medico['costo']:.2f}"
        )

    mostrar_total(len(medicos), "medicos")


# OPCION 8: BUSCAR MEDICO

def buscar_medico():
    print("\n========== BUSCAR MEDICO ==========")

    busqueda = input("Ingrese el nombre del medico: ").strip()

    if not busqueda:
        print("ERROR: debes escribir un nombre para buscar.")
        return

    medicos = consultar(
        """
        SELECT m.id, m.nombre, e.nombre AS especialidad, e.costo
        FROM medicos AS m
        JOIN especialidades AS e ON e.id = m.especialidad_id
        WHERE m.nombre LIKE ?
        ORDER BY m.nombre
        """,
        (f"%{busqueda}%",)
    )

    if not medicos:
        print(f"No se encontraron medicos con el nombre '{busqueda}'.")
        return

    for medico in medicos:
        print(
            f"ID: {medico['id']} | "
            f"Medico: {medico['nombre']} | "
            f"Especialidad: {medico['especialidad']} | "
            f"Costo: Q{medico['costo']:.2f}"
        )

    mostrar_total(len(medicos), "coincidencias")


# MENU PRINCIPAL

def menu():
    crear_tablas()

    print("\nModulo de personas iniciado.")
    print("Base de datos:", RUTA_BD.resolve())

    opciones = {
        "1": registrar_paciente,
        "2": consultar_pacientes,
        "3": buscar_paciente,
        "4": registrar_especialidad,
        "5": consultar_especialidades,
        "6": registrar_medico,
        "7": consultar_medicos,
        "8": buscar_medico
    }

    while True:
        print("""
===================================================
              SISTEMA DE CLINICA
===================================================

PACIENTES
  1. Registrar paciente
  2. Consultar pacientes
  3. Buscar paciente

ESPECIALIDADES
  4. Registrar especialidad
  5. Consultar especialidades

MEDICOS
  6. Registrar medico
  7. Consultar medicos

  8. Buscar medico
  9. Salir
===================================================
""")

        opcion = input("Seleccione una opcion (1-9): ").strip()

        if opcion == "9":
            print("\nModulo de personas cerrado correctamente.")
            print("Gracias por utilizar el sistema.")
            break

        if opcion not in opciones:
            print("\nERROR: opcion incorrecta. Selecciona del 1 al 9.")
            continue

        try:
            opciones[opcion]()

        except sqlite3.Error as error:
            print("\nERROR DE BASE DE DATOS:", error)

        except Exception as error:
            print("\nERROR INESPERADO:", error)

        input("\nPresiona ENTER para regresar al menu...")


# INICIO DEL PROGRAMA

if __name__ == "__main__":
    try:
        menu()

    except sqlite3.Error as error:
        print("\nNo se pudo iniciar el sistema:", error)

    except Exception as error:
        print("\nNo se pudo iniciar el sistema:", error)