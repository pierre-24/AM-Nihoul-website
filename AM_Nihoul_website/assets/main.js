'use strict';

// -- Add close button on messages, if any
document.querySelectorAll('.flash-message .close').forEach(e => {
    e.addEventListener('click', () => {
       e.parentNode.style.display = 'none';
   });
});

// -- Modals
function openModal(el) {
    el.classList.add('modal-open');

    // add cross
    if (el.querySelector('a.modal-close-cross') === null) {
        const title = el.querySelector('h3');
        let link = document.createElement('a');
        link.classList.add('modal-close');
        link.classList.add('modal-close-cross');
        link.innerHTML = '&cross;';
        title.parentNode.insertBefore(link, title);
    }

    // add close on each
    el.querySelectorAll('.modal-close').forEach(e => {
        e.addEventListener('click', () => {
            closeModal(el);
        });
    });
}

function closeModal(el) {
    el.classList.remove('modal-open');
}

document.querySelectorAll('a[data-toggle="modal"]').forEach(e => {
    e.addEventListener('click', () => {
        const target = e.getAttribute('href').substr(1);
        openModal(document.getElementById(target));
    });
});