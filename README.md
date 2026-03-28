🏕 Funds Agent — Glamping Skies
Agente autónomo de monitorização de fundos europeus com geração automática de propostas de candidatura.
Como funciona
Pesquisa diária às 07:00 (hora de Lisboa) via Perplexity API
Análise com IA (Claude) que cruza cada concurso com o perfil da empresa
Geração de proposta completa com valores concretos maximizados
Dashboard web sempre disponível para consulta
Deploy no Railway
1. Criar projecto no Railway
```
railway login
railway init
railway up
```
2. Adicionar variáveis de ambiente
No painel do Railway → Settings → Variables:
```
PERPLEXITY\_API\_KEY=pplx-...
ANTHROPIC\_API\_KEY=sk-ant-...
```
3. Adicionar volume para persistência da base de dados
Railway → Add Volume → Mount path: `/app/data`
4. Aceder ao dashboard
O Railway gera um URL público automaticamente (ex: `funds-agent.railway.app`)
Estrutura do projecto
```
funds-agent/
├── main.py          # API FastAPI
├── agent.py         # Lógica do agente (Perplexity + Claude)
├── database.py      # Base de dados SQLite
├── profile.py       # Perfil das empresas (editar aqui)
├── scheduler.py     # Agendamento diário + servidor
├── requirements.txt # Dependências Python
├── railway.toml     # Configuração Railway
├── static/
│   └── index.html   # Dashboard web
└── data/            # Base de dados (criada automaticamente)
```
Personalização
Para ajustar o perfil da empresa, edita `profile.py`.
Para adicionar novas queries de pesquisa, edita `SEARCH\_QUERIES` em `agent.py`.
API Endpoints
`GET /` — Dashboard
`GET /api/opportunities` — Lista de oportunidades
`GET /api/opportunities/{id}` — Detalhe de uma oportunidade
`GET /api/stats` — Estatísticas
`POST /api/run-search` — Lança pesquisa manual
`GET /api/health` — Health check
