import os
import httpx
from profile import get_profile_summary

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

SYSTEM_PROMPT = f"""És um consultor especialista em fundos europeus e comunitários para Portugal.
Tens acesso completo ao perfil das empresas do teu cliente e ao historial de oportunidades identificadas.
O teu papel é:
- Responder a dúvidas sobre concursos, programas e elegibilidade
- Dar instruções concretas de preenchimento de formulários
- Aconselhar sobre estratégia de candidatura
- Avaliar se uma candidatura específica deve ser feita por meios próprios ou com consultora externa
- Dar conselhos sobre timing, documentação necessária e maximização do valor elegível
- Alertar para riscos, armadilhas comuns e requisitos frequentemente esquecidos

Sê sempre directo, concreto e prático. Usa exemplos reais quando possível.
Nunca dês conselhos vagos — se não souberes algo com certeza, diz-o claramente.
Responde sempre em português europeu.

=== PERFIL DO CLIENTE ===
{get_profile_summary()}

=== CONTEXTO ADICIONAL ===
Empresa prestadora de serviços: Sentido da Lua Lda (NIF 508991609)
CAE Principal actual: 90390-R4 (Apoio às artes do espectáculo)
CAE Secundário actual: 56116-R4 (Refeições take-away)
CAEs a adicionar: 62010-R4, 62020-R4, 73110-R4, 73120-R4, 70220-R4
Capital social: €5.000
Estratégia: Glamping Skies candidata-se; Sentido da Lua presta e fatura os serviços elegíveis.
Foco exclusivo: activos intangíveis a fundo perdido (tecnologia, marketing, IA, internacionalização).
"""

async def chat(messages: list[dict]) -> str:
    """
    Process a chat message with full company context.
    messages: list of {"role": "user"|"assistant", "content": "..."}
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
                "max_tokens": 2000,
                "system": SYSTEM_PROMPT,
                "messages": messages
            }
        )
        data = response.json()
        return data.get("content", [{}])[0].get("text", "Erro ao processar resposta.")
