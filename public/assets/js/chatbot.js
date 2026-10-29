// Chatbot INES : conversation, réservation d'un appel (créneaux INES Booking). Inclus par layouts/main.html et l'accueil v2.
// Même conversation sur toutes les pages (et au retour sur le site) : identifiant gardé dans le navigateur.
const chatSessionId = (function() {
    const fresh = 'chat_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
    try {
        const saved = localStorage.getItem('digitaChatSession');
        if (saved) return saved;
        localStorage.setItem('digitaChatSession', fresh);
    } catch (e) {}
    return fresh;
})();
let chatLoaded = false;

function toggleChatbot() {
    const chatbotWindow = document.getElementById('chatbot-window');
    if (!chatbotWindow) return;
    chatbotWindow.classList.toggle('active');
    if (chatbotWindow.classList.contains('active') && !chatLoaded) loadChatHistory();
}

function addChatMessage(role, html) {
    const messagesContainer = document.getElementById('chatbot-messages');
    const message = document.createElement('div');
    message.className = 'chat-message ' + role;
    message.innerHTML = '<div class="message-content">' + html + '</div>';
    messagesContainer.appendChild(message);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    return message;
}

function loadChatHistory() {
    chatLoaded = true;
    fetch('/api/chatbot/history?session_id=' + encodeURIComponent(chatSessionId))
        .then(r => r.json())
        .then(data => {
            const messages = (data && data.messages) || [];
            messages.forEach(m => addChatMessage(m.role === 'user' ? 'user' : 'bot',
                m.role === 'user' ? escapeHtml(m.content) : formatReply(m.content)));
            if (!messages.length) addChatMessage('bot', "Bonjour, je suis INES, l'assistante DIGITA. Je réponds à vos questions sur nos offres et nos prix. Vous pouvez aussi <strong>réserver un appel de 30 min</strong> avec un consultant, gratuitement.");
        })
        .catch(() => addChatMessage('bot', "Bonjour ! Posez-moi votre question, ou réservez un appel de 30 min avec un consultant."));
}

function sendMessage() {
    const input = document.getElementById('chatbot-input');
    if (!input || input.value.trim() === '') return;
    const userText = input.value.trim();
    addChatMessage('user', escapeHtml(userText));
    input.value = '';
    const typing = addChatMessage('bot', "<em>En train d'écrire...</em>");

    fetch('/api/chatbot/message', {
        method: 'POST',
        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
        body: 'message=' + encodeURIComponent(userText) + '&session_id=' + encodeURIComponent(chatSessionId) + '&page=' + encodeURIComponent(window.location.pathname)
    })
    .then(r => r.json())
    .then(data => {
        typing.remove();
        if (data.success && data.reply) addChatMessage('bot', formatReply(data.reply));
    })
    .catch(() => {
        typing.remove();
        addChatMessage('bot', 'Désolé, une erreur est survenue. Appelez-nous au <a href="tel:+262693487817">06 93 48 78 17</a>.');
    });
}

// Réservation d'un appel de 30 min : créneaux réels d'INES Booking (/api/chatbot/slots).
function openBooking() {
    const box = addChatMessage('bot', '<em>Chargement des créneaux…</em>');
    fetch('/api/chatbot/slots')
        .then(r => r.json())
        .then(data => {
            const days = data.days || [];
            if (!data.success || !days.length) {
                box.querySelector('.message-content').innerHTML = 'Aucun créneau en ligne pour le moment. Laissez votre numéro ici ou appelez le <a href="tel:+262693487817">06 93 48 78 17</a>.';
                return;
            }
            const content = box.querySelector('.message-content');
            content.classList.add('chat-booking');
            content.innerHTML = '<strong>Appel de 30 min avec un consultant</strong> (heure de La Réunion)'
                + '<form><select name="date" required><option value="">Jour</option>'
                + days.map(d => '<option value="' + d.date + '">' + escapeHtml(d.label) + '</option>').join('')
                + '</select><select name="time_slot" required disabled><option value="">Heure</option></select>'
                + '<input name="name" placeholder="Prénom et nom" autocomplete="name" required>'
                + '<input name="email" type="email" placeholder="E-mail" autocomplete="email" required>'
                + '<input name="phone" type="tel" placeholder="Téléphone" autocomplete="tel" required>'
                + '<button type="submit">Confirmer le rendez-vous</button><p class="chat-booking-error" role="alert"></p></form>';
            const form = content.querySelector('form');
            form.date.addEventListener('change', function() {
                const day = days.find(d => d.date === form.date.value);
                form.time_slot.innerHTML = '<option value="">Heure</option>' + (day ? day.slots.map(s => '<option value="' + s + '">' + s.replace(':', ' h ') + '</option>').join('') : '');
                form.time_slot.disabled = !day;
            });
            form.addEventListener('submit', function(e) {
                e.preventDefault();
                const button = form.querySelector('button');
                button.disabled = true;
                fetch('/api/chatbot/appointment', { method: 'POST', body: new FormData(form) })
                    .then(r => r.json())
                    .then(res => {
                        if (!res.success) {
                            form.querySelector('.chat-booking-error').textContent = res.error || "La réservation a échoué.";
                            button.disabled = false;
                            return;
                        }
                        content.innerHTML = '✅ ' + escapeHtml(res.message);
                    })
                    .catch(() => {
                        form.querySelector('.chat-booking-error').textContent = "La réservation a échoué. Appelez le 06 93 48 78 17.";
                        button.disabled = false;
                    });
            });
            document.getElementById('chatbot-messages').scrollTop = 1e6;
        })
        .catch(() => { box.querySelector('.message-content').textContent = 'Réservation indisponible. Appelez le 06 93 48 78 17.'; });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Réponse IA : texte échappé, puis gras, liens vers les pages du site et sauts de ligne.
function formatReply(text) {
    return escapeHtml(text)
        .replace(/^#{1,6}\s*/gm, '')
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/(^|[\s(])(\/[a-z0-9][a-z0-9\-\/#]*)/g, '$1<a href="$2">$2</a>')
        .replace(/\n/g, '<br>');
}
