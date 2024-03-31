// FullScreenChat.tsx

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

const FullScreenChat = () => {
  const [messages, setMessages] = useState([]);
  const navigate = useNavigate();

  const exitFullScreen = () => {
    navigate(-1);
  };

  return (
    <div style={{ position: 'fixed', top: 0, left: 0, width: '100vw', height: '100vh', backgroundColor: 'white', zIndex: 1000 }}>
      <button onClick={exitFullScreen}>Exit Full Screen</button>
    </div>
  );
};

export default FullScreenChat;
