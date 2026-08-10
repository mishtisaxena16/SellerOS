import React, { useState } from "react";

const ChatInput: React.FC = () => {
  const [message, setMessage] = useState("");

  return (
    <div className="chat-input">
      <input
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        placeholder="Ask SellerOS..."
      />

      <button>
        Send
      </button>
    </div>
  );
};

export default ChatInput;