"""
Genera index.html con:
- Sección "Inicio": titulares generales recientes.
- Sección "UNI": inversión, negocios, tecnología, política internacional, cripto y medicina.

La API key se lee de la variable de entorno GNEWS_API_KEY (secret de GitHub Actions).

Nota: el plan gratuito de GNews permite solo 1 petición por segundo, por eso este
script espera un poco entre cada categoría y reintenta si detecta un bloqueo (429).
"""

import os
import sys
import json
import time
import requests
from datetime import datetime, timezone

API_KEY = os.environ.get("GNEWS_API_KEY")
LANG = os.environ.get("NEWS_LANG", "es")
MAX_PER_CATEGORY = 8
PAUSA_ENTRE_PETICIONES = 1.3  # segundos, margen sobre el límite de 1 req/seg del plan free

# URL de tu Worker de Cloudflare (ver cloudflare-worker/worker.js).
# Reemplaza esto por tu URL real una vez que despliegues el Worker.
CHATBOT_ENDPOINT = "https://uni-chatbot.achismiachis787.workers.dev"

if not API_KEY:
    print("ERROR: falta la variable de entorno GNEWS_API_KEY")
    sys.exit(1)

CATEGORIAS = {
    "inicio":      ("Inicio",                 None),
    "inversion":   ("Inversión",               "inversiones OR mercados financieros OR bolsa"),
    "negocios":    ("Negocios",                "negocios OR empresas OR economía"),
    "tecnologia":  ("Tecnología",              "tecnología OR inteligencia artificial"),
    "geopolitica": ("Política internacional",  "política internacional OR geopolítica"),
    "cripto":      ("Cripto",                  "criptomonedas OR bitcoin OR ethereum"),
    "medicina":    ("Medicina",                "medicina OR salud OR avances médicos"),
}


def obtener_noticias(query, intentos=3):
    if query is None:
        endpoint = "https://gnews.io/api/v4/top-headlines"
        params = {"lang": LANG, "max": MAX_PER_CATEGORY, "apikey": API_KEY}
    else:
        endpoint = "https://gnews.io/api/v4/search"
        params = {"q": query, "lang": LANG, "max": MAX_PER_CATEGORY, "apikey": API_KEY}

    ultimo_error = None
    for intento in range(1, intentos + 1):
        resp = requests.get(endpoint, params=params, timeout=30)
        if resp.status_code == 429:
            espera = 2 * intento
            print(f"  Límite de velocidad alcanzado, reintentando en {espera}s...")
            time.sleep(espera)
            ultimo_error = "429 Too Many Requests"
            continue
        try:
            resp.raise_for_status()
        except requests.exceptions.RequestException as e:
            ultimo_error = str(e)
            break
        articulos = resp.json().get("articles", [])
        limpios = []
        for a in articulos:
            limpios.append({
                "title": a.get("title") or "Sin título",
                "description": a.get("description") or "",
                "url": a.get("url") or "#",
                "source": (a.get("source") or {}).get("name", "Fuente desconocida"),
                "publishedAt": a.get("publishedAt") or "",
            })
        return limpios

    raise requests.exceptions.RequestException(ultimo_error or "fallo desconocido")


def construir_datos():
    datos = {"generated_at": datetime.now(timezone.utc).isoformat(), "categorias": {}}
    claves = list(CATEGORIAS.items())
    for i, (clave, (etiqueta, query)) in enumerate(claves):
        print(f"Consultando categoría: {etiqueta}...")
        try:
            articulos = obtener_noticias(query)
        except requests.exceptions.RequestException as e:
            print(f"  Aviso: fallo al traer '{etiqueta}': {e}")
            articulos = []
        datos["categorias"][clave] = {"label": etiqueta, "articles": articulos}
        if i < len(claves) - 1:
            time.sleep(PAUSA_ENTRE_PETICIONES)
    return datos


PLANTILLA = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>UNI — Noticias</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
:root {
  --bg: #F2F2F0;
  --surface: #FFFFFF;
  --ink: #17171A;
  --muted: #75757D;
  --border: #E2E2E0;
  --accent-soft: #EAEAE8;
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  background: var(--bg);
  color: var(--ink);
  font-family: 'Inter', Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
}
a { color: inherit; }
button { font-family: inherit; }

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.001ms !important;
    transition-duration: 0.001ms !important;
  }
}

header {
  position: sticky;
  top: 0;
  z-index: 20;
  background: rgba(242,242,240,0.88);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--border);
  padding-bottom: 14px;
}
.masthead {
  max-width: 720px;
  margin: 0 auto;
  padding: 26px 20px 10px;
  text-align: center;
}
.masthead .logo {
  font-size: 1.9rem;
  font-weight: 800;
  letter-spacing: -0.03em;
  margin: 0;
  animation: caer 0.6s ease;
}
.masthead .tagline {
  font-size: 0.78rem;
  color: var(--muted);
  margin: 4px 0 18px;
}
@keyframes caer {
  from { opacity: 0; transform: translateY(-8px); }
  to { opacity: 1; transform: translateY(0); }
}

nav.tabs {
  position: relative;
  display: inline-flex;
  gap: 2px;
  background: var(--accent-soft);
  border: 1px solid var(--border);
  border-radius: 999px;
  padding: 4px;
}
nav.tabs .pill-indicator {
  position: absolute;
  top: 4px;
  bottom: 4px;
  border-radius: 999px;
  background: var(--ink);
  transition: left 0.35s cubic-bezier(0.65,0,0.35,1), width 0.35s cubic-bezier(0.65,0,0.35,1);
  z-index: 0;
}
nav.tabs button {
  position: relative;
  z-index: 1;
  background: transparent;
  border: none;
  color: var(--muted);
  font-size: 0.84rem;
  font-weight: 500;
  padding: 8px 17px;
  border-radius: 999px;
  cursor: pointer;
  transition: color 0.25s ease;
}
nav.tabs button.active { color: #fff; }
nav.tabs button:hover:not(.active) { color: var(--ink); }

.search-wrap {
  max-width: 720px;
  margin: 12px auto 0;
  padding: 0 20px;
  display: flex;
  justify-content: center;
}
.search-pill {
  display: flex;
  align-items: center;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 999px;
  overflow: hidden;
  transition: box-shadow 0.25s ease;
}
.search-pill.open { box-shadow: 0 4px 14px rgba(0,0,0,0.06); }
.search-icon {
  background: none;
  border: none;
  width: 38px;
  height: 38px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--muted);
  flex-shrink: 0;
}
.search-icon svg { width: 16px; height: 16px; }
.search-pill input {
  border: none;
  outline: none;
  background: transparent;
  font-size: 0.85rem;
  width: 0;
  padding: 0;
  transition: width 0.3s ease, padding 0.3s ease;
  color: var(--ink);
}
.search-pill.open input {
  width: 220px;
  padding: 9px 14px 9px 0;
}

.subchips {
  max-width: 720px;
  margin: 14px auto 0;
  padding: 0 20px;
  display: none;
  gap: 6px;
  overflow-x: auto;
  scrollbar-width: none;
}
.subchips::-webkit-scrollbar { display: none; }
.subchips.visible { display: flex; }
.subchips button {
  flex-shrink: 0;
  background: var(--surface);
  border: 1px solid var(--border);
  color: var(--muted);
  font-size: 0.78rem;
  padding: 6px 13px;
  border-radius: 999px;
  cursor: pointer;
  transition: all 0.2s ease;
}
.subchips button:hover { border-color: var(--ink); color: var(--ink); }
.subchips button.active { border-color: var(--ink); color: #fff; background: var(--ink); }

main {
  max-width: 860px;
  margin: 30px auto 90px;
  padding: 0 20px;
}

.hero {
  perspective: 900px;
  margin-bottom: 34px;
}
.hero-card {
  background: var(--ink);
  color: #fff;
  border-radius: 22px;
  padding: 32px;
  position: relative;
  overflow: hidden;
  transform-style: preserve-3d;
  transition: transform 0.15s ease-out;
  opacity: 0;
  animation: entrarHero 0.6s ease forwards 0.1s;
}
@keyframes entrarHero {
  from { opacity: 0; transform: translateY(16px); }
  to { opacity: 1; transform: translateY(0); }
}
.hero-tag {
  display: inline-block;
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.6px;
  color: #C9C9CC;
  border: 1px solid #3A3A40;
  padding: 4px 10px;
  border-radius: 999px;
  margin-bottom: 16px;
}
.hero-card h2 {
  font-size: 1.6rem;
  line-height: 1.3;
  margin: 0 0 12px;
  font-weight: 700;
  letter-spacing: -0.01em;
}
.hero-card h2 a { text-decoration: none; color: #fff; }
.hero-card h2 a:hover { text-decoration: underline; text-underline-offset: 4px; }
.hero-card p {
  color: #B9B9BE;
  font-size: 0.92rem;
  line-height: 1.6;
  margin: 0 0 18px;
  max-width: 560px;
}
.hero-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 0.76rem;
  color: #9C9CA1;
}

.section-title {
  font-size: 0.95rem;
  font-weight: 600;
  margin: 30px 0 14px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.section-title .count {
  font-size: 0.7rem;
  color: var(--muted);
  font-weight: 400;
  background: var(--accent-soft);
  padding: 2px 8px;
  border-radius: 999px;
}

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 12px;
}

.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 18px;
  display: flex;
  flex-direction: column;
  gap: 9px;
  opacity: 0;
  transform: translateY(14px);
  transition: opacity 0.55s ease, transform 0.55s ease, border-color 0.2s ease, box-shadow 0.2s ease;
  transition-delay: var(--delay, 0s);
}
.card.visible { opacity: 1; transform: translateY(0); }
.card:hover {
  border-color: #CFCFCC;
  box-shadow: 0 10px 22px rgba(0,0,0,0.06);
  transform: translateY(-3px);
}
.card .cat-tag {
  font-size: 0.65rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--muted);
  font-weight: 600;
}
.card h3 {
  font-size: 0.98rem;
  font-weight: 600;
  line-height: 1.4;
  margin: 0;
}
.card h3 a { text-decoration: none; }
.card h3 a:hover { text-decoration: underline; text-underline-offset: 3px; }
.card p.desc {
  font-size: 0.84rem;
  color: var(--muted);
  margin: 0;
  line-height: 1.5;
  flex-grow: 1;
}
.card .meta-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 0.71rem;
  color: var(--muted);
  margin-top: 2px;
  gap: 8px;
  flex-wrap: wrap;
}

.fav-btn {
  background: var(--accent-soft);
  border: 1px solid var(--border);
  color: var(--muted);
  font-size: 0.73rem;
  padding: 5px 11px;
  border-radius: 999px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  transition: border-color 0.2s ease, color 0.2s ease, background 0.2s ease;
}
.fav-btn:hover { border-color: var(--ink); color: var(--ink); }
.fav-btn.on { color: #fff; background: var(--ink); border-color: var(--ink); }
.fav-btn .star {
  display: inline-block;
  transition: transform 0.4s cubic-bezier(0.34,1.56,0.64,1);
}
.fav-btn.pop .star { transform: rotate(-25deg) scale(1.35); }

.empty-state {
  text-align: center;
  padding: 50px 20px;
  color: var(--muted);
  font-size: 0.88rem;
  opacity: 0;
  animation: entrarHero 0.4s ease forwards;
}

footer {
  text-align: center;
  padding: 30px 20px 50px;
  color: var(--muted);
  font-size: 0.72rem;
}

/* ---------- Chatbot ---------- */
#chatToggle {
  position: fixed;
  bottom: 22px;
  right: 22px;
  width: 54px;
  height: 54px;
  border-radius: 50%;
  background: var(--ink);
  color: #fff;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8px 20px rgba(0,0,0,0.18);
  z-index: 50;
  transition: transform 0.2s ease;
}
#chatToggle:hover { transform: scale(1.06); }
#chatToggle svg { width: 22px; height: 22px; }
#chatToggle .icon-close { display: none; }
#chatToggle.open .icon-chat { display: none; }
#chatToggle.open .icon-close { display: block; }

#chatPanel {
  position: fixed;
  bottom: 88px;
  right: 22px;
  width: 340px;
  max-width: calc(100vw - 32px);
  height: 460px;
  max-height: calc(100vh - 130px);
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 20px;
  box-shadow: 0 16px 40px rgba(0,0,0,0.14);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  z-index: 50;
  opacity: 0;
  transform: translateY(14px) scale(0.97);
  pointer-events: none;
  transform-origin: bottom right;
  transition: opacity 0.22s ease, transform 0.22s cubic-bezier(0.34,1.56,0.64,1);
}
#chatPanel.open {
  opacity: 1;
  transform: translateY(0) scale(1);
  pointer-events: auto;
}
.chat-header {
  padding: 16px 18px;
  border-bottom: 1px solid var(--border);
}
.chat-header .titulo { font-weight: 700; font-size: 0.92rem; }
.chat-header .subtitulo { font-size: 0.72rem; color: var(--muted); margin-top: 2px; }

.chat-body {
  flex: 1;
  overflow-y: auto;
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.msg {
  max-width: 82%;
  font-size: 0.83rem;
  line-height: 1.5;
  padding: 9px 13px;
  border-radius: 14px;
  opacity: 0;
  transform: translateY(6px);
  animation: msgIn 0.25s ease forwards;
}
@keyframes msgIn { to { opacity: 1; transform: translateY(0); } }
.msg.bot { align-self: flex-start; background: var(--accent-soft); color: var(--ink); border-bottom-left-radius: 4px; }
.msg.user { align-self: flex-end; background: var(--ink); color: #fff; border-bottom-right-radius: 4px; }

.msg.typing { display: flex; gap: 4px; align-items: center; padding: 12px 14px; }
.msg.typing span {
  width: 6px; height: 6px; border-radius: 50%;
  background: var(--muted);
  animation: rebotar 1s infinite ease-in-out;
}
.msg.typing span:nth-child(2) { animation-delay: 0.15s; }
.msg.typing span:nth-child(3) { animation-delay: 0.3s; }
@keyframes rebotar {
  0%, 60%, 100% { transform: translateY(0); opacity: 0.5; }
  30% { transform: translateY(-4px); opacity: 1; }
}

.chat-input-row {
  display: flex;
  gap: 8px;
  padding: 12px;
  border-top: 1px solid var(--border);
}
.chat-input-row input {
  flex: 1;
  border: 1px solid var(--border);
  border-radius: 999px;
  padding: 9px 14px;
  font-size: 0.83rem;
  outline: none;
  transition: border-color 0.2s ease;
}
.chat-input-row input:focus { border-color: var(--ink); }
.chat-input-row button {
  background: var(--ink);
  color: #fff;
  border: none;
  border-radius: 999px;
  width: 36px;
  height: 36px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: transform 0.15s ease;
}
.chat-input-row button:hover { transform: scale(1.06); }
.chat-input-row button svg { width: 15px; height: 15px; }
</style>
</head>
<body>

<header>
  <div class="masthead">
    <h1 class="logo">UNI</h1>
    <p class="tagline">actualizado __FECHA__</p>
    <nav class="tabs" id="mainTabs">
      <div class="pill-indicator" id="pillIndicator"></div>
    </nav>
  </div>
  <div class="search-wrap">
    <div class="search-pill" id="searchPill">
      <button class="search-icon" id="searchIcon" aria-label="Buscar">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
      </button>
      <input type="text" id="buscador" placeholder="Buscar por palabra clave...">
    </div>
  </div>
  <div class="subchips" id="subchips"></div>
</header>

<main id="main"></main>

<footer>UNI · fuente: GNews API · generado automáticamente cada día</footer>

<button id="chatToggle" aria-label="Abrir asistente">
  <svg class="icon-chat" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/></svg>
  <svg class="icon-close" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
</button>

<div id="chatPanel">
  <div class="chat-header">
    <div class="titulo">Asistente UNI</div>
    <div class="subtitulo">Pregúntame por noticias o cómo usar el sitio</div>
  </div>
  <div class="chat-body" id="chatBody"></div>
  <div class="chat-input-row">
    <input type="text" id="chatInput" placeholder="Escribe tu pregunta...">
    <button id="chatSend" aria-label="Enviar">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
    </button>
  </div>
</div>

<script id="datos-noticias" type="application/json">__DATOS_JSON__</script>
<script>
const DATA = JSON.parse(document.getElementById('datos-noticias').textContent);
const UNI_KEYS = ['inversion','negocios','tecnologia','geopolitica','cripto','medicina'];
const FAV_KEY = 'uni_favoritos';

let vista = 'inicio';
let subcategoria = 'todas';
let filtro = '';

const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('visible');
      observer.unobserve(entry.target);
    }
  });
}, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });

function leerFavoritos() {
  try { return JSON.parse(localStorage.getItem(FAV_KEY)) || []; }
  catch { return []; }
}
function guardarFavoritos(favs) {
  localStorage.setItem(FAV_KEY, JSON.stringify(favs));
}
function esFavorito(url) {
  return leerFavoritos().some(f => f.url === url);
}
function toggleFavorito(articulo, btnEl) {
  let favs = leerFavoritos();
  if (esFavorito(articulo.url)) {
    favs = favs.filter(f => f.url !== articulo.url);
  } else {
    favs.push(articulo);
  }
  guardarFavoritos(favs);
  btnEl.classList.add('pop');
  render();
}

function formatearFecha(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  return d.toLocaleString('es-ES', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' });
}

function moverIndicador(btn) {
  const indicator = document.getElementById('pillIndicator');
  if (!btn) { indicator.style.width = '0px'; return; }
  indicator.style.left = btn.offsetLeft + 'px';
  indicator.style.width = btn.offsetWidth + 'px';
}

function construirTabs() {
  const tabs = document.getElementById('mainTabs');
  const items = [
    { id: 'inicio', label: 'Inicio' },
    { id: 'uni', label: 'UNI' },
    { id: 'favoritos', label: 'Guardadas' },
  ];
  tabs.querySelectorAll('button').forEach(b => b.remove());
  let activo = null;
  items.forEach(it => {
    const btn = document.createElement('button');
    btn.textContent = it.label;
    btn.className = vista === it.id ? 'active' : '';
    btn.onclick = () => { vista = it.id; subcategoria = 'todas'; render(); };
    tabs.appendChild(btn);
    if (vista === it.id) activo = btn;
  });
  requestAnimationFrame(() => moverIndicador(activo));
}

function construirSubchips() {
  const cont = document.getElementById('subchips');
  cont.innerHTML = '';
  if (vista !== 'uni') { cont.classList.remove('visible'); return; }
  cont.classList.add('visible');

  const todasBtn = document.createElement('button');
  todasBtn.textContent = 'Todas';
  todasBtn.className = subcategoria === 'todas' ? 'active' : '';
  todasBtn.onclick = () => { subcategoria = 'todas'; render(); };
  cont.appendChild(todasBtn);

  UNI_KEYS.forEach(k => {
    const btn = document.createElement('button');
    btn.textContent = DATA.categorias[k].label;
    btn.className = subcategoria === k ? 'active' : '';
    btn.onclick = () => { subcategoria = k; render(); };
    cont.appendChild(btn);
  });
}

function tarjetaFavBtn(a) {
  const fav = esFavorito(a.url);
  const btn = document.createElement('button');
  btn.className = 'fav-btn' + (fav ? ' on' : '');
  btn.innerHTML = `<span class="star">${fav ? '★' : '☆'}</span> ${fav ? 'Guardada' : 'Guardar'}`;
  btn.onclick = () => toggleFavorito(a, btn);
  return btn;
}

function tarjeta(a, indice) {
  const div = document.createElement('div');
  div.className = 'card';
  div.style.setProperty('--delay', Math.min((indice % 6) * 0.06, 0.36) + 's');
  div.innerHTML = `
    <div class="cat-tag">${a._catLabel || ''}</div>
    <h3><a href="${a.url}" target="_blank" rel="noopener">${a.title}</a></h3>
    <p class="desc">${a.description || ''}</p>
    <div class="meta-row"><span>${a.source} · ${formatearFecha(a.publishedAt)}</span></div>
  `;
  div.querySelector('.meta-row').appendChild(tarjetaFavBtn(a));
  observer.observe(div);
  return div;
}

function hero(a) {
  const wrap = document.createElement('div');
  wrap.className = 'hero';
  const card = document.createElement('div');
  card.className = 'hero-card';
  card.innerHTML = `
    <span class="hero-tag">${a._catLabel || 'Destacada'}</span>
    <h2><a href="${a.url}" target="_blank" rel="noopener">${a.title}</a></h2>
    <p>${a.description || ''}</p>
    <div class="hero-meta"><span>${a.source} · ${formatearFecha(a.publishedAt)}</span></div>
  `;
  const favBtn = tarjetaFavBtn(a);
  favBtn.style.marginLeft = '10px';
  card.querySelector('.hero-meta').appendChild(favBtn);
  wrap.appendChild(card);

  wrap.addEventListener('mousemove', (e) => {
    const rect = card.getBoundingClientRect();
    const x = (e.clientX - rect.left) / rect.width - 0.5;
    const y = (e.clientY - rect.top) / rect.height - 0.5;
    card.style.transform = `rotateY(${x * 5}deg) rotateX(${-y * 5}deg)`;
  });
  wrap.addEventListener('mouseleave', () => {
    card.style.transform = 'rotateY(0deg) rotateX(0deg)';
  });
  return wrap;
}

function seccion(titulo, articulos, indiceInicial) {
  const wrap = document.createElement('div');
  const h = document.createElement('div');
  h.className = 'section-title';
  h.innerHTML = `${titulo} <span class="count">${articulos.length}</span>`;
  wrap.appendChild(h);

  if (articulos.length === 0) {
    const vacio = document.createElement('div');
    vacio.className = 'empty-state';
    vacio.textContent = 'No hay noticias que mostrar aquí por ahora.';
    wrap.appendChild(vacio);
    return wrap;
  }

  const grid = document.createElement('div');
  grid.className = 'grid';
  articulos.forEach((a, i) => grid.appendChild(tarjeta(a, (indiceInicial || 0) + i)));
  wrap.appendChild(grid);
  return wrap;
}

function aplicarFiltro(lista) {
  if (!filtro.trim()) return lista;
  const f = filtro.trim().toLowerCase();
  return lista.filter(a =>
    (a.title || '').toLowerCase().includes(f) ||
    (a.description || '').toLowerCase().includes(f) ||
    (a.source || '').toLowerCase().includes(f)
  );
}

function render() {
  construirTabs();
  construirSubchips();
  const main = document.getElementById('main');
  main.innerHTML = '';

  if (vista === 'inicio') {
    const arts = aplicarFiltro(DATA.categorias['inicio'].articles.map(a => ({ ...a, _catLabel: 'Inicio' })));
    if (arts.length === 0) {
      main.appendChild(seccion('Últimas noticias', []));
    } else {
      main.appendChild(hero(arts[0]));
      main.appendChild(seccion('Más noticias', arts.slice(1)));
    }
  } else if (vista === 'uni') {
    if (subcategoria === 'todas') {
      UNI_KEYS.forEach(k => {
        const arts = aplicarFiltro(DATA.categorias[k].articles.map(a => ({ ...a, _catLabel: DATA.categorias[k].label })));
        main.appendChild(seccion(DATA.categorias[k].label, arts));
      });
    } else {
      const arts = aplicarFiltro(DATA.categorias[subcategoria].articles.map(a => ({ ...a, _catLabel: DATA.categorias[subcategoria].label })));
      if (arts.length === 0) {
        main.appendChild(seccion(DATA.categorias[subcategoria].label, []));
      } else {
        main.appendChild(hero(arts[0]));
        main.appendChild(seccion('Más en ' + DATA.categorias[subcategoria].label, arts.slice(1)));
      }
    }
  } else if (vista === 'favoritos') {
    main.appendChild(seccion('Tus noticias guardadas', aplicarFiltro(leerFavoritos())));
  }
}

document.getElementById('buscador').addEventListener('input', (e) => {
  filtro = e.target.value;
  render();
});

const searchIcon = document.getElementById('searchIcon');
const searchPill = document.getElementById('searchPill');
searchIcon.addEventListener('click', () => {
  searchPill.classList.toggle('open');
  if (searchPill.classList.contains('open')) {
    document.getElementById('buscador').focus();
  }
});

window.addEventListener('resize', () => {
  const activo = document.querySelector('nav.tabs button.active');
  moverIndicador(activo);
});

render();

/* ---------- Chatbot ---------- */
const CHATBOT_ENDPOINT = "__CHATBOT_ENDPOINT__";

function construirContextoNoticias() {
  const lineas = [];
  for (const clave in DATA.categorias) {
    const cat = DATA.categorias[clave];
    cat.articles.forEach(a => {
      lineas.push(`- [${cat.label}] ${a.title}`);
    });
  }
  return lineas.slice(0, 60).join('\\n');
}
const CONTEXTO_NOTICIAS = construirContextoNoticias();

const chatToggle = document.getElementById('chatToggle');
const chatPanel = document.getElementById('chatPanel');
const chatBody = document.getElementById('chatBody');
const chatInput = document.getElementById('chatInput');
const chatSend = document.getElementById('chatSend');

let chatAbierto = false;
let chatIniciado = false;

function agregarMensaje(texto, tipo) {
  const div = document.createElement('div');
  div.className = 'msg ' + tipo;
  div.textContent = texto;
  chatBody.appendChild(div);
  chatBody.scrollTop = chatBody.scrollHeight;
  return div;
}

function mostrarTyping() {
  const div = document.createElement('div');
  div.className = 'msg bot typing';
  div.innerHTML = '<span></span><span></span><span></span>';
  chatBody.appendChild(div);
  chatBody.scrollTop = chatBody.scrollHeight;
  return div;
}

async function enviarPregunta() {
  const texto = chatInput.value.trim();
  if (!texto) return;
  agregarMensaje(texto, 'user');
  chatInput.value = '';

  if (!CHATBOT_ENDPOINT || CHATBOT_ENDPOINT.indexOf('REEMPLAZA') !== -1) {
    agregarMensaje('El asistente todavía no está configurado. Falta conectar la URL del Worker de Cloudflare.', 'bot');
    return;
  }

  const typingEl = mostrarTyping();
  try {
    const resp = await fetch(CHATBOT_ENDPOINT, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: texto, context: CONTEXTO_NOTICIAS }),
    });
    const data = await resp.json();
    typingEl.remove();
    agregarMensaje(data.reply || 'No pude generar una respuesta.', 'bot');
  } catch (e) {
    typingEl.remove();
    agregarMensaje('No pude conectar con el asistente. Intenta de nuevo en un momento.', 'bot');
  }
}

chatToggle.addEventListener('click', () => {
  chatAbierto = !chatAbierto;
  chatToggle.classList.toggle('open', chatAbierto);
  chatPanel.classList.toggle('open', chatAbierto);
  if (chatAbierto) {
    chatInput.focus();
    if (!chatIniciado) {
      chatIniciado = true;
      agregarMensaje('¡Hola! Puedo recomendarte noticias de la página o resolver dudas sobre cómo usarla. ¿En qué te ayudo?', 'bot');
    }
  }
});
chatSend.addEventListener('click', enviarPregunta);
chatInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') enviarPregunta(); });
</script>
</body>
</html>
"""


def main():
    datos = construir_datos()
    fecha_legible = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")

    html_final = PLANTILLA.replace("__FECHA__", fecha_legible)
    html_final = html_final.replace("__DATOS_JSON__", json.dumps(datos, ensure_ascii=False))
    html_final = html_final.replace("__CHATBOT_ENDPOINT__", CHATBOT_ENDPOINT)

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_final)

    total = sum(len(c["articles"]) for c in datos["categorias"].values())
    print(f"index.html generado con {total} noticias en {len(datos['categorias'])} categorías.")


if __name__ == "__main__":
    main()

