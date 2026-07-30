from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import bcrypt
import psycopg2
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "clave_secreta_por_defecto_123")

# --- CONFIGURACIÓN DE LOGIN MANAGER ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

class Usuario(UserMixin):
    def __init__(self, id, email):
        self.id = id
        self.email = email

@login_manager.user_loader
def load_user(user_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT id, email FROM usuarios WHERE id = %s", (int(user_id),))
    usuario = cursor.fetchone()
    cursor.close()
    conexion.close()
    
    if usuario:
        # Extraemos posición 0 (id) y posición 1 (email)
        return Usuario(usuario[0], usuario[1])
    return None

def obtener_conexion():
    url_base_datos = os.environ.get("DATABASE_URL", "postgresql://usuario:clave@localhost:5432/finanzas")
    return psycopg2.connect(url_base_datos)

def iniciar_base_datos():
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS movimientos (
            id SERIAL PRIMARY KEY,
            usuario_id INTEGER NOT NULL,
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


# --- RUTAS DE AUTENTICACIÓN ---

@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        
        password_encriptada = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        try:
            cursor.execute("INSERT INTO usuarios (email, password) VALUES (%s, %s)", (email, password_encriptada))
            conexion.commit()
            flash("¡Cuenta creada! Ya podés iniciar sesión.", "success")
            return redirect(url_for("login"))
        except psycopg2.errors.UniqueViolation:
            conexion.rollback()
            flash("Ese correo electrónico ya está registrado.", "error")
        finally:
            cursor.close()
            conexion.close()
            
    return render_template("registro.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        cursor.execute("SELECT id, email, password FROM usuarios WHERE email = %s", (email,))
        usuario = cursor.fetchone()
        cursor.close()
        conexion.close()
        
        # usuario[2] es la contraseña encriptada, usuario[0] es el id, usuario[1] es el email
        if usuario and bcrypt.checkpw(password.encode('utf-8'), usuario[2].encode('utf-8')):
            usuario_obj = Usuario(usuario[0], usuario[1])
            login_user(usuario_obj)
            return redirect(url_for("inicio"))
        else:
            flash("Correo electrónico o contraseña incorrectos.", "error")
            
    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


# --- RUTA PRINCIPAL ---

@app.route("/")
@login_required
def inicio():
    categoria_filtrada = request.args.get("categoria_filtro", "Todas")
    
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    
    if categoria_filtrada == "Todas":
        cursor.execute("SELECT id, detalle, monto, tipo, categoria, fecha FROM movimientos WHERE usuario_id = %s ORDER BY id DESC", (current_user.id,))
    else:
        cursor.execute(
            "SELECT id, detalle, monto, tipo, categoria, fecha FROM movimientos WHERE usuario_id = %s AND categoria = %s ORDER BY id DESC",
            (current_user.id, categoria_filtrada)
        )
    lista_movimientos = cursor.fetchall()
    
    cursor.execute("SELECT SUM(monto) FROM movimientos WHERE usuario_id = %s AND tipo = 'Ingreso'", (current_user.id,))
    res_ingresos = cursor.fetchone()
    total_ingresos = float(res_ingresos[0]) if res_ingresos and res_ingresos[0] is not None else 0.0
    
    cursor.execute("SELECT SUM(monto) FROM movimientos WHERE usuario_id = %s AND tipo = 'Egreso'", (current_user.id,))
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
        categoria_seleccionada=categoria_filtrada,
        email_usuario=current_user.email
    )


@app.route("/guardar", methods=["POST"])
@login_required
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
        "INSERT INTO movimientos (usuario_id, detalle, monto, tipo, categoria, fecha) VALUES (%s, %s, %s, %s, %s, %s)",
        (current_user.id, detalle, monto, tipo, categoria, fecha)
    )
    conexion.commit()
    cursor.close()
    conexion.close()
    
    return redirect(url_for("inicio"))


@app.route("/eliminar/<int:movimiento_id>")
@login_required
def eliminar_movimiento(movimiento_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM movimientos WHERE id = %s AND usuario_id = %s", (movimiento_id, current_user.id))
    conexion.commit()
    cursor.close()
    conexion.close()
    
    return redirect(url_for("inicio"))


if __name__ == "__main__":
    puerto = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=puerto, debug=False)
