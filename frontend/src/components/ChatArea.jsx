import React, { useRef, useEffect } from "react";
import Message from "./Message";
import WelcomeMessage from "./WelcomeMessage";
import InputArea from "./InputArea";

const ChatArea = ({
  messages,
  inputMessage,
  onInputChange,
  onSendMessage,
  onKeyPress,
  selectedModel,
  onModelChange,
  models,
  isLoading,
  onSuggestionClick,
  onToggleLeftSidebar,
  onToggleRightSidebar,
}) => {
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  return (
    <div className="main-chat">
      <div className="chat-header">
        <button className="sidebar-toggle" onClick={onToggleLeftSidebar}>
          ☰
        </button>
        <h1>Foundry Playground</h1>
        <button className="sidebar-toggle" onClick={onToggleRightSidebar}>
          ⚙️
        </button>
      </div>

      <div className="messages-container">
        {messages.length === 0 ? (
          <WelcomeMessage onSuggestionClick={onSuggestionClick} />
        ) : (
          messages.map((message) => (
            <Message key={message.id} message={message} />
          ))
        )}
        {isLoading && (
          <div className="message assistant loading">
            <div className="message-content">
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <InputArea
        inputMessage={inputMessage}
        onInputChange={onInputChange}
        onSendMessage={onSendMessage}
        onKeyPress={onKeyPress}
        selectedModel={selectedModel}
        onModelChange={onModelChange}
        models={models}
        isLoading={isLoading}
      />
    </div>
  );
};

export default ChatArea;
