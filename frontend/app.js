const form = document.getElementById('ask-form');
const questionInput = document.getElementById('question');
const submitBtn = document.getElementById('submit-btn');
const btnText = submitBtn.querySelector('.btn-text');
const btnLoading = submitBtn.querySelector('.btn-loading');

const cards = {
    claude: document.getElementById('card-claude'),
    groq: document.getElementById('card-groq'),
    gemini: document.getElementById('card-gemini'),
};

const bodies = {
    claude: document.getElementById('response-claude'),
    groq: document.getElementById('response-groq'),
    gemini: document.getElementById('response-gemini'),
};

const statuses = {
    claude: document.getElementById('status-claude'),
    groq: document.getElementById('status-groq'),
    gemini: document.getElementById('status-gemini'),
};

function resetCards() {
    for (const model of ['claude', 'groq', 'gemini']) {
        bodies[model].textContent = '';
        statuses[model].textContent = '';
        cards[model].classList.remove('streaming');
    }
}

function setLoading(loading) {
    submitBtn.disabled = loading;
    btnText.hidden = loading;
    btnLoading.hidden = !loading;
}

form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const question = questionInput.value.trim();
    if (!question) return;

    resetCards();
    setLoading(true);
    questionInput.value = '';

    for (const model of ['claude', 'groq', 'gemini']) {
        statuses[model].textContent = 'waiting...';
        cards[model].classList.add('streaming');
    }

    try {
        const response = await fetch('/api/ask', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question }),
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop();

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const event = JSON.parse(line.slice(6));
                        handleEvent(event);
                    } catch {}
                }
            }
        }
    } catch (err) {
        for (const model of ['claude', 'groq', 'gemini']) {
            if (!bodies[model].textContent) {
                bodies[model].innerHTML = `<span class="error">Connection error: ${err.message}</span>`;
            }
        }
    } finally {
        setLoading(false);
    }
});

function handleEvent(event) {
    const { model, type, content } = event;

    if (type === 'chunk') {
        if (statuses[model].textContent === 'waiting...') {
            statuses[model].textContent = 'streaming...';
        }
        bodies[model].textContent += content;
    } else if (type === 'error') {
        bodies[model].innerHTML += `<span class="error">\n\nError: ${content}</span>`;
        statuses[model].textContent = 'error';
        cards[model].classList.remove('streaming');
    } else if (type === 'done') {
        statuses[model].textContent = 'done';
        cards[model].classList.remove('streaming');
    }
}

questionInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        form.dispatchEvent(new Event('submit'));
    }
});
