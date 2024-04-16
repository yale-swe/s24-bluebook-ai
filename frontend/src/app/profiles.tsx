"use client";

import React, { useState } from "react";
import styles from "./page.module.css"; 
import { json } from "stream/consumers";

const ProfilePopup = () => {
    const [popupVisible, setPopupVisible] = useState(false);
    const [chatHistoryVisible, setChatHistoryVisible] = useState(false);
    const [username, setUsername] = useState("");
    const [courses, setCourses] = useState<string[]>([]);
    const [search, setSearch] = useState("");
    const [chatHistories, setChatHistories] = useState<{ id: number; summary: string }[]>([]);

    const togglePopupVisibility = () => {
        setPopupVisible(!popupVisible);
    };

    const toggleChatHistory = () => {
        setChatHistoryVisible(!chatHistoryVisible);
    };

    const handleSaveProfile = async () => {
        const response = await fetch('/api/save_profile', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ username }),
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
                setCourses(prevCourses => {
                    // Check if the course already exists based on the course code
                    const exists = prevCourses.some(course => course === data['course']);
                    if (!exists) {
                        return [...prevCourses, data['course']];
                    } else {
                        // alert the user that the course is already added
                        alert('This course is already added.');
                        return prevCourses;
                    }
                });
                setSearch('');
            } else {
                // Handle cases where the course code is not found or invalid
                alert('Invalid course code');
            }
        }
    };

    const reloadChat = async (chatId: number) => {
        console.log(`Reloading chat with ID: ${chatId}`);
        const response = await fetch(`/api/reload_chat/${chatId}`);
        if (response.ok) {
            const data = await response.json();
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
                    <button onClick={toggleChatHistory} className={styles.toggleChatHistoryButton}>Chat History</button>
                    
                    <div className={styles.profileHeader}>User Profile</div>
                    <div className={styles.profileDetails}>
                        <input type="text" value={username} onChange={(e) => setUsername(e.target.value)} placeholder="Username" />
                        <button onClick={handleSaveProfile}>Save</button>
                    </div>
                    <div className={styles.courseSearch}>
                        <input type="text" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search courses" />
                        <button onClick={handleAddCourse}>Add Course</button>
                        {courses.map(course => <div key={course}>{course}</div>)}
                    </div>
                    <button onClick={togglePopupVisibility} className={styles.closeButton}>Close</button>
                </div>
            )}

            {chatHistoryVisible && (
                <div className={`${styles.chatContainer} ${chatHistoryVisible ? styles.chatVisible : ""}`}>
                    <div className={styles.chatHeader}>Chat History</div>
                    <div className={styles.messages}>
                        {chatHistories.map(history => (
                            <div key={history.id} className={styles.message}>
                                <span>{history.summary}</span>
                                <button onClick={() => reloadChat(history.id)}>🔄</button>
                            </div>
                        ))}
                    </div>
                    <button onClick={toggleChatHistory} className={styles.closeButton}>Close</button>
                </div>
            )}
        </>
    );
};

export default ProfilePopup;