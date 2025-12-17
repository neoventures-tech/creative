document.addEventListener('DOMContentLoaded', function () {
    const newConversationBtn = document.getElementById('newConversationBtn');
    if (newConversationBtn) {
        newConversationBtn.addEventListener('click', function (e) {
            // Desabilitar o botão
            this.style.pointerEvents = 'none';
            this.style.opacity = '0.6';

            // Mudar o conteúdo para mostrar loading
            const originalContent = this.innerHTML;
            this.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Criando...';
        });
    }
});