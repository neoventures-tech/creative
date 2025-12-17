"""
Tools para o agente RAG.

Define as ferramentas que o agente pode usar durante a conversa.
O contexto é passado via ToolRuntime para ser thread-safe.
"""
from typing import TYPE_CHECKING

from langchain.tools import ToolRuntime
from langchain.tools import tool
from langchain_core.runnables import RunnableConfig

from agents.langchain.steps.generate_image_gemini_steps import step_validate_params, \
    step_init_gemini_client, step_prepare_reference_images_from_state, step_call_gemini_api, step_save_image
from agents.langchain.utils import PipelineLogger

if TYPE_CHECKING:
    from agents.models import Conversation
    from langchain_core.retrievers import BaseRetriever


class AgentContextSchema:
    """Schema do contexto passado para as steps via ToolRuntime."""
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


@tool(
    description="Generate or edit an image using Gemini 3 Pro based on execution state."
)
def generate_image_gemini(
        prompt: str,
        runtime: ToolRuntime,  # mantém por compatibilidade
        config: RunnableConfig,  # FONTE REAL
):
    logger = PipelineLogger(total_steps=6)
    logger.start("GERAÇÃO DE IMAGEM (GEMINI)")

    try:
        # --------------------------------------------------------------
        # 1️⃣ Contexto de execução (CORRETO)
        # --------------------------------------------------------------
        configurable = config.get("configurable", {})

        agent_context = configurable.get("context")
        if not agent_context:
            raise ValueError("AgentContext não encontrado no RunnableConfig")

        conversation = agent_context.conversation
        ref_img_path = agent_context.reference_image_path
        layout_img_path = agent_context.reference_layout_image_path

        # --------------------------------------------------------------
        # 2️⃣ State (opcional)
        # --------------------------------------------------------------
        state = configurable.get("state", {})

        reply_image_message = state.get("reply_image_message")
        attachments = state.get("attachments", [])
        aspect_ratio = state.get("aspect_ratio", "16:9")

        logger.step(
            step=1,
            message=(
                f"Modo: {'edição' if reply_image_message else 'geração'} | "
                f"Attachments: {len(attachments)} | "
                f"State: {state}"
            ),
            icon="🧠",
        )

        # --------------------------------------------------------------
        # [2/6] Validate params
        # --------------------------------------------------------------
        logger.step(2, "Validando parâmetros", "🧪")
        # Todo: verificar se necessario validar outras imagens
        aspect_ratio = step_validate_params(aspect_ratio, ref_img_path)
        logger.step_success()

        # --------------------------------------------------------------
        # [3/6] Init Gemini
        # --------------------------------------------------------------
        logger.step(3, "Inicializando Gemini", "🤖")
        step_init_gemini_client()
        logger.step_success()

        # --------------------------------------------------------------
        # [4/6] Prepare reference images
        # --------------------------------------------------------------
        logger.step(4, "Preparando imagens", "🖼️")
        reference_image, layout_reference, image_attachments = step_prepare_reference_images_from_state(
            conversation=conversation,
            reference_image_path=ref_img_path,
            reference_layout_image_path=layout_img_path,
            state=state,
        )
        logger.step_success()

        # --------------------------------------------------------------
        # [5/6] Call API
        # --------------------------------------------------------------
        logger.step(5, "Chamando Gemini", "⚡")
        image_bytes = step_call_gemini_api(
            prompt=prompt,
            reference_image=reference_image,
            layout_reference=layout_reference,
            image_attachments=image_attachments
        )
        logger.step_success()

        # --------------------------------------------------------------
        # [6/6] Save
        # --------------------------------------------------------------
        logger.step(6, "Salvando imagem", "💾")
        result = step_save_image(
            conversation=conversation,
            prompt=prompt,
            image_bytes=image_bytes,
            aspect_ratio=aspect_ratio,
        )

        logger.success("Pipeline concluído com sucesso")
        return result

    except Exception as e:
        logger.error("Erro na geração de imagem", e)
        raise


def get_agent_tools():
    """
    Retorna a lista de steps disponíveis para o agente.

    Returns:
        Lista de steps LangChain.
    """
    return [
        # search_documents,
        generate_image_gemini,
    ]
