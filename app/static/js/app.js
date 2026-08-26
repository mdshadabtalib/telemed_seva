/* ===================================================================
   TeleMed Seva — Main JavaScript
   =================================================================== */

document.addEventListener('DOMContentLoaded', () => {
  initAlertDismiss();
  initMobileNav();
  initNotificationPolling();
});

/* --- Alert auto-dismiss --- */
function initAlertDismiss() {
  document.querySelectorAll('.alert-dismiss').forEach(btn => {
    btn.addEventListener('click', () => {
      btn.closest('.alert').style.display = 'none';
    });
  });
  // Auto-dismiss after 5s
  document.querySelectorAll('.alert').forEach(alert => {
    setTimeout(() => {
      alert.style.opacity = '0';
      setTimeout(() => alert.style.display = 'none', 300);
    }, 5000);
  });
}

/* --- Mobile navigation toggle --- */
function initMobileNav() {
  const toggle = document.querySelector('.navbar-toggle');
  const nav = document.querySelector('.navbar-nav');
  if (toggle && nav) {
    toggle.addEventListener('click', () => {
      nav.classList.toggle('open');
    });
  }
}

/* --- Notification count polling --- */
function initNotificationPolling() {
  const badge = document.querySelector('.notification-count');
  if (!badge) return;

  function updateCount() {
    fetch('/notifications/api/count')
      .then(r => r.json())
      .then(data => {
        if (data.count > 0) {
          badge.textContent = data.count;
          badge.style.display = 'flex';
        } else {
          badge.style.display = 'none';
        }
      })
      .catch(() => {});
  }

  setInterval(updateCount, 30000);
}

/* --- Consultation Chat --- */
function initChat(consultationId, currentUserId) {
  const messagesDiv = document.getElementById('chat-messages');
  const form = document.getElementById('chat-form');
  const input = document.getElementById('chat-input');
  let lastMessageId = 0;

  // Set initial lastMessageId from existing messages
  const existingMessages = messagesDiv.querySelectorAll('.chat-message');
  if (existingMessages.length > 0) {
    const last = existingMessages[existingMessages.length - 1];
    lastMessageId = parseInt(last.dataset.id || 0);
  }

  // Send message
  if (form) {
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      const message = input.value.trim();
      if (!message) return;

      const formData = new FormData();
      formData.append('message', message);

      const fileInput = document.getElementById('chat-file');
      if (fileInput && fileInput.files.length > 0) {
        formData.append('file', fileInput.files[0]);
      }

      fetch(`/consultation/send-message/${consultationId}`, {
        method: 'POST',
        body: formData,
        headers: {
          'X-CSRFToken': document.querySelector('meta[name=csrf-token]')?.content || ''
        }
      })
        .then(r => r.json())
        .then(data => {
          if (!data.error) {
            appendMessage(data, true);
            input.value = '';
            if (fileInput) fileInput.value = '';
          }
        })
        .catch(() => {});
    });
  }

  // Poll for new messages
  function pollMessages() {
    fetch(`/consultation/messages/${consultationId}?after=${lastMessageId}`)
      .then(r => r.json())
      .then(data => {
        if (data.messages) {
          data.messages.forEach(msg => {
            if (msg.sender_id !== currentUserId) {
              appendMessage(msg, false);
            }
            lastMessageId = Math.max(lastMessageId, msg.id);
          });
        }
        if (data.status === 'completed') {
          const inputArea = document.querySelector('.chat-input-area');
          if (inputArea) {
            inputArea.innerHTML = '<p class="text-muted" style="padding: 1rem; text-align:center; width:100%;">This consultation has ended.</p>';
          }
          return; // Stop polling
        }
        setTimeout(pollMessages, 3000);
      })
      .catch(() => setTimeout(pollMessages, 5000));
  }

  function appendMessage(msg, isSent) {
    const div = document.createElement('div');
    div.className = `chat-message ${isSent ? 'sent' : ''}`;
    div.dataset.id = msg.id;

    let content = `<div class="chat-bubble">${escapeHtml(msg.content)}`;
    if (msg.file_url) {
      content += `<br><a href="${msg.file_url}" target="_blank" style="color: ${isSent ? 'rgba(255,255,255,0.9)' : 'var(--primary)'};">📎 ${escapeHtml(msg.file_name || 'File')}</a>`;
    }
    content += `</div><div class="chat-time">${msg.sent_at}</div>`;

    div.innerHTML = content;
    messagesDiv.appendChild(div);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
  }

  setTimeout(pollMessages, 3000);
  // Scroll to bottom
  messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

/* --- Appointment Slot Selection --- */
function loadSlots(doctorId, dateInput) {
  const date = dateInput.value;
  if (!date) return;

  const container = document.getElementById('slots-container');
  container.innerHTML = '<p class="text-muted">Loading slots...</p>';

  fetch(`/appointments/api/slots/${doctorId}/${date}`)
    .then(r => r.json())
    .then(data => {
      if (!data.slots || data.slots.length === 0) {
        container.innerHTML = '<p class="text-muted">No slots available on this date.</p>';
        return;
      }

      let html = '<div class="grid grid-3 gap-2">';
      data.slots.forEach(slot => {
        const disabled = !slot.available ? 'disabled' : '';
        const cls = slot.available ? 'btn btn-outline' : 'btn btn-outline disabled';
        html += `<button type="button" class="${cls}" ${disabled}
                   onclick="selectSlot(this, '${slot.start}', '${slot.end}', '${slot.start_str} - ${slot.end_str}')"
                   data-start="${slot.start}" data-end="${slot.end}">
                   ${slot.start_str} - ${slot.end_str}
                 </button>`;
      });
      html += '</div>';
      container.innerHTML = html;
    })
    .catch(() => {
      container.innerHTML = '<p class="text-danger">Failed to load slots.</p>';
    });
}

function selectSlot(btn, start, end, label) {
  // Deselect all
  btn.parentElement.querySelectorAll('.btn').forEach(b => {
    b.classList.remove('btn-primary');
    b.classList.add('btn-outline');
  });
  // Select this one
  btn.classList.remove('btn-outline');
  btn.classList.add('btn-primary');

  document.getElementById('selected-start').value = start;
  document.getElementById('selected-end').value = end;
  document.getElementById('selected-slot-label').textContent = label;

  const bookBtn = document.getElementById('book-btn');
  if (bookBtn) bookBtn.disabled = false;
}

/* --- Cart quantity --- */
function updateCartQuantity(itemId, change) {
  const input = document.getElementById(`qty-${itemId}`);
  if (!input) return;
  let val = parseInt(input.value) + change;
  if (val < 1) val = 1;
  input.value = val;
  document.getElementById(`cart-form-${itemId}`).submit();
}

/* --- Modal --- */
function openModal(id) {
  document.getElementById(id).classList.add('active');
}
function closeModal(id) {
  document.getElementById(id).classList.remove('active');
}

/* --- Prescription form: add medicine row --- */
function addMedicineRow() {
  const tbody = document.getElementById('medicine-rows');
  if (!tbody) return;
  const row = tbody.querySelector('tr').cloneNode(true);
  row.querySelectorAll('input, textarea').forEach(inp => inp.value = '');
  tbody.appendChild(row);
}

function removeMedicineRow(btn) {
  const tbody = document.getElementById('medicine-rows');
  if (tbody.children.length > 1) {
    btn.closest('tr').remove();
  }
}

/* --- Helpers --- */
function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}
