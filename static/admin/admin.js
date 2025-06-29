const modal = document.getElementById('confirm-modal');
const confirmBtn = document.getElementById('confirm-delete-btn');
const cancelBtn = document.getElementById('cancel-btn');
let formToSubmit = null;

function showConfirmModal(button) {
    formToSubmit = button.closest('form');
    modal.style.display = 'block';
}

confirmBtn.onclick = function() {
    if (formToSubmit) {
        formToSubmit.submit();
    }
}

cancelBtn.onclick = function() {
    modal.style.display = 'none';
    formToSubmit = null;
}

window.onclick = function(event) {
    if (event.target == modal) {
        modal.style.display = "none";
        formToSubmit = null;
    }
}