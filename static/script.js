// TTS, Typing Animation, and Memory System for Gemini Chatbot
(function () {
  // Get DOM elements
  const ttsToggle = document.getElementById("tts-toggle"); // Toggle button for text-to-speech
  const ttsIcon = document.getElementById("tts-icon"); // Icon (🔊 / 🔇)
  const botBubble = document.getElementById("bot-response"); // Chat bubble with bot's response
  const stopTypingBtn = document.getElementById("stop-typing-btn"); // Button to stop typing animation

  // Memory system elements
  const memorySidebar = document.getElementById("memory-sidebar");
  const memoryList = document.getElementById("memory-list");
  const memoryToggle = document.getElementById("memory-toggle");
  const clearAllBtn = document.getElementById("clear-all-btn");
  const chatForm = document.getElementById("chat-form");

  // Constants
  const LS_KEY = "tts-muted"; // LocalStorage key for TTS toggle
  const TYPING_SPEED = 40; // Speed of typing (milliseconds per character)
  const TYPING_DELAY = 1500; // Delay before typing starts (in ms)

  // State variables
  let typingStopped = false; // Flag to check if typing has been interrupted
  let typingTimeout = null; // Timeout ID for typing animation

  // ===== TTS FUNCTIONALITY =====

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

  // ===== TYPING ANIMATION =====

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

  // ===== MEMORY SYSTEM =====

  // Format timestamp for display
  function formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    return date.toISOString().split("T")[0]; // YYYY-MM-DD format
  }

  // Format time for display
  function formatTime(timestamp) {
    const date = new Date(timestamp);
    return date.toTimeString().slice(0, 5); // HH:MM format
  }

  // Create memory item HTML
  function createMemoryItem(chat) {
    return `
      <div class="memory-item" data-session-id="${chat.session_id}">
        <div class="memory-content">
          <div class="memory-summary">${chat.summary}</div>
          <div class="memory-time">${formatTime(chat.timestamp)}</div>
        </div>
      </div>
    `;
  }

  // Create date group HTML
  function createDateGroup(date, chats) {
    const chatItems = chats.map(createMemoryItem).join("");
    return `
      <div class="memory-date-group" data-date="${date}">
        <div class="memory-date-header">
          <span class="memory-date">${date}</span>
          <button class="delete-date-btn" data-date="${date}" title="Delete all chats from ${date}">
            🗑️
          </button>
        </div>
        <div class="memory-chats">
          ${chatItems}
        </div>
      </div>
    `;
  }

  // Update memory list display
  function updateMemoryList(memory) {
    if (!memoryList) return;

    if (Object.keys(memory).length === 0) {
      memoryList.innerHTML = `
        <div class="no-memory">
          <p>No chat history yet</p>
          <p>Start a conversation to see it here!</p>
        </div>
      `;
    } else {
      const dateGroups = Object.entries(memory)
        .sort(([a], [b]) => new Date(b) - new Date(a)) // Sort dates newest first
        .map(([date, chats]) => createDateGroup(date, chats))
        .join("");

      memoryList.innerHTML = dateGroups;
      // Re-attach event listeners to new elements
      attachMemoryEventListeners();
    }
  }

  // Fetch memory from API
  async function fetchMemory() {
    try {
      const response = await fetch("/api/memory");
      const data = await response.json();
      updateMemoryList(data.memory);
    } catch (error) {
      console.error("Error fetching memory:", error);
    }
  }

  // Delete memory by date
  async function deleteMemoryByDate(date) {
    if (!confirm(`Are you sure you want to delete all chats from ${date}?`)) {
      return;
    }

    try {
      const response = await fetch(`/api/memory/date/${date}`, {
        method: "DELETE",
      });

      if (response.ok) {
        // Reload the page to update the display
        window.location.reload();
      } else {
        console.error("Failed to delete memory");
      }
    } catch (error) {
      console.error("Error deleting memory:", error);
    }
  }

  // Clear all memory
  async function clearAllMemory() {
    if (
      !confirm(
        "Are you sure you want to clear all chat history? This cannot be undone."
      )
    ) {
      return;
    }

    try {
      const response = await fetch("/api/memory", {
        method: "DELETE",
      });

      if (response.ok) {
        // Reload the page to update the display
        window.location.reload();
      } else {
        console.error("Failed to clear memory");
      }
    } catch (error) {
      console.error("Error clearing memory:", error);
    }
  }

  // Attach event listeners to memory elements
  function attachMemoryEventListeners() {
    // Delete date buttons
    const deleteDateBtns = document.querySelectorAll(".delete-date-btn");
    deleteDateBtns.forEach((btn) => {
      btn.addEventListener("click", (e) => {
        e.stopPropagation();
        const date = btn.dataset.date;
        deleteMemoryByDate(date);
      });
    });

    // Memory items (for potential future click functionality)
    const memoryItems = document.querySelectorAll(".memory-item");
    memoryItems.forEach((item) => {
      item.addEventListener("click", () => {
        // Future: could implement click to load specific chat
        console.log("Memory item clicked:", item.dataset.sessionId);
      });
    });
  }

  // ===== MOBILE SIDEBAR TOGGLE =====

  // Toggle memory sidebar on mobile
  if (memoryToggle) {
    memoryToggle.addEventListener("click", function () {
      memorySidebar.classList.toggle("active");
    });
  }

  // ===== EVENT LISTENERS =====

  // Clear all button
  if (clearAllBtn) {
    clearAllBtn.addEventListener("click", clearAllMemory);
  }

  // Form submission - reload page after sending message
  if (chatForm) {
    chatForm.addEventListener("submit", function () {
      // The form will submit normally and reload the page
      // This ensures the new message appears in the chat history
    });
  }

  // Initial setup
  attachMemoryEventListeners();

  // Auto-scroll chat history to bottom
  const chatHistory = document.getElementById("chat-history");
  if (chatHistory) {
    chatHistory.scrollTop = chatHistory.scrollHeight;
  }
})();
