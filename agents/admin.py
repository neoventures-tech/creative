"""
Admin para Neo Creative.
"""
from django.contrib import admin
from .models import Conversation, Message, GeneratedImage, LLMUsage, Attachment


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    fields = ('role', 'content', 'created_at')
    readonly_fields = ('created_at',)
    can_delete = False


class GeneratedImageInline(admin.TabularInline):
    model = GeneratedImage
    extra = 0
    fields = ('prompt', 'image_url', 'model', 'size', 'quality', 'created_at')
    readonly_fields = ('created_at',)
    can_delete = False


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'created_at', 'updated_at', 'message_count')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('user__username',)
    readonly_fields = ('created_at', 'updated_at')
    inlines = [MessageInline, GeneratedImageInline]

    def message_count(self, obj):
        return obj.messages.count()

    message_count.short_description = 'Mensagens'


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'conversation', 'role', 'content_preview', 'created_at')
    list_filter = ('role', 'created_at')
    search_fields = ('content', 'conversation__id')
    readonly_fields = ('created_at',)

    def content_preview(self, obj):
        return obj.content[:100] + '...' if len(obj.content) > 100 else obj.content

    content_preview.short_description = 'Conteúdo'


@admin.register(GeneratedImage)
class GeneratedImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'conversation', 'prompt_preview', 'model', 'size', 'quality', 'created_at')
    list_filter = ('model', 'size', 'quality', 'created_at')
    search_fields = ('prompt', 'revised_prompt', 'conversation__id')
    readonly_fields = ('created_at',)

    def prompt_preview(self, obj):
        return obj.prompt[:100] + '...' if len(obj.prompt) > 100 else obj.prompt

    prompt_preview.short_description = 'Prompt'


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "attachment_type",
        "name",
        "mime_type",
        "size",
        "message",
        "created_at",
    )

    list_filter = (
        "attachment_type",
        "mime_type",
        "created_at",
    )

    search_fields = (
        "name",
        "mime_type",
        "message__content",
        "message__conversation__id",
    )

    readonly_fields = (
        "created_at",
        "size",
        "mime_type",
    )

    ordering = ("-created_at",)

    raw_id_fields = ("message",)

    def save_model(self, request, obj, form, change):
        """
        Auto-fill metadata if missing.
        """
        if obj.file:
            if not obj.name:
                obj.name = obj.file.name

            if not obj.mime_type:
                obj.mime_type = getattr(obj.file, "content_type", "")

            if not obj.size:
                obj.size = obj.file.size

        super().save_model(request, obj, form, change)


@admin.register(LLMUsage)
class LLMUsageAdmin(admin.ModelAdmin):
    list_display = ('id', 'provider', 'model_name', 'total_tokens', 'total_cost', 'response_time_ms', 'created_at')
    list_filter = ('provider', 'model_name', 'created_at')
    search_fields = ('provider', 'model_name', 'question')
    readonly_fields = ('created_at', 'total_tokens', 'total_cost')
