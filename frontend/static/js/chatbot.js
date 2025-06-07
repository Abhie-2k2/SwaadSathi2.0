// chatbot.js

const toggleBtn = document.getElementById('chatbot-toggle');
const chatbotBox = document.getElementById('chatbot-box');
const chatbotInput = document.getElementById('chatbot-input');
const chatbotMessages = document.getElementById('chatbot-messages');

if (toggleBtn && chatbotBox) {
  toggleBtn.addEventListener('click', () => {
    chatbotBox.style.display = chatbotBox.style.display === 'flex' ? 'none' : 'flex';
  });
}

if (chatbotInput && chatbotMessages) {
  chatbotInput.addEventListener('keydown', async (e) => {
    if (e.key === 'Enter') {
      const userMessage = chatbotInput.value.trim();
      if (!userMessage) return;

      chatbotMessages.innerHTML += `<div><strong>You:</strong> ${userMessage}</div>`;
      chatbotInput.value = '';

      // Dummy Gemini Response Placeholder
      setTimeout(() => {
        chatbotMessages.innerHTML += `<div><strong>Gemini:</strong> I'm here to help with your recipes!</div>`;
        chatbotMessages.scrollTop = chatbotMessages.scrollHeight;
      }, 600);
    }
  });
}
