from flask import Flask, render_template, request, redirect, url_for
import psycopg2
import os

app = Flask(__name__)

def obtener_conexion():
    url_base_datos = os.environ.get("DATABASE_URL", "postgresql://usuario:clave@localhost:5432/finanzas")
    return psycopg2.connect(url_base_datos)

def iniciar_base_datos():
    conexion = obtener_conexion()
    cursor = conexion.cursor()
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


@app.route("/")
def inicio():
    categoria_filtrada = request.args.get("categoria_filtro", "Todas")
    
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    
    # 1. Traemos los movimientos filtrados o completos
    if categoria_filtrada == "Todas":
        cursor.execute("SELECT id, detalle, monto, tipo, categoria, fecha FROM movimientos ORDER BY id DESC")
    else:
        cursor.execute(
            "SELECT id, detalle, monto, tipo, categoria, fecha FROM movimientos WHERE categoria = %s ORDER BY id DESC",
            (categoria_filtrada,)
        )
    lista_movimientos = cursor.fetchall()
    
    # 2. Calculamos ingresos de forma segura
    cursor.execute("SELECT SUM(monto) FROM movimientos WHERE tipo = 'Ingreso'")
    res_ingresos = cursor.fetchone()
    # Si la base de datos devuelve None o una tupla con None, ponemos 0.0
    total_ingresos = float(res_ingresos[0]) if res_ingresos and res_ingresos[0] is not None else 0.0
    
    # 3. Calculamos egresos de forma segura
    cursor.execute("SELECT SUM(monto) FROM movimientos WHERE tipo = 'Egreso'")
    res_egresos = cursor.fetchone()
    total_egresos = float(res_egresos[0]) if res_egresos and res_egresos[0] is not None else 0.0
    
    cursor.close()
    conexion.close()
    
    saldo_neto = total_ingresos - total_egresos
    
    return render_template(
        "index.html", 
        movimientos=lista_movimientos, 
        ingresos=total_ingresos, 
        egresos=total_egresos, 
        saldo=saldo_neto,
        categoria_seleccionada=categoria_filtrada
    )


@app.route("/guardar", methods=["POST"])
def guardar_movimiento():
    detalle = request.form.get("detalle")
    monto_form = request.form.get("monto")
    tipo = request.form.get("tipo")
    categoria = request.form.get("categoria")
    fecha = request.form.get("fecha")
    
    try:
        monto = float(monto_form)
    except (ValueError, TypeError):
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


@app.route("/eliminar/<int:movimiento_id>")
def eliminar_movimiento(movimiento_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM movimientos WHERE id = %s", (movimiento_id,))
    conexion.commit()
    cursor.close()
    conexion.close()
    
    return redirect(url_for("inicio"))


if __name__ == "__main__":
    puerto = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=puerto, debug=False)
