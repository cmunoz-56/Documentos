# Clinica medica - integracion para probar

Fuente: https://github.com/cmunoz-56/Documentos/tree/main

Se agrega main.py. Los cuatro modulos del grupo se conservan exactamente como
se descargaron de GitHub. No se ha creado un PR ni se han subido cambios.

## Ejecutar

1. Extraiga TODO el ZIP en una carpeta nueva. No ejecute dentro del ZIP.
2. Abra esa carpeta con VS Code y abra una terminal.
3. Ejecute `python main.py` en Windows, o `python3 main.py` en Linux.
   En Windows tambien puede usar `py main.py`.

Requiere Python 3; no necesita instalar paquetes con pip.
Mantenga main.py, base_datos.py, personas.py, citas.py y consultas.py juntos.
La base clinica.db se crea junto a base_datos.py y se conserva al cerrar.
El ZIP no contiene pacientes ni una base de datos de prueba.

Si solo quiere usar main.py en su copia del repositorio, coloquelo junto a
los cuatro archivos originales actuales. Para probar desde cero es preferible
usar la carpeta nueva del ZIP; no borre una base con datos que necesite.

## Prueba manual sugerida

En la caratula, presione ENTER. En cada menu, 0 vuelve al anterior.

1. Personas y especialidades > Registrar especialidad: General, Q150.
2. En el mismo menu, registre un medico seleccionando la especialidad real.
3. Registre un paciente: nombre con letras y telefono de ocho digitos.
4. Vuelva y entre a Citas y agenda > Registrar cita. Seleccione los IDs
   mostrados. Use una fecha futura real (AAAA-MM-DD) y una hora como 09:00.
5. Intente crear otra cita para el mismo medico a la misma fecha y hora:
   debe rechazarla. Pruebe tambien una fecha inexistente y una hora invalida.
6. Consulte todas las citas, la agenda del medico y las citas del paciente.
7. Reprograme la cita. Cree otra cita a una hora distinta y cancelela;
   primero pruebe responder N y luego S a la confirmacion.
8. Consultas e ingresos > Registrar consulta: seleccione la cita programada,
   escriba diagnostico y tratamiento. Debe cobrar Q150 y marcarla Atendida.
9. Vea las consultas realizadas y el historial con el ID del paciente.
10. Consulte ingresos usando un intervalo que incluya LA FECHA DE LA CITA:
    debe mostrar una consulta y Q150.00.
11. Cierre con 0, abra de nuevo y compruebe que el historial sigue ahi.

Si los IDs no son 1, use siempre los que aparezcan en pantalla.
Ctrl+C interrumpe la operacion actual y regresa al menu. Para salir normalmente,
use 0 hasta llegar al menu principal y luego 0 otra vez.

## Que integra main.py

- Caratula y un unico punto de inicio.
- Las ocho operaciones de personas.py.
- Registro, listado, agenda, filtro por paciente, reprogramacion y cancelacion
  mediante las funciones de citas.py; muestra IDs existentes al elegir.
- Las cinco operaciones de consultas.py, incluido historial e ingresos.
- Menus con 0 para volver, manejo de entradas invalidas, interrupciones,
  errores SQLite y numeros fuera del rango permitido.

No se reemplaza la logica de negocio de los companeros. Sus menus independientes
siguen disponibles al ejecutar cada modulo directamente.