"use client";

import React, { useState } from "react";
import styles from "./page.module.css"; // Use your specific styles directory

const ProfilePopup = () => {
    const [popupVisible, setPopupVisible] = useState(false);
    const [username, setUsername] = useState("JohnDoe");
    const [email, setEmail] = useState("johndoe@example.com");
    const [courses, setCourses] = useState<string[]>([]);
    const [search, setSearch] = useState("");
    const [chatHistories, setChatHistories] = useState<{ id: number; summary: string }[]>([]);

    const togglePopupVisibility = () => {
        setPopupVisible(!popupVisible);
    };

    const handleSaveProfile = async () => {
        const response = await fetch('/api/save_profile', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ username, email }),
        });
        if (!response.ok) {
            console.error("Failed to save profile");
        }
    };

    const handleAddCourse = async () => {
        if (search) {
            const response = await fetch('http://127.0.0.1:8000/api/verify_course_code', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ search }),
            });
            if (response.ok) {
                const data = await response.json();
                setCourses(prevCourses => [...prevCourses, data]);
                setSearch('');
            }
        }
    };

    const reloadChat = async (chatId: number) => {
        console.log(`Reloading chat with ID: ${chatId}`);
        // Simulate fetching chat data from a backend
        const response = await fetch(`/api/reload_chat/${chatId}`);
        if (response.ok) {
            const data = await response.json();
            // Assuming you have a state for the current chat display:
            // setCurrentChat(data.chatContent);
            console.log("Chat reloaded:", data.chatContent);
        } else {
            console.error("Failed to reload chat");
        }
    };

    const addChatHistory = (summary: string) => {
        const newHistory = { id: Date.now(), summary };
        setChatHistories(prevHistories => [...prevHistories, newHistory]);
    };

    return (
        <>
            <button onClick={togglePopupVisibility} className={styles.floatingProfileButton}>
                
            </button>

            {popupVisible && (
                <div className={`${styles.profileContainer} ${popupVisible ? styles.profileVisible : ""}`}>
                    <div className={styles.profileHeader}>User Profile</div>
                    <div className={styles.profileDetails}>
                        <input type="text" value={username} onChange={(e) => setUsername(e.target.value)} placeholder="Username" />
                        <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email" />
                        <button onClick={handleSaveProfile}>Save</button>
                    </div>
                    <div className={styles.courseSearch}>
                        <input type="text" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search courses" />
                        <button onClick={handleAddCourse}>Add Course</button>
                        {courses.map(course => <div key={course}>{course}</div>)}
                    </div>
                    <div className={styles.chatHistory}>
                        <div className={styles.chatHistoryHeader}>Chat History</div>
                        <div className={styles.chatHistoryList}>
                            {chatHistories.map(history => (
                                <div key={history.id} className={styles.chatTile}>
                                    <span>{history.summary}</span>
                                    <button onClick={() => reloadChat(history.id)}>🔄</button>
                                </div>
                            ))}
                        </div>
                    </div>
                    <button onClick={togglePopupVisibility} className={styles.closeButton}>Close</button>
                </div>
            )}
        </>
    );
};

export default ProfilePopup;