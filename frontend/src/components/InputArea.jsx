import React from "react";

const InputArea = ({
  inputMessage,
  onInputChange,
  onSendMessage,
  onKeyPress,
  selectedModel,
  onModelChange,
  models,
  isLoading,
}) => {
  return (
    <div className="input-container">
      <div className="input-wrapper">
        <textarea
          value={inputMessage}
          onChange={(e) => onInputChange(e.target.value)}
          onKeyPress={onKeyPress}
          placeholder="Type your message here..."
          rows={1}
          disabled={isLoading}
        />
        <button
          className="send-btn"
          onClick={onSendMessage}
          disabled={!inputMessage.trim() || isLoading}
        >
          {isLoading ? "..." : "→"}
        </button>
      </div>
      {/* <div className="input-footer">
        <select
          value={selectedModel}
          onChange={(e) => onModelChange(e.target.value)}
          className="model-select"
        >
          {models.map((model, index) => (
            <option key={index} value={model.id || model.name || model}>
              {model.name || model.id || model}
            </option>
          ))}
        </select>
      </div> */}
      <div
        style={{
          textAlign: "center",
          fontSize: "0.7rem",
          color: "#aaa",
          marginTop: "8px",
        }}
      >
        ©2025 <a href="http://syab.tech/mentee">MenteE™</a> All rights reserved.
      </div>
    </div>
  );
};

export default InputArea;
