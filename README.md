# CRM local

CRM pequeño para administrar clientes y preparar mensajes individuales de WhatsApp en una red local. Está construido con Django 5.2, PostgreSQL, Django Templates, Tailwind CSS y HTMX (sin una SPA ni servicios separados).

> Este repositorio no copia código de Horilla CRM. La interfaz y la lógica se implementan para este proyecto.

## Requisitos

- Docker Engine y Docker Compose v2.
- Un navegador moderno en la computadora del negocio o en otro equipo de la red local.

No hace falta instalar Python, Node.js ni PostgreSQL en la computadora anfitriona para usar Docker Compose.

## Puesta en marcha

La interfaz usa una paleta verde petróleo y azul, navegación lateral y componentes responsive. El logo de MC Soluciones se muestra en la navegación y en el acceso, con una variante clara para el fondo oscuro de la navegación. Los SVG están en `static/images/`. Tailwind se compila durante la construcción de Docker; para ver cambios de interfaz, reconstruí la imagen con `docker compose up --build`.

Desde esta carpeta:

```sh
cp .env.example .env
```

Editá `.env`: definí una `SECRET_KEY` aleatoria, una contraseña local para PostgreSQL y el valor `INITIAL_USERS_PASSWORD` que usarán las tres cuentas iniciales. La contraseña compartida se configura sólo en el `.env` local (excluido de Git); no la guardes en el repositorio. Reemplazá el valor de ejemplo antes de arrancar. Para generar una clave Django:

```sh
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

Agregá a `ALLOWED_HOSTS` el nombre o la IP local del equipo que ejecuta Docker, separados por comas. Después iniciá la aplicación:

```sh
docker compose up --build
```

Al iniciar, el contenedor prepara las migraciones, configura los grupos de permisos, crea las cuentas iniciales que falten, recopila los archivos estáticos y levanta Django en `http://localhost:8000`. Los datos de PostgreSQL se conservan en el volumen `postgres_data`.

Para acceder desde otra computadora de la misma red, usá `http://IP-LOCAL-DEL-SERVIDOR:8000` y agregá esa IP a `ALLOWED_HOSTS` en `.env`. Limitá el acceso al CRM al segmento de red de confianza y configurá contraseñas propias.

### Si aparece `password authentication failed`

El volumen `postgres_data` conserva la contraseña con la que se inicializó PostgreSQL. Cambiar `POSTGRES_PASSWORD` en `.env` no cambia por sí solo la contraseña de una base ya creada. Si no conocés la contraseña anterior, podés restablecerla desde el socket local del contenedor, sin autenticarte como el rol de la aplicación:

```sh
docker compose exec -u postgres db sh -c 'psql -U "$POSTGRES_USER" -d postgres'
```

`-u postgres` selecciona el usuario del sistema dentro del contenedor; `-U "$POSTGRES_USER"` selecciona el rol de PostgreSQL creado al inicializar el volumen. En el prompt de `psql`, configurá una contraseña nueva para ese rol:

```text
\password
```

Ingresá dos veces exactamente la contraseña definida en `POSTGRES_PASSWORD` dentro de `.env` y salí con `\q`. Si el comando informa que el rol no existe, es posible que `POSTGRES_USER` haya cambiado desde que se creó el volumen: revisá el nombre del rol que se usó originalmente y pasalo explícitamente con `-U NOMBRE_DEL_ROL`. Después recreá el contenedor web para que lea el `.env` actualizado:

```sh
docker compose up -d --force-recreate web
```

No uses `docker compose down -v` para corregir este error en una instalación con datos: elimina el volumen de PostgreSQL y con él los clientes, usuarios y mensajes. Si el comando local de `psql` no conecta, revisá `docker compose logs db` antes de cambiar o eliminar el volumen.

## Cuentas iniciales y roles

En el primer arranque se crean automáticamente estas tres cuentas, usando el valor de `INITIAL_USERS_PASSWORD` configurado en `.env`:

| Usuario | Rol |
| --- | --- |
| `superuser` | Superusuario Django, acceso completo |
| `admin` | Administrador de la aplicación y acceso a Django Admin |
| `test` | Operador, acceso de trabajo limitado |

La creación es idempotente: al reiniciar no se restablecen las contraseñas ni se sobrescriben cuentas que ya existan. Cambiá las contraseñas después del primer inicio desde Django Admin o con `python manage.py changepassword USUARIO`. Para agregar usuarios posteriores, desde Django Admin creá el usuario y asignale el grupo **Operadores**. El operador puede consultar, crear, editar y desactivar clientes, ver plantillas y el historial de mensajes, así como preparar y marcar mensajes. No puede eliminar clientes ni modificar plantillas o etiquetas.

Los administradores pueden eliminar clientes desde su ficha, después de marcar una casilla de confirmación. La eliminación de los datos del cliente es permanente. Los mensajes históricos se conservan con el nombre y el teléfono que tenían al prepararse, y siguen apareciendo en **Mensajes enviados**.

En **Plantillas WhatsApp** se pueden crear, editar, desactivar y eliminar los textos rápidos. Las plantillas activas aparecen al preparar un mensaje. Las variables `{nombre}` y `{empresa}` se reemplazan con los datos del cliente. Los cambios en una plantilla no alteran mensajes que ya fueron preparados.

Los grupos **Administradores** y **Operadores** se crean con los permisos de la aplicación al iniciar los servicios, o manualmente con:

```sh
docker compose exec web python manage.py setup_roles
```

La configuración de grupos no convierte automáticamente un usuario en staff ni en superusuario.

## Datos de ejemplo

```sh
docker compose exec web python manage.py seed_demo
```

El comando es idempotente para los clientes de ejemplo y no crea usuarios.

## Migraciones y tests

Las migraciones se ejecutan automáticamente al arrancar el servicio. Para aplicarlas a mano:

```sh
docker compose exec web python manage.py migrate
```

Para ejecutar los tests:

```sh
docker compose exec web python manage.py test
```

El test runner de Django crea una base PostgreSQL temporal y verifica modelos, normalización del teléfono, creación de mensajes y permisos.

## Backup de PostgreSQL

Crear una copia comprimida en la carpeta actual:

```sh
docker compose exec -T db pg_dump -U crm_local -d crm_local -Fc > crm_local.backup
```

Si cambiaste `POSTGRES_USER` o `POSTGRES_DB` en `.env`, reemplazá esos valores en el comando. Para restaurar en una base ya creada:

```sh
cat crm_local.backup | docker compose exec -T db pg_restore -U crm_local -d crm_local --clean --if-exists
```

Guardá las copias fuera de la computadora del negocio y probá la restauración periódicamente. El volumen de Docker no sustituye a un backup.

## WhatsApp en esta versión

El CRM guarda el texto preparado, el usuario y la plantilla utilizada, abre `wa.me` con el teléfono internacional y el mensaje codificado, y registra el estado **Abierto en WhatsApp**. La persona que opera debe revisar la conversación y tocar **Enviar** en WhatsApp. Luego puede volver al CRM y elegir **Marcar como enviado**. El apartado **Mensajes enviados** muestra los mensajes marcados de esa manera, ordenados por su fecha de confirmación.

El CRM no integra la API de Meta, no envía mensajes por sí mismo y no puede verificar que WhatsApp haya entregado un mensaje. El diseño mantiene separada la preparación/historial para poder agregar un proveedor de envío en una etapa posterior.

## Configuración de producción

`DEBUG`, `SECRET_KEY` y `ALLOWED_HOSTS` se leen de variables de entorno. Para producción, desactivá `DEBUG`, configurá una clave secreta fuerte y definí explícitamente los hosts permitidos. No publiques `.env` ni reutilices las credenciales de ejemplo.
