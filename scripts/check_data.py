"""Valida relaciones del catálogo. No vuelve a leer los PDF."""
import json
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]


def https(url, label):
    parsed = urlsplit(url or '')
    assert parsed.scheme == 'https' and parsed.hostname, f'Fuente inválida: {label}'


def reading(value, label):
    assert isinstance(value, dict), f'Falta la lectura del pasaje: {label}'
    assert value.get('label') in ('fascista', 'dudosa', 'no_fascista'), f'Lectura desconocida: {label}'
    indicators = value.get('indicators')
    assert isinstance(indicators, list) and all(type(item) is int and 1 <= item <= 7 for item in indicators), f'Indicadores inválidos: {label}'
    note = value.get('note', '')
    assert isinstance(note, str), f'Nota inválida: {label}'
    if value['label'] == 'no_fascista':
        assert indicators == [] and note == '', f'Una lectura no fascista no lleva indicador ni nota: {label}'
    elif value['label'] == 'dudosa':
        assert indicators and note.strip(), f'Una lectura dudosa necesita indicador y nota: {label}'
    else:
        assert note.strip(), f'Una lectura fascista necesita nota: {label}'
        strong = {3, 4, 5, 6, 7}
        assert strong.intersection(indicators) or ({1, 2} <= set(indicators)), f'Un fascista no puede apoyarse solo en el indicador 1 o solo en el 2: {label}'


def warning(value, label):
    if not value:
        return
    assert isinstance(value, dict), f'Advertencia inválida: {label}'
    angles = ('pluralism', 'inclusion', 'welfare')
    for key in angles:
        assert isinstance(value.get(key, ''), str), f'Advertencia inválida: {label}'
    assert any(value.get(key, '').strip() for key in angles), f'La advertencia no explica el pasaje: {label}'
    banner = value.get('banner')
    assert isinstance(banner, list) and banner and all(isinstance(part, str) and part.strip() for part in banner), f'El banner de la advertencia no explica el caso: {label}'


def main():
    data = json.loads((ROOT / 'dist/data.json').read_text(encoding='utf-8'))
    parties = [party['id'] for party in data['parties']]
    ministries = [item['id'] for item in data['ministries']]
    proposals = [item['id'] for item in data['proposals']]
    for label, values in [('candidaturas', parties), ('ministerios', ministries), ('propuestas', proposals)]:
        assert len(values) == len(set(values)), f'Identificadores duplicados en {label}'
    assert 'topics' not in data, 'El catálogo todavía usa temas editoriales'
    province_ids = [item['id'] for item in data['provinces']]
    seen = []
    for community in data['communities']:
        assert community['name'].strip()
        for province in community['provinces']:
            assert province in province_ids, f'Provincia desconocida: {province}'
            seen.append(province)
    assert sorted(seen) == sorted(province_ids), 'Las comunidades no cubren todas las circunscripciones'
    assert len(seen) == len(set(seen)), 'Una circunscripción está en dos comunidades'
    by_party = {party['id']: party for party in data['parties']}
    cells = set()
    for proposal in data['proposals']:
        assert proposal['party'] in by_party, f'Candidatura desconocida: {proposal["id"]}'
        assert proposal['ministry'] in ministries, f'Ministerio desconocido: {proposal["id"]}'
        key = (proposal['party'], proposal['ministry'])
        assert key not in cells, f'Celda duplicada: {key}'
        cells.add(key)
        https(proposal['url'], proposal['id'])
        assert proposal['summary'].strip() and proposal['title'].strip()
        assert proposal['locator'].strip()
        if proposal['status'] == 'contrastada':
            assert proposal['excerpt'].strip(), f'Ficha sin cita: {proposal["id"]}'
            reading(proposal.get('reading'), proposal['id'])
            warning(proposal.get('warning'), proposal['id'])
            assert proposal['authoring'] in ('extracto', 'modelo')
            if proposal['page'] is None:
                assert proposal['locator'].startswith('Apartado'), f'Ficha web sin apartado: {proposal["id"]}'
            else:
                assert type(proposal['page']) is int and proposal['page'] > 0
        elif proposal['status'] == 'sin-medida':
            assert not proposal.get('excerpt')
            assert proposal['page'] is None
            assert not proposal.get('reading'), f'Lectura en una ficha sin cita: {proposal["id"]}'
            assert not proposal.get('warning'), f'Advertencia en una ficha sin cita: {proposal["id"]}'
            assert not proposal.get('also'), f'Un segundo programa en una ficha sin cita: {proposal["id"]}'
        else:
            raise AssertionError(f'Estado desconocido: {proposal["id"]}')
        also = proposal.get('also')
        if also:
            https(also['url'], proposal['id'])
            assert also['excerpt'].strip() and also['locator'].strip() and also['title'].strip()
            reading(also.get('reading'), proposal['id'] + ' · segundo programa')
    for party in data['parties']:
        program = party['program']
        owned = [item for item in data['proposals'] if item['party'] == party['id']]
        if program is None:
            assert not party['reviewed'], f'Sin programa y marcada como revisada: {party["id"]}'
            assert not owned, f'Fichas sin documento: {party["id"]}'
            continue
        assert program['status'] in ('completo', 'avance', 'bases')
        assert program['title'].strip()
        https(program['url'], party['id'])
        if program.get('also'):
            https(program['also'], party['id'])
        if party['reviewed']:
            assert program['retrieved'], f'Falta la fecha de lectura: {party["id"]}'
            assert {item['ministry'] for item in owned} == set(ministries), f'Faltan ministerios: {party["id"]}'
        else:
            assert not owned, f'Fichas de un documento no contrastado: {party["id"]}'
    manifest_path = ROOT / 'sources' / 'manifest.json'
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        for source in manifest['programs']:
            assert source['party'] in by_party, f'El manifiesto cita una candidatura ajena: {source["party"]}'
            https(source['url'], source['party'])
    for metric in data['metrics']:
        assert metric['ministry'] in ministries
        assert metric['max'] > 0 and metric['unit'] and metric['note']
        seen_parties = set()
        for value in metric['values']:
            assert value['party'] not in seen_parties, 'Valor duplicado en un indicador'
            seen_parties.add(value['party'])
            origin = next(item for item in data['proposals'] if item['id'] == value['proposal'])
            assert origin['party'] == value['party']
            assert origin['status'] == 'contrastada'
            assert 0 <= value['value'] <= metric['max']
            assert value['context'].strip()
    contrasted = sum(item['status'] == 'contrastada' for item in data['proposals'])
    print(f'Catálogo válido: {len(parties)} candidaturas, {len(ministries)} ministerios y {contrasted} fichas contrastadas.')


if __name__ == '__main__':
    main()
