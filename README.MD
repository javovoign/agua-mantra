# 💧 Agua Mantra - Sistema de Gestión de Pedidos

Proyecto integrado para el emprendimiento **Agua Mantra** (Santiago 
, Chile). El sistema permite a los clientes realizar pedidos de bidones de agua, pagar mediante Webpay Plus, y a los administradores y choferes gestionar inventario, rutas de despacho y la asignación de pedidos.

## 🛠️ Tecnologías Utilizadas
*   **Backend:** Django (Python [Tu versión de Python, ej: 3.11])
*   **Base de Datos:** SQLite (Entorno de desarrollo)
*   **Pasarela de Pago:** Transbank Webpay Plus (Ambiente de Integración)
*   **Control de Versiones:** Git

## 📋 Requisitos Previos
*   Python instalado en el sistema.
*   Git (opcional, para clonar el repositorio).

## 🚀 Guía de Instalación y Ejecución

Sigue estos pasos para desplegar el proyecto en tu entorno local desde cero:

### 1. Clonar el proyecto (o descomprimir)
```bash
git clone [https://github.com/javovoign/agua-mantra.git]
cd agua_mantra

2. Crear y activar el entorno virtual"
Windows:
python -m venv venv
venv\Scripts\activate

Mac/Linux:
python3 -m venv venv
source venv/bin/activate

3. Instalar dependencias
pip install -r requirements.txt

4. Configurar la Base de Datos
Aplica las migraciones necesarias para crear la estructura:
python manage.py migrate

5. Crear Superusuario (Administrador)
Crea tu cuenta de acceso con privilegios:

bash
python manage.py createsuperuser

6. Configurar Roles y Grupos (Crucial)
El sistema requiere dos grupos específicos para funcionar correctamente.

Levanta el servidor: *** python manage.py runserver ***

Ve a http://localhost:8000/admin/ y entra con tu superusuario.

Dirígete a Authentication and Authorization > Groups > Add Group.

Crea exactamente los siguientes grupos:

Administrador
Chofer

7. Iniciar el servidor
python manage.py runserver

💳 Nota sobre Webpay
Las credenciales en el archivo services/webpay.py corresponden al Ambiente de Integración de Transbank. No se realizarán cargos reales. Puedes probar el flujo de pago exitoso utilizando las tarjetas de prueba que proporciona Transbank en su documentación oficial.

👥 Equipo de Desarrollo
[Javier] - Desarrollador

Martín - Scrum Master

Tristán - Documentación y Pruebas
