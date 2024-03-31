'use client';

import { useState } from 'react'; 
import { useChat } from 'ai/react';
import styles from '/Users/victorzhou/s24-bluebook-ai/frontend/src/app/page.module.css'; // change to ur own directory

export default function Chat() {
  const { messages, input, handleInputChange, handleSubmit } = useChat();

  const [isDarkMode, setIsDarkMode] = useState(false); 

  const toggleDarkMode = () => {
    setIsDarkMode(!isDarkMode); 
  }; 

  return (
    <>
      {/* Navbar starts here */}
      <div className={styles.navbar}>
        <div className={styles.navItem}>
          Contact
          <div className={styles.dropdownContent}>
            <a href="#">Contact Information</a> {/* Adjust href as needed */}
          </div>
        </div>
        <div className={styles.navItem}>
          About
          <div className={styles.dropdownContent}>
            <a href="#">About Section</a> {/* Adjust href as needed */}
          </div>
        </div>
        <div className={styles.navItem}>
          Profile
          <div className={styles.dropdownContent}>
            <a href="#">User Profile</a> {/* Adjust href as needed */}
          </div>
        </div>
      </div>
      {/* Navbar ends here */}
    <div className={styles.chatContainer}>
      {/* Logo addition starts here */}
      <div className={styles.logoContainer}>
        <img src="/logo.png" alt="Logo" className={styles.logo} />
        <span className={styles.chatbotName}>BluebookAI</span> 
      </div>
      {/* Logo addition ends here */}
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
      {/* Dark mode toggle button */}
      <button className={styles.darkModeToggle} onClick={toggleDarkMode}>
        {isDarkMode ? 'Light Mode' : 'Dark Mode'}
      </button>
    </div>
    {/* About Section starts here */}
    <div id="about" className={styles.infoSection}>
        <h2>About BluebookAI</h2>
        <p>
          BluebookAI aims to enhance Yale University students’ course selection experience by augmenting CourseTable with a natural
          language interface that can provide customized course recommendations in response to student queries.
        </p>
      </div>
      {/* About Section ends here */}

      {/* Contact Information starts here */}
      <div id="contact" className={styles.infoSection}>
        <h2>Contact Information</h2>
        <p>Email: aaabbb@yale.edu</p>
        <p>Phone: 123-456-7890</p>
      </div>
      {/* Contact Information ends here */}
   </>
  );
}
