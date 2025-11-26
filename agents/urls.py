"""
URLs para Neo Creative.
"""
from django.urls import path
from .views import (
    ConversationListView,
    ConversationDetailView,
    ConversationCreateView,
    ConversationUpdateView,
    ConversationDeleteView,
    ChatView,
    GeneratedImageListView,
)

app_name = 'agents'

urlpatterns = [
    # Conversas
    path('', ConversationListView.as_view(), name='conversation_list'),
    path('conversation/new/', ConversationCreateView.as_view(), name='conversation_create'),
    path('conversation/<int:pk>/', ConversationDetailView.as_view(), name='conversation_detail'),
    path('conversation/<int:pk>/edit/', ConversationUpdateView.as_view(), name='conversation_update'),
    path('conversation/<int:pk>/delete/', ConversationDeleteView.as_view(), name='conversation_delete'),

    # Chat (AJAX)
    path('conversation/<int:pk>/chat/', ChatView.as_view(), name='chat'),

    # Imagens de exemplo
    # Galeria de imagens geradas
    path('images/', GeneratedImageListView.as_view(), name='generated_image_list'),
]