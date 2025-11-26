from django.db import models
from django.conf import settings

# Create your models here.

class Conversation(models.Model):
    """
    Armazena conversas com a IA para geração de imagens.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='neo_conversations',
        null=True,
        blank=True,
        verbose_name='Usuário'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Conversa"
        verbose_name_plural = "Conversas"
        ordering = ['-updated_at']

    def __str__(self):
        user_name = self.user.username if self.user else "Anônimo"
        return f"Conversa {self.id} - {user_name}"


class Message(models.Model):
    """
    Armazena mensagens trocadas na conversa.
    """
    ROLE_CHOICES = [
        ('user', 'Usuário'),
        ('assistant', 'Assistente'),
        ('system', 'Sistema'),
    ]

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name='Conversa'
    )

    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        verbose_name='Papel'
    )

    content = models.TextField(
        verbose_name='Conteúdo',
        help_text='Conteúdo da mensagem em texto'
    )

    response = models.TextField(verbose_name='Resposta da IA', blank=True, null=True)


    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Mensagem"
        verbose_name_plural = "Mensagens"
        ordering = ['created_at']

    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."


class GeneratedImage(models.Model):
    """
    Armazena imagens geradas pelo DALL·E.
    """
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='generated_images',
        verbose_name='Conversa'
    )

    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='generated_images',
        verbose_name='Mensagem',
        null=True,
        blank=True
    )

    prompt = models.TextField(
        verbose_name='Prompt',
        help_text='Prompt usado para gerar a imagem'
    )

    image_url = models.URLField(
        max_length=2000,
        verbose_name='URL da Imagem',
        help_text='URL da imagem gerada pelo DALL·E'
    )

    revised_prompt = models.TextField(
        verbose_name='Prompt Revisado',
        help_text='Prompt revisado pelo DALL·E',
        blank=True
    )

    model = models.CharField(
        max_length=50,
        default='dall-e-3',
        verbose_name='Modelo'
    )

    size = models.CharField(
        max_length=20,
        default='1024x1024',
        verbose_name='Tamanho'
    )

    quality = models.CharField(
        max_length=20,
        default='standard',
        verbose_name='Qualidade'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Imagem Gerada"
        verbose_name_plural = "Imagens Geradas"
        ordering = ['-created_at']

    def __str__(self):
        return f"Imagem {self.id} - {self.prompt[:50]}..."


class LLMUsage(models.Model):
    """
    Rastreamento de uso e custos de chamadas à LLM.

    Armazena métricas de cada chamada ao modelo de IA para:
    - Estimar custos
    - Monitorar uso
    - Identificar conversas caras
    - Otimizar prompts
    """

    # Relacionamento com Message (opcional para manter compatibilidade)
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='llm_usages',
        null=True,
        blank=True,
        verbose_name='Mensagem',
        help_text='Mensagem associada a este uso de LLM'
    )

    # Identificação da chamada
    question = models.TextField(
        verbose_name="Pergunta",
        help_text="Pergunta feita pelo usuário",
        null=True,
        blank=True
    )

    # Informações do modelo
    provider = models.CharField(
        max_length=50,
        verbose_name="Provedor",
        help_text="Ex: openai, anthropic, google"
    )

    model_name = models.CharField(
        max_length=100,
        verbose_name="Modelo",
        help_text="Ex: gpt-4o, claude-3-5-sonnet-20241022"
    )

    # Tokens
    input_tokens = models.IntegerField(
        default=0,
        verbose_name="Tokens de Entrada",
        help_text="Tokens enviados (prompt + contexto)"
    )

    output_tokens = models.IntegerField(
        default=0,
        verbose_name="Tokens de Saída",
        help_text="Tokens gerados na resposta"
    )

    total_tokens = models.IntegerField(
        default=0,
        verbose_name="Total de Tokens",
        help_text="Soma de entrada + saída"
    )

    # Tokens em cache (para Anthropic prompt caching)
    cache_creation_tokens = models.IntegerField(
        default=0,
        verbose_name="Tokens de Criação de Cache",
        help_text="Tokens usados para criar o cache (Anthropic)"
    )

    cache_read_tokens = models.IntegerField(
        default=0,
        verbose_name="Tokens Lidos do Cache",
        help_text="Tokens lidos do cache (Anthropic - ~90% desconto)"
    )

    # Custos estimados (em USD)
    input_cost = models.DecimalField(
        max_digits=10,
        decimal_places=6,
        default=0,
        verbose_name="Custo de Entrada (USD)",
        help_text="Custo estimado dos tokens de entrada"
    )

    output_cost = models.DecimalField(
        max_digits=10,
        decimal_places=6,
        default=0,
        verbose_name="Custo de Saída (USD)",
        help_text="Custo estimado dos tokens de saída"
    )

    cache_creation_cost = models.DecimalField(
        max_digits=10,
        decimal_places=6,
        default=0,
        verbose_name="Custo de Criação de Cache (USD)"
    )

    cache_read_cost = models.DecimalField(
        max_digits=10,
        decimal_places=6,
        default=0,
        verbose_name="Custo de Leitura de Cache (USD)"
    )

    total_cost = models.DecimalField(
        max_digits=10,
        decimal_places=6,
        default=0,
        verbose_name="Custo Total (USD)",
        help_text="Soma de todos os custos"
    )

    # Metadados adicionais
    response_time_ms = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="Tempo de Resposta (ms)",
        help_text="Tempo em milissegundos da chamada"
    )

    context_size = models.IntegerField(
        default=0,
        verbose_name="Tamanho do Contexto",
        help_text="Número de caracteres do contexto adicional carregado"
    )

    tools_used = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Ferramentas Usadas",
        help_text="Lista de ferramentas chamadas nesta interação"
    )

    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Uso de LLM"
        verbose_name_plural = "Usos de LLM"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['provider', 'model_name']),
        ]

    def __str__(self):
        return f"{self.provider}/{self.model_name} - {self.total_tokens} tokens - ${self.total_cost}"

    def save(self, *args, **kwargs):
        """Calcula totais antes de salvar"""
        self.total_tokens = self.input_tokens + self.output_tokens
        self.total_cost = (
            self.input_cost +
            self.output_cost +
            self.cache_creation_cost +
            self.cache_read_cost
        )
        super().save(*args, **kwargs)

