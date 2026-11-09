#!/usr/bin/env python3
"""
Genera la web estática de España al Minuto en la carpeta _site/.

Lee los RSS configurados en config.json, se queda con titular, enlace, medio y hora
(no copia textos de las noticias) y escribe index.html, las páginas legales,
sitemap.xml y robots.txt.

Uso:
  python3 build.py                     # descarga los RSS y genera _site/
  python3 build.py --fixture prueba.xml  # usa un RSS local para todas las fuentes (pruebas)
  python3 build.py --strict            # falla si quedan datos del titular sin rellenar

Solo usa la biblioteca estándar de Python 3.9+.
"""
import argparse
import email.utils
import html
import json
import re
import shutil
import sys
import unicodedata
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

RAIZ = Path(__file__).resolve().parent
SALIDA = RAIZ / "_site"
MADRID = ZoneInfo("Europe/Madrid")

SECCIONES = {
    "general": "Portada",
    "politica": "España",
    "economia": "Economía",
    "sociedad": "Sociedad",
    "deportes": "Deportes",
    "internacional": "Internacional",
    "cultura": "Cultura",
    "canarias": "Canarias",
}

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]


def e(texto):
    return html.escape(str(texto or ""), quote=True)


# ---------- Lectura de RSS / Atom ----------

def descargar(url, agente):
    req = urllib.request.Request(url, headers={"User-Agent": agente, "Accept": "application/rss+xml, application/xml, text/xml, */*"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read()


def local(tag):
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def hijo(nodo, nombre):
    for h in nodo:
        if local(h.tag) == nombre:
            return h
    return None


def texto_hijo(nodo, *nombres):
    for n in nombres:
        h = hijo(nodo, n)
        if h is not None:
            valor = "".join(h.itertext()).strip()
            if valor:
                return valor
    return ""


def leer_fecha(valor):
    if not valor:
        return None
    try:
        d = email.utils.parsedate_to_datetime(valor)
    except (TypeError, ValueError):
        try:
            d = datetime.fromisoformat(valor.replace("Z", "+00:00"))
        except ValueError:
            return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d.astimezone(timezone.utc)


def limpiar_titular(t):
    t = html.unescape(re.sub(r"<[^>]+>", "", t or ""))
    return re.sub(r"\s+", " ", t).strip()


def analizar(xml_bytes):
    """Devuelve [(titulo, enlace, fecha_utc)] de un RSS 2.0 o Atom."""
    raiz = ET.fromstring(xml_bytes)
    items = []
    nodos = [n for n in raiz.iter() if local(n.tag) in ("item", "entry")]
    for n in nodos:
        titulo = limpiar_titular(texto_hijo(n, "title"))
        enlace = texto_hijo(n, "link")
        if not enlace:  # Atom: <link href="..."/>
            for h in n:
                if local(h.tag) == "link" and h.get("href") and h.get("rel", "alternate") == "alternate":
                    enlace = h.get("href")
                    break
        fecha = leer_fecha(texto_hijo(n, "pubDate", "published", "updated", "date"))
        if titulo and enlace and enlace.startswith(("http://", "https://")) and fecha:
            items.append((titulo, enlace.strip(), fecha))
    return items


def clave(titulo):
    t = unicodedata.normalize("NFKD", titulo.lower())
    t = "".join(c for c in t if c.isalnum() or c == " ")
    return " ".join(t.split())[:80]


def recoger(cfg, fixture=None):
    agente = f"EspanaAlMinutoBot/1.0 (+{cfg['sitio']['url']})"
    lim = cfg["limites"]
    ahora = datetime.now(timezone.utc)
    corte = ahora - timedelta(hours=lim["horas_max"])
    vistas, noticias, informe = set(), [], []
    for f in cfg["fuentes"]:
        try:
            datos = Path(fixture).read_bytes() if fixture else descargar(f["url"], agente)
            items = analizar(datos)
        except Exception as err:  # una fuente caída no detiene la web
            informe.append(f"  ✗ {f['medio']} ({f['seccion']}): {type(err).__name__}: {err}")
            continue
        items.sort(key=lambda x: x[2], reverse=True)
        n = 0
        for titulo, enlace, fecha in items:
            if fecha < corte or fecha > ahora + timedelta(minutes=10):
                continue
            k = clave(titulo)
            if k in vistas:
                continue
            vistas.add(k)
            noticias.append({"titulo": titulo, "url": enlace, "fecha": fecha,
                             "medio": f["medio"], "seccion": f["seccion"]})
            n += 1
            if n >= lim["max_por_fuente"]:
                break
        informe.append(f"  ✓ {f['medio']} ({f['seccion']}): {n} titulares")
    noticias.sort(key=lambda x: x["fecha"], reverse=True)
    return noticias[: lim["max_noticias"]], informe


# ---------- Plantillas ----------

def maqueta(cfg, titulo_pag, descripcion, ruta, cuerpo, actual=""):
    s = cfg["sitio"]
    base = s["url"].rstrip("/")
    canonica = f"{base}/{ruta}" if ruta else f"{base}/"
    titulo_completo = s["nombre"] if not titulo_pag else f"{titulo_pag} · {s['nombre']}"
    def nav(href, txt, clave_nav):
        cur = ' aria-current="page"' if clave_nav == actual else ""
        return f'<a href="{href}"{cur}>{txt}</a>'
    jsonld = ""
    if not ruta:
        jsonld = ('<script type="application/ld+json">' + json.dumps({
            "@context": "https://schema.org", "@type": "WebSite",
            "name": s["nombre"], "url": canonica, "inLanguage": "es-ES",
            "description": s["descripcion"]}, ensure_ascii=False) + "</script>")
    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(titulo_completo)}</title>
<meta name="description" content="{e(descripcion)}">
<link rel="canonical" href="{e(canonica)}">
<meta property="og:type" content="website">
<meta property="og:locale" content="es_ES">
<meta property="og:site_name" content="{e(s['nombre'])}">
<meta property="og:title" content="{e(titulo_completo)}">
<meta property="og:description" content="{e(descripcion)}">
<meta property="og:url" content="{e(canonica)}">
<meta name="twitter:card" content="summary">
<meta name="color-scheme" content="light dark">
<link rel="icon" href="favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="estilos.css">
{jsonld}
</head>
<body>
<a class="saltar" href="#contenido">Saltar al contenido</a>
<header class="cab">
  <div class="cab-in">
    <a class="marca" href="./">España al <span>Minuto</span></a>
    <nav aria-label="Principal">{nav("./", "Titulares", "inicio")}{nav("aviso-legal.html", "Aviso legal", "aviso")}</nav>
  </div>
</header>
<main id="contenido" class="pagina">
{cuerpo}
</main>
<footer class="pie">
  <div class="pie-in">
    <p><strong>{e(s['nombre'])}</strong> recopila titulares publicados por otros medios y enlaza a la noticia original. Los titulares y contenidos pertenecen a sus respectivos medios.</p>
    <nav aria-label="Legal">{nav("aviso-legal.html", "Aviso legal", "aviso")}{nav("privacidad.html", "Política de privacidad", "privacidad")}{nav("cookies.html", "Política de cookies", "cookies")}{nav("aviso-legal.html#retirada", "Retirada de contenidos", "-")}</nav>
    <p class="nota">Esta web no usa cookies ni rastreadores.</p>
  </div>
</footer>
</body>
</html>
"""


def fecha_larga(d):
    d = d.astimezone(MADRID)
    return f"{DIAS[d.weekday()]} {d.day} de {MESES[d.month - 1]} de {d.year}"


def pagina_inicio(cfg, noticias, generado):
    s = cfg["sitio"]
    usadas = [k for k in SECCIONES if any(n["seccion"] == k for n in noticias)]
    chips = ['<button type="button" class="chip" data-s="todas" aria-pressed="true">Todo</button>']
    for k in usadas:
        cuantas = sum(1 for n in noticias if n["seccion"] == k)
        chips.append(f'<button type="button" class="chip s-{k}" data-s="{k}" aria-pressed="false"><i></i>{SECCIONES[k]} <span>{cuantas}</span></button>')

    filas, dia_prev = [], None
    for i, n in enumerate(noticias):
        local_d = n["fecha"].astimezone(MADRID)
        dia = local_d.date()
        if dia != dia_prev:
            filas.append(f'<li class="dia" data-dia>{e(fecha_larga(n["fecha"]).capitalize())}</li>')
            dia_prev = dia
        iso = n["fecha"].isoformat().replace("+00:00", "Z")
        filas.append(f"""<li class="item s-{n['seccion']}{' primero' if i == 0 else ''}" data-s="{n['seccion']}">
  <time datetime="{iso}">{local_d:%H:%M}</time>
  <div class="cuerpo">
    <div class="meta"><span class="sec">{e(SECCIONES.get(n['seccion'], n['seccion']))}</span><span class="medio">{e(n['medio'])}</span><span class="hace" data-t="{iso}"></span></div>
    <h2><a href="{e(n['url'])}" target="_blank" rel="noopener">{e(n['titulo'])}</a></h2>
  </div>
</li>""")
    if not noticias:
        filas.append('<li class="vacio">No se han podido cargar titulares en esta actualización. Vuelve a intentarlo en unos minutos.</li>')

    gen_iso = generado.isoformat().replace("+00:00", "Z")
    cuerpo = f"""
<section class="portada">
  <p class="antetitulo"><span class="punto" aria-hidden="true"></span> Actualizado <time id="generado" datetime="{gen_iso}">{generado.astimezone(MADRID):%H:%M}</time> (hora peninsular) · se renueva cada hora</p>
  <h1>Lo último en España, hora a hora</h1>
  <p class="entradilla">{e(s['descripcion'])}</p>
  <div class="filtros" role="group" aria-label="Filtrar por sección">{''.join(chips)}</div>
  <label class="buscar"><span class="vh">Buscar en los titulares</span><input id="q" type="search" placeholder="Buscar en los titulares…" autocomplete="off"></label>
</section>
<ol class="hilo" id="hilo">
{chr(10).join(filas)}
</ol>
<p class="sin-res" id="sinres" hidden>No hay titulares que coincidan con la búsqueda.</p>
<p class="aviso-fuentes">Las horas son las de publicación en cada medio, en hora peninsular (en Canarias, una hora menos). Al pulsar un titular sales de esta web hacia la del medio, que tiene sus propias políticas de privacidad y cookies.</p>
<script src="app.js" defer></script>
"""
    return maqueta(cfg, "", s["descripcion"], "", cuerpo, "inicio")


def pagina_legal(cfg, archivo, titulo, descripcion, ruta, actual):
    plantilla = (RAIZ / "plantillas" / archivo).read_text(encoding="utf-8")
    valores = {
        "SITIO": cfg["sitio"]["nombre"], "URL": cfg["sitio"]["url"].rstrip("/"),
        "FECHA": cfg["sitio"]["fecha_textos_legales"],
        "TITULAR": cfg["titular"]["nombre"], "NIF": cfg["titular"]["nif"],
        "DOMICILIO": cfg["titular"]["domicilio"], "EMAIL": cfg["titular"]["email"],
    }
    cuerpo = re.sub(r"\{\{(\w+)\}\}", lambda m: e(valores[m.group(1)]), plantilla)
    return maqueta(cfg, titulo, descripcion, ruta, f'<article class="legal">{cuerpo}</article>', actual)


# ---------- Principal ----------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fixture", help="RSS local para usar en todas las fuentes (pruebas)")
    ap.add_argument("--strict", action="store_true", help="falla si faltan datos del titular")
    args = ap.parse_args()

    cfg = json.loads((RAIZ / "config.json").read_text(encoding="utf-8"))
    pendientes = [k for k, v in cfg["titular"].items() if v.startswith("[")]
    if "TU-USUARIO" in cfg["sitio"]["url"]:
        pendientes.append("sitio.url")
    if pendientes:
        msg = "Faltan datos en config.json: " + ", ".join(pendientes)
        if args.strict:
            sys.exit("ERROR: " + msg)
        print("AVISO: " + msg + " (las páginas legales no son válidas hasta rellenarlos)")

    noticias, informe = recoger(cfg, args.fixture)
    generado = datetime.now(timezone.utc).replace(microsecond=0)

    if SALIDA.exists():
        shutil.rmtree(SALIDA)
    SALIDA.mkdir()
    for f in (RAIZ / "estaticos").iterdir():
        shutil.copy(f, SALIDA / f.name)

    paginas = {
        "index.html": pagina_inicio(cfg, noticias, generado),
        "aviso-legal.html": pagina_legal(cfg, "aviso-legal.html", "Aviso legal",
            "Datos del titular, condiciones de uso, propiedad intelectual y retirada de contenidos.", "aviso-legal.html", "aviso"),
        "privacidad.html": pagina_legal(cfg, "privacidad.html", "Política de privacidad",
            "Qué datos personales se tratan en esta web, para qué y cómo ejercer tus derechos.", "privacidad.html", "privacidad"),
        "cookies.html": pagina_legal(cfg, "cookies.html", "Política de cookies",
            "Esta web no utiliza cookies ni tecnologías de seguimiento.", "cookies.html", "cookies"),
    }
    for nombre, contenido in paginas.items():
        (SALIDA / nombre).write_text(contenido, encoding="utf-8")

    base = cfg["sitio"]["url"].rstrip("/")
    hoy = generado.date().isoformat()
    urls = [("", hoy, "hourly", "1.0"), ("aviso-legal.html", None, "yearly", "0.2"),
            ("privacidad.html", None, "yearly", "0.2"), ("cookies.html", None, "yearly", "0.2")]
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for ruta, mod, freq, pri in urls:
        sm.append(f"  <url><loc>{e(base + '/' + ruta)}</loc>" + (f"<lastmod>{mod}</lastmod>" if mod else "") +
                  f"<changefreq>{freq}</changefreq><priority>{pri}</priority></url>")
    sm.append("</urlset>")
    (SALIDA / "sitemap.xml").write_text("\n".join(sm) + "\n", encoding="utf-8")
    (SALIDA / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {base}/sitemap.xml\n", encoding="utf-8")
    (SALIDA / ".nojekyll").write_text("", encoding="utf-8")

    print(f"Generado {SALIDA} con {len(noticias)} titulares:")
    print("\n".join(informe))


if __name__ == "__main__":
    main()
