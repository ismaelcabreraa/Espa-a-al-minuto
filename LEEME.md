# España al Minuto: cómo publicarla

Web estática de titulares de España que se regenera sola cada hora con GitHub Actions y se publica gratis en GitHub Pages. No usa cookies, analítica ni servicios de terceros, así que no necesita banner de cookies.

## 1. Rellena tus datos (obligatorio antes de publicar)

Abre `config.json` y cambia:

- `titular`: tu nombre y apellidos, NIF, domicilio y correo de contacto. La LSSI obliga a mostrarlos en el aviso legal. Si no quieres publicar tu domicilio particular, puedes usar un apartado de correos o una dirección profesional, pero debe ser una dirección donde puedas recibir notificaciones.
- `sitio.url`: la dirección final de la web, por ejemplo `https://tuusuario.github.io/espana-al-minuto` o tu dominio propio.

Mientras queden campos entre corchetes, el generador avisará de que las páginas legales no son válidas.

## 2. Súbela a GitHub

1. Crea una cuenta en github.com si no la tienes.
2. Crea un repositorio público llamado `espana-al-minuto`.
3. Sube todo el contenido de esta carpeta, incluida la carpeta oculta `.github`. Lo más sencillo es usar «Add file → Upload files» en la web del repositorio y arrastrar los archivos.
4. En el repositorio, ve a **Settings → Pages** y en «Source» elige **GitHub Actions**.
5. Ve a la pestaña **Actions**, abre «Actualizar y publicar» y pulsa **Run workflow**. En un par de minutos la web estará en la dirección que indique.

A partir de ahí se actualiza sola cada hora. GitHub puede retrasar unos minutos las ejecuciones programadas, y las pausa si el repositorio pasa 60 días sin actividad; en ese caso basta con volver a activarlas en Actions.

## 3. Dominio propio (opcional)

Compra un dominio (por ejemplo, un `.es`) y en **Settings → Pages → Custom domain** escríbelo. GitHub te indicará los registros DNS que debes crear en tu proveedor de dominio. Después, actualiza `sitio.url` en `config.json`.

## 4. Date de alta en Google

1. Entra en Google Search Console (search.google.com/search-console) y añade tu web.
2. Verifica que es tuya. Con dominio propio, mediante un registro DNS; con github.io, subiendo el archivo HTML de verificación que te da Google a la carpeta `estaticos/`.
3. En «Sitemaps» envía `sitemap.xml`.

## 5. Fuentes de noticias

Están en `config.json` → `fuentes`. Cada una tiene el medio, la sección y la dirección de su RSS. Si una fuente deja de funcionar, la web sigue generándose con las demás, y el registro de la ejecución en la pestaña Actions indica cuál falló. Puedes quitar o añadir fuentes editando esa lista. Las secciones válidas son: `general`, `politica`, `economia`, `sociedad`, `deportes`, `internacional`, `cultura` y `canarias`.

La web solo muestra titular, medio, hora y enlace, sin copiar texto ni imágenes de las noticias. Si un medio te pide que lo retires, quítalo de la lista.

## 6. Antes de añadir publicidad o analítica

- Si añades Google Analytics, AdSense o similar, tendrás que poner un banner de cookies que permita aceptar y rechazar con la misma facilidad, y actualizar las páginas de privacidad y cookies.
- Las condiciones de GitHub Pages no permiten usarlo para sitios principalmente comerciales. Si quieres monetizar la web, publícala en Cloudflare Pages o Netlify, que funcionan igual con la carpeta `_site`, y actualiza el proveedor de alojamiento en `plantillas/privacidad.html` y `plantillas/cookies.html`.

## Probarla en tu ordenador

Con Python 3.9 o superior instalado:

```
python3 build.py
```

Genera la web en la carpeta `_site`. Abre `_site/index.html` en el navegador.

## Estructura

| Archivo | Para qué sirve |
|---|---|
| `config.json` | Tus datos, la URL de la web y las fuentes RSS |
| `build.py` | Descarga los RSS y genera la web en `_site/` |
| `plantillas/` | Textos de aviso legal, privacidad y cookies |
| `estaticos/` | Estilos, script de filtros y favicon |
| `.github/workflows/actualizar.yml` | Ejecución automática cada hora y publicación |
