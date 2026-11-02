# Suficiencia Escrita — Rejillas V2 y V3

Plataforma de valoración docente de trabajos escritos académicos con portal del estudiante, informes y exportación CSV para Power BI.

## Estado y alcance
Este repositorio contiene un prototipo educativo. **No es un sistema institucional seguro todavía**. Antes de cargar información real de estudiantes: implementar autenticación individual, consentimiento informado, controles de acceso, registro de auditoría, copias de seguridad y política de protección de datos de Colombia. No subir archivos de estudiantes a GitHub.

## Inicio local
```bash
pip install -r requirements.txt
export ADMIN_PASSWORD="cambia-esta-clave-por-una-muy-segura"
python server.py
```
Abrir http://localhost:8080

## Publicación
El archivo `render.yaml` propone una Web Service de Render. Un despliegue de prueba sin disco persistente perderá resultados tras reinicios. No utilizar con alumnos reales sin almacenamiento persistente y mejoras de seguridad.

## Evaluación
Se consideran las competencias lingüística y textual-discursiva de la Rejilla V2 y ampliaciones V3. Escala personalizada A 1.0–2.9; B 3.0–3.9; C 4.0–4.5; D 4.6–5.0. La calificación publicada siempre requiere valoración docente. No determina automáticamente plagio o uso de inteligencia artificial.

## Reconocimiento
La Rejilla V2 original atribuye su diseño a Clara Lucía Pradilla Torres, Erica Ramírez Morales, María Yasmín Soto Alvarado y Elsa María Ortiz Casallas (2017). Esta implementación es una adaptación tecnológica, sin atribuir titularidad de la obra original.
