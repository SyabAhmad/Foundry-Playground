import React from "react";

const LeftSidebar = ({
  conversations,
  currentConversation,
  onNewChat,
  onSelectConversation,
  onDeleteConversation,
  showSidebar,
}) => {
  if (!showSidebar) return null;

  return (
    <div className="sidebar left-sidebar">
      <div className="sidebar-header">
        <button className="new-chat-btn" onClick={onNewChat}>
          <span>+</span> New Chat
        </button>
      </div>
      <div className="conversations-list">
        {conversations.map((conv) => (
          <div
            key={conv.id}
            className={`conversation-item ${
              currentConversation?.id === conv.id ? "active" : ""
            }`}
          >
            <div
              className="conversation-content"
              onClick={() => onSelectConversation(conv)}
            >
              <div className="conversation-title">{conv.title}</div>
              <div className="conversation-date">
                {new Date(
                  conv.created_at || conv.createdAt
                ).toLocaleDateString()}
              </div>
            </div>
            <button
              className="delete-conversation-btn"
              onClick={(e) => {
                e.stopPropagation();
                if (window.confirm(`Delete conversation "${conv.title}"?`)) {
                  onDeleteConversation(conv.id);
                }
              }}
              title="Delete conversation"
            >
              🗑️
            </button>
          </div>
        ))}
      </div>
      <div className="sidebar-footer">
        <button className="sidebar-btn">Settings</button>
        <button className="sidebar-btn">Help</button>
      </div>
    </div>
  );
};

export default LeftSidebar;
