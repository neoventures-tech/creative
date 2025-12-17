const fileInput = document.getElementById('fileInput');
const attachmentsPreview = document.getElementById('attachmentsPreview');

let selectedFiles = [];

fileInput.addEventListener('change', function () {
    for (const file of Array.from(this.files)) {
        selectedFiles.push(file);
    }

    updateAttachmentsPreview();
    syncFileInput();
});

function updateAttachmentsPreview() {
    attachmentsPreview.innerHTML = '';

    if (selectedFiles.length === 0) {
        attachmentsPreview.classList.add('d-none');
        return;
    }

    attachmentsPreview.classList.remove('d-none');

    selectedFiles.forEach((file, index) => {
        const item = document.createElement('div');
        item.className =
            'd-flex align-items-center gap-2 px-2 py-1 border rounded bg-white shadow-sm';

        item.innerHTML = `
            <i class="bi bi-paperclip"></i>
            <span class="text-truncate" style="max-width: 140px;">
                ${file.name}
            </span>
            <button
                type="button"
                class="btn btn-sm btn-outline-danger border-0 p-0 ms-1"
                onclick="removeAttachment(${index})"
                title="Remover"
            >
                <i class="bi bi-x fs-5"></i>
            </button>
        `;

        attachmentsPreview.appendChild(item);
    });
}

function removeAttachment(index) {
    selectedFiles.splice(index, 1);
    updateAttachmentsPreview();
    syncFileInput();
}

function syncFileInput() {
    const dataTransfer = new DataTransfer();
    selectedFiles.forEach(file => dataTransfer.items.add(file));
    fileInput.files = dataTransfer.files;
}