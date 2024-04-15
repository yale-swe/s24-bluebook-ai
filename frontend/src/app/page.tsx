"use client";

import React, { useState } from "react";
import { useEffect } from "react";
import styles from "./page.module.css"; // change to ur own directory
import { format } from "path";

export default function Chat() {
  const [isTyping, setIsTyping] = useState(false);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([
    { id: "welcome-msg", content: "How may I help you?", role: "ai" },
  ]);
  const [chatVisible, setChatVisible] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    // Check for CAS ticket in URL parameters
    const urlParams = new URLSearchParams(window.location.search);
    const ticket = urlParams.get("ticket");

    if (ticket) {
      validateTicket(ticket);
    }
  }, []);

  const handleInputChange = (e: {
    target: { value: React.SetStateAction<string> };
  }) => {
    setInput(e.target.value);
  };

  // Call this function after your authentication logic or on page load
  useEffect(() => {
    clearTicketFromUrl();
  }, []);

  const handleSubmit = async (e: { preventDefault: () => void }) => {
    e.preventDefault();

    setInput("");

    // add the user's message to the chat.
    const newUserMessage = {
      id: `user-${Date.now()}`,
      content: input,
      role: "user",
    };

    setMessages((messages) => [...messages, newUserMessage]);
    setIsTyping(true);

    const response = await fetch("http://127.0.0.1:8000/api/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      // body: JSON.stringify({ message: [{ content: input, role: 'user' }] }),
      body: JSON.stringify({
        message: [...messages, newUserMessage],
      }),
    });

    setIsTyping(false);

    if (response.ok) {
      const data = await response.json();
      // simulateTypingEffect(data.message[0].content, 'ai', `ai-${Date.now()}`);
      simulateTypingEffect(data.response, "ai", `ai-${Date.now()}`);
    } else {
      console.error("Failed to send message");
    }
  };

  const simulateTypingEffect = (
    message: string,
    role: string,
    messageId: string
  ) => {
    let index = 0;
    const typingSpeedMs = 20;

    const typeCharacter = () => {
      if (index < message.length) {
        const updatedMessage = {
          id: messageId,
          content: message.substring(0, index + 1),
          role: role,
        };
        setMessages((currentMessages) => {
          // is message being typed already in array
          const existingIndex = currentMessages.findIndex(
            (msg) => msg.id === messageId
          );
          let newMessages = [...currentMessages];
          if (existingIndex >= 0) {
            // update existing message
            newMessages[existingIndex] = updatedMessage;
          } else {
            // add new message if it doesn't exist
            newMessages.push(updatedMessage);
          }
          return newMessages;
        });
        index++;
        setTimeout(typeCharacter, typingSpeedMs);
      }
    };

    typeCharacter();
  };

  const toggleChatVisibility = () => {
    console.log("Toggling chat visibility. Current state:", chatVisible);
    setChatVisible(!chatVisible);
  };

  // Redirect to CAS login page
  const redirectToCasLogin = () => {
    const casLoginUrl = `https://secure.its.yale.edu/cas/login?service=${encodeURIComponent(
      window.location.href
    )}`;
    window.location.href = casLoginUrl;
  };

  const validateTicket = async (ticket: string) => {
    const serviceUrl = window.location.origin + "/";

    try {
      const response = await fetch("http://127.0.0.1:8000/validate_ticket", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ ticket, service_url: serviceUrl }),
      });

      if (response.ok) {
        const data = await response.json();
        setIsAuthenticated(data.isAuthenticated); // Update the state based on the response
        clearTicketFromUrl();
      } else {
        console.error(
          "Failed to validate ticket - server responded with an error"
        );
      }
    } catch (error) {
      console.error("Failed to validate ticket:", error);
    }
  };

  // Function to clear the ticket from the URL
  const clearTicketFromUrl = () => {
    const url = new URL(window.location.href);
    url.searchParams.delete("ticket"); // Remove the ticket parameter

    window.history.replaceState({}, document.title, url.pathname + url.search);
  };

  const handleButtonClick = () => {
    if (isAuthenticated) {
      toggleChatVisibility();
    } else {
      redirectToCasLogin();
    }
  };

  const formatMessage = (content: string) => {
    const boldRegex = /\*\*(.*?)\*\*/g;
    return content.split(boldRegex).map((part, index) => {
      // Every even index is not bold, odd indices are the bold text between **.
      if (index % 2 === 0) {
        // Normal text
        return part;
      } else {
        // Bold text
        return <strong key={index}>{part}</strong>;
      }
    });
  };

  return (
    <>
      <button
        onClick={handleButtonClick}
        className={styles.floatingChatButton}
        aria-label="Toggle Chat"
      >
        {}
      </button>

      {chatVisible && (
        <div
          className={`${styles.chatContainer} ${
            chatVisible ? styles.chatVisible : ""
          }`}
        >
          <div className={styles.chatHeader}>BluebookAI Assistant</div>
          <div className={styles.messages}>
            {messages.map((m) => (
              <div
                key={m.id}
                className={`${styles.message} ${
                  m.role === "user" ? styles.user : styles.ai
                }`}
              >
                {formatMessage(m.content)}
              </div>
            ))}
            {isTyping && (
              <div className={styles["typing-indicator"]}>
                <span></span>
                <span></span>
                <span></span>
              </div>
            )}
          </div>
          <form onSubmit={handleSubmit} className={styles.inputForm}>
            <input
              type="text"
              className={styles.inputField}
              value={input}
              placeholder="Say something..."
              onChange={handleInputChange}
            />
            <button type="submit" className={styles.sendButton}>
              Send
            </button>
          </form>
        </div>
      )}
    </>
  );
}
