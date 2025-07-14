// TTS, Typing Animation, and Memory System for Gemini Chatbot
(function () {
  // Get DOM elements
  const ttsToggle = document.getElementById("tts-toggle");
  const ttsIcon = document.getElementById("tts-icon");
  const botBubble = document.getElementById("bot-response");
  const stopTypingBtn = document.getElementById("stop-typing-btn");

  // Memory system elements
  const memorySidebar = document.getElementById("memory-sidebar");
  const memoryList = document.getElementById("memory-list");
  const memoryToggle = document.getElementById("memory-toggle");
  const clearAllBtn = document.getElementById("clear-all-btn");
  const newChatBtn = document.getElementById("new-chat-btn");
  const chatForm = document.getElementById("chat-form");

  // Constants
  const LS_KEY = "tts-muted";
  const TYPING_SPEED = 40;
  const TYPING_DELAY = 1500;

  // State variables
  let typingStopped = false;
  let typingTimeout = null;
  let isRenaming = false;

  // ===== TTS FUNCTIONALITY =====

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

  // ===== TYPING ANIMATION =====

  function showTypingAnimation(finalText) {
    if (!botBubble) return;

    typingStopped = false;

    botBubble.innerHTML =
      '<strong>Gemini:</strong> <span class="typing-indicator">Gemini is typing...</span>';

    typingTimeout = setTimeout(() => {
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
          speak(text);
        }
      }

      typeChar();
    }, TYPING_DELAY);
  }

  if (stopTypingBtn) {
    stopTypingBtn.addEventListener("click", function () {
      typingStopped = true;
      if (typingTimeout) clearTimeout(typingTimeout);
    });
  }

  if (botBubble && botBubble.dataset.animate === "true") {
    showTypingAnimation(botBubble.dataset.finalText || botBubble.textContent);
  } else if (botBubble) {
    const text = botBubble.textContent.replace(/^Gemini:\s*/i, "");
    if (!isMuted()) speak(text);
  }

  // ===== CHAT MEMORY SYSTEM =====

  function formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    return date.toISOString().split("T")[0];
  }

  function createMemoryItem(chat) {
    const isActive = window.location.search.includes(`chat_id=${chat.id}`);
    const activeClass = isActive ? " active" : "";

    return `
      <div class="memory-item${activeClass}" data-chat-id="${chat.id}">
        <div class="memory-content">
          <div class="memory-title">${chat.title}</div>
          <div class="memory-date">${chat.date}</div>
        </div>
        <div class="memory-actions">
          <button class="memory-menu-btn" title="More options">⋮</button>
          <div class="memory-dropdown">
            <button class="rename-memory-btn" data-chat-id="${chat.id}">
              ✏️ Rename
            </button>
            <button class="delete-memory-btn" data-chat-id="${chat.id}">
              🗑️ Delete
            </button>
          </div>
        </div>
      </div>
    `;
  }

  async function updateMemoryList() {
    if (!memoryList) return;

    try {
      const response = await fetch("/api/chats");
      const data = await response.json();
      const chats = data.chats || [];

      if (chats.length === 0) {
        memoryList.innerHTML = `
          <div class="no-memory">
            <p>No chat history yet</p>
            <p>Start a conversation to see it here!</p>
          </div>
        `;
      } else {
        const memoryItems = chats
          .sort((a, b) => new Date(b.date) - new Date(a.date))
          .map(createMemoryItem)
          .join("");

        memoryList.innerHTML = memoryItems;
        attachMemoryEventListeners();
      }
    } catch (error) {
      console.error("Error fetching chats:", error);
    }
  }

  async function deleteMemory(chatId) {
    if (!confirm("Are you sure you want to delete this chat session?")) {
      return;
    }

    try {
      const response = await fetch(`/api/chats/${chatId}`, {
        method: "DELETE",
      });

      if (response.ok) {
        // If we're currently viewing this chat, redirect to home
        const currentChatId = new URLSearchParams(window.location.search).get(
          "chat_id"
        );
        if (currentChatId === chatId) {
          window.location.href = "/";
        } else {
          updateMemoryList();
        }
      } else {
        console.error("Failed to delete chat");
      }
    } catch (error) {
      console.error("Error deleting chat:", error);
    }
  }

  async function renameMemory(chatId, newTitle) {
    try {
      const response = await fetch(`/api/chats/${chatId}/rename`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ title: newTitle }),
      });

      if (response.ok) {
        // Update the UI immediately
        const memoryItem = document.querySelector(`[data-chat-id="${chatId}"]`);
        if (memoryItem) {
          const titleElement = memoryItem.querySelector(".memory-title");
          if (titleElement) {
            titleElement.textContent = newTitle;
          }
        }
      } else {
        console.error("Failed to rename chat");
      }
    } catch (error) {
      console.error("Error renaming chat:", error);
    }
  }

  function startRename(chatId) {
    // Cancel any existing rename operation
    if (isRenaming) {
      const existingInput = document.querySelector(".memory-title-input");
      if (existingInput) {
        const existingTitle =
          existingInput.parentNode.querySelector(".memory-title");
        existingTitle.style.display = "";
        existingInput.remove();
      }
    }

    const memoryItem = document.querySelector(`[data-chat-id="${chatId}"]`);
    if (!memoryItem) return;

    const titleElement = memoryItem.querySelector(".memory-title");
    const currentTitle = titleElement.textContent;

    // Create input field
    const input = document.createElement("input");
    input.type = "text";
    input.className = "memory-title-input";
    input.value = currentTitle;
    input.style.cssText = `
      background: #40414f;
      border: 1px solid #00f0ff;
      border-radius: 4px;
      color: #fff;
      font-size: 13px;
      padding: 4px 8px;
      width: 100%;
      outline: none;
      font-family: inherit;
    `;

    // Replace title with input
    titleElement.style.display = "none";
    titleElement.parentNode.insertBefore(input, titleElement);
    input.focus();
    input.select();

    isRenaming = true;

    // Handle save on Enter or blur
    function saveRename() {
      const newTitle = input.value.trim();
      if (newTitle && newTitle !== currentTitle) {
        renameMemory(chatId, newTitle);
      } else if (!newTitle) {
        // If empty, restore original title
        titleElement.textContent = currentTitle;
      }

      // Restore title element
      titleElement.style.display = "";
      input.remove();
      isRenaming = false;
    }

    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        saveRename();
      } else if (e.key === "Escape") {
        e.preventDefault();
        titleElement.style.display = "";
        input.remove();
        isRenaming = false;
      }
    });

    input.addEventListener("blur", saveRename);
  }

  async function createNewChat() {
    try {
      const response = await fetch("/api/chats/new", {
        method: "POST",
      });

      if (response.ok) {
        const data = await response.json();
        // Redirect to the new chat
        window.location.href = `/?chat_id=${data.chat.id}`;
      } else {
        console.error("Failed to create new chat");
      }
    } catch (error) {
      console.error("Error creating new chat:", error);
    }
  }

  function loadChat(chatId) {
    window.location.href = `/?chat_id=${chatId}`;
  }

  async function clearAllMemory() {
    if (
      !confirm(
        "Are you sure you want to clear all chat history? This cannot be undone."
      )
    ) {
      return;
    }

    try {
      const response = await fetch("/api/chats", {
        method: "DELETE",
      });

      if (response.ok) {
        // Redirect to home page
        window.location.href = "/";
      } else {
        console.error("Failed to clear memory");
      }
    } catch (error) {
      console.error("Error clearing memory:", error);
    }
  }

  function attachMemoryEventListeners() {
    // Delete memory buttons
    const deleteButtons = document.querySelectorAll(".delete-memory-btn");
    deleteButtons.forEach((button) => {
      button.addEventListener("click", (e) => {
        e.stopPropagation();
        const chatId = button.dataset.chatId;
        deleteMemory(chatId);
      });
    });

    // Rename memory buttons
    const renameButtons = document.querySelectorAll(".rename-memory-btn");
    renameButtons.forEach((button) => {
      button.addEventListener("click", (e) => {
        e.stopPropagation();
        const chatId = button.dataset.chatId;
        startRename(chatId);
      });
    });

    // Memory items (click to load chat)
    const memoryItems = document.querySelectorAll(".memory-item");
    memoryItems.forEach((item) => {
      item.addEventListener("click", () => {
        const chatId = item.dataset.chatId;
        loadChat(chatId);
      });
    });
  }

  // ===== MOBILE SIDEBAR TOGGLE =====

  if (memoryToggle) {
    memoryToggle.addEventListener("click", function () {
      memorySidebar.classList.toggle("active");
    });
  }

  // ===== EVENT LISTENERS =====

  if (newChatBtn) {
    newChatBtn.addEventListener("click", createNewChat);
  }

  if (clearAllBtn) {
    clearAllBtn.addEventListener("click", clearAllMemory);
  }

  if (chatForm) {
    chatForm.addEventListener("submit", function () {
      // The form will submit normally and reload the page
    });
  }

  // Initial setup
  updateMemoryList();

  // Auto-scroll chat history to bottom
  const chatHistory = document.getElementById("chat-history");
  if (chatHistory) {
    chatHistory.scrollTop = chatHistory.scrollHeight;
  }
})();
