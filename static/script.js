// TTS and Typing Animation for Gemini Chatbot
(function () {
  // Get DOM elements
  const ttsToggle = document.getElementById("tts-toggle"); // Toggle button for text-to-speech
  const ttsIcon = document.getElementById("tts-icon"); // Icon (🔊 / 🔇)
  const botBubble = document.getElementById("bot-response"); // Chat bubble with bot's response
  const stopTypingBtn = document.getElementById("stop-typing-btn"); // Button to stop typing animation

  // Constants
  const LS_KEY = "tts-muted"; // LocalStorage key for TTS toggle
  const TYPING_SPEED = 40; // Speed of typing (milliseconds per character)
  const TYPING_DELAY = 1500; // Delay before typing starts (in ms)

  // State variables
  let typingStopped = false; // Flag to check if typing has been interrupted
  let typingTimeout = null; // Timeout ID for typing animation

  // Check if TTS is muted from localStorage
  function isMuted() {
    return localStorage.getItem(LS_KEY) === "true";
  }

  // Save mute setting to localStorage and update icon
  function setMuted(muted) {
    localStorage.setItem(LS_KEY, muted);
    updateIcon();
  }

  // Change TTS icon based on mute state
  function updateIcon() {
    if (!ttsIcon) return;
    ttsIcon.textContent = isMuted() ? "🔇" : "🔊";
  }

  // Speak out the text using browser's speech synthesis
  function speak(text) {
    if (!window.speechSynthesis || isMuted() || !text) return;

    // Cancel any ongoing speech
    window.speechSynthesis.cancel();

    // Prepare a new speech utterance
    const utter = new window.SpeechSynthesisUtterance(text);
    utter.rate = 1.05;
    utter.pitch = 1.1;
    utter.volume = 1;
    utter.lang = "en-US";

    // Speak the text
    window.speechSynthesis.speak(utter);
  }

  // Handle click on TTS toggle button
  if (ttsToggle) {
    ttsToggle.addEventListener("click", function (e) {
      e.preventDefault();
      setMuted(!isMuted()); // Toggle mute state
    });
  }

  // Initial icon update when script loads
  updateIcon();

  // Show typing animation for bot response
  function showTypingAnimation(finalText) {
    if (!botBubble) return;

    typingStopped = false;

    // Show typing indicator
    botBubble.innerHTML =
      '<strong>Gemini:</strong> <span class="typing-indicator">Gemini is typing...</span>';

    // Wait before typing starts
    typingTimeout = setTimeout(() => {
      const text = finalText.replace(/^Gemini:\s*/i, ""); // Remove "Gemini:" if present
      let i = 0;

      // Replace typing indicator with empty span for animated text
      botBubble.innerHTML =
        '<strong>Gemini:</strong> <span id="typed-response"></span>';
      const typedSpan = document.getElementById("typed-response");

      // Recursive function to type character by character
      function typeChar() {
        if (typingStopped) return;
        if (i <= text.length) {
          typedSpan.textContent = text.slice(0, i); // Show part of the text
          i++;
          typingTimeout = setTimeout(
            typeChar,
            TYPING_SPEED + Math.floor(Math.random() * 10) // Add some variation to typing speed
          );
        } else {
          // After typing ends, speak the text if not muted
          speak(text);
        }
      }

      typeChar(); // Start typing
    }, TYPING_DELAY);
  }

  // If "Stop Typing" button is clicked
  if (stopTypingBtn) {
    stopTypingBtn.addEventListener("click", function () {
      typingStopped = true; // Stop further typing
      if (typingTimeout) clearTimeout(typingTimeout); // Clear any scheduled typing
      // Keeps text as it is currently typed
    });
  }

  // If bot response exists and animation is enabled, show typing animation
  if (botBubble && botBubble.dataset.animate === "true") {
    showTypingAnimation(botBubble.dataset.finalText || botBubble.textContent);
  } else if (botBubble) {
    // If no animation, just speak directly if not muted
    const text = botBubble.textContent.replace(/^Gemini:\s*/i, "");
    if (!isMuted()) speak(text);
  }
})();
