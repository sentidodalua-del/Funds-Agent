try:
    from config import ANTHROPIC_API_KEY as _ANT_KEY, PERPLEXITY_API_KEY as _PPLX_KEY
except ImportError:
    _ANT_KEY = ""
    _PPLX_KEY = ""

import os
os.environ.setdefault("ANTHROPIC_API_KEY", _ANT_KEY)
os.environ.setdefault("PERPLEXITY_API_KEY", _PPLX_KEY)

import os
import httpx
import json

PERPLEXITY_API_KEY = os.environ.get("PERPLEXITY_API_KEY", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

async def find_consultancies(opportunity: dict) -> list[dict]:
    """
    For a given opportunity, find and screen the 3 best consultancies
    specialised in that specific programme and sector.
    """
    program = opportunity.get("program", "")
    area = opportunity.get("area", "")
    managing_entity = opportunity.get("managing_entity", "")

    # Step 1: Search for relevant consultancies via Perplexity
    search_results = await _search_consultancies(program, area, managing_entity)

    # Step 2: Screen and rank with Claude
    ranked = await _screen_and_rank(search_results, opportunity)

    return ranked[:3]


async def _search_consultancies(program: str, area: str, managing_entity: str) -> str:
    queries = [
        f"consultoras especializadas {program} Portugal fundos europeus track record aprovações",
        f"empresas consultoria candidaturas {area} {managing_entity} Portugal resultados",
        f"melhores consultoras fundos comunitários Portugal turismo digitalização reviews reputação",
    ]

    results = []
    async with httpx.AsyncClient(timeout=30) as client:
        for query in queries:
            try:
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
                                    "És um especialista em consultoras de fundos europeus em Portugal. "
                                    "Pesquisa empresas reais com nome, website, especialização comprovada, "
                                    "track record verificável e reputação online. "
                                    "Inclui apenas empresas com presença verificável. Responde em português."
                                )
                            },
                            {"role": "user", "content": query}
                        ],
                        "return_citations": True,
                        "search_recency_filter": "year"
                    }
                )
                data = response.json()
                text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                if text:
                    results.append(text)
            except Exception as e:
                print(f"Consultancy search error: {e}")

    return "\n\n---\n\n".join(results)


async def _screen_and_rank(search_results: str, opportunity: dict) -> list[dict]:
    """Use Claude to screen, verify and rank consultancies."""
    prompt = f"""
Analisas consultoras de fundos europeus para recomendar as 3 melhores para uma candidatura específica.

=== CANDIDATURA EM QUESTÃO ===
Programa: {opportunity.get('program')}
Área: {opportunity.get('area')}
Entidade gestora: {opportunity.get('managing_entity')}
Valor da candidatura: {opportunity.get('proposed_budget', {}).get('total_investment', 'N/A') if isinstance(opportunity.get('proposed_budget'), dict) else 'N/A'}
Sector: Turismo rural / Digitalização / Internacionalização

=== RESULTADOS DA PESQUISA ===
{search_results}

=== CRITÉRIOS DE SCREENING ===
1. Especialização comprovada neste programa específico ou área similar
2. Track record — candidaturas aprovadas verificáveis, taxa de sucesso
3. Reputação online — reviews, presença digital, referências
4. Idoneidade — sem processos públicos conhecidos, situação fiscal presumivelmente regular
5. Adequação ao perfil — experiência com microempresas, turismo, Alentejo ou similares
6. Transparência — website claro, contactos reais, equipa identificável

=== INSTRUÇÃO ===
Com base na pesquisa, selecciona e apresenta as 3 consultoras mais adequadas para esta candidatura específica.
Sê rigoroso: só inclui empresas com evidência real de existência e competência.
Se não houver 3 com qualidade suficiente, inclui menos e justifica.

Responde APENAS com JSON válido, sem texto adicional:

[
  {{
    "name": "Nome da consultora",
    "website": "https://...",
    "location": "Cidade, Portugal",
    "specialization": "Especialização principal verificada",
    "programs_expertise": ["Portugal 2030", "PRR", "Horizon Europe"],
    "track_record": "Descrição do track record verificável — projectos aprovados, taxas de sucesso, clientes notáveis",
    "online_reputation": "Resumo da reputação online — reviews, referências, presença digital",
    "suitability_for_this_call": "Porque é adequada especificamente para ESTA candidatura",
    "screening_score": 85,
    "screening_notes": "Notas do screening — pontos fortes e eventuais reservas",
    "contact": "Email ou telefone se disponível",
    "estimated_fee": "Estimativa de honorários (% de sucesso ou valor fixo se conhecido)"
  }}
]

screening_score: 0-100 (100 = perfeitamente adequada e verificada)
"""

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            },
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 3000,
                "messages": [{"role": "user", "content": prompt}]
            }
        )
        data = response.json()
        text = data.get("content", [{}])[0].get("text", "[]").strip()
        text = text.replace("```json", "").replace("```", "").strip()
        try:
            return json.loads(text)
        except Exception:
            start = text.find("[")
            end = text.rfind("]") + 1
            if start != -1 and end > start:
                return json.loads(text[start:end])
            return []
