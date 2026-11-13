# MATEMATIKO PARA ENÊ

Aplicativo de prática de Matemática para o ENEM, feito com React, TypeScript e Vite. O mesmo repositório do antigo “ENEM em foco” é usado para manter a integração com a Vercel. O catálogo contém 147 questões distintas de aplicações regulares impressas entre 2019 e 2023. Cada questão pode integrar mais de um dos nove temas.

## Uso

Na tela de entrada, digite `rock`. Essa senha é validada no navegador e serve como uma barreira visual simples; não protege os arquivos do site. A sessão dura até o fim da aba. Respostas, revisão de erros e tempo medido por questão são salvos apenas no navegador.

Em cada questão, o cronômetro só começa ao clicar em **Iniciar**. É possível pausar e zerar. Ao confirmar uma alternativa, o cronômetro para automaticamente e o tempo da tentativa fica registrado com a resposta. A opção **Tentar novamente** permite reiniciar a questão e o tempo.

## Rodar e publicar

```sh
npm ci
npm run build
npm run dev
```

Na Vercel, use Vite, `npm run build` e saída `dist`. O arquivo `vercel.json` fornece o fallback das rotas de navegação para `index.html`. Não há backend, banco de dados ou variáveis de ambiente.

## Questões e fontes

O catálogo publicado está em `public/questions.json`; as imagens estão em `public/questions/`. Os cadernos e gabaritos oficiais do Inep foram usados como referência final, com URLs por ano em `data/review/*-sources.json`. A [API ENEM](https://api.enem.dev/) foi usada para acelerar a transcrição inicial. Ela é um projeto comunitário, independente do Inep. O conjunto de dados e API trazem a licença [GPL-2.0](https://github.com/yunger7/enem-api/blob/main/LICENSE); mantenha essa atribuição ao redistribuir o catálogo.

As resoluções e classificações foram escritas para este aplicativo. A dificuldade é uma estimativa pedagógica: interpretação/modelagem, conceitos/etapas e cálculos/representações recebem 0 a 2 pontos cada. Soma 0–2 é Fácil; 3–4 é Média; 5–6 é Difícil. Essa classe não equivale à TRI nem à porcentagem histórica de acerto.

`data/coverage.json` registra quantidades por tema e ano, questões excluídas com motivo e divergências corrigidas no gabarito importado. Nenhum ano anterior a 2019 foi necessário para alcançar o mínimo de cinco questões por tema.

Para regenerar o catálogo, clone `https://github.com/yunger7/enem-api.git` em uma pasta `enem-source` adjacente a este repositório, deixe os arquivos de revisão e PDFs oficiais em `data/review` e `work/review`, respectivamente, e execute:

```sh
python scripts/build_questions.py
python scripts/validate_content.py
```
