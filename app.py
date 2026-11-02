import os, sqlite3, uuid, csv, io, secrets, datetime
from pathlib import Path
from functools import wraps
from flask import Flask, request, redirect, session, render_template_string, abort, send_file, url_for, Response
from werkzeug.utils import secure_filename

app=Flask(__name__)
app.secret_key=os.getenv("SECRET_KEY",secrets.token_hex(32))
app.config["MAX_CONTENT_LENGTH"]=8*1024*1024
ROOT=Path(os.getenv("DATA_DIR","/var/data" if Path("/var/data").exists() else "var"))
ROOT.mkdir(parents=True,exist_ok=True)
(ROOT/"uploads").mkdir(exist_ok=True)
DB=ROOT/"evaluaciones.sqlite3"
R2=[("1.1","Ortografía"),("1.2","Puntuación"),("1.3","Concordancia"),("1.4","Estructura oracional"),("1.5","Secuenciación de párrafos"),("2.1","Título"),("2.2","Tipo de texto"),("2.3","Superestructura"),("2.4","Léxico disciplinar"),("2.5","Progresión temática"),("2.6","Tesis"),("2.7","Plan argumentativo"),("2.8","Recursos de argumentación"),("2.9","Posicionamiento crítico"),("2.10","Interlocutor"),("2.11","Pertinencia temática"),("2.12","Correspondencia del título"),("2.13","Citas y referencias")]
R3=R2+[("3.1","Precisión conceptual"),("3.2","Rigor científico"),("3.3","Integridad de fuentes"),("3.4","Voz académica"),("3.5","Revisión editorial")]

PLAN_RUBRICA={
"1.1":("Competencia lingüística","Revisar tildes, grafías y normas ortográficas; corregir cada error y releer el texto."),
"1.2":("Competencia lingüística","Comprobar puntos, comas y otros signos de puntuación según el sentido de cada oración."),
"1.3":("Competencia lingüística","Revisar concordancia de género, número, persona y tiempos verbales."),
"1.4":("Competencia lingüística","Reformular oraciones ambiguas o excesivamente extensas y ordenar sus elementos."),
"1.5":("Competencia lingüística","Desarrollar párrafos con una idea central, explicación y transición pertinente."),
"2.1":("Competencia texto-discursiva","Proponer un título atractivo, preciso y coherente con la temática y el contenido."),
"2.2":("Competencia texto-discursiva","Mantener el carácter expositivo-argumentativo; no limitarse a narrar o resumir."),
"2.3":("Competencia texto-discursiva","Organizar la superestructura solicitada: introducción, desarrollo argumentativo y cierre."),
"2.4":("Competencia texto-discursiva","Utilizar terminología disciplinar precisa sin sobrecargar el texto."),
"2.5":("Competencia texto-discursiva","Construir progresión temática: cada párrafo debe aportar información nueva a la idea global."),
"2.6":("Competencia texto-discursiva","Formular una tesis clara, discutible y relacionada con la pregunta central."),
"2.7":("Competencia texto-discursiva","Organizar argumentos en una secuencia lógica que respalde la tesis."),
"2.8":("Competencia texto-discursiva","Combinar datos, ejemplos, explicaciones y contraargumentos pertinentes."),
"2.9":("Competencia texto-discursiva","Explicitar una postura crítica fundamentada y reconocer otras perspectivas."),
"2.10":("Competencia texto-discursiva","Adecuar el lenguaje al lector académico y al propósito comunicativo."),
"2.11":("Competencia texto-discursiva","Responder a la consigna sin desviarse hacia contenidos secundarios."),
"2.12":("Competencia texto-discursiva","Verificar que el título anunciado corresponda realmente a la tesis y al desarrollo."),
"2.13":("Competencia texto-discursiva","Sustentar las afirmaciones con fuentes comprobables, citas en texto y referencias completas."),
"3.1":("Ampliación V3","Precisar definiciones y distinguir afirmaciones documentadas de opiniones."),
"3.2":("Ampliación V3","Contrastar información fiable y explicar la relación entre las evidencias y las conclusiones."),
"3.3":("Ampliación V3","Atribuir ideas y citas con honestidad; verificar autenticidad de referencias y reconocer el apoyo de herramientas cuando sea exigido."),
"3.4":("Ampliación V3","Construir una voz académica propia mediante síntesis, interpretación y postura fundamentada."),
"3.5":("Ampliación V3","Aplicar una revisión final de estructura, estilo, gramática, referencias y presentación.")
}

def db():
 c=sqlite3.connect(DB);c.row_factory=sqlite3.Row;return c
with db() as c:
 c.execute("CREATE TABLE IF NOT EXISTS trabajos(id TEXT PRIMARY KEY,codigo TEXT UNIQUE,nombre TEXT,curso TEXT,titulo TEXT,version TEXT,archivo TEXT,fecha TEXT,nota REAL,fortalezas TEXT,mejoras TEXT,recomendaciones TEXT,integridad TEXT)")
 c.execute("CREATE TABLE IF NOT EXISTS criterios(trabajo TEXT,codigo TEXT,descripcion TEXT,nivel TEXT,PRIMARY KEY(trabajo,codigo))")
def nivel(x):
 return "Pendiente" if x is None else ("A" if x<3 else "B" if x<4 else "C" if x<=4.5 else "D")
def docente(f):
 @wraps(f)
 def g(*a,**k):
  if not session.get("docente"):return redirect("/acceso")
  return f(*a,**k)
 return g
PAGE='''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#0b4f87"><meta name="description" content="Suficiencia Escrita: evaluación formativa de textos académicos."><title>{{title}} · Suficiencia Escrita</title><style>
:root{--blue:#0b4f87;--navy:#0b2d4b;--green:#078669;--mint:#e2f7ef;--sky:#eef6fd;--text:#17344b;--muted:#62788b;--border:#dbe7ef;--shadow:0 16px 46px rgba(19,62,95,.10)}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;color:var(--text);background:radial-gradient(circle at 95% 5%,#d9f5eb 0,transparent 34%),linear-gradient(180deg,#f5faff,#edf5f8);font:16px/1.6 Inter,system-ui,"Segoe UI",Arial,sans-serif}
header{position:sticky;top:0;z-index:50;background:rgba(255,255,255,.94);backdrop-filter:blur(16px);border-bottom:1px solid #dce9f0;padding:0 4%}
nav{max-width:1180px;margin:auto;min-height:78px;display:flex;align-items:center;gap:12px;flex-wrap:nowrap}nav b{margin-right:auto;color:var(--navy);font-size:21px;font-weight:850;letter-spacing:-.7px;white-space:nowrap}nav a{text-decoration:none;color:#34556b;padding:11px 13px;border-radius:12px;font-size:14px;font-weight:700;white-space:nowrap;transition:.2s}nav a:hover,nav a:focus-visible{background:#e6f3fb;color:#095b93}nav a:last-child{color:white;background:linear-gradient(120deg,#095e96,#07876c);box-shadow:0 7px 17px #0d6c8629}nav .nav-toggle{display:none;margin:0;background:#e8f5f5;color:#174860;padding:9px 12px}
main{max-width:1180px;margin:32px auto;padding:0 20px;min-height:64vh}.hero{background:linear-gradient(115deg,#0a3155 0%,#095b91 52%,#098a6d 100%);color:white;padding:clamp(32px,5vw,68px);border-radius:30px;position:relative;overflow:hidden;box-shadow:0 24px 64px #164d7138}.hero:before{content:"";position:absolute;width:340px;height:340px;border:1px solid #ffffff30;border-radius:50%;right:-70px;top:-110px;box-shadow:0 0 0 50px #ffffff08,0 0 0 104px #ffffff06}.hero>*{position:relative}.hero h1{font-size:clamp(35px,5.1vw,64px);line-height:1.12;letter-spacing:-1.8px;max-width:810px}.hero p{max-width:800px;color:#e8faff;font-size:clamp(15px,1.7vw,20px)}.hero .btn{background:white;color:#0a5484}.hero .btn.blue{background:#ffffff20;color:white;border:1px solid #ffffff55}
.box,.card{border:1px solid var(--border);background:#fff;border-radius:22px;padding:clamp(18px,3vw,30px);margin:18px 0;box-shadow:var(--shadow)}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(225px,1fr));gap:18px}.grid .box{margin:4px 0}.box h1,.box h2,.box h3{color:var(--navy)}h1{font-size:clamp(27px,3.5vw,44px);letter-spacing:-.8px;line-height:1.19}h2{font-size:clamp(20px,2.5vw,28px);line-height:1.3}label{display:block;font-weight:750;margin:16px 0 7px;color:#254960}input,select,textarea{width:100%;padding:14px 15px;border:1px solid #bed3df;border-radius:12px;background:#fbfdff;color:#1a364a;font:inherit;outline-offset:3px}input:focus,select:focus,textarea:focus{border-color:#078e77;box-shadow:0 0 0 3px #08a78818}textarea{min-height:115px}button,.btn{display:inline-block;border:0;background:linear-gradient(125deg,#08629a,#07886a);color:#fff;text-decoration:none;padding:13px 19px;border-radius:13px;font-size:15px;font-weight:780;margin:9px 5px 9px 0;cursor:pointer;box-shadow:0 8px 20px #12738e29;transition:transform .2s,box-shadow .2s}button:hover,.btn:hover{transform:translateY(-2px);box-shadow:0 12px 24px #12738e42}.blue{background:#0b5788}.small{color:var(--muted);font-size:14px}.tag{display:inline-block;background:var(--mint);color:#0a6652;border-radius:999px;padding:6px 13px;font-weight:750;overflow-wrap:anywhere}.table{overflow:auto;border:1px solid #e1eaf0;border-radius:16px}table{width:100%;border-collapse:collapse}th,td{padding:14px;text-align:left;border-bottom:1px solid #e5edf2;font-size:14px}th{background:#eaf5fa;color:#20455e;font-size:12px;text-transform:uppercase;letter-spacing:.04em}tr:nth-child(even){background:#f9fcfe}tr:hover{background:#f0f9fa}.notice{background:#fff7df;border-left:4px solid #e3a93b;padding:16px;border-radius:11px;color:#6e541b}.mark-verde{background:#d5f4df;color:#0b5730;padding:5px 9px;border-radius:7px}.mark-amarillo{background:#fff0b6;color:#654b00;padding:5px 9px;border-radius:7px}.mark-rojo{background:#ffdce0;color:#7b1728;padding:5px 9px;border-radius:7px}.mark-azul{background:#dcecff;color:#163d7a;padding:5px 9px;border-radius:7px}.snippet{border-left:4px solid #70b2cb;padding:16px;margin:16px 0;background:#f6fafc;border-radius:12px}.snippet blockquote{margin:12px 0;line-height:1.7;overflow-wrap:anywhere}footer{background:#0c304d;color:#d2e8f3;text-align:center;padding:33px 16px;margin-top:70px;font-size:13px}footer strong{color:#fff}.section-label{font-size:12px;text-transform:uppercase;letter-spacing:2px;font-weight:800;color:#117b78}.feature-symbol{width:48px;height:48px;border-radius:15px;background:linear-gradient(130deg,#e7f3ff,#d6f7e9);display:grid;place-items:center;font-size:24px;margin-bottom:15px}.metrics{margin-top:26px}.metrics .box{border-top:4px solid #0d8a79}.step{display:inline-grid;place-items:center;width:33px;height:33px;background:#e4f4f3;color:#0b7769;border-radius:50%;font-weight:900;margin-right:7px}
@media(max-width:760px){header{padding:0 14px}nav{flex-wrap:wrap;min-height:70px;gap:0}nav b{font-size:18px;padding:12px 0}nav .nav-toggle{display:inline-block}nav a{display:none;width:100%;padding:14px;border-top:1px solid #eff3f8}nav.open a{display:block}nav a:last-child{margin-bottom:10px}.hero{border-radius:22px;padding:31px 23px}main{margin:20px auto;padding:0 12px}.box{padding:19px}.grid{gap:11px}.grid .box{margin:2px 0}}
@media print{header,.print-hide,footer,button{display:none!important}body{background:white}.box{box-shadow:none;border:1px solid #ddd}main{margin:0;max-width:100%}}
</style></head><body><header><nav id="topnav"><b>✦ Suficiencia Escrita</b><button class="nav-toggle" aria-label="Abrir o cerrar menú" aria-expanded="false" onclick="var n=document.getElementById('topnav');var o=n.classList.toggle('open');this.setAttribute('aria-expanded',String(o))">☰ Menú</button><a href="/">Inicio</a><a href="/entregar">Subir trabajo</a><a href="/consulta">Mis resultados</a><a href="/docente">Panel docente</a></nav></header><main>{{content|safe}}</main><footer><strong>Suficiencia Escrita</strong> · Evaluación y retroalimentación académica<br>Diseño pedagógico y dirección conceptual: <strong>Licenciado en Lengua Castellana y Literatura y Mg. en Administración Educativa, Stiven Eduardo Bermúdez</strong><br>Adaptación tecnológica V2/V3 · Reconocimiento a las autoras de la Rejilla V2 original (2017).<br><span style="opacity:.75">Herramienta formativa: el diagnóstico automático no acredita plagio ni autoría por IA.</span></footer></body></html>'''
def view(title,content,**kwargs):return render_template_string(PAGE,title=title,content=render_template_string(content,**kwargs))
@app.get("/")
def home():
 return view("Inicio",'''<section class="hero"><p style="font-size:12px;letter-spacing:2px;font-weight:800">PLATAFORMA ACADÉMICA · REJILLAS V2 Y V3</p><h1>Escribe con criterio.<br>Crece con cada versión.</h1><p>Una experiencia educativa para fortalecer textos argumentativos y científicos mediante diagnóstico inmediato, retroalimentación formativa y seguimiento docente.</p><a class="btn" href="/entregar">✦ Evaluar mi trabajo</a> <a class="btn blue" href="/consulta">Consultar mi resultado</a></section><section style="padding:42px 0 12px"><p class="section-label">Una experiencia centrada en el aprendizaje</p><h2>Del texto a una ruta de mejoramiento</h2><div class="grid"><div class="box"><div class="feature-symbol">✍</div><h3>Entrega inteligente</h3><p>Adjunta tu documento en Word, PDF o TXT desde el móvil o computador.</p></div><div class="box"><div class="feature-symbol">◈</div><h3>Diagnóstico inmediato</h3><p>Recibe indicadores formales, una nota orientativa y observaciones para revisar tu texto.</p></div><div class="box"><div class="feature-symbol">◎</div><h3>Retroalimentación integral</h3><p>Identifica fortalezas, título, material base, argumentos y aspectos por mejorar.</p></div><div class="box"><div class="feature-symbol">▥</div><h3>Visión docente</h3><p>Califica criterios V2/V3 y exporta datos para construir indicadores en Power BI.</p></div></div></section><section class="box"><p class="section-label">Proceso de evaluación</p><h2>En tres pasos sencillos</h2><div class="grid"><div><p><span class="step">1</span> <b>Sube el documento</b></p><p class="small">Elige la versión de rejilla y adjunta tu trabajo.</p></div><div><p><span class="step">2</span> <b>Revisa tu informe</b></p><p class="small">Explora los criterios, marcaciones y recomendaciones.</p></div><div><p><span class="step">3</span> <b>Mejora tu escritura</b></p><p class="small">Aplica los ajustes antes de la evaluación docente definitiva.</p></div></div></section><section class="box"><p class="section-label">Escala de valoración</p><h2>Cuatro niveles de desempeño</h2><div class="grid"><div><span class="mark-rojo">A · 1.0 a 2.9</span><p class="small">Insuficiente</p></div><div><span class="mark-amarillo">B · 3.0 a 3.9</span><p class="small">Básico</p></div><div><span class="mark-azul">C · 4.0 a 4.5</span><p class="small">Alto</p></div><div><span class="mark-verde">D · 4.6 a 5.0</span><p class="small">Superior</p></div></div><p class="small">Escala personalizada de evaluación. La nota automática es provisional; la calificación final requiere validación docente.</p></section><section class="box"><h2>Una plataforma que reconoce el aprendizaje</h2><p>Esta versión usa la lectura base de UNICEF para la actividad de salud mental adolescente y redes sociales. Evalúa señales de título pertinente y citación, sin sustituir la interpretación pedagógica del docente.</p><p class="notice"><b>Modo demostración gratuito:</b> utiliza exclusivamente documentos ficticios. El almacenamiento gratuito puede perderse con reinicios del servidor.</p><a class="btn" href="/entregar">Comenzar evaluación</a></section>''')

def diagnostico_automatico(archivo, titulo=""):
 """Análisis inmediato de indicadores textuales; no equivale a una calificación docente."""
 import re
 from collections import Counter
 extension=archivo.suffix.lower()
 try:
  if extension==".txt":
   texto=archivo.read_text(encoding="utf-8-sig",errors="replace")
  elif extension==".docx":
   from docx import Document
   texto="\n".join(p.text for p in Document(str(archivo)).paragraphs)
  elif extension==".pdf":
   from pypdf import PdfReader
   lector=PdfReader(str(archivo))
   if len(lector.pages)>60:return {"error":"Para un análisis preliminar, el documento no debe superar 60 páginas."}
   texto="\n".join(p.extract_text() or "" for p in lector.pages)
  else:return {"error":"Formato no admitido"}
 except Exception:
  return {"error":"No fue posible extraer el texto. Revisa que el archivo no esté protegido ni sea un PDF escaneado."}
 palabras=re.findall(r"\b[^\W\d_]+(?:[-'][^\W\d_]+)*\b",texto.lower(),flags=re.UNICODE)
 n=len(palabras)
 if n<80:return {"error":"No se identificó suficiente texto editable para generar un diagnóstico. Se necesitan al menos 80 palabras; en PDF escaneado no hay extracción automática."}
 parrafos=[p.strip() for p in re.split(r"\n\s*\n|\r\n\s*\r\n",texto) if len(p.strip())>=35]
 oraciones=[o.strip() for o in re.split(r"[.!?]+(?:\s|$)",texto) if len(o.strip())>=15]
 referencias=bool(re.search(r"\b(referencias|bibliograf[ií]a|fuentes consultadas)\b",texto,re.I))
 # El documento base para la actividad es el artículo de UNICEF sobre salud mental adolescente y redes sociales.
 # La detección nominal no demuestra lectura, comprensión o una cita APA correcta.
 indicio_unicef=bool(re.search(r"\bUNICEF\b",texto,re.I))
 fuente_tema=bool(re.search(r"salud mental",texto,re.I) and re.search(r"redes sociales",texto,re.I))
 titulo=titulo.strip()
 titulo_tema=bool(re.search(r"redes|sociales|pantallas|adolescent|bienestar|salud mental|conexi[oó]n|digital",titulo,re.I))
 titulo_sugerente=bool(re.search(r"[:¿?!—-]",titulo) or len(titulo.split())>=6)
 fuente_ref=bool(re.search(r"(?is)(referencias|bibliograf[ií]a)\b[\s\S]{0,3500}UNICEF",texto))
 conectores=sum(1 for frase in ["sin embargo","por lo tanto","además","en consecuencia","por otra parte","no obstante","en conclusión","por ejemplo"] if frase in texto.lower())
 citas=bool(re.search(r"\([A-ZÁÉÍÓÚÑ][^()]{1,60},?\s*(?:19|20)\d{2}\)|\[(?:1|2|3|4|5)\]",texto))
 promedio=round(n/max(len(oraciones),1),1)
 repetidos=sum(x-1 for x in Counter(tuple(palabras[i:i+5]) for i in range(max(0,n-4))).values() if x>1)
 puntos=[]
 if n>=500:puntos.append(("Extensión","El documento aporta material suficiente para revisar su desarrollo."))
 else:puntos.append(("Extensión","Ampliar el desarrollo del tema con argumentos y ejemplos."))
 if len(parrafos)>=4:puntos.append(("Organización","Se identifican varios bloques de texto; revisar la unidad temática de cada párrafo."))
 else:puntos.append(("Organización","Separar las ideas en párrafos con función clara."))
 if conectores>=2:puntos.append(("Cohesión","Se identifican conectores discursivos; comprobar que expresen relaciones lógicas."))
 else:puntos.append(("Cohesión","Fortalecer las relaciones entre argumentos mediante conectores pertinentes."))
 if citas and referencias:puntos.append(("Fuentes","Se observan señales de citas y referencias; verificar correspondencia y autenticidad."))
 else:puntos.append(("Fuentes","Revisar la presencia de citas y lista de referencias conforme a APA 7."))
 if promedio>35:puntos.append(("Sintaxis","La longitud media de algunas oraciones aconseja revisar claridad y puntuación."))
 else:puntos.append(("Sintaxis","Revisar concordancia y precisión; la longitud de las oraciones por sí sola no prueba calidad."))
 if repetidos>10:puntos.append(("Repetición","Se detectaron secuencias repetidas que conviene revisar en contexto."))
 # Índice orientativo calculado con variables observables; NO es nota A–D ni juicio académico.
 indice=round(100*(min(n/500,1)*0.25+min(len(parrafos)/4,1)*0.2+min(conectores/2,1)*0.2+(.20 if citas else 0)+(.15 if referencias else 0)))
 # Estimación explicable limitada a cinco indicadores observables.
 # NO permite concluir la calidad de los argumentos ni sustituye la evaluación de un docente.
 checks=[
  ("Competencia lingüística","1.1–1.5","Claridad y segmentación",promedio<=35,
   "Oraciones de extensión manejable, sujeto a revisión sintáctica." if promedio<=35 else "Dividir oraciones extensas y comprobar la puntuación."),
  ("Competencia texto-discursiva","2.1–2.5","Estructura y progresión",len(parrafos)>=4,
   "Se distinguen bloques de texto; verificar su unidad temática." if len(parrafos)>=4 else "Organizar introducción, desarrollo y conclusión en párrafos diferenciados."),
  ("Argumentación crítica","2.6–2.10","Desarrollo argumentativo",conectores>=2 and n>=400,
   "Se observan conectores y desarrollo textual; la tesis debe revisarse manualmente." if conectores>=2 and n>=400 else "Formular una tesis explícita y sostenerla con razones y contraargumentos."),
  ("Referenciación","2.13","Fuentes documentales",citas and referencias,
   "Se observan patrones de citas y apartado de referencias; verificar fuentes." if citas and referencias else "Incorporar citas verificables y referencias bibliográficas completas."),
  ("Escritura académica","3.1–3.5","Revisión y rigor",n>=500 and promedio<=35,
   "La extensión y segmentación permiten revisar el desarrollo; el rigor científico aún requiere evaluación." if n>=500 and promedio<=35 else "Ampliar el desarrollo conceptual y revisar precisión y legibilidad.")
 ]
 if not referencias and citas: checks[3]=(checks[3][0],checks[3][1],checks[3][2],False,"Se observan citas, pero falta identificar una lista de referencias.")
 checks.append(("Superestructura textual","2.1 y 2.12","Título pertinente y atractivo",titulo_tema and titulo_sugerente,
   "El título plantea una relación temática y un recurso de interés. Comprobar que sea preciso y corresponda a la tesis." if titulo_tema and titulo_sugerente else "Reescribe el título con precisión temática y un enfoque que despierte interés sin caer en exageraciones; por ejemplo, usa una pregunta o un contraste con sentido académico."))
 checks.append(("Fuente de lectura obligatoria","2.13 y 3.3","Uso y referencia del material base UNICEF",indicio_unicef and fuente_ref and citas and fuente_tema,
   "Se identifican señales de uso de UNICEF, tema pertinente, cita y referencia: verifica autoría, fecha, URL y correspondencia." if indicio_unicef and fuente_ref and citas and fuente_tema else "Integra con tus propias palabras una idea pertinente del artículo base de UNICEF, cítalo en el texto y agrega su referencia completa al final. Comprueba los datos bibliográficos reales del artículo."))
 cumplidos=sum(1 for c in checks if c[3])
 # Nota preliminar heurística: 2.0 a 4.0. Nunca presentar como calificación o
 # calidad científica demostrada; el valor es solo una ayuda a la autoevaluación.
 nota_preliminar=round(2.0+2.0*cumplidos/len(checks),1)
 codigo_nivel=nivel(nota_preliminar)
 fortalezas=[c[2]+": "+c[4] for c in checks if c[3]]
 mejoras=[c[2]+": "+c[4] for c in checks if not c[3]]
 if not fortalezas: fortalezas=["El documento aporta texto para iniciar un proceso de revisión académica."]
 niveles={"A":"B","B":"C","C":"D","D":"D"}
 accion={
 "A":"Prioriza organizar párrafos, construir una tesis y aportar fuentes fiables.",
 "B":"Para avanzar a C, desarrolla cada argumento con pruebas, conecta las ideas y completa APA 7.",
 "C":"Para aspirar a D, contrasta autores, considera contraargumentos y profundiza en la conclusión.",
 "D":"Mantén la solidez del texto y revisa coherencia, originalidad de las ideas y exactitud de todas las fuentes."
 }
 # Ruta integral de mejora: TODOS los criterios, con objetivos C y D.
 # La versión real se recibe desde la entrega; se usa la referencia amplia y se filtra allí.
 plan_integral=[{"codigo":code,"criterio":label,"dimension":PLAN_RUBRICA[code][0],
   "recomendacion":PLAN_RUBRICA[code][1],
   "objetivo_c":"Aplicar el criterio con suficiencia y evidencia verificable (nivel C).",
   "objetivo_d":"Aplicar el criterio con precisión, autonomía, profundidad y consistencia (nivel D).",
   "verificacion":"Requiere revisión docente del contenido completo."}
   for code,label in R3]
 plan_integral.append({"codigo":"F.1","criterio":"Uso de la lectura base UNICEF",
   "dimension":"Consigna de la actividad","recomendacion":"Integrar y explicar críticamente el material suministrado; verificar la referencia original y su correspondencia con la cita.",
   "objetivo_c":"Relacionar ideas de la lectura con la tesis y citar correctamente.",
   "objetivo_d":"Contrastar e interpretar la lectura de forma crítica, con atribución rigurosa.",
   "verificacion":"Requiere comparación con la lectura base."})
 plan_integral.append({"codigo":"F.2","criterio":"Título de alto impacto y pertinencia",
   "dimension":"Consigna de la actividad","recomendacion":"Redactar un título llamativo, específico y fiel al contenido, evitando sensacionalismo.",
   "objetivo_c":"Título preciso, claro y coherente con la tesis.",
   "objetivo_d":"Título memorable y original, con fuerza expresiva sin perder rigor.",
   "verificacion":"Requiere lectura de la tesis y del desarrollo."})
 # Señalizaciones transparentes, no son coincidencias externas ni detección de plagio.
 marcados=[]
 for idx,fragmento in enumerate(oraciones[:90]):
  if len(marcados)>=12: break
  if len(fragmento.split())>=38:
   marcados.append({"color":"rojo","tipo":"Oración extensa","texto":fragmento[:420],"motivo":"Dividir o reformular para mejorar legibilidad; confirmar en contexto."})
  elif re.search(r"\b(sin embargo|por lo tanto|además|no obstante|en consecuencia)\b",fragmento,re.I) and len(marcados)<12:
   marcados.append({"color":"verde","tipo":"Conector identificado","texto":fragmento[:420],"motivo":"Revisar que la relación lógica propuesta sea correcta."})
 if not marcados and oraciones:
  marcados.append({"color":"azul","tipo":"Revisión contextual","texto":oraciones[0][:420],"motivo":"Identificar tesis, idea principal y conexión con el propósito del texto."})
 detalle=[{"competencia":c[0],"codigo":c[1],"indicador":c[2],"estado":"Evidencia formal" if c[3] else "Revisar","accion":c[4],"color":"verde" if c[3] else "amarillo"} for c in checks]
 return {"palabras":n,"parrafos":len(parrafos),"oraciones":len(oraciones),"indice":indice,
 "observaciones":puntos,"nota_preliminar":nota_preliminar,"nivel_preliminar":codigo_nivel,
 "siguiente_nivel":niveles[codigo_nivel],"fortalezas":fortalezas,"mejoras":mejoras,
 "ruta":accion[codigo_nivel],"criterios":detalle,"plan_integral":plan_integral,"marcados":marcados,
 "limitaciones":"Nota orientativa y NO oficial, basada únicamente en señales formales detectables. No evalúa la calidad real de una tesis o fuentes, no mide plagio y no identifica autoría por IA. La nota definitiva y las observaciones académicas profundas requieren revisión docente."}

@app.route("/entregar",methods=["GET","POST"])
def entregar():
 if request.method=="POST":
  if os.getenv("DEMO_MODE","false").lower()=="true" and request.form.get("ficticio")!="si":abort(400,"En la demostración solo se admiten datos ficticios; confirma su uso.")
  archivo=request.files.get("archivo")
  if not archivo or not archivo.filename or archivo.filename.rsplit(".",1)[-1].lower() not in ("pdf","docx","txt"):abort(400,"Formato no permitido")
  if not all(request.form.get(x,"").strip() for x in ("nombre","curso","titulo")):abort(400,"Faltan datos")
  uid=uuid.uuid4().hex;code=secrets.token_urlsafe(16)
  filename=uid+"."+archivo.filename.rsplit(".",1)[-1].lower()
  archivo.save(ROOT/"uploads"/filename)
  analisis=diagnostico_automatico(ROOT/"uploads"/filename, request.form["titulo"])
  with db() as c:c.execute("INSERT INTO trabajos(id,codigo,nombre,curso,titulo,version,archivo,fecha) VALUES(?,?,?,?,?,?,?,?)",(uid,code,request.form["nombre"][:140],request.form["curso"][:80],request.form["titulo"][:180],request.form.get("version","V3"),filename,datetime.datetime.now(datetime.timezone.utc).isoformat()))
  return view("Entrega recibida",r'''<div class="box" id="informe"><p class="small">INFORME GLOBAL DE SUFICIENCIA ESCRITA · {{version}} · DIAGNÓSTICO INMEDIATO</p><h1>Evaluación formativa de tu trabajo</h1><p>Trabajo recibido. Este análisis es preliminar y orienta la revisión antes de la nota definitiva del docente.</p><p><b>Código privado:</b> <span class="tag">{{code}}</span></p>{% if analisis.error %}<p class="notice">{{analisis.error}}</p>{% else %}<div class="grid"><div class="box"><p class="small">NOTA AUTOMÁTICA ORIENTATIVA</p><h1>{{'%.1f'|format(analisis.nota_preliminar)}} / 5.0</h1><p><b>Nivel {{analisis.nivel_preliminar}}</b> · No es nota docente</p></div><div class="box"><p class="small">INDICADORES FORMALES</p><h1>{{analisis.indice}} / 100</h1><p>{{analisis.palabras}} palabras · {{analisis.parrafos}} bloques identificados</p></div></div><div class="box"><h2>Informe integral preliminar</h2><p>Según los indicadores formales observados, tu escrito se ubica provisionalmente en el <b>nivel {{analisis.nivel_preliminar}}</b>. Este resultado no acredita la calidad de tu argumentación ni de tus fuentes. La revisión docente podrá modificarlo.</p><h3>Fortalezas observables</h3>{% for v in analisis.fortalezas %}<p>✅ {{v}}</p>{% endfor %}<h3>Aspectos que debes mejorar</h3>{% for v in analisis.mejoras %}<p>⚠️ {{v}}</p>{% endfor %}<h3>Ruta para avanzar al nivel {{analisis.siguiente_nivel}}</h3><p><b>{{analisis.ruta}}</b></p></div><div class="box"><h2>Rejilla V2 / V3: título, argumentación, lectura base y evidencias parciales</h2><div class="table"><table><thead><tr><th>Competencia</th><th>Referencia</th><th>Indicador</th><th>Resultado</th><th>Acción concreta</th></tr></thead><tbody>{% for c in analisis.criterios %}<tr><td>{{c.competencia}}</td><td>{{c.codigo}}</td><td>{{c.indicador}}</td><td><span class="mark-{{c.color}}">{{c.estado}}</span></td><td>{{c.accion}}</td></tr>{% endfor %}</tbody></table></div><p class="small">Esta tabla no reemplaza la rejilla completa ni determina el desempeño de todos sus criterios.</p></div><div class="box"><h2>Fragmentos del texto con marcas de revisión</h2><p class="small">Resaltado inspirado en sistemas de anotación: verde = revisar acierto formal; amarillo = aspecto pendiente; rojo = posible mejora de claridad; azul = revisión contextual. <b>Estos colores no indican coincidencia con otras fuentes, plagio ni IA.</b></p><div class="grid"><div><span class="mark-verde">Verde: evidencia formal</span></div><div><span class="mark-amarillo">Amarillo: revisar</span></div><div><span class="mark-rojo">Rojo: claridad</span></div><div><span class="mark-azul">Azul: contextualizar</span></div></div>{% for m in analisis.marcados %}<div class="snippet"><p><span class="mark-{{m.color}}">{{m.tipo}}</span></p><blockquote>{{m.texto}}</blockquote><p class="small"><b>Recomendación:</b> {{m.motivo}}</p></div>{% endfor %}</div><div class="box"><h2>Plan integral para alcanzar C y D: todos los criterios</h2><p>Este plan conserva los criterios de la rejilla original V2 y la ampliación V3. No presupone que todos los aspectos estén mal: cada recomendación indica qué evidencias debe comprobar y mejorar el estudiante. Para nivel A o B, se muestra el plan completo, no solo los indicadores automáticos.</p><div class="table"><table><thead><tr><th>Código</th><th>Criterio</th><th>Cómo mejorar</th><th>Meta C</th><th>Meta D</th></tr></thead><tbody>{% for p in analisis.plan_integral %}{% if version == 'V3' or not p.codigo.startswith('3.') %}<tr><td>{{p.codigo}}</td><td>{{p.criterio}}</td><td>{{p.recomendacion}}</td><td>{{p.objetivo_c}}</td><td>{{p.objetivo_d}}</td></tr>{% endif %}{% endfor %}</tbody></table></div><p class="small">Las metas C/D son orientaciones operativas de esta adaptación; la Rejilla V2 no define por sí sola descriptores detallados para cada nivel. La ubicación exacta requiere juicio docente.</p></div><p class="notice">{{analisis.limitaciones}}</p><div class="print-hide"><button type="button" onclick="window.print()">Guardar como PDF / imprimir</button> <button type="button" class="blue" id="wa">Compartir informe previo por WhatsApp</button></div>{% endif %}<p class="small">La demostración gratuita puede perder los archivos al reiniciarse; usa solo información ficticia. No compartas tu código privado.</p><a class="btn print-hide" href="{{url_for('resultado',code=code)}}">Consultar futura nota docente</a></div>{% if not analisis.error %}<script>(function(){const el=document.getElementById("wa");if(!el)return;el.onclick=function(){const msg="Informe preliminar de suficiencia escrita ("+{{version|tojson}}+"):\nNivel orientativo "+{{analisis.nivel_preliminar|tojson}}+" · Nota NO oficial "+{{analisis.nota_preliminar|tojson}}+"/5.0\nFortalezas:\n"+{{analisis.fortalezas|join('\n')|tojson}}+"\nPor mejorar:\n"+{{analisis.mejoras|join('\n')|tojson}}+"\nRecomendación:\n"+{{analisis.ruta|tojson}}+"\nResultado automático, sujeto a revisión docente.";window.open("https://api.whatsapp.com/send?text="+encodeURIComponent(msg),"_blank","noopener,noreferrer");};})();</script>{% endif %}''',code=code,analisis=analisis,version=request.form.get("version","V3"))
 return view("Entregar",'''<div class="box"><h1>Entregar trabajo escrito</h1><form method="post" enctype="multipart/form-data"><label>Nombre del estudiante</label><input name="nombre" maxlength="140" required><label>Curso o grupo</label><input name="curso" maxlength="80" required><label>Título del trabajo</label><input name="titulo" maxlength="180" required><label>Rejilla de evaluación</label><select name="version"><option>V3</option><option>V2</option></select><label>Documento (PDF, Word DOCX o TXT; máximo 8 MB)</label><input type="file" name="archivo" accept=".pdf,.docx,.txt" required><p class="notice">Usa esta plataforma únicamente cuando tu institución haya autorizado el tratamiento de los datos estudiantiles. No se utiliza el archivo para determinar automáticamente si fue hecho con IA.</p>{% if demo %}<p class="notice"><b>DEMO GRATUITA:</b> la información puede perderse cuando se reinicie el servicio. No cargues nombres ni trabajos reales de estudiantes. Solo datos de ejemplo.</p><label><input style="width:auto" type="checkbox" name="ficticio" value="si" required> Confirmo que los datos y el documento son ficticios.</label>{% endif %}<button>Enviar trabajo</button></form></div>''',demo=os.getenv('DEMO_MODE','false').lower()=='true')
@app.get("/consulta")
def consulta():return view("Consultar",'''<div class="box"><h1>Consultar evaluación</h1><form action="/r" method="get"><label>Código privado</label><input name="code" required><button>Consultar resultado</button></form></div>''')
@app.get("/r")
def buscar():return redirect(url_for("resultado",code=request.args.get("code","")))
@app.get("/resultado/<code>")
def resultado(code):
 with db() as c:
  row=c.execute("SELECT * FROM trabajos WHERE codigo=?",(code,)).fetchone()
  if not row:abort(404)
  items=c.execute("SELECT * FROM criterios WHERE trabajo=? ORDER BY codigo",(row["id"],)).fetchall()
 return view("Informe individual",'''<div class="box"><p class="small">INFORME DE SUFICIENCIA ESCRITA · {{row.version}}</p><h1>{{row.titulo}}</h1><p><b>Estudiante:</b> {{row.nombre}} · <b>Grupo:</b> {{row.curso}}</p>{% if row.nota is not none %}<h2>Resultado: {{'%.1f'|format(row.nota)}} / 5.0 · Nivel {{nivel(row.nota)}}</h2><h3>Fortalezas</h3><p>{{row.fortalezas or 'Sin observaciones'}}</p><h3>Por mejorar</h3><p>{{row.mejoras or 'Sin observaciones'}}</p><h3>Recomendaciones</h3><p>{{row.recomendaciones or 'Sin observaciones'}}</p><h3>Integridad académica</h3><p>{{row.integridad or 'No se registraron observaciones'}}</p><h3>Valoración por criterios</h3><div class="table"><table><tr><th>Código</th><th>Criterio</th><th>Nivel</th></tr>{% for i in items %}<tr><td>{{i.codigo}}</td><td>{{i.descripcion}}</td><td>{{i.nivel}}</td></tr>{% endfor %}</table></div><button onclick="window.print()" class="print-hide">Imprimir / Guardar PDF</button><button class="print-hide" onclick="navigator.share?navigator.share({title:'Resultado académico',text:'Mi evaluación de suficiencia escrita: {{row.titulo}}'}):alert('Puedes imprimir este informe como PDF')">Compartir</button>{% else %}<p class="notice">Tu trabajo está recibido y pendiente de calificación docente.</p>{% endif %}</div>''',row=row,items=items,nivel=nivel,chr=chr)
@app.route("/acceso",methods=["GET","POST"])
def login():
 if request.method=="POST":
  configured=os.getenv("DOCENTE_PASSWORD","")
  if configured and secrets.compare_digest(request.form.get("password",""),configured):
   session.clear();session["docente"]=True;return redirect("/docente")
  return view("Acceso",'<div class="box"><h1>Acceso no autorizado</h1><p>La contraseña no es correcta o no ha sido configurada.</p><a href="/acceso">Volver</a></div>'),401
 return view("Acceso docente",'''<div class="box"><h1>Acceso docente</h1><form method="post"><label>Contraseña</label><input type="password" name="password" required><button>Ingresar</button></form></div>''')
@app.get("/salir")
def salir():session.clear();return redirect("/")
@app.get("/docente")
@docente
def panel():
 with db() as c:
  rows=c.execute("SELECT id,nombre,curso,titulo,version,fecha,nota FROM trabajos ORDER BY fecha DESC").fetchall()
  data=[dict(x) for x in c.execute("SELECT nota FROM trabajos WHERE nota IS NOT NULL").fetchall()]
 total=len(rows);assessed=len(data);average=round(sum(x["nota"] for x in data)/assessed,2) if assessed else 0
 return view("Panel docente",'''<div class="box"><h1>Panel del docente</h1><p><b>Trabajos:</b> {{total}} · <b>Calificados:</b> {{assessed}} · <b>Pendientes:</b> {{total-assessed}} · <b>Promedio:</b> {{average}}</p><a class="btn" href="/estadisticas.csv">Exportar CSV Power BI</a> <a href="/salir" class="btn blue">Salir</a><div class="table"><table><tr><th>Estudiante</th><th>Grupo</th><th>Trabajo</th><th>Rejilla</th><th>Nota</th><th>Acción</th></tr>{% for r in rows %}<tr><td>{{r.nombre}}</td><td>{{r.curso}}</td><td>{{r.titulo}}</td><td>{{r.version}}</td><td>{{r.nota if r.nota is not none else 'Pendiente'}}</td><td><a href="/calificar/{{r.id}}">Evaluar</a></td></tr>{% endfor %}</table></div></div>''',rows=rows,total=total,assessed=assessed,average=average)
@app.route("/calificar/<uid>",methods=["GET","POST"])
@docente
def calificar(uid):
 with db() as c:
  row=c.execute("SELECT * FROM trabajos WHERE id=?",(uid,)).fetchone()
  if not row:abort(404)
  rubric=R2 if row["version"]=="V2" else R3
  if request.method=="POST":
   try:score=float(request.form["nota"])
   except (ValueError,KeyError):abort(400)
   if not (1<=score<=5):abort(400,"Nota fuera de rango")
   c.execute("UPDATE trabajos SET nota=?,fortalezas=?,mejoras=?,recomendaciones=?,integridad=? WHERE id=?",(score,*[request.form.get(k,"")[:5000] for k in ("fortalezas","mejoras","recomendaciones","integridad")],uid))
   for code,label in rubric:
    val=request.form.get("nivel_"+code,"Sin valorar")
    c.execute("INSERT OR REPLACE INTO criterios VALUES(?,?,?,?)",(uid,code,label,val))
   return redirect("/docente")
  from markupsafe import escape
  fields=''.join('<tr><td>'+escape(code)+'</td><td>'+escape(label)+'</td><td><select name="nivel_'+escape(code)+'"><option>Sin valorar</option><option>A</option><option>B</option><option>C</option><option>D</option></select></td></tr>' for code,label in rubric)
  html='''<div class="box"><h1>Evaluar trabajo</h1><p><b>Estudiante:</b> {{row.nombre}} · {{row.curso}}</p><p><b>Título:</b> {{row.titulo}}</p><p><a class="btn blue" href="/archivo/{{row.id}}">Descargar documento</a></p><form method="post"><h2>Rejilla {{row.version}}</h2><div class="table"><table><tr><th>Código</th><th>Condición de evaluación</th><th>Nivel</th></tr>'''+fields+'''</table></div><label>Nota definitiva (1.0–5.0)</label><input name="nota" type="number" min="1" max="5" step="0.1" required value="{{row.nota if row.nota is not none else ''}}">{% for key,title in [('fortalezas','Fortalezas'),('mejoras','Aspectos por mejorar'),('recomendaciones','Recomendaciones'),('integridad','Observaciones de integridad académica')] %}<label>{{title}}</label><textarea name="{{key}}">{{row[key] or ''}}</textarea>{% endfor %}<p class="notice">Nunca concluyas plagio o uso de IA únicamente por patrones de escritura: contrasta fuentes y evidencias.</p><button>Publicar evaluación</button></form></div>'''
  return view("Calificar",html,row=row)
@app.get("/archivo/<uid>")
@docente
def archivo(uid):
 with db() as c:row=c.execute("SELECT archivo FROM trabajos WHERE id=?",(uid,)).fetchone()
 if not row:abort(404)
 path=ROOT/"uploads"/row["archivo"]
 if not path.exists():abort(404)
 return send_file(path,as_attachment=True,download_name="trabajo."+path.suffix.lstrip("."))
@app.get("/estadisticas.csv")
@docente
def stats():
 with db() as c:rows=c.execute("SELECT nombre,curso,titulo,version,fecha,nota FROM trabajos ORDER BY fecha").fetchall()
 output=io.StringIO();w=csv.writer(output);w.writerow(["estudiante","grupo","trabajo","rejilla","fecha","nota","nivel"])
 for r in rows:w.writerow([*list(r),nivel(r["nota"])])
 return Response("\ufeff"+output.getvalue(),mimetype="text/csv",headers={"Content-Disposition":"attachment; filename=indicadores_suficiencia.csv"})
@app.get("/health")
def health():return {"ok":True}
if __name__=="__main__":
 app.run(host="0.0.0.0",port=int(os.getenv("PORT","8080")))
