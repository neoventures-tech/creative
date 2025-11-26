"""
Agente criativo para geração de imagens com DALL·E 3.
Suporta conversação com contexto de imagens de exemplo.
"""
import os
import pathlib
import time
import base64
from typing import List, Dict, Any
from pathlib import Path
from dataclasses import dataclass
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from agents.langchain.tools import get_agent_tools


@dataclass
class AgentContext:
    """Schema do contexto passado para as tools via ToolRuntime."""
    conversation: Any
    reference_image_path: str


def load_system_prompt_from_file() -> str:
    """
    Carrega o system prompt do arquivo system_prompt.md.

    Returns:
        String com o conteúdo do system prompt
    """
    current_dir = Path(__file__).parent
    prompt_file = current_dir / "system_prompt.md"

    try:
        with open(prompt_file, 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"✓ System prompt carregado de: {prompt_file.name}")
        return content
    except Exception as e:
        print(f"✗ Erro ao carregar system prompt: {e}")
        return "Você é um assistente de IA especializado em gerar imagens criativas usando DALL·E 3."

def create_creative_agent(
    conversation: Any,
    model_name: str = "gpt-4o-mini",
    temperature: float = 0.7
):
    """
    Cria um agente criativo para conversação e geração de imagens.

    Args:
        conversation: Instância do modelo Conversation
        model_name: Nome do modelo OpenAI a usar
        temperature: Temperatura para criatividade (0-1)

    Returns:
        Agente LangGraph configurado
    """
    # Configurar LLM
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY não configurada")

    llm = ChatOpenAI(
        model=model_name,
        temperature=temperature,
        api_key=api_key
    )

    # Obter tools
    tools = get_agent_tools()

    # Carregar system prompt do arquivo .md
    system_prompt = load_system_prompt_from_file()

    # Criar agente usando LangChain
    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=system_prompt,
        context_schema=AgentContext,
    )

    return agent


def chat_with_agent(
    conversation: Any,
    user_message: str,
    model_name: str = "gpt-4o-mini",
    temperature: float = 0.7
) -> Dict[str, Any]:
    """
    Envia uma mensagem do usuário (apenas texto) para o agente.

    O contexto de treinamento (system_prompt.md + imagens) é carregado
    automaticamente apenas na primeira mensagem.

    Args:
        conversation: Instância do modelo Conversation
        user_message: Mensagem em texto do usuário (SEM imagens)
        model_name: Nome do modelo OpenAI
        temperature: Temperatura para criatividade

    Returns:
        Dict com 'response', 'usage' e metadados
    """
    from agents.models import Message, LLMUsage

    try:
        print("\n" + "="*80)
        print("🔍 INÍCIO DO PROCESSAMENTO")
        print("="*80)

        # Criar agente (carrega system_prompt.md automaticamente)
        print("\n📝 [1/7] Criando agente...")
        try:
            agent_executor = create_creative_agent(
                conversation=conversation,
                model_name=model_name,
                temperature=temperature
            )
            print("✓ Agente criado com sucesso")
        except Exception as e:
            print(f"✗ ERRO ao criar agente: {e}")
            import traceback
            traceback.print_exc()
            raise

        # Carregar histórico da conversa (exceto mensagens de sistema)
        print("\n📚 [2/7] Carregando histórico da conversa...")
        try:
            chat_history = []
            previous_messages = conversation.messages.exclude(role='system').order_by('created_at')

            for msg in previous_messages:
                if msg.role == "user":
                    chat_history.append(HumanMessage(content=msg.content))
                elif msg.role == "assistant":
                    chat_history.append(AIMessage(content=msg.content))

            print(f"✓ Histórico carregado: {len(chat_history)} mensagens")
        except Exception as e:
            print(f"✗ ERRO ao carregar histórico: {e}")
            import traceback
            traceback.print_exc()
            raise

        # Salvar mensagem do usuário
        print("\n💾 [3/7] Salvando mensagem do usuário...")
        try:
            Message.objects.create(
                conversation=conversation,
                role="user",
                content=user_message
            )
            print("✓ Mensagem salva")
        except Exception as e:
            print(f"✗ ERRO ao salvar mensagem: {e}")
            import traceback
            traceback.print_exc()
            raise

        # Invocar agente
        print("\n🤖 [4/7] Preparando contexto do agente...")
        try:
            start_time = time.time()

            # Montar mensagens: [contexto de imagens] + [histórico] + [mensagem atual]
            messages = []

            # Adicionar histórico
            messages.extend(chat_history)

            # Adicionar mensagem atual do usuário (apenas texto)
            messages.append(HumanMessage(content=user_message))

            reference_image_path = str(pathlib.Path(__file__).parent / "data" / "template.jpeg")
            print(f"   Caminho da imagem: {reference_image_path}")
            print(f"   Total de mensagens: {len(messages)}")

            # Criar contexto usando o dataclass
            agent_context = AgentContext(
                conversation=conversation,
                reference_image_path=reference_image_path
            )
            print("✓ Contexto preparado")
        except Exception as e:
            print(f"✗ ERRO ao preparar contexto: {e}")
            import traceback
            traceback.print_exc()
            raise

        print("\n🚀 [5/7] Invocando agente LLM...")
        try:
            result = agent_executor.invoke(
                {"messages": messages},
                context=agent_context,
            )
            print("✓ Agente invocado com sucesso")
        except Exception as e:
            print(f"✗ ERRO ao invocar agente: {e}")
            import traceback
            traceback.print_exc()
            raise

        print("\n📊 [6/7] Processando resposta...")
        try:
            response_time_ms = int((time.time() - start_time) * 1000)

            # Extrair resposta da última mensagem do agente
            agent_messages = result.get("messages", [])
            response_text = ""
            if agent_messages:
                last_message = agent_messages[-1]
                response_text = last_message.content if hasattr(last_message, 'content') else str(last_message)

            print(f"✓ Resposta extraída ({len(response_text)} caracteres)")
        except Exception as e:
            print(f"✗ ERRO ao processar resposta: {e}")
            import traceback
            traceback.print_exc()
            raise

        print("\n💾 [7/7] Salvando resposta e calculando custos...")
        try:
            # Salvar resposta do assistente
            assistant_msg = Message.objects.create(
                conversation=conversation,
                role="assistant",
                content=response_text
            )

            # Estimar tokens e custos
            # Nota: Se há contexto de imagens, o custo será maior
            base_tokens = len(user_message) // 4
            output_tokens = len(response_text) // 4

            # Adicionar tokens das imagens (se houver contexto)
            # image_tokens = len(training_context) * 765 if training_context else 0  # ~765 tokens por imagem em alta resolução
            image_tokens =  0  # ~765 tokens por imagem em alta resolução
            input_tokens = base_tokens + image_tokens

            # Custos do GPT-4o
            input_cost_per_1k = 0.0025  # $2.50 por 1M tokens
            output_cost_per_1k = 0.010   # $10.00 por 1M tokens

            input_cost = (input_tokens / 1000) * input_cost_per_1k
            output_cost = (output_tokens / 1000) * output_cost_per_1k

            # Salvar uso
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

            print(f"✓ Dados salvos - Custo total: ${llm_usage.total_cost:.6f}")
            print("\n" + "="*80)
            print("✅ PROCESSAMENTO CONCLUÍDO COM SUCESSO")
            print("="*80 + "\n")

        except Exception as e:
            print(f"✗ ERRO ao salvar dados: {e}")
            import traceback
            traceback.print_exc()
            raise

        return {
            "response": response_text,
            "message_id": assistant_msg.id,
            "usage": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
                "total_cost": float(llm_usage.total_cost),
                "response_time_ms": response_time_ms,
                "training_images_loaded":  0,
            }
        }

    except Exception as e:
        import traceback
        traceback.print_exc()

        return {
            "response": f"Erro ao processar mensagem: {str(e)}",
            "error": str(e),
            "usage": {
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0,
                "total_cost": 0.0,
                "response_time_ms": 0,
                "training_images_loaded": False,
            }
        }