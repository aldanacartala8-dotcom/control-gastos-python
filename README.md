# Control de Gastos Personales (Versión Cloud)

Esta es una aplicación web dinámica desarrollada en Python orientada a la gestión y control de finanzas personales. Esta versión está completamente optimizada para el despliegue en la nube, utilizando una arquitectura moderna que separa el servidor de la base de datos para garantizar la persistencia de la información.

## 🚀 Características y Funcionalidades
* **Cálculos Financieros en Tiempo Real:** Procesa y calcula de forma automática los Ingresos Totales, Egresos Totales y el Saldo Disponible neto.
* **Interfaz Adaptativa:** Panel visual con tarjetas de colores que cambian dinámicamente según el estado del saldo del usuario (azul para saldos positivos, gris para saldos negativos).
* **Persistencia en la Nube:** Migración de almacenamiento local a una base de datos PostgreSQL remota, evitando la pérdida de información en servidores compartidos.
* **Manejo de Excepciones:** Validación en el backend de los montos ingresados para asegurar la integridad de los datos financieros.

## 🛠️ Tecnologías Utilizadas
* **Lenguaje:** Python 3.x
* **Framework Web:** Flask
* **Base de Datos:** PostgreSQL (en producción)
* **Servidor Web:** Gunicorn (WSGI HTTP Server para entornos Linux)

## 📦 Configuración para Despliegue (Render.com)
1. Conecta este repositorio a un **Web Service** en Render.
2. Crea una base de datos **PostgreSQL** en Render y copia su dirección.
3. En la configuración del Web Service, añade una variable de entorno llamada `DATABASE_URL` y pega la dirección de tu base de datos.
4. Define el comando de inicio como:
   ```bash
   gunicorn app:app
   ```
