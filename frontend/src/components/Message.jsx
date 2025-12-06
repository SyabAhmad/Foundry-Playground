import React from "react";

const Message = ({ message }) => {
  return (
    <div
      className={`message ${message.role} ${message.isError ? "error" : ""}`}
    >
      <div className="message-content">{message.content}</div>
      <div className="message-timestamp">
        {new Date(message.timestamp).toLocaleTimeString()}
      </div>
    </div>
  );
};

export default Message;
