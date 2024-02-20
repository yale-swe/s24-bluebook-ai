'use client';

import { useChat } from 'ai/react';
import styles from '/Users/tselmegulammandakh/Downloads/cpsc439/s24-bluebook-ai/frontend/src/app/page.module.css'; // change to ur own directory
import React, { FormEvent } from 'react';
import { useState, useEffect } from 'react';

export default function Chat() {
  const {
    messages, input, handleInputChange, append, setMessages
  } = useChat();

  const [initialMessage, setInitialMessage] = useState({ id: 'welcome-msg', content: 'How may I help you?', role: 'ai' });

  useEffect(() => {
    // load initial message from flask backend
    setInitialMessage({ id: 'welcome-msg', content: 'How may I help you?', role: 'ai' });
  }, []);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault(); 

    const response = await fetch('http://127.0.0.1:8000/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ message: [{ content: input, role: 'user' }] }),
    });

    if (response.ok) {
      const data = await response.json();
      console.log(data);

    } else {
      console.error('Failed to send message');
    }
  };

  return (
    <div className={styles.chatContainer}>
      <div className={styles.messages}>
        <div className={styles.message + ' ' + styles.ai}>{initialMessage.content}</div>

        {messages.map((m) => (
          <div key={m.id} className={`${styles.message} ${m.role === 'user' ? styles.user : styles.ai}`}>
            {m.content}
          </div>
        ))}
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
  );
}