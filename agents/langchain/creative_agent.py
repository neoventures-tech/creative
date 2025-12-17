"""
Agente criativo para geração de imagens com Gemini.
Suporta conversação com contexto de imagens de exemplo.
"""
from typing import Dict, Any

from agents.langchain.steps.creative_agent_steps import get_agent_executor, build_chat_history, save_user_message, \
    prepare_agent_context_and_state, invoke_agent, process_agent_response, save_assistant_response_and_usage, Attachment
from agents.langchain.utils import PipelineLogger


def chat_with_agent(
        conversation: Any,
        user_message: str,
        model_name: str = "gpt-4o-mini",
        temperature: float = 0.7,
        reply_image_message: str | None = None,
        attachments: list[Attachment] | None = None,
) -> Dict[str, Any]:
    """
    Envia uma mensagem do usuário (apenas texto) para o agente,
    suportando STATE e CONFIG no novo formato.
    """

    try:
        logger = PipelineLogger(total_steps=7)
        logger.start()

        # --------------------------------------------------------------
        # [1/7] Create agent executor
        # --------------------------------------------------------------
        logger.step(1, "Criando agente...", "📝")
        agent_executor = get_agent_executor(
            model_name=model_name,
            temperature=temperature,
        )
        logger.step_success("Agente criado")

        # --------------------------------------------------------------
        # [2/7] Build chat history
        # --------------------------------------------------------------
        logger.step(2, "Carregando histórico da conversa...", "📚")
        chat_history = build_chat_history(conversation)
        logger.step_success(f"{len(chat_history)} mensagens carregadas")

        # --------------------------------------------------------------
        # [3/7] Save user message
        # --------------------------------------------------------------
        logger.step(3, "Salvando mensagem do usuário...", "💾")
        save_user_message(conversation, user_message, reply_image_message)
        logger.step_success("Mensagem do usuário salva")

        # --------------------------------------------------------------
        # [4/7] Prepare agent context + state
        # --------------------------------------------------------------
        logger.step(4, "Preparando contexto do agente...", "🤖")
        messages, agent_context, state, start_time = prepare_agent_context_and_state(
            conversation=conversation,
            chat_history=chat_history,
            user_message=user_message,
            reply_image_message=reply_image_message,
            attachments=attachments,
        )
        logger.step_success(
            f"Contexto preparado ({len(messages)} mensagens, "
            f"state keys: {list(state.keys()) if state else []})"
        )

        # --------------------------------------------------------------
        # [5/7] Invoke agent (NEW CONFIG FORMAT)
        # --------------------------------------------------------------
        logger.step(5, "Invocando agente LLM...", "🚀")
        result = invoke_agent(
            agent_executor=agent_executor,
            messages=messages,
            agent_context=agent_context,
            state=state,
        )
        logger.step_success("Agente invocado")

        # --------------------------------------------------------------
        # [6/7] Process response
        # --------------------------------------------------------------
        logger.step(6, "Processando resposta do agente...", "📊")
        response_text, response_time_ms = process_agent_response(
            result,
            start_time,
        )
        logger.step_success(f"Resposta extraída ({len(response_text)} chars)")

        # --------------------------------------------------------------
        # [7/7] Save response and usage
        # --------------------------------------------------------------
        logger.step(7, "Salvando resposta e métricas de uso...", "💾")
        assistant_msg, llm_usage, input_tokens, output_tokens = (
            save_assistant_response_and_usage(
                conversation=conversation,
                response_text=response_text,
                user_message=user_message,
                chat_history=chat_history,
                response_time_ms=response_time_ms,
                model_name=model_name,
            )
        )
        logger.step_success(
            f"Uso salvo — input: {input_tokens}, output: {output_tokens}"
        )

        logger.success()

        return {
            "response": response_text,
            "message_id": assistant_msg.id,
            "usage": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
                "total_cost": float(llm_usage.total_cost),
                "response_time_ms": response_time_ms,
                "training_images_loaded": False,
            },
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
            },
        }
