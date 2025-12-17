function clearReplyData() {
    const form = document.getElementById('chatForm');

    ['reply_image_message']
        .forEach(name => {
            const input = form.querySelector(`input[name="${name}"]`);
            if (input) input.remove();
        });
}

function upsertHiddenInput(form, name, value) {
    let input = form.querySelector(`input[name="${name}"]`);

    if (!input) {
        input = document.createElement('input');
        input.type = 'hidden';
        input.name = name;
        form.appendChild(input);
    }

    input.value = value ?? '';
}

function showReply() {
    const replyContainer = document.getElementById('reply-container');

    replyContainer.classList.remove('d-none');

    // force reflow so transition works
    replyContainer.offsetHeight;

    replyContainer.classList.remove('reply-hidden');
    replyContainer.classList.add('reply-visible');
}

function hideReply() {

    const replyContainer = document.getElementById('reply-container');

    replyContainer.classList.remove('reply-visible');
    replyContainer.classList.add('reply-hidden');

    replyContainer.addEventListener('transitionend', function handler() {
        replyContainer.classList.add('d-none');
        replyContainer.removeEventListener('transitionend', handler);
    });
}

function setReplyMessage(btn) {

    const form = document.getElementById('chatForm');

    if (!btn) {
        void hideReply()
        void clearReplyData()
        return;
    }

    const message = {
        id: btn.dataset.id,
        role: btn.dataset.role,
        content: btn.dataset.content,
        image_url: btn.dataset.imageUrl || null
    }

    // Text elements
    const roleEl = document.getElementById("reply-role");
    const contentEl = document.getElementById("reply-content");
    const imageEl = document.getElementById("reply-image");

    if (!roleEl || !contentEl || !imageEl) return;

    // Set role and content
    roleEl.textContent = message.role || "";
    contentEl.textContent = message.content || "";

    // Reset image container
    imageEl.innerHTML = "";

    // Optional image
    if (message.image_url) {
        const img = document.createElement("img");
        img.src = message.image_url;
        img.alt = "Reply image";
        img.className = "img-fluid rounded mt-2";
        img.style.maxWidth = "100%";

        imageEl.appendChild(img);
        imageEl.style.display = "block";
    } else {
        imageEl.style.display = "none";
    }

    upsertHiddenInput(form, 'reply_image_message', message.id);

    void showReply()

}