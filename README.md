# UNI — Página de noticias automática

Esta página se actualiza sola cada día usando GitHub Actions y la API de GNews.

**Secciones:**
- **Inicio** — titulares generales recientes.
- **UNI** — inversión, negocios, tecnología, política internacional, cripto y medicina (con chips para filtrar por subtema).
- **Buscador** — filtra en tiempo real por palabra clave en cualquier sección.
- **Guardadas** — marca noticias con "☆ Guardar" para leerlas después. Se guardan en el navegador de cada visitante (localStorage), así que son privadas de cada dispositivo, no compartidas entre visitantes.

## Pasos para ponerla en marcha

### 1. Crea el repositorio
1. Ve a https://github.com/new
2. Ponle un nombre, por ejemplo `mis-noticias`.
3. Que sea **público** (necesario para usar GitHub Pages gratis).
4. Crea el repositorio.

### 2. Sube estos archivos
Sube toda esta carpeta al repositorio, manteniendo la estructura:
```
.github/workflows/actualizar-noticias.yml
scripts/generar_noticias.py
README.md
```
Puedes hacerlo arrastrando los archivos en la interfaz web de GitHub ("Add file" → "Upload files"), o con git desde tu computadora.

### 3. Agrega tu API key como "secret"
1. En tu repositorio, ve a **Settings** → **Secrets and variables** → **Actions**.
2. Clic en **New repository secret**.
3. Nombre: `GNEWS_API_KEY`
4. Valor: pega tu API key de GNews.
5. Guarda.

Esto mantiene tu key privada; nunca queda visible en el código.

### 4. Activa GitHub Pages
1. Ve a **Settings** → **Pages**.
2. En "Source", elige la rama `main` y la carpeta `/ (root)`.
3. Guarda. GitHub te dará una URL tipo `https://tu-usuario.github.io/mis-noticias/`.

### 5. Ejecuta el workflow por primera vez
1. Ve a la pestaña **Actions** de tu repositorio.
2. Selecciona "Actualizar noticias" en la lista de workflows.
3. Clic en **Run workflow** (botón a la derecha) para generar el primer `index.html`.
4. Espera 1-2 minutos y revisa tu URL de GitHub Pages.

A partir de ahí, el workflow se ejecutará solo todos los días a las 08:00 UTC (puedes cambiar la hora editando el `cron` en el archivo `.yml`) y también lo puedes disparar manualmente cuando quieras desde la pestaña Actions.

## Personalización

- **Idioma:** cambia `NEWS_LANG` en el `.yml` (`es`, `en`, etc.)
- **Categorías de UNI:** edita el diccionario `CATEGORIAS` en `scripts/generar_noticias.py` — puedes cambiar las palabras de búsqueda de cada tema o agregar una categoría nueva (solo agrega una línea con clave, etiqueta y query).
- **Cantidad de noticias por categoría:** cambia `MAX_PER_CATEGORY` en el script (máximo 10 en el plan gratuito de GNews).
- **Horario:** el `cron` en el `.yml` (formato: minuto hora día mes día-semana, siempre en UTC).

## Límite de la API

El plan gratuito de GNews permite 100 peticiones al día. Cada ejecución del workflow hace 7 peticiones (Inicio + las 6 categorías de UNI), así que sobra margen incluso corriéndolo varias veces al día.
