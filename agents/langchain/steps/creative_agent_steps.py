import os
import pathlib
import time
from dataclasses import dataclass
from typing import Any, TypedDict, Optional, List

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI

from agents.langchain.tools import get_agent_tools
from agents.langchain.utils import md_to_token_friendly
from agents.models import Message, LLMUsage, GeneratedImage


# =========================================================
# Context & State Schemas
# =========================================================

@dataclass
class AgentContext:
    """Execution-only context (NOT visible to the LLM)."""
    conversation: Any
    reference_image_path: str
    reference_layout_image_path: str


class Attachment(TypedDict):
    name: str
    path: str
    mime_type: str
    size_bytes: int


class AgentState(TypedDict, total=False):
    reply_image_message: Optional[str]
    attachments: List[Attachment]


# =========================================================
# Prompt Loader
# =========================================================

import pathlib
from typing import List


def load_system_prompt_from_files() -> str:
    """
    Carrega múltiplos arquivos Markdown de prompts, processa para formato
    token-friendly e retorna um único system prompt consolidado.

    - Mantém os MDs originais para manutenção
    - Remove formatação Markdown
    - Garante ordem determinística (01_, 02_, ...)
    - Evita arquivos vazios
    - Usa separadores lógicos leves para LLM
    """

    fallback_prompt = (
        "Você é um assistente de IA especializado em geração e edição de imagens."
    )

    current_dir = pathlib.Path(__file__).parent
    prompts_dir = current_dir.parent / "prompts"

    if not prompts_dir.exists() or not prompts_dir.is_dir():
        print("✗ Pasta de prompts não encontrada ou inválida")
        return fallback_prompt

    prompt_contents: List[str] = []

    try:
        # Ordenação determinística por nome (01_, 02_, etc)
        prompt_files = sorted(prompts_dir.glob("*.md"), key=lambda f: f.name)

        if not prompt_files:
            print("✗ Nenhum arquivo .md encontrado na pasta de prompts")
            return fallback_prompt

        for file in prompt_files:
            try:
                with open(file, "r", encoding="utf-8") as f:
                    raw_content = f.read().strip()

                if not raw_content:
                    print(f"⚠️ Prompt vazio ignorado: {file.name}")
                    continue

                processed_content = md_to_token_friendly(raw_content)

                if not processed_content:
                    print(f"⚠️ Prompt sem conteúdo útil após processamento: {file.name}")
                    continue

                prompt_contents.append(
                    f"\n\n===== {file.stem.upper()} =====\n\n{processed_content}"
                )

                print(f"    ✓ Prompt carregado: {file.name}")

            except Exception as file_error:
                print(f"✗ Erro ao processar {file.name}: {file_error}")

        if not prompt_contents:
            print("✗ Nenhum prompt válido foi carregado")
            return fallback_prompt

        full_prompt = "".join(prompt_contents).strip()

        print("✓ System prompt montado com sucesso")
        return full_prompt

    except Exception as e:
        print(f"✗ Erro geral ao carregar prompts: {e}")
        return fallback_prompt


# =========================================================
# Agent Creation
# =========================================================

def create_creative_agent(
        model_name: str = "gpt-4o-mini",
        temperature: float = 0.7,
):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY não configurada")

    llm = ChatOpenAI(
        model=model_name,
        temperature=temperature,
        api_key=api_key,
    )

    tools = get_agent_tools()
    system_prompt = load_system_prompt_from_files()

    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=system_prompt,
        context_schema=AgentContext,
    )

    return agent


def get_agent_executor(
        model_name: str = "gpt-4o",
        temperature: float = 0.7,
):
    try:
        return create_creative_agent(
            model_name=model_name,
            temperature=temperature,
        )
    except Exception:
        import traceback
        traceback.print_exc()
        raise


# =========================================================
# Conversation Helpers
# =========================================================

def build_chat_history(conversation):
    try:
        chat_history = []

        previous_messages = (
            conversation.messages
            .exclude(role="system")
            .order_by("created_at")
        )

        for msg in previous_messages:
            if msg.role == "user":
                chat_history.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                chat_history.append(AIMessage(content=msg.content))

        return chat_history

    except Exception:
        import traceback
        traceback.print_exc()
        raise


def save_user_message(conversation, user_message, reply_image_message=None):
    try:
        Message.objects.create(
            conversation=conversation,
            role="user",
            content=user_message,
            reply_to_id=reply_image_message
        )
    except Exception:
        import traceback
        traceback.print_exc()
        raise


# =========================================================
# Context & State Preparation
# =========================================================

def prepare_agent_context_and_state(
        conversation: Any,
        chat_history: list,
        user_message: str,
        reply_image_message: Optional[str] = None,
        attachments: Optional[list] = None,
):
    start_time = time.time()

    messages = []
    messages.extend(chat_history)

    state: AgentState = {}
    system_messages = []

    # -----------------------------
    # Attachments (ANTES do user message)
    # -----------------------------
    file_attachments = []
    file_descriptions = []

    if attachments:
        for file in attachments:
            if file.content_type.startswith("image/"):
                file_attachments.append(file)
            else:
                file_descriptions.append(
                    f"- {file.name} ({file.content_type}, {file.size} bytes)"
                )

    # 📸 Images → state
    if file_attachments:
        state["attachments"] = file_attachments

        system_messages.append(
            SystemMessage(
                content=(
                    "O usuário enviou uma ou mais imagens anexas. "
                    "Quando o usuário disser 'essa imagem' ou 'essa logo', "
                    "ele está se referindo às imagens anexadas nesta mensagem."
                )
            )
        )

    # 📎 Outros arquivos
    if file_descriptions:
        system_messages.append(
            SystemMessage(
                content=(
                        "O usuário também enviou os seguintes arquivos:\n"
                        + "\n".join(file_descriptions)
                )
            )
        )

    # -----------------------------
    # Reply image (edição)
    # -----------------------------
    if reply_image_message:
        image = (
            GeneratedImage.objects
            .filter(
                conversation=conversation,
                message_id=reply_image_message,
            )
            .order_by("-created_at")
            .first()
        )

        if image and image.image_url:
            state["reply_image_message"] = image.image_url
            system_messages.append(
                SystemMessage(
                    content=(
                        "O usuário está editando uma imagem existente. "
                        "Use a imagem referenciada como base."
                    )
                )
            )

    # -----------------------------
    # Inject system messages
    # -----------------------------
    if system_messages:
        messages.extend(system_messages)

    # -----------------------------
    # User instruction (FINAL)
    # -----------------------------
    messages.append(
        HumanMessage(
            content=user_message
        )
    )

    agent_context = AgentContext(
        conversation=conversation,
        reference_image_path=str(
            pathlib.Path(__file__).parent.parent / "data" / "template.png"
        ),
        reference_layout_image_path=str(
            pathlib.Path(__file__).parent.parent / "data" / "layout.png"
        ),
    )

    return messages, agent_context, state, start_time


# =========================================================
# Agent Invocation (NEW FORMAT)
# =========================================================

def invoke_agent(
        agent_executor,
        messages: list,
        agent_context: AgentContext,
        state: Optional[AgentState] = None,
):
    try:
        payload = {"messages": messages}

        config: RunnableConfig = {
            "context": agent_context,
            "configurable": {},
        }

        if state:
            config["configurable"]["state"] = state

        return agent_executor.invoke(
            payload,
            config=config,
        )

    except Exception:
        import traceback
        traceback.print_exc()
        raise


# =========================================================
# Agent Response Processing
# =========================================================

def process_agent_response(result: dict, start_time: float):
    try:
        response_time_ms = int((time.time() - start_time) * 1000)

        agent_messages = result.get("messages", [])
        response_text = ""

        if agent_messages:
            last_message = agent_messages[-1]
            response_text = (
                last_message.content
                if hasattr(last_message, "content")
                else str(last_message)
            )

        return response_text, response_time_ms

    except Exception:
        import traceback
        traceback.print_exc()
        raise


# =========================================================
# Persistence & Usage Tracking
# =========================================================

def save_assistant_response_and_usage(
        conversation: Any,
        response_text: str,
        user_message: str,
        chat_history: list,
        response_time_ms: int,
        model_name: str,
):
    try:
        assistant_msg = Message.objects.create(
            conversation=conversation,
            role="assistant",
            content=response_text,
        )

        base_tokens = len(user_message) // 4
        output_tokens = len(response_text) // 4

        input_tokens = base_tokens
        input_cost_per_1k = 0.0025
        output_cost_per_1k = 0.0100

        input_cost = (input_tokens / 1000) * input_cost_per_1k
        output_cost = (output_tokens / 1000) * output_cost_per_1k

        llm_usage = LLMUsage.objects.create(
            message=assistant_msg,
            provider="openai",
            model_name=model_name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            input_cost=input_cost,
            output_cost=output_cost,
            response_time_ms=response_time_ms,
            context_size=len(chat_history),
        )

        return assistant_msg, llm_usage, input_tokens, output_tokens

    except Exception:
        import traceback
        traceback.print_exc()
        raise
