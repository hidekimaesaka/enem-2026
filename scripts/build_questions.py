"""Build the reviewed, self-contained question catalogue from audited source records."""
import collections
import json
import re
import shutil
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT.parent / 'enem-source' / 'public'
OUT = ROOT / 'public' / 'questions'
TOPICS = ('combinatoria','plana','espacial','probabilidade','algebra','trigonometria','funcoes','pa','pg')

def read(path):return json.loads(path.read_text(encoding='utf8'))
def save(path,value):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

def official_keys(year):
    path=ROOT/'data'/'official-keys'/f'{year}.json'
    return {int(k):v for k,v in read(path).items()}

def fix_raw(year,items):
    # Corrections made against the original PDF and its published answer key.
    if year==2020:
        items[140]['alternatives'][2]['text']='3 caixas do tipo A e 2 caixas do tipo B.'
        items[168]={
            'year':2020,'index':168,'context':
            'Num recipiente com a forma de paralelepípedo reto-retângulo, colocou-se água até a altura de 8 cm e um objeto, que ficou flutuando na superfície da água. Para retirar o objeto, a coluna de água deve atingir pelo menos 15 cm. Serão colocadas bolinhas de volume 6 cm³ cada, totalmente submersas. A base interna do recipiente mede 3 cm por 4 cm.\n\n![Esquema do recipiente](/questions/2020/168/official.png)',
            'alternativesIntroduction':'O número mínimo de bolinhas necessárias para atingir o nível desejado é',
            'correctAlternative':'A','alternatives':[{'letter':c,'text':v,'file':None} for c,v in zip('ABCDE',['14.','16.','18.','30.','34.'])]}
    if year==2021:
        items[175]['alternatives'][3]['text']='8 trapézios isósceles e 12 quadrados.'
        items[175]['alternatives'].append({'letter':'E','text':'12 trapézios escalenos e 12 retângulos.','file':None})
    if year==2022:
        items[143]['correctAlternative']='D'
        items[144]['alternatives']=[{'letter':c,'text':v,'file':None} for c,v in zip('ABCDE',['0','6','7','8','9'])]
        items[166]['alternatives']=[{'letter':c,'text':v,'file':None} for c,v in zip('ABCDE',['0','1','2','3','4'])]
    if year==2023:
        items[141]['context']='No alojamento de uma universidade, há quartos com padrão superior. Para sortear um quarto, cada estudante inscrito recebe cartões com seu nome: um cartão para cada estudante do primeiro ano, dois para cada estudante do segundo e três para cada estudante do terceiro. Inscreveram-se 200 estudantes do primeiro ano, 150 do segundo e 100 do terceiro. Todos os cartões têm a mesma chance de sorteio.'
        items[142]['context']='A água utilizada pelos 75 moradores de um vilarejo provém de um reservatório cilíndrico de raio 5 m, reabastecido no primeiro dia de cada mês. Cada pessoa consome em média 200 L por dia. Depois de um gasto extra nos primeiros 20 dias de junho, o nível da água ficou em 1,5 m. Os moradores decidem racionar pelos dez dias restantes. Use π = 3.'
        items[146]['context']='O triângulo da figura é denominado triângulo mágico. Nos seis círculos, escrevem-se os números de 1 a 6, sem repetição. O objetivo é fazer com que as somas dos números em cada lado sejam iguais.\n\n'+items[146]['context']
        items[160]['context']=items[160]['context'].replace('6 caracteres especiais !, @, #, $,   , &','6 caracteres especiais !, @, #, $, %, &')
        items[170]['context']=items[170]['context'].replace('V x\nx\nx\n','V(x) = x²/4 − 10x + 105') if 'V x\nx\nx\n' in items[170]['context'] else items[170]['context']
    return items

def localize(text,year,index):
    def repl(match):
        url=match.group(0)
        parsed=urlparse(url)
        if parsed.path.endswith('broken-image.svg'):raise ValueError(f'broken image {year}/{index}')
        rel=parsed.path.lstrip('/')
        src=SRC/rel
        if not src.is_file():raise FileNotFoundError(src)
        dest=OUT/str(year)/str(index)/src.name
        dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(src,dest)
        return '/questions/'+str(year)+'/'+str(index)+'/'+src.name
    return re.sub(r'https://enem\.dev/[^\s)]+',repl,text or '')

def main():
    allq=[];coverage={};exclusions={}; corrections=[]
    for year in range(2019,2024):
        raw={int(q['index']):q for q in read(ROOT/'data'/'raw'/f'{year}.json') if 136<=int(q['index'])<=180}
        recovered=ROOT/'data'/'review'/f'{year}-recovered.json'
        if recovered.exists():raw.update({int(q['index']):q for q in read(recovered)})
        raw=fix_raw(year,raw)
        reviewed={int(q['index']):q for q in read(ROOT/'data'/'review'/f'{year}.json')}
        keys=official_keys(year)
        assert set(reviewed)==set(range(136,181)),f'Incomplete review {year}'
        counts=collections.Counter();excluded=[]
        for index,review in sorted(reviewed.items()):
            if review.get('excluded'):
                excluded.append({'number':index,'reason':review['excluded']})
                continue
            assert index in raw,(year,index,'missing raw')
            q=raw[index]
            official=keys.get(index)
            if official not in ('A','B','C','D','E'):raise ValueError(f'No official key {year}/{index}: {official}')
            if q['correctAlternative']!=official:corrections.append({'year':year,'number':index,'api':q['correctAlternative'],'official':official})
            alts=q['alternatives']
            assert len(alts)==5,(year,index,'alternative count')
            assert [a['letter'] for a in alts]==list('ABCDE'),(year,index,'letters')
            assert review['topics'] and set(review['topics'])<=set(TOPICS),(year,index,'topics')
            assert len(review['rubric'])==3 and all(isinstance(v,int) and 0<=v<=2 for v in review['rubric']),(year,index,'rubric')
            assert len(review['explanation'])>=2 and all(s.strip() for s in review['explanation']),(year,index,'explanation')
            assert review['rationale'].strip(),(year,index,'rationale')
            context=localize(q.get('context'),year,index)
            prompt=localize(q.get('alternativesIntroduction'),year,index)
            assert context.strip() and prompt.strip(),(year,index,'empty content')
            alternatives=[]
            for alt in alts:
                text=localize(alt.get('text'),year,index) or None
                file=localize(alt.get('file'),year,index) or None
                assert text or file,(year,index,'empty alternative',alt['letter'])
                alternatives.append({'letter':alt['letter'],'text':text,'file':file})
            for topic in review['topics']:counts[topic]+=1
            allq.append({'id':f'{year}-{index}','year':year,'index':index,'topics':review['topics'],'context':context,'alternativesIntroduction':prompt,'alternatives':alternatives,'correctAlternative':official,'explanation':review['explanation'],'rubric':review['rubric'],'rationale':review['rationale'],'source':read(ROOT/'data'/'review'/f'{year}-sources.json')['examUrl']})
        coverage[str(year)]=dict(included=sum(counts.values()),unique=len([q for q in allq if q['year']==year]),topics=dict(counts))
        exclusions[str(year)]=excluded
    counts=collections.Counter(t for q in allq for t in q['topics'])
    assert all(counts[t]>=5 for t in TOPICS),counts
    assert len({q['id'] for q in allq})==len(allq)
    save(ROOT/'public'/'questions.json',allq)
    save(ROOT/'data'/'coverage.json',{'totalUniqueQuestions':len(allq),'byTopic':dict(counts),'byYear':coverage,'answerKeyCorrections':corrections,'excluded':exclusions,'earlierYearsNeeded':False})
    print(len(allq),dict(counts),'answer corrections',corrections)

if __name__=='__main__':main()
