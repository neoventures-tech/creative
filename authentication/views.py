"""
Views de autenticação.
"""
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views import View


class LoginView(View):
    """View para login de usuários."""

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('agents:home')

        form = AuthenticationForm()
        return render(request, 'authentication/login.html', {'form': form})

    def post(self, request):
        form = AuthenticationForm(data=request.POST)

        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Bem-vindo, {user.username}!')

            # Redireciona para a página solicitada ou para a home
            next_url = request.GET.get('next', 'agents:home')
            return redirect(next_url)

        messages.error(request, 'Usuário ou senha inválidos.')
        return render(request, 'authentication/login.html', {'form': form})


class LogoutView(View):
    """View para logout de usuários."""

    def get(self, request):
        logout(request)
        messages.success(request, 'Você saiu com sucesso.')
        return redirect('agents:home')