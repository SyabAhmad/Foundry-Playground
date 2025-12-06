import React from "react";

const WelcomeMessage = ({ onSuggestionClick }) => {
  return (
    <div className="welcome-message">
      <h2>Welcome to Foundry Playground</h2>
      <p>
        Start a conversation with AI models powered by Microsoft Foundry Local
      </p>
      <div className="suggestions">
        <div
          className="suggestion"
          onClick={() =>
            onSuggestionClick("Explain quantum computing in simple terms")
          }
        >
          Explain quantum computing
        </div>
        <div
          className="suggestion"
          onClick={() =>
            onSuggestionClick(
              "Write a Python function to calculate fibonacci numbers"
            )
          }
        >
          Python fibonacci function
        </div>
        <div
          className="suggestion"
          onClick={() =>
            onSuggestionClick("What are the benefits of renewable energy?")
          }
        >
          Benefits of renewable energy
        </div>
      </div>
    </div>
  );
};

export default WelcomeMessage;
