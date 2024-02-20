'use client';

import { useChat } from 'ai/react';
import styles from '/Users/tselmegulammandakh/Downloads/cpsc439/s24-bluebook-ai/frontend/src/app/page.module.css'; // change to ur own directory

export default function Chat() {
  const { messages, input, handleInputChange, handleSubmit } = useChat();

  // initializing with welcome message manually
  const initialMessage = { id: 'welcome-msg', content: 'How may I help you?', role: 'ai' };

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