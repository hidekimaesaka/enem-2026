import json,re,pathlib,collections
root=pathlib.Path(__file__).resolve().parents[1]
items=json.loads((root/'public/questions.json').read_text(encoding='utf8'))
assert len({q['id'] for q in items})==len(items)
topics=collections.Counter(t for q in items for t in q['topics'])
assert len(topics)==9 and min(topics.values())>=5,topics
for q in items:
    assert q['id']==f"{q['year']}-{q['index']}"
    assert q['year'] in range(2019,2024) and 136<=q['index']<=180
    assert len(q['alternatives'])==5
    assert [a['letter'] for a in q['alternatives']]==list('ABCDE')
    assert q['correctAlternative'] in 'ABCDE'
    assert len(q['explanation'])>=2
    for text in [q['context'],q['alternativesIntroduction']]+[a['text'] or '' for a in q['alternatives']]+q['explanation']:
        assert '�' not in text,(q['id'],'replacement character')
        assert 'https://enem.dev/' not in text,(q['id'],'remote image')
    alltext=' '.join(q['explanation'])
    mentioned=re.findall(r'[Aa]lternativa\s+([A-E])\b',alltext)
    assert all(x==q['correctAlternative'] for x in mentioned),(q['id'],mentioned,q['correctAlternative'])
    urls=re.findall(r'/questions/\d+/\d+/[^\s)]+',q['context']+' '+q['alternativesIntroduction']+' '+' '.join((a['text'] or '')+' '+(a['file'] or '') for a in q['alternatives']))
    for url in urls:assert (root/'public'/url.lstrip('/')).is_file(),(q['id'],url)
print('Validated',len(items),'questions;',dict(topics))
