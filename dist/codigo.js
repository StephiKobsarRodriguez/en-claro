// Visor de archivos: el texto se inserta con textContent, nunca como HTML.
const descriptions = {
  'dist/index.html': 'Estructura de la aplicación, vistas y metodología.',
  'dist/app.js': 'Selección de candidaturas, filtros, infografías, fuentes y estado compartido en la URL.',
  'dist/style.css': 'Diseño visual, estilos de impresión y adaptación a móvil.',
  'dist/data.json': 'Catálogo editorial con propuestas, fuentes, localizadores e indicadores.',
  'README.md': 'Guía para ejecutar el proyecto, entender su arquitectura y subirlo a GitHub.',
  'scripts/check_data.py': 'Comprueba referencias, fuentes e indicadores del catálogo con Python estándar.',
  'scripts/package_repo.py': 'Genera este visor de archivos y el ZIP portable del repositorio.',
  '.github/workflows/checks.yml': 'Comprobaciones automáticas de JavaScript y datos al subir cambios a GitHub.',
  '.github/workflows/pages.yml': 'Publica la carpeta dist en GitHub Pages.',
  '.gitignore': 'Exclusiones de archivos locales y paquetes generados.',
  'dist/codigo.html': 'Página del visor del código.',
  'dist/codigo.js': 'Lógica del visor del código.'
};
let sources = {};
let current = '';

function openFile(name) {
  if (!Object.hasOwn(sources, name)) return;
  current = name;
  document.getElementById('filename').textContent = name;
  document.getElementById('description').textContent = descriptions[name] || '';
  document.getElementById('code').textContent = sources[name];
  document.getElementById('copy').disabled = false;
  document.getElementById('status').textContent = '';
  document.querySelectorAll('#files button').forEach(button => {
    const selected = button.textContent === name;
    button.classList.toggle('active', selected);
    button.setAttribute('aria-pressed', String(selected));
  });
  history.replaceState(null, '', '#file=' + encodeURIComponent(name));
}

document.getElementById('copy').addEventListener('click', async () => {
  try {
    await navigator.clipboard.writeText(sources[current]);
    document.getElementById('status').textContent = 'Archivo copiado.';
  } catch {
    document.getElementById('status').textContent = 'Selecciona el texto del archivo para copiarlo.';
  }
});

(async function loadSources() {
  try {
    const response = await fetch('source-files.json');
    if (!response.ok) throw new Error('No se pudieron cargar los archivos.');
    sources = await response.json();
    for (const name of Object.keys(sources)) {
      const button = document.createElement('button');
      button.textContent = name;
      button.addEventListener('click', () => openFile(name));
      document.getElementById('files').appendChild(button);
    }
    const requested = new URLSearchParams(location.hash.slice(1)).get('file');
    openFile(Object.hasOwn(sources, requested) ? requested : 'dist/app.js');
  } catch (error) {
    document.getElementById('filename').textContent = 'No se pudo cargar el código';
    document.getElementById('status').textContent = error.message;
  }
})();
