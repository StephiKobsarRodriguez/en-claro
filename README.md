# En claro · Comparador de programas

Web estática interactiva para comparar programas de las generales de España del 29/11/2026 por ministerio y por comunidad autónoma. Lectura de documentos: 22/11/2026.

## Qué demuestra este proyecto

- Visualización interactiva de información documental con tres vistas complementarias.
- Modelado de propuestas, candidaturas, ministerios, comunidades e indicadores en JSON.
- Estado de navegación compartible mediante la URL.
- Trazabilidad de cada resumen a una fuente primaria y un localizador.
- Tratamiento explícito de datos pendientes y diferencias entre indicadores.
- Diseño adaptable, controles de formulario nativos y detalle en un diálogo modal.

Es un prototipo de frontend en **HTML, CSS y JavaScript**, sin framework ni backend. La web no llama a ningún modelo: lee fichas ya escritas en `data.json`. Python sirve el sitio en local, valida el catálogo y, con `scripts/extract_cards.py`, vuelve a leer los PDF oficiales. Esa lectura usa `pypdf`. Si existe la variable `OPENAI_API_KEY`, el mismo script pide al modelo la síntesis de cada ficha; si no existe, publica el fragmento literal. La clave no se guarda en el repositorio. El modelo se elige con `OPENAI_MODEL` y, si hace falta, `OPENAI_BASE_URL`.

## Ejecutar

```bash
python scripts/package_repo.py
python -m http.server 8000 --directory dist --bind 0.0.0.0
```

Abre http://localhost:8000. No requiere instalación de paquetes ni backend de cálculo.

## Arquitectura

```text
en-claro/
├── dist/
│   ├── index.html          # Aplicación y contenido de metodología
│   ├── app.js              # Filtros, ministerios, fuentes y estado en URL
│   ├── style.css           # Estilos responsive y de impresión
│   ├── data.json           # Catálogo de fichas contrastadas
│   ├── codigo.html         # Visor de archivos
│   ├── codigo.js           # Lógica del visor
│   ├── source-files.json   # Instantánea generada de los archivos
│   └── repositorio.zip     # Descarga generada del proyecto
├── scripts/
│   ├── check_data.py       # Validación de integridad del catálogo
│   ├── extract_cards.py    # Lectura de programas y redacción de fichas
│   ├── ministries.py       # Ministerios vigentes y comunidades
│   └── package_repo.py     # Generación del visor y del ZIP
├── sources/
│   ├── manifest.json       # URL oficial de cada programa localizado
│   └── review.json         # Incidencias de lectura, sin pasar a la web
├── .github/workflows/
│   └── checks.yml          # Comprobaciones en GitHub Actions
├── .gitignore
└── README.md
```

`app.js` carga `data.json` y mantiene la selección de candidaturas, ministerio, comunidad y visualización. Al elegir una comunidad se listan todas las candidaturas que concurren en alguna de sus circunscripciones, incluidas Ceuta y Melilla. Los enlaces del detalle salen de la ficha. El fragmento de la URL permite reproducir una comparación sin almacenar un perfil de usuario.

`codigo.js` carga una instantánea de los archivos y los presenta mediante `textContent`. El ZIP de entrega contiene los archivos portables; la identidad del alojamiento actual se conserva en el checkout de Sites.

## Archivos

- `dist/index.html`: estructura y metodología.
- `dist/style.css`: diseño y adaptación móvil.
- `dist/app.js`: filtro por comunidad autónoma, ministerios, fichas con cita y página, vías de actuación, cifras, vista compartida e impresión.
- `dist/data.json`: candidaturas, comunidades, ministerios y fichas. Una ficha contrastada guarda la cita literal y la página.
- `scripts/`: utilidades locales sin dependencias externas.
- `.github/workflows/checks.yml`: comprobaciones al hacer push o abrir una pull request.

El catálogo contiene 66 denominaciones electorales, incluidas coaliciones y variantes. Se obtienen de votomunicipal.es a partir del BOE-A-2026-23103. Datos normalizados CC BY 4.0; atribución y enlace al BOE dentro de la aplicación. No se ha auditado la normalización completa frente al BOE.

La comparación usa los 22 ministerios del Real Decreto 829/2023 consolidado. Las fichas se generan solo para candidaturas con un documento propio localizado en [sources/manifest.json](sources/manifest.json). El resto aparece en el filtro y queda pendiente: no se afirma que carezcan de programa. Si el documento leído no contiene una cita verificable para un ministerio, la celda dice que no hay un punto contrastado en ese documento.

Cada ficha contrastada enlaza a la fuente primaria. En PDF, `page` es la página física del archivo. La cita tiene que aparecer en esa página. No se redistribuyen los PDF: `sources/raw/` y `sources/pages/` quedan fuera del repositorio.

No se asignan puntuaciones ideológicas ni recomendaciones de voto. Los indicadores numéricos solo entran cuando comparten unidad y condiciones; no se asignan ceros a datos ausentes. Esta edición no publica indicadores numéricos.

Las cifras mostradas son compromisos documentales, no mediciones de cumplimiento ni evaluaciones de viabilidad. El alcance y las condiciones pueden diferir aunque el número sea idéntico.

## Ampliar contenido

Añade la URL oficial en `sources/manifest.json` y ejecuta:

```bash
pip install pypdf
python scripts/extract_cards.py
```

Puedes pasar uno o varios identificadores de candidatura para releer solo esos programas. Con `OPENAI_API_KEY`, el script pide al modelo título y síntesis en castellano y descarta la ficha si la cita no está en la página. Sin esa clave, la ficha muestra el fragmento literal. Actualiza la fecha de lectura. No incorpores un programa antiguo como si fuera el del 29N.

El código del frontend no solicita información personal. Las visitas se cuentan con GoatCounter, sin cookies y sin identificar a quien entra. El enlace compartido contiene únicamente las candidaturas seleccionadas, el ministerio, la vista y la comunidad. Las fuentes tipográficas se solicitan a Google Fonts y tienen fuentes locales de reserva.

## Publicación

Sitio estático `dist/` en Sites; audiencia privada. El ZIP de código se descarga desde el pie de la web.

## Comprobaciones

Requiere Node.js para comprobar la sintaxis y Python 3 para revisar el catálogo:

```bash
node --check dist/app.js
node --check dist/codigo.js
python scripts/check_data.py
```

El validador comprueba identificadores únicos, ministerios, que cada circunscripción pertenezca a una sola comunidad, fuentes HTTPS, citas en las fichas contrastadas y una celda por candidatura y ministerio en los documentos ya leídos. **No vuelve a abrir los PDF**, ni sustituye las pruebas de interacción o una auditoría de accesibilidad.

GitHub Actions ejecuta estas comprobaciones automáticamente. Las pruebas completas en navegador y la revisión visual siguen pendientes; no se presentan como realizadas.

## Subir a tu GitHub

1. Descarga y descomprime el ZIP. Abre `en-claro` en VS Code.
2. Crea un repositorio vacío en GitHub, sin añadir allí README o `.gitignore`.
3. Desde la terminal de esa carpeta, ejecuta:

```bash
git init -b main
git add .
git commit -m "Initial commit: En claro political manifesto comparator"
git remote add origin https://github.com/TU_USUARIO/en-claro.git
git push -u origin main
```

Configura tu nombre y correo de Git localmente si aún no lo has hecho. Si el repositorio ya existe, conserva su historial y utiliza su remoto en vez de inicializar otro.

Antes de presentar una demo pública en el portfolio, despliega tu propia copia: el alojamiento actual de Sites es privado. La carpeta publicable es `dist/`; ejecuta `python scripts/package_repo.py` antes de desplegar para regenerar el visor y la descarga. No hace falta desplegar Python.

Descripción breve sugerida para GitHub:

> Comparador visual de programas electorales por ministerio y comunidad autónoma, con fichas citadas página a página. Prototipo en HTML, CSS y JavaScript.

## Próximas mejoras

- Localizar el programa oficial de las candidaturas que siguen pendientes.
- Incorporar pruebas de interacción en navegador y revisión de accesibilidad.
- Separar la lógica del frontend en módulos pequeños conforme crezca la aplicación.
- Añadir cifras solo cuando la unidad y las condiciones permitan compararlas.
