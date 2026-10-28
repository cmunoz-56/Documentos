import sqlite3
from contextlib import closing
from datetime import datetime

from base_datos import conectar, crear_tablas


def validar_id(valor):
    if isinstance(valor, bool) or not isinstance(valor, (str, int)):
        raise ValueError("El ID debe ser un numero entero positivo.")
    texto = str(valor).strip()
    if not texto.isascii() or not texto.isdigit():
        raise ValueError("El ID debe ser un numero entero positivo.")
    numero = int(texto)
    if not 1 <= numero <= 9223372036854775807:
        raise ValueError("El ID esta fuera del rango permitido.")
    return numero


def validar_fecha(fecha):
    if not isinstance(fecha, str):
        raise ValueError("Escribe la fecha como AAAA-MM-DD.")
    fecha = fecha.strip()
    try:
        valor = datetime.strptime(fecha, "%Y-%m-%d")
    except ValueError:
        raise ValueError("La fecha no existe o no tiene el formato AAAA-MM-DD.")
    if valor.strftime("%Y-%m-%d") != fecha:
        raise ValueError("Escribe la fecha completa como AAAA-MM-DD.")
    return fecha


def validar_fecha_hora(fecha, hora):
    fecha = validar_fecha(fecha)
    if not isinstance(hora, str):
        raise ValueError("Escribe la hora como HH:MM, de 00:00 a 23:59.")
    hora = hora.strip()
    try:
        momento = datetime.strptime(fecha + " " + hora, "%Y-%m-%d %H:%M")
    except ValueError:
        raise ValueError("La hora no es valida. Usa HH:MM, de 00:00 a 23:59.")
    if momento.strftime("%H:%M") != hora:
        raise ValueError("Escribe la hora completa como HH:MM.")
    if momento <= datetime.now():
        raise ValueError("La cita debe tener una fecha y hora futuras.")
    return fecha, hora


def verificar_disponibilidad(conexion, paciente_id, medico_id, fecha, hora, cita_id=0):
    ocupada = conexion.execute(
        """SELECT medico_id FROM citas
           WHERE fecha = ? AND hora = ? AND estado != 'Cancelada'
           AND id != ? AND (medico_id = ? OR paciente_id = ?)""",
        (fecha, hora, cita_id, medico_id, paciente_id)
    ).fetchone()
    if ocupada:
        if ocupada["medico_id"] == medico_id:
            raise ValueError("El medico ya tiene una cita en esa fecha y hora.")
        raise ValueError("El paciente ya tiene una cita en esa fecha y hora.")


def buscar_cita_pendiente(conexion, cita_id):
    cita = conexion.execute("SELECT * FROM citas WHERE id = ?", (cita_id,)).fetchone()
    if cita is None:
        raise ValueError("La cita no existe.")
    consulta = conexion.execute(
        "SELECT id FROM consultas WHERE cita_id = ?", (cita_id,)
    ).fetchone()
    if cita["estado"] != "Programada" or consulta is not None:
        raise ValueError("Solo puedes cambiar citas Programadas y sin consulta registrada.")
    return cita


def registrar_cita(paciente_id, medico_id, fecha, hora):
    try:
        paciente_id = validar_id(paciente_id)
        medico_id = validar_id(medico_id)
        fecha, hora = validar_fecha_hora(fecha, hora)
        with closing(conectar()) as conexion:
            with conexion:
                conexion.execute("BEGIN IMMEDIATE")
                paciente = conexion.execute(
                    "SELECT id FROM pacientes WHERE id = ?", (paciente_id,)
                ).fetchone()
                medico = conexion.execute(
                    "SELECT id FROM medicos WHERE id = ?", (medico_id,)
                ).fetchone()
                if paciente is None:
                    raise ValueError("El paciente no existe. Primero registralo con Cris.")
                if medico is None:
                    raise ValueError("El medico no existe. Primero registralo con Cris.")
                verificar_disponibilidad(conexion, paciente_id, medico_id, fecha, hora)
                cursor = conexion.execute(
                    """INSERT INTO citas (paciente_id, medico_id, fecha, hora, estado)
                       VALUES (?, ?, ?, ?, 'Programada')""",
                    (paciente_id, medico_id, fecha, hora)
                )
                cita_id = cursor.lastrowid
        return cita_id
    except (ValueError, sqlite3.Error) as error:
        print("ERROR al registrar la cita:", error)
        return None


def consultar_citas(medico_id=None, fecha=None, estado=None, paciente_id=None):
    try:
        sql = """SELECT c.id, c.paciente_id, p.nombre AS paciente,
                        c.medico_id, m.nombre AS medico, e.nombre AS especialidad,
                        c.fecha, c.hora, c.estado
                 FROM citas AS c
                 JOIN pacientes AS p ON p.id = c.paciente_id
                 JOIN medicos AS m ON m.id = c.medico_id
                 JOIN especialidades AS e ON e.id = m.especialidad_id
                 WHERE 1 = 1"""
        datos = []
        if medico_id is not None:
            sql += " AND c.medico_id = ?"
            datos.append(validar_id(medico_id))
        if fecha is not None:
            sql += " AND c.fecha = ?"
            datos.append(validar_fecha(fecha))
        if estado is not None:
            if estado not in ("Programada", "Atendida", "Cancelada"):
                raise ValueError("El estado debe ser Programada, Atendida o Cancelada.")
            sql += " AND c.estado = ?"
            datos.append(estado)
        if paciente_id is not None:
            sql += " AND c.paciente_id = ?"
            datos.append(validar_id(paciente_id))
        sql += " ORDER BY c.fecha, c.hora, c.id"
        with closing(conectar()) as conexion:
            return [dict(fila) for fila in conexion.execute(sql, datos).fetchall()]
    except (ValueError, sqlite3.Error) as error:
        print("ERROR al consultar las citas:", error)
        return []


def reprogramar_cita(cita_id, fecha, hora):
    try:
        cita_id = validar_id(cita_id)
        fecha, hora = validar_fecha_hora(fecha, hora)
        with closing(conectar()) as conexion:
            with conexion:
                conexion.execute("BEGIN IMMEDIATE")
                cita = buscar_cita_pendiente(conexion, cita_id)
                verificar_disponibilidad(
                    conexion, cita["paciente_id"], cita["medico_id"], fecha, hora, cita_id
                )
                conexion.execute(
                    "UPDATE citas SET fecha = ?, hora = ? WHERE id = ?",
                    (fecha, hora, cita_id)
                )
        return True
    except (ValueError, sqlite3.Error) as error:
        print("ERROR al reprogramar la cita:", error)
        return False


def cancelar_cita(cita_id):
    try:
        cita_id = validar_id(cita_id)
        with closing(conectar()) as conexion:
            with conexion:
                conexion.execute("BEGIN IMMEDIATE")
                buscar_cita_pendiente(conexion, cita_id)
                conexion.execute(
                    "UPDATE citas SET estado = 'Cancelada' WHERE id = ?", (cita_id,)
                )
        return True
    except (ValueError, sqlite3.Error) as error:
        print("ERROR al cancelar la cita:", error)
        return False


def mostrar_citas(citas):
    if not citas:
        print("No hay citas para mostrar.")
        return
    for cita in citas:
        print(
            f"ID: {cita['id']} | {cita['fecha']} {cita['hora']} | "
            f"Paciente: {cita['paciente']} | Medico: {cita['medico']} | "
            f"Especialidad: {cita['especialidad']} | Estado: {cita['estado']}"
        )
    print("Total de citas:", len(citas))


def mostrar_personas():
    with closing(conectar()) as conexion:
        pacientes = conexion.execute(
            "SELECT id, nombre FROM pacientes ORDER BY nombre, id"
        ).fetchall()
        medicos = conexion.execute(
            "SELECT id, nombre FROM medicos ORDER BY nombre, id"
        ).fetchall()
    if not pacientes or not medicos:
        print("Primero deben existir pacientes y medicos registrados por Cris.")
        return False
    print("\nPACIENTES")
    for paciente in pacientes:
        print(f"{paciente['id']}: {paciente['nombre']}")
    print("\nMEDICOS")
    for medico in medicos:
        print(f"{medico['id']}: {medico['nombre']}")
    return True


def menu():
    try:
        crear_tablas()
        while True:
            print("\nCITAS DE LA CLINICA")
            print("1. Registrar cita")
            print("2. Consultar todas las citas")
            print("3. Consultar agenda de un medico")
            print("4. Reprogramar cita")
            print("5. Cancelar cita")
            print("0. Volver o salir")
            opcion = input("Seleccione una opcion: ").strip()
            if opcion == "0":
                return
            try:
                if opcion == "1":
                    if mostrar_personas():
                        paciente = input("ID del paciente: ")
                        medico = input("ID del medico: ")
                        fecha = input("Fecha (AAAA-MM-DD): ")
                        hora = input("Hora (HH:MM, formato de 24 horas): ")
                        cita_id = registrar_cita(paciente, medico, fecha, hora)
                        if cita_id is not None:
                            print("Cita registrada correctamente. ID:", cita_id)
                elif opcion == "2":
                    mostrar_citas(consultar_citas())
                elif opcion == "3":
                    medico = input("ID del medico: ")
                    fecha = input("Fecha (AAAA-MM-DD): ")
                    mostrar_citas(consultar_citas(medico_id=medico, fecha=fecha))
                elif opcion == "4":
                    cita_id = input("ID de la cita: ")
                    fecha = input("Nueva fecha (AAAA-MM-DD): ")
                    hora = input("Nueva hora (HH:MM): ")
                    if reprogramar_cita(cita_id, fecha, hora):
                        print("Cita reprogramada correctamente.")
                elif opcion == "5":
                    cita_id = input("ID de la cita: ")
                    confirmar = input("Confirma la cancelacion escribiendo S: ").strip().upper()
                    if confirmar == "S":
                        if cancelar_cita(cita_id):
                            print("Cita cancelada correctamente.")
                    else:
                        print("La cita se conserva.")
                else:
                    print("Opcion incorrecta. Selecciona del 0 al 5.")
            except sqlite3.Error as error:
                print("ERROR de base de datos:", error)
    except (KeyboardInterrupt, EOFError):
        print("\nModulo de citas cerrado.")
    except sqlite3.Error as error:
        print("No se pudo iniciar el modulo de citas:", error)


if __name__ == "__main__":
    menu()
