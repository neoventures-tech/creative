"""
URLs para Neo Creative.
"""
from django.urls import path
from .views import (
    HomeView,
    ConversationListView,
    ConversationDetailView,
    ConversationCreateView,
    ConversationDeleteView,
    ChatView,
    GeneratedImageListView,
)

app_name = 'agents'

urlpatterns = [
    # Home
    path('', HomeView.as_view(), name='home'),

    # Conversas
    path('conversations/', ConversationListView.as_view(), name='conversation_list'),
    path('conversation/new/', ConversationCreateView.as_view(), name='conversation_create'),
    path('conversation/<int:pk>/', ConversationDetailView.as_view(), name='conversation_detail'),
    path('conversation/<int:pk>/delete/', ConversationDeleteView.as_view(), name='conversation_delete'),

    # Chat (AJAX)
    path('conversation/<int:pk>/chat/', ChatView.as_view(), name='chat'),

    # Galeria de imagens geradas
    path('images/', GeneratedImageListView.as_view(), name='generated_image_list'),
]