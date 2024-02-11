'use client';

import { useChat } from 'ai/react';
import styles from '/Users/tselmegulammandakh/Downloads/cpsc439/s24-bluebook-ai/frontend/src/app/page.module.css'; // change to ur own directory

export default function Chat() {
  const { messages, input, handleInputChange, handleSubmit } = useChat();
  return (
    <div className={styles.chatContainer}>
      <div className={styles.messages}>
      {messages.map(m => (
          <div key={m.id} className={`${styles.message} ${m.role === 'user' ? styles.user : ''}`}>
            {m.content}
          </div>
        ))}
      </div>
      <form onSubmit={handleSubmit} className={styles.inputForm}>
        <input
          className={styles.inputField}
          value={input}
          placeholder="Say something..."
          onChange={handleInputChange}
        />
      </form>
    </div>
  );
}
