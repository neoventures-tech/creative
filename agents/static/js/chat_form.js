document.getElementById('chatForm').addEventListener('submit', async function (e) {
    e.preventDefault();

    const form = document.getElementById('chatForm');
    const messageInput = document.getElementById('messageInput');
    const fileInput = document.getElementById('fileInput');

    const message = form.elements['message'].value;
    const replyImageMessage = form.elements['reply_image_message']?.value;
    const file = fileInput?.files[0];

    if (!message && !file) return;

    // show loading
    document.getElementById('loadingMessage').classList.remove('d-none');

    // build form data
    const formData = new FormData();
    formData.append('message', message);
    formData.append('model_name', 'gpt-4o');
    formData.append('temperature', 0.7);

    if (replyImageMessage) {
        formData.append('reply_image_message', replyImageMessage);
    }

    if (file) {
        for (const file of fileInput.files) {
            formData.append('attachment', file);
        }
    }

    // clear input
    messageInput.value = '';
    fileInput.value = '';

    // scroll to bottom
    const messagesContainer = document.getElementById('messagesContainer');
    messagesContainer.scrollTop = messagesContainer.scrollHeight;

    // hide reply
    hideReply();
    clearReplyData();

    try {
        const chatUrl = form.dataset.chatUrl;
        const response = await fetch(chatUrl, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (response.ok) {
            location.reload();
        } else {
            alert('Erro: ' + (data.error || 'Erro ao enviar mensagem'));
            document.getElementById('loadingMessage').classList.add('d-none');
        }
    } catch (error) {
        console.error('Erro:', error);
        alert('Erro ao conectar com o servidor');
        document.getElementById('loadingMessage').classList.add('d-none');
    }
});


// Auto-scroll to bottom on load
window.addEventListener('load', function () {
    const messagesContainer = document.getElementById('messagesContainer');
    messagesContainer.scrollTop = messagesContainer.scrollHeight;

    // Retornar foco para o input após reload
    const messageInput = document.getElementById('messageInput');
    messageInput.focus();
});

// Attachments
document.getElementById('attachBtn').addEventListener('click', function () {
    document.getElementById('fileInput').click();
});