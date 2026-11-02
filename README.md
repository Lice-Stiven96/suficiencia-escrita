## DEMOSTRACIÓN GRATUITA
El archivo `render.yaml` ahora usa el plan `free` y establece `DEMO_MODE=true`. Se exige confirmar datos ficticios para simular la entrega. **No usar con información de estudiantes reales**: Render Free elimina archivos y SQLite al reiniciarse y no tiene disco persistente. Esta versión no es para producción. Después de crear el Web Service en Render habrá una URL HTTPS que deberá probarse, no puede predecirse de antemano.

# Suficiencia Escrita · Aplicación web V2/V3

Portal móvil para trabajos escritos de suficiencia académica, con carga de archivos PDF/DOCX/TXT, evaluación manual por criterios, informe privado mediante código y CSV para Power BI.

## Estado actual
Código fuente publicado en GitHub. **Aún no hay una dirección HTTPS del aplicativo funcionando**: es necesario crear el servicio de alojamiento en Render y probarlo. Esta es una versión piloto y no está autorizada para almacenar datos reales de menores sin evaluación institucional de seguridad y privacidad.

## Ejecución local
1. Instala Python 3.11 o superior.
2. `pip install -r requirements.txt`
3. Establece las variables `DOCENTE_PASSWORD` y `SECRET_KEY` (valores fuertes, privados).
4. Ejecuta `python app.py`. Abre `http://localhost:8080`.

## Publicación en Render
1. Inicia sesión en https://dashboard.render.com/ .
2. **New → Blueprint** y selecciona el repositorio `Lice-Stiven96/suficiencia-escrita`.
3. Render detectará `render.yaml`. Selecciona el plan Free y revisa que el costo mensual del servicio sea $0. No hay disco persistente.
4. Configura `DOCENTE_PASSWORD` y confirma el despliegue. `SECRET_KEY` se genera de manera automática.
5. Comprueba la ruta `/health`, la carga de la portada y los flujos con registros ficticios antes de publicar la dirección a estudiantes.

## Límites y mejoras imprescindibles
- No hay cuentas individuales ni aislamiento por curso; el código de resultado es un secreto tipo enlace y debe guardarse.
- Cualquier persona con acceso al formulario puede enviar archivos; falta protección contra spam y controles adicionales de archivos.
- Faltan CSRF, auditoría, copia de seguridad, retención y eliminación segura, cifrado/gestión de datos y política de tratamiento.
- La interfaz incluye versiones resumidas de los criterios; **no equivale a un dictamen automatizado de plagio o uso de IA**, ni sustituye la aplicación integral de la rejilla original.
- El repositorio actualmente es público: nunca incluir información, documentos o credenciales de estudiantes.
- El botón compartir usa el diálogo nativo cuando está disponible; para WhatsApp se puede compartir manualmente. No hay número docente configurado.

## Niveles
A = 1.0–2.9, B = 3.0–3.9, C = 4.0–4.5, D = 4.6–5.0. La nota es definitiva **solo cuando la registra el docente**.

## Créditos
La Rejilla V2 de 2017 atribuye su elaboración a Clara Lucía Pradilla Torres, Erica Ramírez Morales, María Yasmín Soto Alvarado y Elsa María Ortiz Casallas. El proyecto incorpora una adaptación tecnológica, sin atribuir titularidad sobre el documento original.
