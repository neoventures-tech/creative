"""
Serializers para a API do Neo Creative.
"""
from rest_framework import serializers
from .models import Conversation, Message, GeneratedImage, LLMUsage


class ExampleImageSerializer(serializers.ModelSerializer):
    """Serializer para imagens de exemplo."""

    class Meta:
        model = ExampleImage
        fields = ['id', 'image', 'description', 'created_at']
        read_only_fields = ['id', 'created_at']


class GeneratedImageSerializer(serializers.ModelSerializer):
    """Serializer para imagens geradas."""

    class Meta:
        model = GeneratedImage
        fields = [
            'id', 'prompt', 'image_url', 'revised_prompt',
            'model', 'size', 'quality', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class MessageSerializer(serializers.ModelSerializer):
    """Serializer para mensagens."""

    generated_images = GeneratedImageSerializer(many=True, read_only=True)

    class Meta:
        model = Message
        fields = ['id', 'role', 'content', 'created_at', 'generated_images']
        read_only_fields = ['id', 'created_at']


class ConversationSerializer(serializers.ModelSerializer):
    """Serializer para conversas."""

    messages = MessageSerializer(many=True, read_only=True)
    example_images = ExampleImageSerializer(many=True, read_only=True)
    generated_images = GeneratedImageSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = [
            'id', 'user', 'system_prompt',
            'messages', 'example_images', 'generated_images',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ConversationCreateSerializer(serializers.ModelSerializer):
    """Serializer para criação de conversas."""

    class Meta:
        model = Conversation
        fields = ['system_prompt']


class ChatMessageSerializer(serializers.Serializer):
    """Serializer para enviar mensagens ao agente."""

    message = serializers.CharField(required=True, help_text="Mensagem do usuário")
    model_name = serializers.CharField(
        default="gpt-4o",
        help_text="Modelo OpenAI a usar (gpt-4o, gpt-4-turbo, etc.)"
    )
    temperature = serializers.FloatField(
        default=0.7,
        min_value=0.0,
        max_value=2.0,
        help_text="Temperatura para criatividade (0-1)"
    )


class ChatResponseSerializer(serializers.Serializer):
    """Serializer para resposta do agente."""

    response = serializers.CharField(help_text="Resposta do assistente")
    message_id = serializers.IntegerField(help_text="ID da mensagem salva")
    usage = serializers.DictField(help_text="Informações de uso e custos")


class LLMUsageSerializer(serializers.ModelSerializer):
    """Serializer para uso de LLM."""

    class Meta:
        model = LLMUsage
        fields = [
            'id', 'provider', 'model_name',
            'input_tokens', 'output_tokens', 'total_tokens',
            'input_cost', 'output_cost', 'total_cost',
            'response_time_ms', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']