// TTS and Typing Animation for Gemini Chatbot
(function () {
  const ttsToggle = document.getElementById("tts-toggle");
  const ttsIcon = document.getElementById("tts-icon");
  const botBubble = document.getElementById("bot-response");
  const stopTypingBtn = document.getElementById("stop-typing-btn");
  const LS_KEY = "tts-muted";
  const TYPING_SPEED = 40; // ms per character
  const TYPING_DELAY = 1500; // ms before typing starts
  let typingStopped = false;
  let typingTimeout = null;

  function isMuted() {
    return localStorage.getItem(LS_KEY) === "true";
  }
  function setMuted(muted) {
    localStorage.setItem(LS_KEY, muted);
    updateIcon();
  }
  function updateIcon() {
    if (!ttsIcon) return;
    ttsIcon.textContent = isMuted() ? "🔇" : "🔊";
  }
  function speak(text) {
    if (!window.speechSynthesis || isMuted() || !text) return;
    window.speechSynthesis.cancel();
    const utter = new window.SpeechSynthesisUtterance(text);
    utter.rate = 1.05;
    utter.pitch = 1.1;
    utter.volume = 1;
    utter.lang = "en-US";
    window.speechSynthesis.speak(utter);
  }
  if (ttsToggle) {
    ttsToggle.addEventListener("click", function (e) {
      e.preventDefault();
      setMuted(!isMuted());
    });
  }
  updateIcon();

  // Typing animation logic
  function showTypingAnimation(finalText) {
    if (!botBubble) return;
    typingStopped = false;
    botBubble.innerHTML =
      '<strong>Gemini:</strong> <span class="typing-indicator">Gemini is typing...</span>';
    typingTimeout = setTimeout(() => {
      // Remove typing indicator and start typing the actual response
      const text = finalText.replace(/^Gemini:\s*/i, "");
      let i = 0;
      botBubble.innerHTML =
        '<strong>Gemini:</strong> <span id="typed-response"></span>';
      const typedSpan = document.getElementById("typed-response");
      function typeChar() {
        if (typingStopped) return;
        if (i <= text.length) {
          typedSpan.textContent = text.slice(0, i);
          i++;
          typingTimeout = setTimeout(
            typeChar,
            TYPING_SPEED + Math.floor(Math.random() * 10)
          );
        } else {
          // Done typing, trigger TTS if not muted
          speak(text);
        }
      }
      typeChar();
    }, TYPING_DELAY);
  }

  // Stop typing handler
  if (stopTypingBtn) {
    stopTypingBtn.addEventListener("click", function () {
      typingStopped = true;
      if (typingTimeout) clearTimeout(typingTimeout);
      // Leaves the text as-is (freezes at current state)
    });
  }

  // On page load, if there's a bot response, animate it
  if (botBubble && botBubble.dataset.animate === "true") {
    showTypingAnimation(botBubble.dataset.finalText || botBubble.textContent);
  } else if (botBubble) {
    // If not animating, just update TTS icon and speak if needed
    const text = botBubble.textContent.replace(/^Gemini:\s*/i, "");
    if (!isMuted()) speak(text);
  }
})();
