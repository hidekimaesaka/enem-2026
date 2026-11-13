"""Build the reviewed science catalogue from the 2019–2023 printed blue booklets."""
import collections
import csv
import json
import re
import shutil
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT.parent / 'enem-source' / 'public'
REVIEW = ROOT / 'data' / 'science-hints.tsv'
KEYS = ROOT / 'data' / 'science-keys.json'
OUT = ROOT / 'public' / 'questions'


def read(path):
    return json.loads(path.read_text(encoding='utf8'))


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf8')


def read_reviews():
    with REVIEW.open(encoding='utf8', newline='') as stream:
        rows = list(csv.DictReader(stream, delimiter='|'))
    assert len(rows) == 225, len(rows)
    reviews = {}
    for row in rows:
        id_ = row['id']
        assert id_ not in reviews, id_
        if row['difficulty'] == 'X':
            reviews[id_] = {'excluded': row['reasoning']}
            continue
        assert row['difficulty'] in 'EMD', id_
        reviews[id_] = {
            'area': row['area'], 'topics': [row['area'] + ':' + topic for topic in row['topics'].split(',')],
            'rubric': {'E': [1, 1, 0], 'M': [1, 1, 1], 'D': [2, 2, 1]}[row['difficulty']],
            'reasoning': row['reasoning'],
        }
    return reviews


def source_question(year, index):
    path = SOURCE / str(year) / 'questions' / str(index) / 'details.json'
    if path.exists():
        return read(path)
    return read(ROOT / 'data' / 'science-recovered.json')[f'{year}-{index}']


def localize(text, year, index):
    def replace(match):
        url = match.group(0)
        path = urlparse(url).path.lstrip('/')
        if path.endswith('broken-image.svg'):
            raise ValueError(f'Unverified image in {year}/{index}')
        source = SOURCE / path
        if not source.is_file():
            raise FileNotFoundError(source)
        dest = OUT / str(year) / str(index) / source.name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dest)
        return f'/questions/{year}/{index}/{source.name}'

    return re.sub(r'https://enem\.dev/[^\s)]+', replace, text or '')


def main():
    reviews = read_reviews()
    keys = read(KEYS)
    assert len(reviews) == 225 and len(keys) == 225
    questions = []
    excluded = []
    corrections = []
    for year in range(2019, 2024):
        for index in range(91, 136):
            id_ = f'{year}-{index}'
            review = reviews[id_]
            key = keys[id_]
            if review.get('excluded'):
                excluded.append({'id': id_, 'reason': review['excluded']})
                continue
            assert key in 'ABCDE', (id_, key)
            raw = source_question(year, index)
            if raw['correctAlternative'] != key:
                corrections.append({'id': id_, 'imported': raw['correctAlternative'], 'official': key})
            context = raw.get('context') or ''
            prompt = raw.get('alternativesIntroduction') or ''
            if id_ == '2021-119':
                context = context.replace('construção 9com resistência mecânica e à degradação)', 'construção (com resistência mecânica e resistência à degradação)')
            if id_ == '2022-109':
                context = context.replace('Oelementoiodo(I)temfunçãobiológicaeéacumulado', 'O elemento iodo (I) tem função biológica e é acumulado')
            if id_ == '2023-129':
                context = context.replace('![](https://enem.dev/broken-image.svg)', 'C₁₂H₈Cl₆', 1)
                context = context.replace('![](https://enem.dev/broken-image.svg)', 'A figura do caderno oficial apresenta uma estrutura cíclica simétrica com seis átomos de cloro ligados ao esqueleto de carbono.', 1)
            if not context:
                if id_ == '2023-99':
                    context, prompt = prompt, 'Em qual material biológico dos cães a presença desse protozoário representa risco de transmissão dessa zoonose?'
                elif id_ == '2023-102':
                    context, prompt = prompt.split(' Para se produzir', 1)
                    prompt = 'Para se produzir' + prompt
                else:
                    context, sep, prompt = prompt.rpartition('\n')
                    assert sep and context and prompt, id_
            alternatives = raw['alternatives']
            if id_ == '2022-132':
                alternatives = [dict(alt, text=(alt.get('text') or '').replace('Ompetição', 'Competição')) for alt in alternatives]
            if id_ == '2021-105':
                alternatives = [*alternatives, {'letter': 'E', 'text': 'Força para cima na carga positiva e para baixo na negativa.', 'file': None}]
            if id_ == '2023-132':
                context = re.sub(r'!\[\]\(https://enem\.dev/2023/questions/132/99a53ed4-bbd2-4aa0-9301-ee4cd640a4b6\.jpg\)', ' P₀', context)
                context = re.sub(r'!\[\]\(https://enem\.dev/2023/questions/132/2367c9cb-2c1a-4b79-b582-86fc01088ff8\.jpg\)', 'T₀', context)
                descriptions = [
                    'Gráfico com pressão constante no início do resfriamento e queda vertical ao final.',
                    'Gráfico horizontal: pressão constante enquanto a temperatura diminui.',
                    'Curva: a pressão aumenta conforme a temperatura diminui.',
                    'Reta decrescente: a pressão aumenta conforme a temperatura diminui.',
                ]
                alternatives = [dict(alt, text=descriptions[i]) if i < 4 else alt for i, alt in enumerate(alternatives)]
            assert len(alternatives) == 5 and [a['letter'] for a in alternatives] == list('ABCDE'), id_
            assert context.strip() and prompt.strip(), id_
            assert len(review['rubric']) == 3 and all(type(v) is int and 0 <= v <= 2 for v in review['rubric']), id_
            area = review['area']
            assert area in ('biologia', 'fisica', 'quimica'), id_
            assert review['topics'] and all(t.startswith(area + ':') for t in review['topics']), id_
            prepared = []
            for alt in alternatives:
                text = localize(alt.get('text'), year, index) or None
                file = localize(alt.get('file'), year, index) or None
                assert text or file, (id_, alt['letter'])
                prepared.append({'letter': alt['letter'], 'text': text, 'file': file})
            correct = next(alt for alt in prepared if alt['letter'] == key)
            conclusion = (f'Assim, a alternativa {key} — {correct["text"]} — responde ao enunciado.'
                          if correct['text'] else f'Assim, o diagrama da alternativa {key} representa o resultado.')
            explanation = [part.strip() for part in review['reasoning'].split(';') if part.strip()]
            explanation.append(conclusion)
            assert len(explanation) >= 2, id_
            questions.append({
                'id': id_, 'year': year, 'index': index, 'area': area,
                'topics': review['topics'], 'context': localize(context, year, index),
                'alternativesIntroduction': localize(prompt, year, index),
                'alternatives': prepared, 'correctAlternative': key,
                'explanation': explanation, 'rubric': review['rubric'],
                'rationale': review['reasoning'],
                'source': read(ROOT / 'data' / 'review' / f'{year}-sources.json')['examUrl'],
            })
    existing = read(ROOT / 'public' / 'questions.json')
    math = [dict(q, area='matematica') for q in existing if q.get('area', 'matematica') == 'matematica']
    combined = math + questions
    assert len({q['id'] for q in combined}) == len(combined)
    write(ROOT / 'public' / 'questions.json', combined)
    by_year = collections.Counter(q['year'] for q in questions)
    by_area = collections.Counter(q['area'] for q in questions)
    by_topic = collections.Counter(t for q in questions for t in q['topics'])
    by_year_area = {str(year): dict(collections.Counter(q['area'] for q in questions if q['year'] == year)) for year in range(2019, 2024)}
    by_year_topic = {str(year): dict(sorted(collections.Counter(t for q in questions if q['year'] == year for t in q['topics']).items())) for year in range(2019, 2024)}
    write(ROOT / 'data' / 'science-coverage.json', {
        'examined': 225, 'published': len(questions),
        'byYear': dict(sorted(by_year.items())), 'byArea': dict(by_area),
        'byTopic': dict(sorted(by_topic.items())), 'byYearArea': by_year_area,
        'byYearTopic': by_year_topic,
        'excluded': excluded, 'answerKeyCorrections': corrections,
        'transcriptionCorrections': [
            {'ids': ['2019-98', '2019-100', '2019-128'], 'reason': 'Itens ausentes da base auxiliar, transcritos do caderno oficial.'},
            {'ids': ['2021-105', '2023-132'], 'reason': 'Alternativas gráficas ausentes descritas a partir do caderno oficial.'},
            {'ids': ['2021-119', '2022-109', '2022-132', '2023-99', '2023-102', '2023-129'], 'reason': 'Falhas de transcrição, imagem ou separação de campos corrigidas.'},
        ],
    })
    print('Science', len(questions), dict(by_area), 'excluded', excluded)


if __name__ == '__main__':
    main()
