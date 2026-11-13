"""Validate the combined Mathematics and Natural Sciences catalogue."""
import collections
import json
import pathlib
import re

root = pathlib.Path(__file__).resolve().parents[1]
items = json.loads((root / 'public/questions.json').read_text(encoding='utf8'))
keys = json.loads((root / 'data/science-keys.json').read_text(encoding='utf8'))
coverage = json.loads((root / 'data/science-coverage.json').read_text(encoding='utf8'))
assert len(items) == 371
assert len({q['id'] for q in items}) == len(items)
assert coverage['examined'] == 225 and coverage['published'] == 224
assert [e['id'] for e in coverage['excluded']] == ['2020-135']
areas = collections.Counter(q['area'] for q in items)
assert areas == {'matematica': 147, 'biologia': 80, 'fisica': 79, 'quimica': 65}, areas
topics = collections.Counter(t for q in items for t in q['topics'])
assert len(topics) == 27 and min(topics.values()) >= 5, topics

for q in items:
    id_ = q['id']
    assert id_ == f"{q['year']}-{q['index']}"
    assert 2019 <= q['year'] <= 2023
    assert (136 <= q['index'] <= 180) if q['area'] == 'matematica' else (91 <= q['index'] <= 135)
    assert q['topics'] and len(q['topics']) == len(set(q['topics']))
    assert all(t in topics and (q['area'] == 'matematica' or t.startswith(q['area'] + ':')) for t in q['topics'])
    assert len(q['alternatives']) == 5
    assert [a['letter'] for a in q['alternatives']] == list('ABCDE')
    assert q['correctAlternative'] in 'ABCDE'
    if q['area'] != 'matematica':
        assert keys[id_] == q['correctAlternative'], id_
    assert len(q['explanation']) >= 2 and all(step.strip() for step in q['explanation'])
    assert len(q['rubric']) == 3 and all(type(v) is int and 0 <= v <= 2 for v in q['rubric'])
    assert q['rationale'].strip()
    assert q['context'].strip() and q['alternativesIntroduction'].strip()
    assert q['source'].startswith('https://download.inep.gov.br/'), id_
    for alt in q['alternatives']:
        assert alt['text'] or alt['file'], (id_, alt['letter'])
    for content in [q['context'], q['alternativesIntroduction']] + [a['text'] or '' for a in q['alternatives']] + q['explanation']:
        assert '�' not in content, (id_, 'replacement character')
        assert 'https://enem.dev/' not in content, (id_, 'remote image')
    mentioned = re.findall(r'[Aa]lternativa\s+([A-E])\b', ' '.join(q['explanation']))
    assert all(x == q['correctAlternative'] for x in mentioned), (id_, mentioned)
    all_content = q['context'] + ' ' + q['alternativesIntroduction'] + ' ' + ' '.join((a['text'] or '') + ' ' + (a['file'] or '') for a in q['alternatives'])
    for url in re.findall(r'/questions/\d+/\d+/[^\s)]+', all_content):
        assert (root / 'public' / url.lstrip('/')).is_file(), (id_, url)

print('Validated', len(items), 'questions', dict(areas), 'topics', len(topics))
