"""
Tools para o agente RAG.

Define as ferramentas que o agente pode usar durante a conversa.
O contexto é passado via ToolRuntime para ser thread-safe.
"""
import os
from typing import TYPE_CHECKING

from django.conf import settings
from langchain.tools import tool, ToolRuntime
from openai import OpenAI
import google.generativeai as genai

from agents.utils import load_image_as_input

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
Mantenha FIELMENTE o layout e estilo da imagem de referência (template).

⚠️ CRÍTICO: Siga EXATAMENTE a estrutura visual do template.

{prompt}

---

ESTRUTURA OBRIGATÓRIA (seguir template EXATAMENTE):
1. **CABEÇALHO SUPERIOR**
   - Faixa horizontal azul escuro no topo.
   - Texto em branco no centro começando com: "COMO PODEMOS..." seguido da pergunta do desafio.

2. **PARTE ESQUERDA / CENTRO – CONTEXTO E PROBLEMA**
   - Ilustrações em estilo cartoon técnico (equipamentos de mineração, operadores, processos, ambiente).
   - Mostrar a situação atual e os problemas visuais (ex.: poeira, fumaça, vibração, sujeira, sucata, risco).
   - Incluir pequenos textos próximos aos elementos, rótulos e explicações.
   - Incluir ícones de alerta (triângulos vermelhos), setas, destaques e observações.
   - Pode ter medições, gráficos simples, balões de fala ou anotações práticas.
   - Mostrar erros, limitações ou dificuldades do processo atual.

3. **BLOCO DIREITO – OBJETIVOS E BENEFÍCIOS**
   - Criar um retângulo vertical em bege/amarelo claro.
   - Dentro dele, incluir uma lista de itens marcados com estrelas (★).
   - Cada item deve representar benefícios, melhorias ou resultados esperados.
   - Acima da caixa, inserir um ícone de alvo, indicando o "objetivo da solução".

4. **ESTILO VISUAL**
   - Estilo cartoon coerente, linhas grossas, contornos marcados, sombras leves.
   - Paleta padrão: azul escuro, amarelo, bege, vermelho para alertas, tons suaves.
   - Pequenas legendas espalhadas explicando elementos.
   - Mistura equilibrada entre imagens e texto.

5. **RODAPÉ**
   - Colocar logos da empresa do desafio à esquerda.
   - Colocar o logo "mininghub." à direita.
   - Fundo cinza muito claro.

6. **NARRATIVA VISUAL**
   - O lado esquerdo sempre representa o PROBLEMA.
   - O lado direito sempre representa a SOLUÇÃO / BENEFÍCIOS.
   - Incluir sempre um contraste claro entre o “antes” e o “depois”.

Mantenha exatamente esse layout em todas as próximas criações.
Inclua apenas os elementos específicos do desafio atual conforme fornecido.

IMPORTANTE: Manter PROPORÇÕES e POSICIONAMENTO do template original.
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
                    # model="gpt-image-1",
                    model="gpt-image-1-mini",
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


@tool
def generate_image_gemini(
    prompt: str,
    runtime: ToolRuntime,
    aspect_ratio: str = "16:9",
    is_editing: bool = False,
) -> str:
    """
    Gera uma imagem usando Gemini 3 Pro Image Generation API (image-to-image) mantendo o estilo da imagem de referência.

    QUANDO USAR:
    - Quando o usuário pedir para criar/modificar uma imagem usando Gemini
    - Quando quiser usar o modelo Gemini para geração de imagens de alta qualidade
    - Para criar variações mantendo estilo da imagem de referência

    REGRAS:
    1. O prompt deve descrever as mudanças/conteúdo desejado
    2. A imagem de referência serve como base para estilo e layout
    3. Usa o modelo gemini-3-pro-image-preview para geração de alta qualidade (até 2K)

    Args:
        prompt: Descrição da imagem desejada ou modificações
        aspect_ratio: Proporção da imagem. Opções: "1:1", "16:9", "4:3", "9:16", "3:4"

    Returns:
        str: Caminho da imagem gerada ou mensagem de erro
    """
    global last_image_input
    try:
        print("\n" + "="*80)
        print("🎨 INICIANDO GERAÇÃO DE IMAGEM COM GEMINI")
        print("="*80)

        import base64
        from pathlib import Path
        from agents.models import GeneratedImage
        from PIL import Image
        import io

        print("\n[1/6] Extraindo contexto...")
        try:
            conversation = runtime.context.conversation
            reference_image_path = runtime.context.reference_image_path
            reference_layout_image_path = runtime.context.reference_layout_image_path
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
            # Validar aspect_ratio
            valid_ratios = ["1:1", "16:9", "4:3", "9:16", "3:4"]
            if aspect_ratio not in valid_ratios:
                aspect_ratio = "16:9"
            print(f"✓ Aspect ratio validado: {aspect_ratio}")

            # Verificar se o arquivo existe
            if not Path(reference_image_path).exists():
                return f"Erro: Imagem de referência não encontrada: {reference_image_path}"
            print(f"✓ Arquivo de referência encontrado")
        except Exception as e:
            print(f"✗ ERRO na validação: {e}")
            import traceback
            traceback.print_exc()
            return f"Erro na validação: {str(e)}"

        print("\n[3/6] Inicializando cliente Gemini...")
        try:
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                return "Erro: GEMINI_API_KEY não configurada no ambiente"

            genai.configure(api_key=api_key)
            print("✓ Cliente Gemini inicializado")
        except Exception as e:
            print(f"✗ ERRO ao inicializar cliente: {e}")
            import traceback
            traceback.print_exc()
            return f"Erro ao inicializar cliente Gemini: {str(e)}"

        print("\n[4/6] Preparando prompt e imagem...")
        try:
            layout_reference = Image.open(reference_layout_image_path)
            if is_editing:
                last_image = GeneratedImage.objects.filter(
                    conversation=conversation.id
                ).order_by('-created_at').first()

                print(last_image)

                if not last_image or not last_image.image_url:
                    raise ValueError("No previous image found for editing.")

                print("✓ Editing mode — loading last generated image")

                # ------------------------------------------------------------
                # Convert image_url → absolute filesystem path
                # Example:
                # /media/generated_images/img.png
                # becomes:
                # /yourproject/media/generated_images/img.png
                # ------------------------------------------------------------
                relative_path = last_image.image_url.replace(settings.MEDIA_URL, "")
                full_path = os.path.join(settings.MEDIA_ROOT, relative_path)

                # Now open it normally
                reference = Image.open(full_path)
                print(f"✓ Last image opened: {reference.size}")

                # Convert to Gemini input

            else:
                # Normal mode — use the user-provided image
                reference = Image.open(reference_image_path)
                print(f"✓ Default reference image loaded: {reference.size}")


        except Exception as e:
            print(f"✗ ERRO ao preparar prompt: {e}")
            import traceback
            traceback.print_exc()
            return f"Erro ao preparar prompt: {str(e)}"

        print("\n[5/6] Chamando API Gemini para gerar imagem...")
        try:
            # Configurar modelo Gemini 3 Pro - mais avançado para geração de imagens
            model = genai.GenerativeModel("gemini-3-pro-image-preview")



            # Gerar imagem
            response = model.generate_content(
                [prompt, reference, layout_reference],
                generation_config=genai.GenerationConfig(
                    temperature=1.0,
                )
            )

            print("✓ API Gemini respondeu com sucesso")

            # Extrair imagem da resposta
            generated_image = None
            for part in response.parts:
                if hasattr(part, 'inline_data') and part.inline_data.mime_type.startswith('image/'):
                    generated_image = part.inline_data.data
                    break

            if not generated_image:
                return "Erro: API Gemini não retornou uma imagem"

        except Exception as e:
            print(f"✗ ERRO na chamada da API Gemini: {e}")
            import traceback
            traceback.print_exc()
            return f"Erro na API Gemini: {str(e)}"

        print("\n[6/6] Salvando imagem...")
        try:
            # Salvar a imagem localmente
            output_dir = Path("media/generated_images")
            output_dir.mkdir(parents=True, exist_ok=True)

            from datetime import datetime
            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"gemini_{timestamp_str}_{conversation.id}.png"
            output_path = output_dir / output_filename

            with open(output_path, "wb") as f:
                f.write(generated_image)
            print(f"✓ Arquivo salvo: {output_path} ({len(generated_image)} bytes)")

            # Salvar no banco
            image_url = f"/{output_path}"

            generated_image_record = GeneratedImage.objects.create(
                conversation=conversation,
                prompt=prompt,
                image_url=image_url,
                model="gemini-3-pro-image-preview",
                size=aspect_ratio,
                quality="high",  # Gemini 3 Pro oferece alta qualidade
            )
            print(f"✓ Registro criado no banco (ID: {generated_image_record.id})")
            print(f"   URL da imagem: {image_url}")

            print("\n" + "="*80)
            print("✅ IMAGEM GERADA COM SUCESSO VIA GEMINI")
            print("="*80 + "\n")

            return f"✅ Imagem gerada com sucesso usando Gemini!\n\nArquivo salvo em: {output_path}\n\nURL: {image_url}"

        except Exception as e:
            print(f"✗ ERRO ao salvar imagem: {e}")
            import traceback
            traceback.print_exc()
            return f"Erro ao salvar imagem: {str(e)}"

    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"Erro ao gerar imagem com Gemini: {str(e)}"


def get_agent_tools():
    """
    Retorna a lista de tools disponíveis para o agente.

    Returns:
        Lista de tools LangChain.
    """
    return [
        # search_documents,
        # generate_image,
        generate_image_gemini,
    ]