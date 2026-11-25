"""Construye las fichas del catálogo a partir de los programas oficiales.

Descarga cada PDF del manifiesto, elige pasajes con el léxico ministerial y
redacta la tarjeta. Si existe OPENAI_API_KEY, la redacción la hace ese modelo
(OPENAI_MODEL, por defecto gpt-4o-mini; OPENAI_BASE_URL opcional). Si no hay
clave, la ficha publica el fragmento literal, sin añadir medidas. El título
El título lo escribe getTitle(): resume el pasaje en una frase y en la lengua del propio texto. El resultado queda en sources/titles.json.

Una ficha contrastada solo entra en el catálogo si la cita aparece en la
página indicada. Si el documento no aporta un pasaje verificable, la celda
queda como sin punto contrastado en ese documento.
"""
import hashlib
import html
import json
import os
import re
import ssl
import subprocess
import sys
import unicodedata
import urllib.request
from datetime import date
from pathlib import Path

from pypdf import PdfReader

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ministries import COMMUNITIES, INSTRUMENTS, MINISTRIES

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'dist' / 'data.json'
MANIFEST = ROOT / 'sources' / 'manifest.json'
RAW = ROOT / 'sources' / 'raw'
PAGES = ROOT / 'sources' / 'pages'
REVIEW = ROOT / 'sources' / 'review.json'
TODAY = date.today().isoformat()
ABSENT = {
    'completo': 'Este programa no recoge ningún punto contrastado sobre este ministerio.',
    'bases': 'En las bases del programa localizadas no hay ningún punto contrastado sobre este ministerio.',
    'avance': 'En el avance localizado no hay un punto contrastado sobre este ministerio.',
}


def fold(text):
    text = unicodedata.normalize('NFKD', text or '')
    text = ''.join(char for char in text if not unicodedata.combining(char))
    return text.lower()


def norm(text):
    text = (text or '').replace('\u00ad', '')
    return re.sub(r'\s+', ' ', text).strip()


def slug(party_id):
    return re.sub(r'[^A-Za-z0-9._-]+', '_', party_id)


def keyword_score(text, keywords):
    folded = fold(norm(text))
    total = 0
    longest = 0
    for keyword in keywords:
        needle = fold(keyword).strip()
        if not needle:
            continue
        if len(needle) <= 4:
            count = len(re.findall(r'(?<!\w)' + re.escape(needle) + r'(?!\w)', folded))
        else:
            count = folded.count(needle)
        if count:
            total += count
            longest = max(longest, len(needle))
    return total, longest


def acceptable(total, longest):
    return total >= 2 or (total >= 1 and longest >= 8)


def paragraphs(page_text):
    compact = re.sub(r'[ \t]+', ' ', page_text or '')
    compact = re.sub(r'\n{2,}', '\n\n', compact)
    chunks = [norm(chunk) for chunk in compact.split('\n\n')]
    chunks = [chunk for chunk in chunks if len(chunk) > 45]
    if len(chunks) > 1:
        return chunks
    lines = [norm(line) for line in (page_text or '').splitlines() if norm(line)]
    blocks = []
    buffer = []
    for line in lines:
        buffer.append(line)
        if len(' '.join(buffer)) > 380:
            blocks.append(' '.join(buffer))
            buffer = []
    if buffer:
        blocks.append(' '.join(buffer))
    return [block for block in blocks if len(block) > 45]


def usable(text):
    if 'desarrollo web' in fold(text) or 'servicios profesionales de informatica' in fold(text):
        return False
    letters = re.findall(r'[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]', text)
    if len(letters) < 40:
        return False
    if text.count('…') + text.count('.') > max(12, len(text) // 8):
        return False
    return True


def download(url, dest):
    if dest.exists() and dest.stat().st_size > 1000:
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ['curl', '-fsSL', '--http1.1', '--retry', '2', '-A', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36', '-H', 'Accept: application/pdf,*/*', '-e', 'https://www.google.com/', '-o', str(dest), url],
        check=True,
        timeout=180,
    )


def html_text(raw):
    raw = html.unescape(raw).replace('\xa0', ' ').replace('\u00ad', '')
    raw = re.sub(r'[ \t]+', ' ', raw)
    raw = re.sub(r' *\n *', '\n', raw)
    return re.sub(r'\n{3,}', '\n\n', raw).strip()


def read_html(raw):
    raw = re.sub(r'(?is)<footer\b[^>]*>.*?</footer>', ' ', raw)
    raw = re.sub(r'(?is)<(script|style|noscript|svg)[^>]*>.*?</\1>', ' ', raw)
    raw = re.sub(r'(?i)<br\s*/?>', '\n', raw)
    raw = re.sub(r'(?i)<h([1-3])[^>]*>', r'\n@@H@@', raw)
    raw = re.sub(r'(?i)</h[1-3]>', '@@/H@@\n\n', raw)
    raw = re.sub(r'(?i)</(p|li|tr|div|h[1-6])>', '\n\n', raw)
    text = re.sub(r'<[^>]+>', ' ', raw)
    pages = []
    for chunk in text.split('@@H@@')[1:]:
        heading, body = chunk.split('@@/H@@', 1) if '@@/H@@' in chunk else (chunk, '')
        heading, body = norm(heading), html_text(body)
        sentences = len(re.findall(r'[.!?]', body))
        if sentences < 2 and re.search(r'\b0[1-9]\b', body):
            continue
        if len(re.findall(r'[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]', body)) < 80:
            continue
        pages.append({
            'page': len(pages) + 1,
            'section': heading[:180] or f'Apartado {len(pages) + 1}',
            'text': f'{heading}\n\n{body}',
        })
    if not pages:
        whole = html_text(re.sub(r'@@/?H@@', '\n', text))
        pages.append({'page': 1, 'section': 'Página del programa', 'text': whole})
    return pages


def read_pages(path):
    reader = PdfReader(str(path))
    if reader.is_encrypted:
        reader.decrypt('')
    pages = []
    for index, page in enumerate(reader.pages, start=1):
        pages.append({'page': index, 'text': page.extract_text() or ''})
    return pages


def policy_children(raw, url):
    path = url.split('?', 1)[0].split('#', 1)[0]
    if not path.rstrip('/').endswith(('/politiques', '/politicas', '/programa', '/program')):
        return []
    base = path if path.endswith('/') else path + '/'
    found = []
    for link in re.findall(r'href=["\'](https?://[^"\']+)["\']', raw):
        link = link.split('#', 1)[0].split('?', 1)[0]
        if not link.startswith(base):
            continue
        rest = link[len(base):].strip('/')
        if not rest or '/' in rest:
            continue
        link = link if link.endswith('/') else link + '/'
        if link not in found:
            found.append(link)
    return found if len(found) >= 3 else []


def load_pages(party_id, url, kind='pdf'):
    cached = PAGES / f'{slug(party_id)}.json'
    if cached.exists():
        return json.loads(cached.read_text(encoding='utf-8'))
    RAW.mkdir(parents=True, exist_ok=True)
    dest = RAW / f'{slug(party_id)}.{"html" if kind == "html" else "pdf"}'
    download(url, dest)
    if kind == 'html':
        raw = dest.read_text(encoding='utf-8', errors='replace')
        children = policy_children(raw, url)
        if children:
            pages = []
            for index, link in enumerate(children, start=1):
                child = RAW / f'{slug(party_id)}-{index}.html'
                download(link, child)
                sections = [
                    item for item in read_html(child.read_text(encoding='utf-8', errors='replace'))
                    if not any(token in fold(item['section']) for token in ('militant', 'newsletter', 'cookie', 'en parlem'))
                ]
                pages.append({
                    'page': index,
                    'section': sections[0]['section'] if sections else f'Apartado {index}',
                    'text': '\n\n'.join(item['text'] for item in sections),
                    'url': link,
                })
        else:
            pages = read_html(raw)
    else:
        pages = read_pages(dest)
    PAGES.mkdir(parents=True, exist_ok=True)
    cached.write_text(json.dumps(pages, ensure_ascii=False), encoding='utf-8')
    return pages


def header_keys(pages):
    counts = {}
    for page in pages:
        seen = set()
        for paragraph in paragraphs(page['text']):
            if not usable(paragraph):
                continue
            key = fold(paragraph)[:180]
            if key in seen:
                continue
            seen.add(key)
            counts[key] = counts.get(key, 0) + 1
    limit = max(4, int(len(pages) * 0.3))
    return {key for key, count in counts.items() if count >= limit}


def candidates(pages, ministry, blocked):
    found = []
    for page in pages:
        page_text = page['text']
        for paragraph in paragraphs(page_text):
            if not usable(paragraph):
                continue
            key = fold(paragraph)[:180]
            if key in blocked:
                continue
            scored = []
            for item in MINISTRIES:
                total, longest = keyword_score(paragraph, item['keywords'])
                scored.append((item['id'], total, longest, total * 10 + longest))
            ranked = sorted(scored, key=lambda row: row[3], reverse=True)
            winner, runner = ranked[0], ranked[1]
            broad = sum(1 for row in scored if acceptable(row[1], row[2]))
            ambiguous = runner[3] > 0 and winner[3] < runner[3] * 1.35
            if winner[0] != ministry['id'] or broad >= 6 or ambiguous or not acceptable(winner[1], winner[2]):
                continue
            folded = fold(paragraph)
            if ministry['id'] == 'inclusion' and 'seguridad social' in folded and any(
                token in folded for token in ('codigo postal', 'n.i.f', 'numero de identificacion')
            ):
                continue
            total = winner[3]
            found.append({
                'page': page['page'],
                'text': paragraph,
                'page_text': page_text,
                'score': total,
                'section': page.get('section'),
                'url': page.get('url'),
            })
    found.sort(key=lambda item: item['score'], reverse=True)
    unique = []
    seen = set()
    for item in found:
        marker = (item['page'], fold(item['text'])[:180])
        if marker in seen:
            continue
        seen.add(marker)
        unique.append(item)
    return unique[:4]


def on_topic(span, ministry):
    total, longest = keyword_score(span, ministry['keywords'])
    return acceptable(total, longest)


def literal_span(paragraph, page_text, ministry):
    page_norm = norm(page_text)
    page_fold = fold(page_norm)
    text = norm(paragraph)
    if fold(text) not in page_fold:
        return None
    parts = re.split(r'(?<=[.!?])\s+', text)
    options = []
    for index, part in enumerate(parts):
        piece = part.strip()
        if len(piece) < 40:
            continue
        span = piece
        if index + 1 < len(parts) and len(span) < 280:
            span = f'{piece} {parts[index + 1].strip()}'
        options.append(span)
    options.append(text)
    for span in options:
        span = clip(span)
        start = re.search(r'[A-ZÁÉÍÓÚÑ¿¡]', span)
        if start and 0 < start.start() < 90:
            span = span[start.start():].strip()
        if len(span) < 40 or fold(span) not in page_fold or not on_topic(span, ministry):
            continue
        return span
    return None


def clip(text, limit=420):
    text = norm(text)
    if len(text) <= limit:
        return text
    cut = text[:limit]
    stop = max(cut.rfind('. '), cut.rfind('; '))
    if stop > 160:
        return cut[:stop + 1].strip()
    return cut.rsplit(' ', 1)[0].strip()


def instruments(text):
    folded = fold(text)
    tags = []
    for tag, words in INSTRUMENTS.items():
        if any(fold(word) in folded for word in words):
            tags.append(tag)
    return tags


def verify(excerpt, page_text):
    return bool(excerpt) and fold(norm(excerpt)) in fold(norm(page_text))


def first_sentence(text):
    parts = re.split(r'(?<=[.!?])\s+', norm(text))
    sentence = parts[0] if parts else norm(text)
    if len(sentence) > 140:
        sentence = sentence[:140].rsplit(' ', 1)[0]
    return sentence


_VERB = re.compile(
    r'(?i)(?<!\w)(?:es|son|está|están|sea|sean|será|serán|hay|tiene|tienen|tendrá|tendrán|'
    r'puede|pueden|podrá|podrán|debe|deben|'
    r'\w+(?:remos|rán|irá|ará|erá))(?!\w)'
)
_INFINITIVE = re.compile(r'(?i)^(?:\w+(?:ar|er|ir))\b')


def _has_verb(text):
    return bool(_VERB.search(text) or _INFINITIVE.match(text.strip()))


def _agree_adjective(adjective, subject):
    word = adjective.lower()
    feminine = bool(re.search(r'(?:as|a)\b', subject.lower()))
    if feminine and word.endswith('os'):
        return word[:-2] + 'as'
    if feminine and word.endswith('o'):
        return word[:-1] + 'a'
    return word


def _plain_sentence(sentence):
    """Deja la medida en una frase: sujeto, condiciones y verbo. Sin la explicación posterior."""
    sentence = sentence.strip(' .')
    subject = re.split(r'\s+que\s+', sentence, maxsplit=1)[0]

    def fines(match):
        return _agree_adjective(match.group(1), subject)

    sentence = re.sub(r'\bque se dediquen a fines (\w+)', fines, sentence, flags=re.I)
    sentence = re.sub(r',?\s*o que se pongan en ', ' o en ', sentence, flags=re.I)
    sentence = re.sub(r'\ba un precio\b', 'a precio', sentence, flags=re.I)
    sentence = re.sub(r'\bserán objeto de este nuevo impuesto\b', 'pagarán un nuevo impuesto', sentence, flags=re.I)
    sentence = re.sub(r'\bserá objeto de este nuevo impuesto\b', 'pagará un nuevo impuesto', sentence, flags=re.I)
    if ':' in sentence:
        left, right = sentence.split(':', 1)
        right = right.strip()
        if 18 <= len(right) and len(left) <= 70 and _has_verb(right):
            sentence = right
    sentence = sentence.replace('ﬁ', 'fi').replace('ﬂ', 'fl')
    sentence = re.sub(r',\s+que estén\b', ' que estén', sentence, flags=re.I)
    sentence = re.sub(r',\s+(?:un|una|unha|el|la|los|las|y|o|e)\s*$', '', sentence, flags=re.I)
    sentence = re.sub(r'\s+', ' ', sentence).strip(' ,;')
    if len(sentence) <= 180 or not _has_verb(sentence):
        return sentence
    verb = _VERB.search(sentence) or _INFINITIVE.match(sentence)
    tail = sentence[verb.end():]
    cut = len(tail)
    for mark in (' utilizando ', ' asegurando ', ' garantizando ', ' con el fin de ', ' para '):
        at = tail.find(mark)
        if at >= 24:
            cut = min(cut, at)
    if cut < len(tail):
        sentence = (sentence[:verb.end()] + tail[:cut]).strip(' ,;')
    if len(sentence) > 180:
        head = sentence[:180]
        stop = max(head.rfind(', '), head.rfind('; '))
        if stop >= verb.end() + 12:
            sentence = head[:stop]
    return sentence.strip(' ,;')


def _claim_sentences(source):
    source = re.sub(r'(\w)-\s+(\w)', r'\1\2', source)
    source = re.sub(r'(\w)\s+-\s+(\w)', r'\1\2', source)
    source = re.sub(r'\s*[●•▪‣✓]\s*', '. ', source)
    source = re.sub(r'\s+\d+\.\s*$', '', source)
    parts = [part.strip() for part in re.split(r'(?<=[.!?])\s+', source) if part.strip()]
    claims = []
    for part in parts:
        for piece in _split_clauses(part):
            piece = re.sub(r'^[º°.\-\d\s]+', '', piece).strip(' -–—')
            if len(piece) < 18 or _spaced_letters(piece):
                plain = _plain_run(piece) if piece else ''
                piece = plain or piece
            if len(piece) < 18 or piece.endswith('-'):
                continue
            if re.match(r'^(?:su objetivo|esto significa|porque|de este modo|en este sentido|por ello|además)\b', piece, re.I):
                continue
            if piece[:1].islower() and not _has_verb(piece):
                continue
            claims.append(piece)
    return claims


def title_key(text):
    return hashlib.sha1((text or '').encode('utf-8')).hexdigest()[:12]


def load_title_cache():
    path = ROOT / 'sources' / 'titles.json'
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding='utf-8'))


def ask_title(text, ministry=None):
    """Pide al modelo un título que resume el pasaje, sin añadir medidas."""
    key = os.environ.get('OPENAI_API_KEY', '').strip()
    if not key:
        return ''
    ministry_name = ministry.get('name') if isinstance(ministry, dict) else (ministry or '')
    payload = {
        'model': os.environ.get('OPENAI_MODEL', 'gpt-4o-mini'),
        'temperature': 0,
        'messages': [
            {
                'role': 'system',
                'content': (
                    'Interpretas un pasaje de un programa electoral y escribes un solo título que resume la medida, '
                    'en la misma lengua del pasaje. Si el texto está en catalán, valenciano, gallego, euskera u otra lengua, '
                    'el título se queda en esa lengua y no se traduce al castellano. Una frase completa y gramatical, '
                    'de menos de 140 caracteres. No copies el inicio del pasaje ni lo cortes a medias. No añadas medidas, '
                    'cifras ni sujetos que no estén en el texto. Sin comillas ni prefijos. '
                    'El ejemplo solo ilustra la forma del resumen, no la lengua: '
                    '«Las viviendas que se dediquen a fines turísticos, que estén vacías, o que se pongan '
                    'en alquiler a un precio abusivo serán objeto de este nuevo impuesto» se resume como '
                    '«Las viviendas turísticas que estén vacías o en alquiler a precio abusivo pagarán un nuevo impuesto».'
                ),
            },
            {
                'role': 'user',
                'content': f'Ministerio: {ministry_name}\n\nPasaje:\n{text}',
            },
        ],
    }
    base = os.environ.get('OPENAI_BASE_URL', 'https://api.openai.com/v1').rstrip('/')
    request = urllib.request.Request(
        base + '/chat/completions',
        data=json.dumps(payload).encode('utf-8'),
        headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'},
    )
    secure = ssl.create_default_context()
    try:
        import certifi
        secure.load_verify_locations(certifi.where())
    except Exception:
        pass
    with urllib.request.urlopen(request, timeout=90, context=secure) as response:
        body = json.loads(response.read().decode('utf-8'))
    title = body['choices'][0]['message']['content'].strip().strip('"').strip('«»')
    title = re.sub(r'\s+', ' ', title)
    return title[:180].strip()


def getTitle(text, ministry=None):
    """Título que resume el pasaje, en la lengua del propio texto. Si ya está en la caché, se reutiliza."""
    source = norm(text)
    if not source:
        return ''
    cached = load_title_cache().get(title_key(text))
    if cached:
        return cached
    try:
        drafted = ask_title(source, ministry)
    except Exception:
        drafted = ''
    return drafted or _fit_title(first_sentence(source), 140)


def _split_clauses(text):
    function = {'de', 'del', 'la', 'el', 'los', 'las', 'en', 'a', 'al', 'un', 'una', 'su', 'sus', 'por', 'para', 'con', 'y', 'o', 'e', 'u', 'que', 'se', 'lo', 'le'}
    starters = {'todos', 'todas', 'todo', 'toda', 'por', 'en', 'con', 'para', 'sobre', 'desde', 'entre', 'segun', 'durante', 'tras', 'hacia', 'hasta', 'como', 'que', 'si', 'cada', 'este', 'esta', 'estos', 'estas', 'sus', 'su'}
    pieces = []
    buf = []
    for token in text.split(' '):
        core = re.sub(r'[^\w]', '', token, flags=re.U)
        prev = re.sub(r'[^\w]', '', buf[-1], flags=re.U) if buf else ''
        heading = (
            buf and len(core) > 2 and core[:1].isupper() and core[1:2].islower()
            and prev[:1].islower() and prev.lower() not in function
        )
        new_sentence = buf and core[:1].isupper() and core.lower() in {'el', 'la', 'los', 'las', 'un', 'una'} and len(prev) > 3 and prev.lower() not in starters and prev.lower() not in function
        caps_break = buf and re.fullmatch(r'[A-ZÁÉÍÓÚÜÑ]{2,}', prev) and core[:1].isupper() and core[1:2].islower()
        if heading or caps_break or new_sentence:
            pieces.append(' '.join(buf))
            buf = [token]
        else:
            buf.append(token)
    if buf:
        pieces.append(' '.join(buf))
    return pieces


def _spaced_letters(text):
    words = [re.sub(r'[^\w]', '', word, flags=re.U) for word in text.split(' ') if re.search(r'\w', word)]
    if len(words) < 6:
        return False
    singles = sum(1 for word in words if len(word) == 1)
    return singles / len(words) > 0.35


def _plain_run(text):
    tokens = text.split(' ')
    run = []
    best = []
    for token in tokens:
        core = re.sub(r'[^\w]', '', token, flags=re.U)
        small = core.lower() in {'y', 'o', 'e', 'u', 'de', 'del', 'la', 'el', 'los', 'las', 'en', 'a', 'al', 'un', 'una'}
        if len(core) >= 4 or (run and small):
            run.append(token)
        else:
            if len(' '.join(run)) > len(' '.join(best)):
                best = run
            run = []
    if len(' '.join(run)) > len(' '.join(best)):
        best = run
    phrase = re.sub(r'^[\d\s.)]+', '', ' '.join(best)).strip(' ,;:-–—·')
    return phrase if len(phrase) >= 18 else ''


def _title_clause(clause):
    started_lower = clause[:1].islower()
    clause = re.sub(r'^[º°.\-\d\s]+', '', clause).strip(' -–—')
    clause = re.sub(r'\s+\d{1,4}$', '', clause).strip()
    if _spaced_letters(clause):
        clause = _plain_run(clause)
        if not clause:
            return ''
    clause = re.sub(r'^(?:y|e|o|u)\s+', '', clause, flags=re.I).strip()
    if len(clause) < 18 or (started_lower and clause[:1].islower()):
        return ''
    if clause[:1].islower():
        clause = clause[:1].upper() + clause[1:]
    if re.match(
        r'^(?:también|asimismo|además|por ello|por eso|por tanto|en este sentido|en definitiva|de este modo|esto significa)\b',
        clause, re.I,
    ):
        return ''
    if ':' in clause:
        left = clause.split(':', 1)[0].strip(' -–—')
        if 18 <= len(left) <= 92 and left[:1].isupper():
            clause = left
    clause = re.sub(r'(\w)-\s+(\w)', r'\1\2', clause)
    broken = re.search(r'\s+-\s+', clause)
    if broken and broken.start() >= 24:
        clause = clause[:broken.start()]
    title = _fit_title(clause)
    return title if len(title) >= 18 else ''


def _fit_title(title, limit=92):
    title = re.sub(r'(\w)-\s+(\w)', r'\1\2', norm(title))
    dangling = {'y', 'o', 'e', 'u', 'de', 'del', 'la', 'el', 'los', 'las', 'en', 'a', 'al', 'para', 'con', 'por', 'un', 'una', 'que', 'se', 'sus', 'su', 'ante', 'sobre', 'como'}
    if len(title) > limit:
        head = title[:limit]
        stops = [head.rfind(mark) for mark in (', ', '; ', ' y ', ' para ')]
        stops = [pos for pos in stops if pos >= 40]
        title = head[:max(stops)] if stops else head.rsplit(' ', 1)[0]
    title = title.strip(' ,;:-–—')
    words = title.split(' ')
    while len(words) > 3 and words[-1].lower().strip('.,;:') in dangling:
        words.pop()
    title = ' '.join(words).strip(' ,;:-–—')
    letters = [char for char in title if char.isalpha()]
    if letters and sum(char.isupper() for char in letters) / len(letters) > 0.7:
        small = dangling | {'que', 'se'}
        styled = []
        for index, word in enumerate(title.split(' ')):
            core = re.sub(r'^[^\w]+|[^\w]+$', '', word, flags=re.U).lower()
            if index and core in small:
                styled.append(word.lower())
            else:
                styled.append(word[:1].upper() + word[1:].lower())
        title = ' '.join(styled)
    elif title[:1].islower():
        title = title[:1].upper() + title[1:]
    return title


def ask_model(ministry, options):
    key = os.environ.get('OPENAI_API_KEY', '').strip()
    if not key:
        return None
    context = '\n\n'.join(
        f'PÁGINA {item["page"]}\n{item["text"]}' for item in options
    )
    payload = {
        'model': os.environ.get('OPENAI_MODEL', 'gpt-4o-mini'),
        'temperature': 0,
        'messages': [
            {
                'role': 'system',
                'content': (
                    'Redactas una ficha electoral solo con el texto aportado. '
                    'Responde JSON con covers (booleano), title, summary, excerpt y page. '
                    'title y summary van en castellano y no añaden medidas que no estén en el texto. '
                    'excerpt es una cita literal contigua del pasaje, en el idioma original, de menos de 400 caracteres. '
                    'page es el número de página de esa cita. '
                    'Si el texto no contiene una medida de este ministerio, covers es false y el resto va vacío.'
                ),
            },
            {
                'role': 'user',
                'content': f'Ministerio: {ministry["name"]}\n\n{context}',
            },
        ],
    }
    base = os.environ.get('OPENAI_BASE_URL', 'https://api.openai.com/v1').rstrip('/')
    request = urllib.request.Request(
        base + '/chat/completions',
        data=json.dumps(payload).encode('utf-8'),
        headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'},
    )
    secure = ssl.create_default_context()
    try:
        import certifi
        secure.load_verify_locations(certifi.where())
    except Exception:
        pass
    with urllib.request.urlopen(request, timeout=90, context=secure) as response:
        body = json.loads(response.read().decode('utf-8'))
    content = body['choices'][0]['message']['content']
    content = re.sub(r'^```(?:json)?|```$', '', content.strip(), flags=re.I | re.M).strip()
    return json.loads(content)


def absent_card(party_id, ministry, program):
    return {
        'id': f'{party_id}-{ministry["id"]}',
        'party': party_id,
        'ministry': ministry['id'],
        'status': 'sin-medida',
        'title': 'Sin punto contrastado',
        'summary': ABSENT[program['status']],
        'url': program['url'],
        'page': None,
        'locator': 'Documento consultado, sin cita verificable para este ministerio',
        'retrieved': TODAY,
    }


def contrasted_card(party_id, ministry, program, title, summary, excerpt, page, authoring, section=None, source_url=None):
    return {
        'id': f'{party_id}-{ministry["id"]}',
        'party': party_id,
        'ministry': ministry['id'],
        'status': 'contrastada',
        'title': title,
        'summary': summary,
        'excerpt': excerpt,
        'url': source_url or program['url'],
        'page': None if section else page,
        'locator': f'Apartado «{section}»' if section else f'Página {page} del PDF',
        'tags': instruments(excerpt),
        'authoring': authoring,
        'retrieved': TODAY,
    }


def build_card(party_id, ministry, program, pages, blocked, review):
    options = candidates(pages, ministry, blocked)
    if not options:
        return absent_card(party_id, ministry, program), None
    if os.environ.get('OPENAI_API_KEY', '').strip():
        try:
            drafted = ask_model(ministry, options)
        except Exception as error:
            review.append({
                'party': party_id,
                'ministry': ministry['id'],
                'reason': f'El modelo no respondió: {error}',
            })
            drafted = None
        if not drafted or not drafted.get('covers'):
            review.append({
                'party': party_id,
                'ministry': ministry['id'],
                'reason': 'El modelo no encontró una medida en los pasajes.',
            })
            return absent_card(party_id, ministry, program), None
        page = drafted.get('page')
        source = next((item for item in options if item['page'] == page), options[0])
        excerpt = norm(drafted.get('excerpt') or '')
        if not verify(excerpt, source['page_text']):
            review.append({
                'party': party_id,
                'ministry': ministry['id'],
                'reason': 'La cita del modelo no está en la página indicada.',
                'excerpt': excerpt,
                'page': page,
            })
            return absent_card(party_id, ministry, program), None
        return contrasted_card(
            party_id, ministry, program,
            getTitle(excerpt, ministry),
            norm(drafted.get('summary') or '') or excerpt,
            excerpt, source['page'], 'modelo', source.get('section'), source.get('url'),
        ), fold(source['text'])[:180]
    best = options[0]
    excerpt = literal_span(best['text'], best['page_text'], ministry)
    if not excerpt or not verify(excerpt, best['page_text']):
        review.append({
            'party': party_id,
            'ministry': ministry['id'],
            'reason': 'El fragmento elegido no coincide con la página.',
            'excerpt': excerpt,
            'page': best['page'],
        })
        return absent_card(party_id, ministry, program), None
    if best.get('section') and fold(norm(excerpt)) == fold(best['section']):
        return absent_card(party_id, ministry, program), None
    return contrasted_card(
        party_id, ministry, program, getTitle(excerpt, ministry), excerpt,
        excerpt, best['page'], 'extracto', best.get('section'), best.get('url'),
    ), fold(best['text'])[:180]


def combine_programs(primary, secondary):
    by_ministry = {card['ministry']: card for card in secondary}
    combined = []
    for card in primary:
        other = by_ministry[card['ministry']]
        if card['status'] != 'contrastada' and other['status'] == 'contrastada':
            other = dict(other)
            other['id'] = card['id']
            combined.append(other)
            continue
        if card['status'] == 'contrastada' and other['status'] == 'contrastada':
            card = dict(card)
            card['also'] = {
                'title': other['title'],
                'summary': other['summary'],
                'excerpt': other['excerpt'],
                'url': other['url'],
                'page': other['page'],
                'locator': other['locator'],
            }
        elif card['status'] == 'sin-medida' and other['status'] == 'sin-medida':
            card = dict(card)
            card['summary'] = 'Ninguno de los dos programas citados recoge un punto contrastado sobre este ministerio.'
        combined.append(card)
    return combined


def shell(data, manifest):
    by_party = {item['party']: item for item in manifest['programs']}
    data['reviewed'] = TODAY
    data['ministries'] = [
        {'id': item['id'], 'name': item['name'], 'short': item['short']}
        for item in MINISTRIES
    ]
    data.pop('topics', None)
    data['metrics'] = []
    data['proposals'] = []
    data['communities'] = COMMUNITIES
    for party in data['parties']:
        source = by_party.get(party['id'])
        party['reviewed'] = False
        if source:
            party['program'] = {
                'url': source['url'],
                'kind': source['kind'],
                'status': source['status'],
                'title': source['title'],
                'retrieved': None,
            }
            if source.get('also'):
                party['program']['also'] = source['also']
        else:
            party['program'] = None
    return data


def main():
    only = set(sys.argv[1:])
    original = json.loads(DATA.read_text(encoding='utf-8'))
    manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
    data = shell(json.loads(json.dumps(original)), manifest)
    if only:
        previous = {party['id']: party for party in original['parties']}
        for party in data['parties']:
            if party['id'] in only:
                continue
            party['program'] = previous[party['id']].get('program')
            party['reviewed'] = bool(previous[party['id']].get('reviewed'))
        data['proposals'] = [
            item for item in original.get('proposals', [])
            if item.get('ministry') and item['party'] not in only
        ]
    review = []
    page_cache = {}
    for source in manifest['programs']:
        if only and source['party'] not in only:
            continue
        party = next(item for item in data['parties'] if item['id'] == source['party'])
        print(f'Leyendo {source["party"]}…', flush=True)
        try:
            cache_key = (source['url'], source.get('kind', 'pdf'))
            if cache_key not in page_cache:
                page_cache[cache_key] = load_pages(source['party'], source['url'], source.get('kind', 'pdf'))
            pages = page_cache[cache_key]
        except Exception as error:
            review.append({'party': source['party'], 'reason': f'No se pudo leer el documento: {error}'})
            print(f'  error: {error}', flush=True)
            continue
        if not any(page['text'].strip() for page in pages):
            review.append({'party': source['party'], 'reason': 'El PDF no contiene texto extraíble.'})
            print('  sin texto extraíble', flush=True)
            continue
        party['program']['retrieved'] = TODAY
        blocked = header_keys(pages)
        used = set()
        cards = []
        for ministry in MINISTRIES:
            card, marker = build_card(source['party'], ministry, party['program'], pages, blocked | used, review)
            cards.append(card)
            if marker:
                used.add(marker)
        if source.get('also'):
            second_key = (source['also'], source.get('alsoKind', source.get('kind', 'pdf')))
            if second_key not in page_cache:
                page_cache[second_key] = load_pages(source['party'] + ' también', source['also'], second_key[1])
            second_program = dict(party['program'])
            second_program['url'] = source['also']
            second_blocked = header_keys(page_cache[second_key])
            second_used = set()
            second_cards = []
            for ministry in MINISTRIES:
                card, marker = build_card(source['party'], ministry, second_program, page_cache[second_key], second_blocked | second_used, review)
                second_cards.append(card)
                if marker:
                    second_used.add(marker)
            cards = combine_programs(cards, second_cards)
        party['reviewed'] = True
        data['proposals'] = [item for item in data['proposals'] if item['party'] != source['party']]
        data['proposals'].extend(cards)
        contrasted = sum(item['status'] == 'contrastada' for item in cards)
        print(f'  {contrasted} fichas contrastadas de {len(cards)}', flush=True)
        DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    if only and REVIEW.exists():
        kept = [
            item for item in json.loads(REVIEW.read_text(encoding='utf-8'))
            if item.get('party') not in only
        ]
        review = kept + review
    REVIEW.parent.mkdir(parents=True, exist_ok=True)
    REVIEW.write_text(json.dumps(review, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Catálogo escrito: {len(data["proposals"])} fichas, {len(review)} incidencias.')


if __name__ == '__main__':
    main()
