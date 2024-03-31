'use client';

import React, { useState } from 'react';
import styles from '/Users/tselmegulammandakh/Downloads/cpsc439/s24-bluebook-ai/frontend/src/app/page.module.css'; // change to ur own directory

export default function Chat() {
  const [isTyping, setIsTyping] = useState(false);
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState([{ id: 'welcome-msg', content: 'How may I help you?', role: 'ai' }]);
  const [chatVisible, setChatVisible] = useState(false);

  const handleInputChange = (e: { target: { value: React.SetStateAction<string>; }; }) => {
    setInput(e.target.value);
  };

  const handleSubmit = async (e: { preventDefault: () => void; }) => {
    e.preventDefault();
  
    // add the user's message to the chat.
    const newUserMessage = { id: `user-${Date.now()}`, content: input, role: 'user' };
    setMessages(messages => [...messages, newUserMessage]);

    setIsTyping(true);
  
    const response = await fetch('http://127.0.0.1:8000/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      // body: JSON.stringify({ message: [{ content: input, role: 'user' }] }),
      body: JSON.stringify({ message: input }),
    });
    
    setIsTyping(false); 

    if (response.ok) {
      const data = await response.json();
      // simulateTypingEffect(data.message[0].content, 'ai', `ai-${Date.now()}`);
      simulateTypingEffect(data.response, 'ai', `ai-${Date.now()}`);
    } else {
      console.error('Failed to send message');
    }
  
    setInput('');
  };
  
  const simulateTypingEffect = (message: string, role: string, messageId: string) => {
    let index = 0;
    const typingSpeedMs = 20;
  
    const typeCharacter = () => {
      if (index < message.length) {
        const updatedMessage = { id: messageId, content: message.substring(0, index + 1), role: role };
        setMessages(currentMessages => {
          // is message being typed already in array
          const existingIndex = currentMessages.findIndex(msg => msg.id === messageId);
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
  

  return (
    <>
    <button 
      onClick={toggleChatVisibility} 
      className={styles.floatingChatButton}
      aria-label="Toggle Chat"
    >
      {}
    </button>

    {chatVisible && (
      <div className={`${styles.chatContainer} ${chatVisible ? styles.chatVisible : ''}`}>
          <div className={styles.chatHeader}>
            BluebookAI Assistant
          </div>
        <div className={styles.messages}>
          {messages.map((m) => (
            <div key={m.id} className={`${styles.message} ${m.role === 'user' ? styles.user : styles.ai}`}>
              {m.content}
            </div>
          ))}
          {isTyping && (
          <div className={styles.typingIndicator}>
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
          <button type="submit" className={styles.sendButton}>Send</button>
        </form>
      </div>
    )}
    </>
  );
}
