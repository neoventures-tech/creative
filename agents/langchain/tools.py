"""
Tools para o agente RAG.

Define as ferramentas que o agente pode usar durante a conversa.
O contexto é passado via ToolRuntime para ser thread-safe.
"""
import os
from typing import TYPE_CHECKING
from langchain.tools import tool, ToolRuntime
from openai import OpenAI

if TYPE_CHECKING:
    from agents.models import Conversation
    from langchain_core.retrievers import BaseRetriever


class AgentContextSchema:
    """Schema do contexto passado para as tools via ToolRuntime."""
    conversation: "Conversation"
    retriever: "BaseRetriever"


@tool
def search_documents(query: str, runtime: ToolRuntime) -> str:
    """
    Busca documentos relevantes na base de conhecimento.

    Use esta ferramenta SEMPRE que precisar buscar informações para responder
    perguntas do usuário. Busque nos documentos disponíveis antes de responder.

    Args:
        query: A consulta/pergunta para buscar nos documentos.

    Returns:
        Conteúdo dos documentos relevantes encontrados.
    """
    retriever = getattr(runtime.context, "retriever", None)

    if not retriever:
        return "Erro: Nenhum retriever configurado para busca de documentos."

    docs = retriever.invoke(query)

    if not docs:
        return "Nenhum documento relevante encontrado para esta consulta."

    return "\n\n---\n\n".join([d.page_content for d in docs])



@tool
def generate_image(
    prompt: str,
    runtime: ToolRuntime,
    size: str = "1536x1024",
) -> str:
    """
      Edita uma imagem usando gpt-image-1 (image-to-image) mantendo o estilo da imagem de referência.

    QUANDO USAR:
    - Quando o usuário pedir para modificar uma imagem mantendo o estilo
    - Quando houver uma imagem de referência e mudanças específicas a fazer
    - Para criar variações de imagens existentes

    REGRAS:
    1. O prompt deve descrever as mudanças desejadas
    2. A imagem de referência serve como base para estilo e layout
    3. Requer organização OpenAI verificada

    Args:
        reference_image_path: Caminho para a imagem de referência
        prompt: Descrição das modificações desejadas
        size: Tamanho da imagem. Opções: "256x256", "512x512", "1024x1024", "1536x1024", "1024x1536"

    Returns:
        str: Caminho da imagem gerada ou mensagem de erro
    """
    try:
        print("\n" + "="*80)
        print("🎨 INICIANDO GERAÇÃO DE IMAGEM")
        print("="*80)

        import base64
        from pathlib import Path
        from agents.models import GeneratedImage

        print("\n[1/6] Extraindo contexto...")
        try:
            conversation = runtime.context.conversation
            reference_image_path = runtime.context.reference_image_path
            print(f"✓ Contexto extraído")
            print(f"   - Conversation ID: {conversation.id if conversation else 'None'}")
            print(f"   - Imagem referência: {reference_image_path}")
        except Exception as e:
            print(f"✗ ERRO ao extrair contexto: {e}")
            import traceback
            traceback.print_exc()
            return f"Erro ao extrair contexto: {str(e)}"

        if not conversation:
            return "Erro: Conversa não encontrada no contexto."

        print("\n[2/6] Validando parâmetros...")
        try:
            # Validar tamanho
            valid_sizes = ["256x256", "512x512", "1024x1024", "1536x1024", "1024x1536"]
            if size not in valid_sizes:
                size = "1536x1024"
            print(f"✓ Tamanho validado: {size}")

            # Verificar se o arquivo existe
            if not Path(reference_image_path).exists():
                return f"Erro: Imagem de referência não encontrada: {reference_image_path}"
            print(f"✓ Arquivo de referência encontrado")
        except Exception as e:
            print(f"✗ ERRO na validação: {e}")
            import traceback
            traceback.print_exc()
            return f"Erro na validação: {str(e)}"

        print("\n[3/6] Inicializando cliente OpenAI...")
        try:
            api_key = os.getenv("OPENAI_API_KEY")
            client = OpenAI(api_key=api_key)
            print("✓ Cliente OpenAI inicializado")
        except Exception as e:
            print(f"✗ ERRO ao inicializar cliente: {e}")
            import traceback
            traceback.print_exc()
            return f"Erro ao inicializar cliente OpenAI: {str(e)}"

        print("\n[4/6] Preparando prompt...")
        try:
            full_prompt = f"""
Gere uma nova imagem mantendo o layout, estilo e paleta da imagem de referência enviada.

⚠️ IMPORTANTE: A imagem deve mostrar O PROBLEMA/SITUAÇÃO DE RISCO descrita no desafio abaixo, NÃO a solução ou comportamento correto.

DESCRIÇÃO DO DESAFIO/CENÁRIO:
{prompt}

---

# 🎨 DIRETRIZES DE LAYOUT (Mining Hub)

## 1. Cabeçalho Superior Azul com Pergunta
- Faixa azul no topo
- Pergunta iniciando com "Como podemos…?" relacionada ao desafio
- Texto em branco, destacado

## 2. Área Principal com Ilustrações (centro/esquerda)
- Desenhos em estilo **cartoon técnico industrial** mostrando:
  - **A SITUAÇÃO DE RISCO/PROBLEMA descrita**
  - Pessoas, máquinas, equipamentos no contexto problemático
  - Riscos visíveis no ambiente
- Ícones e elementos visuais:
  - Triângulos de alerta vermelhos indicando perigos
  - Setas explicativas apontando riscos
  - Pequenas notas/balões identificando problemas
- **FOCO: Mostrar o desafio/problema atual, não a solução**

## 3. Coluna Lateral Direita com Objetivos
- Bloco retangular claro (bege/amarelo suave)
- Lista com marcadores em estrela (★)
- Destaca benefícios esperados e objetivos
- Sempre posicionada à direita

## 4. Estilo Visual Padronizado
- Cores: azul escuro, amarelo/bege, vermelho de alerta
- Estilo cartoon uniforme (traço técnico industrial)
- Elementos de comunicação:
  - Ícones de alerta (triângulos vermelhos)
  - Setas indicativas
  - Balões/blocos de texto flutuantes

## 5. Estrutura Narrativa: PROBLEMA em destaque
1. **Situação problemática/risco** na região ilustrada central
2. **Perigos e dificuldades** destacados com ícones visuais de alerta
3. **Objetivos/metas** (não soluções detalhadas) na coluna direita

## 6. Logos no Rodapé
- Logo da empresa patrocinadora (se aplicável)
- Logo do **mininghub**
- Posicionados no canto inferior direito

---

## 🎯 REGRA CRÍTICA
**Ilustre fielmente a SITUAÇÃO DE RISCO descrita no desafio.**
**NÃO mostre como resolver o problema ou comportamento correto.**
**A imagem deve representar o CENÁRIO PROBLEMÁTICO.**

---

Mantenha: layout de referência, estilo cartoon técnico industrial, paleta de cores, estrutura geral.
"""
            print(f"✓ Prompt preparado ({len(full_prompt)} caracteres)")
        except Exception as e:
            print(f"✗ ERRO ao preparar prompt: {e}")
            import traceback
            traceback.print_exc()
            return f"Erro ao preparar prompt: {str(e)}"

        print("\n[5/6] Chamando API OpenAI para editar imagem...")
        try:
            # Abrir e enviar a imagem de referência
            with open(reference_image_path, "rb") as image_file:
                print(f"   Enviando arquivo: {reference_image_path}")
                response = client.images.edit(
                    model="gpt-image-1",
                    image=image_file,
                    prompt=full_prompt,
                    size=size,
                    n=1
                )
            print("✓ API respondeu com sucesso")
        except Exception as e:
            print(f"✗ ERRO na chamada da API OpenAI: {e}")
            import traceback
            traceback.print_exc()
            return f"Erro na API OpenAI: {str(e)}"

        print("\n[6/6] Salvando imagem...")
        try:
            # Obter a imagem resultante (base64)
            output_bytes = base64.b64decode(response.data[0].b64_json)
            print(f"✓ Imagem decodificada ({len(output_bytes)} bytes)")

            # Salvar a imagem localmente
            output_dir = Path("media/generated_images")
            output_dir.mkdir(parents=True, exist_ok=True)

            output_filename = f"edited_{Path(reference_image_path).stem}_{conversation.id}.png"
            output_path = output_dir / output_filename

            with open(output_path, "wb") as f:
                f.write(output_bytes)
            print(f"✓ Arquivo salvo: {output_path}")

            # Salvar no banco (usar caminho relativo começando com /media/)
            # Converter caminho absoluto para URL relativa
            image_url = f"/{output_path}"  # Adiciona / no início para URL absoluta

            generated_image = GeneratedImage.objects.create(
                conversation=conversation,
                prompt=full_prompt,
                image_url=image_url,
                model="gpt-image-1",
                size=size,
                quality="standard",
            )
            print(f"✓ Registro criado no banco (ID: {generated_image.id})")
            print(f"   URL da imagem: {image_url}")

            print("\n" + "="*80)
            print("✅ IMAGEM GERADA COM SUCESSO")
            print("="*80 + "\n")

            return f"✅ Imagem editada com sucesso!\n\nArquivo salvo em: {output_path}\n\nURL: {image_url}"

        except Exception as e:
            print(f"✗ ERRO ao salvar imagem: {e}")
            import traceback
            traceback.print_exc()
            return f"Erro ao salvar imagem: {str(e)}"

    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"Erro ao editar imagem: {str(e)}"


def get_agent_tools():
    """
    Retorna a lista de tools disponíveis para o agente.

    Returns:
        Lista de tools LangChain.
    """
    return [
        # search_documents,
        generate_image,
    ]