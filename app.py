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
PAGE='''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#08765f"><title>{{title}} · Suficiencia Escrita</title><style>
*{box-sizing:border-box}body{margin:0;font:16px system-ui,Arial;color:#183448;background:#f3f7fa}header{background:linear-gradient(110deg,#074e7a,#08765f);color:white;padding:18px 5%}nav{max-width:1020px;margin:auto;display:flex;gap:20px;flex-wrap:wrap;align-items:center}nav b{font-size:23px;margin-right:auto}nav a{color:white;text-decoration:none;font-weight:650}main{max-width:1020px;margin:28px auto;padding:0 18px}.hero{background:linear-gradient(115deg,#07557e,#07916e);padding:38px;color:white;border-radius:22px}.box{border:1px solid #d3e2eb;background:white;border-radius:16px;padding:24px;margin:16px 0;box-shadow:0 5px 18px #2342}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px}h1{font-size:clamp(26px,4vw,40px);margin-top:0}h2{font-size:23px}label{display:block;font-weight:700;margin:12px 0 5px}input,select,textarea{width:100%;padding:12px;border:1px solid #b8cad4;border-radius:10px;font:inherit;background:white;color:#183448}textarea{min-height:90px}button,.btn{display:inline-block;border:0;background:#08765f;color:white;text-decoration:none;padding:12px 17px;border-radius:10px;font-weight:700;font-size:15px;margin:10px 0;cursor:pointer}.blue{background:#0c648e}.small{color:#5b7180;font-size:14px}.tag{background:#dff4ed;color:#075d4e;border-radius:20px;padding:5px 12px;font-weight:700}.table{overflow-x:auto}table{width:100%;border-collapse:collapse}th,td{padding:10px;text-align:left;border-bottom:1px solid #e0e8ec;font-size:14px}.notice{background:#fff7df;padding:14px;border-radius:10px}footer{text-align:center;color:#657a85;padding:30px 12px;font-size:13px}@media(max-width:550px){.hero{padding:22px}.box{padding:18px}nav b{width:100%}}@media print{header,.print-hide,footer{display:none}}
.mark-verde{background:#d5f4df;color:#0b5730;padding:4px 8px;border-radius:6px}.mark-amarillo{background:#fff0b6;color:#654b00;padding:4px 8px;border-radius:6px}.mark-rojo{background:#ffdce0;color:#7b1728;padding:4px 8px;border-radius:6px}.mark-azul{background:#dcecff;color:#163d7a;padding:4px 8px;border-radius:6px}.snippet{border-left:4px solid #dae4ed;padding:12px 16px;margin:15px 0;background:#f7fafc;border-radius:8px}.snippet blockquote{margin:12px 0;line-height:1.65;overflow-wrap:anywhere}@media print{button{display:none}}</style></head><body><header><nav><b>✍️ Suficiencia Escrita</b><a href="/">Inicio</a><a href="/entregar">Estudiantes</a><a href="/consulta">Resultados</a><a href="/docente">Docentes</a></nav></header><main>{{content|safe}}</main><footer>Suficiencia Escrita · Rejillas V2 y V3 · Herramienta formativa, sin dictámenes automáticos de plagio o IA</footer></body></html>'''
def view(title,content,**kwargs):return render_template_string(PAGE,title=title,content=render_template_string(content,**kwargs))
@app.get("/")
def home():
 return view("Inicio",'''<section class="hero"><p>PLATAFORMA DE PRODUCCIÓN ESCRITA ACADÉMICA Y CIENTÍFICA · DEMOSTRACIÓN GRATUITA</p><h1>Evaluar con criterios. Mejorar con evidencia.</h1><p>Presentación de trabajos escritos de suficiencia, retroalimentación formativa y seguimiento académico con las rejillas Versión 2 y Versión 3.</p><a class="btn" href="/entregar">Entregar trabajo</a> <a class="btn blue" href="/consulta">Consultar resultado</a></section><div class="grid"><div class="box"><h2>Estudiantes</h2><p>Sube tu trabajo y recibe un código privado para consultar su valoración.</p></div><div class="box"><h2>Docentes</h2><p>Evalúa competencias lingüísticas, texto-discursivas y académicas con observaciones detalladas.</p></div><div class="box"><h2>Indicadores</h2><p>Promedios, distribución A–D y exportación CSV para Power BI.</p></div></div><div class="box"><h2>Escala de desempeño</h2><p><b>A:</b> 1.0–2.9 · <b>B:</b> 3.0–3.9 · <b>C:</b> 4.0–4.5 · <b>D:</b> 4.6–5.0</p><p class="small">Esta es la escala personalizada de la plataforma, no una equivalencia automática con escalas oficiales de otras instituciones.</p></div>''')

def diagnostico_automatico(archivo):
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
 cumplidos=sum(1 for c in checks if c[3])
 # Nota preliminar heurística: 2.0 a 4.0. Nunca presentar como calificación o
 # calidad científica demostrada; el valor es solo una ayuda a la autoevaluación.
 nota_preliminar=round(2.0+0.4*cumplidos,1)
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
 "ruta":accion[codigo_nivel],"criterios":detalle,"marcados":marcados,
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
  analisis=diagnostico_automatico(ROOT/"uploads"/filename)
  with db() as c:c.execute("INSERT INTO trabajos(id,codigo,nombre,curso,titulo,version,archivo,fecha) VALUES(?,?,?,?,?,?,?,?)",(uid,code,request.form["nombre"][:140],request.form["curso"][:80],request.form["titulo"][:180],request.form.get("version","V3"),filename,datetime.datetime.now(datetime.timezone.utc).isoformat()))
  return view("Entrega recibida",r'''<div class="box" id="informe"><p class="small">INFORME GLOBAL DE SUFICIENCIA ESCRITA · {{version}} · DIAGNÓSTICO INMEDIATO</p><h1>Evaluación formativa de tu trabajo</h1><p>Trabajo recibido. Este análisis es preliminar y orienta la revisión antes de la nota definitiva del docente.</p><p><b>Código privado:</b> <span class="tag">{{code}}</span></p>{% if analisis.error %}<p class="notice">{{analisis.error}}</p>{% else %}<div class="grid"><div class="box"><p class="small">NOTA AUTOMÁTICA ORIENTATIVA</p><h1>{{'%.1f'|format(analisis.nota_preliminar)}} / 5.0</h1><p><b>Nivel {{analisis.nivel_preliminar}}</b> · No es nota docente</p></div><div class="box"><p class="small">INDICADORES FORMALES</p><h1>{{analisis.indice}} / 100</h1><p>{{analisis.palabras}} palabras · {{analisis.parrafos}} bloques identificados</p></div></div><div class="box"><h2>Informe integral preliminar</h2><p>Según los indicadores formales observados, tu escrito se ubica provisionalmente en el <b>nivel {{analisis.nivel_preliminar}}</b>. Este resultado no acredita la calidad de tu argumentación ni de tus fuentes. La revisión docente podrá modificarlo.</p><h3>Fortalezas observables</h3>{% for v in analisis.fortalezas %}<p>✅ {{v}}</p>{% endfor %}<h3>Aspectos que debes mejorar</h3>{% for v in analisis.mejoras %}<p>⚠️ {{v}}</p>{% endfor %}<h3>Ruta para avanzar al nivel {{analisis.siguiente_nivel}}</h3><p><b>{{analisis.ruta}}</b></p></div><div class="box"><h2>Rejilla de valoración V2 / V3: evidencias parciales</h2><div class="table"><table><thead><tr><th>Competencia</th><th>Referencia</th><th>Indicador</th><th>Resultado</th><th>Acción concreta</th></tr></thead><tbody>{% for c in analisis.criterios %}<tr><td>{{c.competencia}}</td><td>{{c.codigo}}</td><td>{{c.indicador}}</td><td><span class="mark-{{c.color}}">{{c.estado}}</span></td><td>{{c.accion}}</td></tr>{% endfor %}</tbody></table></div><p class="small">Esta tabla no reemplaza la rejilla completa ni determina el desempeño de todos sus criterios.</p></div><div class="box"><h2>Fragmentos del texto con marcas de revisión</h2><p class="small">Resaltado inspirado en sistemas de anotación: verde = revisar acierto formal; amarillo = aspecto pendiente; rojo = posible mejora de claridad; azul = revisión contextual. <b>Estos colores no indican coincidencia con otras fuentes, plagio ni IA.</b></p><div class="grid"><div><span class="mark-verde">Verde: evidencia formal</span></div><div><span class="mark-amarillo">Amarillo: revisar</span></div><div><span class="mark-rojo">Rojo: claridad</span></div><div><span class="mark-azul">Azul: contextualizar</span></div></div>{% for m in analisis.marcados %}<div class="snippet"><p><span class="mark-{{m.color}}">{{m.tipo}}</span></p><blockquote>{{m.texto}}</blockquote><p class="small"><b>Recomendación:</b> {{m.motivo}}</p></div>{% endfor %}</div><p class="notice">{{analisis.limitaciones}}</p><div class="print-hide"><button type="button" onclick="window.print()">Guardar como PDF / imprimir</button> <button type="button" class="blue" id="wa">Compartir informe previo por WhatsApp</button></div>{% endif %}<p class="small">La demostración gratuita puede perder los archivos al reiniciarse; usa solo información ficticia. No compartas tu código privado.</p><a class="btn print-hide" href="{{url_for('resultado',code=code)}}">Consultar futura nota docente</a></div>{% if not analisis.error %}<script>(function(){const el=document.getElementById("wa");if(!el)return;el.onclick=function(){const msg="Informe preliminar de suficiencia escrita ("+{{version|tojson}}+"):\nNivel orientativo "+{{analisis.nivel_preliminar|tojson}}+" · Nota NO oficial "+{{analisis.nota_preliminar|tojson}}+"/5.0\nFortalezas:\n"+{{analisis.fortalezas|join('\n')|tojson}}+"\nPor mejorar:\n"+{{analisis.mejoras|join('\n')|tojson}}+"\nRecomendación:\n"+{{analisis.ruta|tojson}}+"\nResultado automático, sujeto a revisión docente.";window.open("https://api.whatsapp.com/send?text="+encodeURIComponent(msg),"_blank","noopener,noreferrer");};})();</script>{% endif %}''',code=code,analisis=analisis,version=request.form.get("version","V3"))
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
