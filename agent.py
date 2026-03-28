import os
import json
import asyncio
import httpx
from datetime import datetime
from profile import get_profile_summary, COMPANY_PROFILE
from database import save_opportunity, log_search

PERPLEXITY_API_KEY = os.environ.get("PERPLEXITY_API_KEY", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

SEARCH_QUERIES = [
    "concursos abertos Portugal 2030 turismo digitalização 2025 2026 fundo perdido microempresa",
    "avisos candidatura Alentejo 2030 abertos 2026 PME internacionalização marketing",
    "IAPMEI concursos abertos 2026 transformação digital turismo PME",
    "Turismo de Portugal avisos candidatura abertos 2026 digitalização internacionalização",
    "PRR concursos abertos 2026 digitalização empresas turismo",
    "AICEP apoios internacionalização PME turismo 2026 candidaturas abertas",
    "Horizon Europe open calls 2026 tourism digitalization SME Portugal",
    "EU funding tenders 2026 rural tourism digitalization intangible assets SME",
    "TED europa concursos abertos turismo rural Portugal 2026",
    "ANI concursos inovação digital turismo 2026 candidaturas abertas",
    "fundos europeus marketing digital redes sociais turismo 2026 apoios",
    "apoios inteligência artificial automação turismo Portugal 2026 fundo perdido",
    # Perfil B — Físico / Sustentabilidade
    "apoios painéis solares fotovoltaicos turismo alojamento Portugal 2026 fundo perdido",
    "fundos eficiência energética alojamento turismo rural Alentejo 2026 candidaturas abertas",
    "Portugal 2030 transição energética eficiência energética PME microempresa 2026 avisos abertos",
    "Fundo Ambiental apoios eficiência energética turismo 2026 candidaturas",
    "PRR eficiência energética reabilitação alojamento turismo 2026 apoios",
    "POSEUR programa sustentabilidade turismo rural energia renovável 2026",
    "apoios substituição coberturas reabilitação alojamento turismo rural 2026 fundo perdido",
    "Alentejo 2030 sustentabilidade energia renovável microempresa turismo 2026 avisos",
]

async def search_perplexity(query: str) -> str:
    """Search using Perplexity API."""
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            "https://api.perplexity.ai/chat/completions",
            headers={
                "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "sonar",
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "És um especialista em fundos europeus e comunitários para Portugal. "
                            "Pesquisa concursos e avisos de candidatura ABERTOS ACTUALMENTE. "
                            "Para cada concurso encontrado indica: nome, programa, entidade gestora, "
                            "dotação, taxa de apoio, prazo, link oficial. "
                            "Foca-te em factos concretos e verifica se os prazos ainda estão em aberto. "
                            "Responde sempre em português."
                        )
                    },
                    {"role": "user", "content": query}
                ],
                "return_citations": True,
                "search_recency_filter": "month"
            }
        )
        data = response.json()
        return data.get("choices", [{}])[0].get("message", {}).get("content", "")

async def analyze_with_claude(search_results: list[str]) -> list[dict]:
    """Use Claude to analyze search results and generate proposals."""
    profile = get_profile_summary()
    combined_results = "\n\n---\n\n".join(search_results)

    prompt = f"""
{profile}

=== RESULTADOS DA PESQUISA DE HOJE ===
{combined_results}

=== INSTRUÇÃO ===
Analisa os resultados acima e identifica TODOS os concursos/avisos de financiamento encontrados.
Para cada concurso, cria uma ficha completa em JSON.

Aplica o perfil da empresa rigorosamente:
- Exclui concursos não elegíveis (obras, empréstimos, sectores incompatíveis, empresas >10 trabalhadores)
- Considera sempre a elegibilidade para microempresas, turismo, Alentejo, baixa densidade
- Prioriza fundos a fundo perdido
- Verifica se os activos intangíveis e serviços tecnológicos são elegíveis

Para cada concurso elegível, gera uma proposta de candidatura CONCRETA com valores MAXIMIZADOS.
Selecciona apenas as componentes do projecto elegíveis neste concurso específico.
Os valores devem ser os máximos possíveis dentro das regras do aviso.

Responde APENAS com um array JSON válido, sem texto adicional, sem markdown, sem backticks.
Formato exacto:

[
  {{
    "title": "Nome do concurso/aviso",
    "program": "Nome do programa (ex: Portugal 2030, Alentejo 2030)",
    "managing_entity": "Entidade gestora (ex: IAPMEI, Turismo de Portugal)",
    "area": "Área temática (ex: Digitalização, Internacionalização, Marketing)",
    "deadline": "Data limite (ex: 30 Junho 2026 ou Contínuo)",
    "total_budget": "Dotação total do aviso (ex: €5.000.000)",
    "max_per_project": "Máximo por candidatura (ex: €200.000)",
    "support_rate": "Taxa de apoio (ex: 75% fundo perdido)",
    "official_link": "URL oficial se disponível",
    "source": "Fonte da informação",
    "relevance_score": 85,
    "relevance_label": "Alta",
    "eligibility_analysis": "Análise detalhada da elegibilidade: porque somos elegíveis, condicionantes, riscos",
    "eligible_components": "Quais as componentes do nosso projecto elegíveis neste concurso",
    "proposed_budget": {{
      "components": [
        {{"name": "Nome da componente", "description": "Descrição detalhada dos serviços", "value": 60000}},
        {{"name": "Outra componente", "description": "Descrição", "value": 45000}}
      ],
      "total_investment": 105000,
      "support_amount": 78750,
      "own_contribution": 26250,
      "support_rate_applied": "75%"
    }},
    "proposal_text": "Texto completo da proposta de candidatura pronto a adaptar. Deve ser profissional, detalhado, com justificação dos investimentos e alinhamento com os objectivos do programa.",
    "next_steps": "Lista de passos concretos para candidatar: documentos necessários, prazos internos, contactos",
    "urgency": "Alta"
  }}
]

relevance_score: 0-100 (100 = perfeitamente adequado)
relevance_label: "Alta" (>70), "Média" (40-70), "Baixa" (<40)
urgency: "Alta" (prazo <30 dias), "Média" (30-90 dias), "Baixa" (>90 dias ou contínuo)
investment_profile: "A" (só intangíveis/Sentido da Lua), "B" (só físico/empreiteiro), "AB" (ambos — gera 2 entradas separadas)

REGRA IMPORTANTE: Se o concurso for elegível para ambos os perfis (AB), cria DUAS entradas JSON separadas no array,
uma para cada perfil, com propostas orçamentais distintas e sem misturar componentes.
Para concursos do Perfil B (físico), inclui sempre no next_steps: "Obter orçamentos de empreiteiros certificados antes de candidatar."

Se não encontrares concursos elegíveis, devolve um array vazio: []
"""

    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            },
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 8000,
                "messages": [{"role": "user", "content": prompt}]
            }
        )
        data = response.json()
        text = data.get("content", [{}])[0].get("text", "[]")

        # Clean and parse JSON
        text = text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        text = text.strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to extract JSON array
            start = text.find("[")
            end = text.rfind("]") + 1
            if start != -1 and end > start:
                return json.loads(text[start:end])
            return []

async def run_daily_search():
    """Main agent function - runs all searches and saves results."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print("[" + now + "] Starting daily EU funds search...")
    
    if not PERPLEXITY_API_KEY:
        log_search("error", 0, 0, "PERPLEXITY_API_KEY not set")
        return
    if not ANTHROPIC_API_KEY:
        log_search("error", 0, 0, "ANTHROPIC_API_KEY not set")
        return

    # Run all searches in parallel
    search_results = []
    tasks = [search_perplexity(q) for q in SEARCH_QUERIES]
    
    try:
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for r in results:
            if isinstance(r, str) and r:
                search_results.append(r)
            elif isinstance(r, Exception):
                print(f"Search error: {r}")
    except Exception as e:
        print(f"Search batch error: {e}")
        log_search("error", 0, 0, str(e))
        return

    if not search_results:
        log_search("error", 0, 0, "No search results returned")
        return

    print(f"[{datetime.now()}] Got {len(search_results)} search results. Analyzing with Claude...")

    # Analyze with Claude in batches to avoid token limits
    batch_size = 4
    all_opportunities = []
    
    for i in range(0, len(search_results), batch_size):
        batch = search_results[i:i+batch_size]
        try:
            opps = await analyze_with_claude(batch)
            all_opportunities.extend(opps)
            await asyncio.sleep(2)  # Rate limit
        except Exception as e:
            print(f"Claude analysis error for batch {i}: {e}")

    # Save to database
    new_count = 0
    for opp in all_opportunities:
        if isinstance(opp, dict) and opp.get("title"):
            # Convert proposed_budget dict to string for storage
            if isinstance(opp.get("proposed_budget"), dict):
                opp["proposed_budget"] = json.dumps(opp["proposed_budget"], ensure_ascii=False)
            is_new = save_opportunity(opp)
            if is_new:
                new_count += 1

    log_search("success", len(all_opportunities), new_count)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print("[" + now + "] Done. Found " + str(len(all_opportunities)) + " opportunities, " + str(new_count) + " new.")
