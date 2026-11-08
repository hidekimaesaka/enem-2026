# ENEM em foco

App estático e responsivo com 41 questões autorais de Linguagens e Ciências Humanas, cinco alternativas, correção imediata, explicações, dificuldade estimada e revisão das erradas. O progresso fica salvo no navegador via localStorage.

## Publicar na Vercel

Importe este repositório como novo projeto. Use o preset **Other**, diretório raiz `./`, sem comando de build e diretório de saída `.`. Não são necessárias variáveis de ambiente ou banco de dados.

## Executar localmente

Abra `index.html` no navegador, ou execute `python -m http.server 8000` nesta pasta e acesse `http://localhost:8000`.

## Arquivos

- `index.html`: estrutura da página.
- `style.css`: estilos responsivos.
- `questions.js`: 41 questões, alternativas, gabaritos e explicações.
- `app.js`: navegação, correção e persistência local.

As questões são exercícios autorais baseados nos tópicos do caderno fornecido, não itens oficiais do ENEM. A dificuldade é uma estimativa pedagógica e não representa calibração pela TRI. Fontes tipográficas são carregadas do Google Fonts, com fontes locais como alternativa.
