"""
Views para Neo Creative - Sistema de geração de imagens com IA.
"""
import os
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, DeleteView
from django.views import View
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
import json

from .models import Conversation, Message, GeneratedImage
from .langchain.creative_agent import chat_with_agent


class HomeView(View):
    """Landing page do Neo Creative."""

    def get(self, request):
        # Se o usuário estiver autenticado, mostra a home
        # Senão, também mostra a home (público)
        return render(request, 'agents/home.html')


class ConversationListView(LoginRequiredMixin, ListView):
    """Lista todas as conversas do usuário."""
    model = Conversation
    template_name = 'agents/conversation_list.html'
    context_object_name = 'conversations'
    paginate_by = 20

    def get_queryset(self):
        """Filtra conversas do usuário autenticado."""
        return Conversation.objects.filter(user=self.request.user).order_by('-updated_at')


class ConversationDetailView(LoginRequiredMixin, DetailView):
    """Exibe detalhes de uma conversa e permite chat."""
    model = Conversation
    template_name = 'agents/conversation_detail.html'
    context_object_name = 'conversation'

    def get_queryset(self):
        """Apenas conversas do usuário logado."""
        return Conversation.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        conversation = self.get_object()
        context['chat_messages'] = conversation.messages.all().order_by('created_at')
        context['generated_images'] = conversation.generated_images.all().order_by('-created_at')
        return context


class ConversationCreateView(LoginRequiredMixin, View):
    """Cria uma nova conversa e redireciona direto para ela."""

    def get(self, request):
        # Cria a conversa para o usuário logado
        conversation = Conversation.objects.create(user=request.user)

        # Envia a primeira mensagem automaticamente
        try:
            chat_with_agent(
                conversation=conversation,
                user_message="vamos lá",
                model_name='gpt-4o',
                temperature=0.7
            )
        except Exception as e:
            messages.warning(request, f'Conversa criada, mas houve um erro ao enviar a primeira mensagem: {str(e)}')

        messages.success(request, 'Conversa criada com sucesso!')
        # Redireciona para a página de detalhes da conversa
        return redirect('agents:conversation_detail', pk=conversation.pk)


class ConversationDeleteView(LoginRequiredMixin, DeleteView):
    """Deleta uma conversa."""
    model = Conversation
    template_name = 'agents/conversation_confirm_delete.html'
    success_url = reverse_lazy('agents:conversation_list')

    def get_queryset(self):
        """Apenas conversas do usuário logado."""
        return Conversation.objects.filter(user=self.request.user)

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Conversa deletada com sucesso!')
        return super().delete(request, *args, **kwargs)


@method_decorator([csrf_exempt, login_required], name='dispatch')
class ChatView(View):
    """View para enviar mensagens ao agente via AJAX."""

    def post(self, request, pk):
        try:
            # Buscar apenas conversas do usuário logado
            conversation = get_object_or_404(Conversation, pk=pk, user=request.user)

            # Parse JSON data
            data = json.loads(request.body)
            user_message = data.get('message', '')
            model_name = data.get('model_name', 'gpt-4o')
            temperature = float(data.get('temperature', 0.7))

            if not user_message:
                return JsonResponse({'error': 'Mensagem vazia'}, status=400)

            # Enviar para o agente
            result = chat_with_agent(
                conversation=conversation,
                user_message=user_message,
                model_name=model_name,
                temperature=temperature
            )

            return JsonResponse(result)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


class GeneratedImageListView(LoginRequiredMixin, ListView):
    """Lista todas as imagens geradas."""
    model = GeneratedImage
    template_name = 'agents/generated_image_list.html'
    context_object_name = 'images'
    paginate_by = 20

    def get_queryset(self):
        """Filtra imagens do usuário autenticado."""
        return GeneratedImage.objects.filter(
            conversation__user=self.request.user
        ).order_by('-created_at')
