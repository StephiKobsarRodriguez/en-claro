"""Genera el visor y el ZIP del código portable, sin identidad del alojamiento."""
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
FILES = [
    'README.md', '.gitignore', '.github/workflows/checks.yml',
    '.github/workflows/pages.yml',
    'dist/index.html', 'dist/app.js', 'dist/style.css', 'dist/data.json',
    'dist/codigo.html', 'dist/codigo.js',
    'scripts/check_data.py', 'scripts/package_repo.py',
    'scripts/ministries.py', 'scripts/extract_cards.py',
    'sources/manifest.json', 'sources/review.json', 'sources/titles.json',
]

def main():
    sources = {name: (ROOT / name).read_text(encoding='utf-8') for name in FILES}
    snapshot = ROOT / 'dist/source-files.json'
    snapshot.write_text(json.dumps(sources, ensure_ascii=False, indent=2), encoding='utf-8')
    archive = ROOT / 'dist/repositorio.zip'
    with ZipFile(archive, 'w', ZIP_DEFLATED) as package:
        for name in FILES + ['dist/source-files.json']:
            package.write(ROOT / name, 'en-claro/' + name)
    with ZipFile(archive) as package:
        assert package.testzip() is None
    print(f'ZIP y visor actualizados: {len(FILES)} archivos fuente.')

if __name__ == '__main__':
    main()
