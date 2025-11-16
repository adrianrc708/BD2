# AppTiendaOracle - Sistema de Gestión

Proyecto de aplicación de escritorio para la gestión de una tienda, construido con Python, CustomTkinter y una base de datos Oracle.

## ¿Cómo ejecutar el proyecto?

Sigue estos pasos para configurar y ejecutar el proyecto.

1.  **Instalar Dependencias**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Configurar Conexión**
    * Ve a la carpeta `db/`.
    * Crea una **copia** del archivo `db_connector_example.py`.
    * Renombra la copia a `db_connector.py`.
    * Abre `db_connector.py` y rellena `DB_USER`, `DB_PASS`, y `DB_DSN` con tus credenciales de Oracle.

3.  **Ejecutar la Aplicación**
    Una vez completada la configuración, ejecuta el archivo principal:
    ```bash
    python app_main.py
    ```