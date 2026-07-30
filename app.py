from flask import Flask, render_template, request, redirect, url_for
import psycopg2 # Cambiamos sqlite3 por psycopg2 (PostgreSQL)
import os

app = Flask(__name__)

# --- PASO 1: CONEXIÓN INTELIGENTE A LA BASE DE DATOS ---
def obtener_conexion():
    # En internet, Render nos dará una URL secreta. Si estamos en la compu, usa una de prueba.
    url_base_datos = os.environ.get("DATABASE_URL", "postgresql://usuario:clave@localhost:5432/finanzas")
    return psycopg2.connect(url_base_datos)

def iniciar_base_datos():
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    # En PostgreSQL se usa SERIAL en vez de AUTOINCREMENT, y TEXT cambia por VARCHAR
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS movimientos (
            id SERIAL PRIMARY KEY,
            detalle VARCHAR(255) NOT NULL,
            monto NUMERIC(10, 2) NOT NULL,
            tipo VARCHAR(50) NOT NULL,
            categoria VARCHAR(100) NOT NULL,
            fecha VARCHAR(50) NOT NULL
        )
    """)
    conexion.commit()
    cursor.close()
    conexion.close()

iniciar_base_datos()


# --- PASO 2: LOGICÁ Y CÁLCULOS ---
@app.route("/")
def inicio():
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    
    # 1. Traemos la lista de todos los movimientos
    cursor.execute("SELECT id, detalle, monto, tipo, categoria, fecha FROM movimientos ORDER BY id DESC")
    lista_movimientos = cursor.fetchall()
    
    # 2. Calculamos el total de INGRESOS
    cursor.execute("SELECT SUM(monto) FROM movimientos WHERE tipo = 'Ingreso'")
    resultado_ingresos = cursor.fetchone()[0]
    total_ingresos = float(resultado_ingresos) if resultado_ingresos else 0.0
    
    # 3. Calculamos el total de EGRESOS
    cursor.execute("SELECT SUM(monto) FROM movimientos WHERE tipo = 'Egreso'")
    resultado_egresos = cursor.fetchone()[0]
    total_egresos = float(resultado_egresos) if resultado_egresos else 0.0
    
    cursor.close()
    conexion.close()
    
    # 4. Calculamos el saldo final
    saldo_neto = total_ingresos - total_egresos
    
    return render_template(
        "index.html", 
        movimientos=lista_movimientos, 
        ingresos=total_ingresos, 
        egresos=total_egresos, 
        saldo=saldo_neto
    )


# --- PASO 3: REGISTRAR UN NUEVO MOVIMIENTO ---
@app.route("/guardar", methods=["POST"])
def guardar_movimiento():
    detalle = request.form.get("detalle")
    tipo = request.form.get("tipo")
    categoria = request.form.get("categoria")
    fecha = request.form.get("fecha")
    
    try:
        monto = float(request.form.get("monto"))
    except ValueError:
        return redirect(url_for("inicio"))

    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(
        "INSERT INTO movimientos (detalle, monto, tipo, categoria, fecha) VALUES (%s, %s, %s, %s, %s)",
        (detalle, monto, tipo, categoria, fecha)
    )
    conexion.commit()
    cursor.close()
    conexion.close()
    
    return redirect(url_for("inicio"))


if __name__ == "__main__":
    # Agregamos configuración para que funcione en los puertos del servidor de internet
    puerto = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=puerto, debug=False)
