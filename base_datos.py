"""Base de datos del Sistema de Clínica Médica (Equipo 2).

Archivo encargado: José.
Usa únicamente sqlite3, incluido con Python.

Para usarlo desde otro archivo:
    from base_datos import conectar, crear_tablas

    crear_tablas()              # Crea las tablas si todavía no existen
    conexion = conectar()       # Abre la base de datos
    conexion.close()            # Cierra la conexión al terminar
"""

import sqlite3
from pathlib import Path

RUTA_BD = Path(__file__).resolve().parent / "clinica.db"


def conectar():
    """Abre la base de datos y activa las relaciones entre tablas."""
    conexion = sqlite3.connect(RUTA_BD)
    conexion.row_factory = sqlite3.Row
    conexion.execute("PRAGMA foreign_keys = ON")
    return conexion


def crear_tablas():
    """Crea las cinco tablas del proyecto si aún no existen."""
    conexion = conectar()
    try:
        conexion.executescript("""
            CREATE TABLE IF NOT EXISTS especialidades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL UNIQUE,
                costo REAL NOT NULL CHECK (costo >= 0)
            );

            CREATE TABLE IF NOT EXISTS medicos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                especialidad_id INTEGER NOT NULL,
                FOREIGN KEY (especialidad_id) REFERENCES especialidades(id)
            );

            CREATE TABLE IF NOT EXISTS pacientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                telefono TEXT
            );

            CREATE TABLE IF NOT EXISTS citas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                paciente_id INTEGER NOT NULL,
                medico_id INTEGER NOT NULL,
                fecha TEXT NOT NULL,
                hora TEXT NOT NULL,
                estado TEXT NOT NULL DEFAULT 'Programada'
                    CHECK (estado IN ('Programada', 'Atendida', 'Cancelada')),
                FOREIGN KEY (paciente_id) REFERENCES pacientes(id),
                FOREIGN KEY (medico_id) REFERENCES medicos(id)
            );

            CREATE TABLE IF NOT EXISTS consultas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cita_id INTEGER NOT NULL UNIQUE,
                diagnostico TEXT NOT NULL,
                tratamiento TEXT NOT NULL,
                total REAL NOT NULL CHECK (total >= 0),
                FOREIGN KEY (cita_id) REFERENCES citas(id)
            );

            -- Impide asignar dos citas al mismo médico a la misma hora.
            -- Si se cancela una cita, ese horario vuelve a estar disponible.
            CREATE UNIQUE INDEX IF NOT EXISTS idx_medico_fecha_hora
                ON citas (medico_id, fecha, hora)
                WHERE estado != 'Cancelada';
        """)
        conexion.commit()
    finally:
        conexion.close()


if __name__ == "__main__":
    crear_tablas()
    print("Base de datos creada correctamente.")
    print("Archivo:", RUTA_BD.name)
    print("Tablas: especialidades, medicos, pacientes, citas y consultas.")