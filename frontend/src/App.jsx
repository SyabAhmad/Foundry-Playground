import { useState, useEffect } from "react";
import "./App.css";
import { LeftSidebar, RightSidebar, ChatArea } from "./components";

const API_BASE_URL = "http://localhost:5000/api";

function App() {
  const [conversations, setConversations] = useState([]);
  const [currentConversation, setCurrentConversation] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [models, setModels] = useState([]);
  const [selectedModel, setSelectedModel] = useState("");
  const [showLeftSidebar, setShowLeftSidebar] = useState(true);
  const [showRightSidebar, setShowRightSidebar] = useState(true);
  const [userId] = useState("demo-user"); // For demo purposes

  const fetchModels = async () => {
    try {
      console.log("Fetching models...");
      const response = await fetch(`${API_BASE_URL}/models`);
      const data = await response.json();
      console.log("Models response:", data);

      if (data.success && data.models) {
        // Handle both OpenAI format and our custom format
        let modelsList = data.models;
        if (data.source === "foundry_local" && Array.isArray(data.models)) {
          // Already in the right format
          modelsList = data.models;
        }

        console.log("Setting models:", modelsList);
        setModels(modelsList);
        if (modelsList.length > 0 && !selectedModel) {
          const firstModel = modelsList[0].id || modelsList[0];
          console.log("Setting selected model:", firstModel);
          setSelectedModel(firstModel);
        }
      } else {
        console.log("No models in response or success=false");
      }
    } catch (error) {
      console.error("Error fetching models:", error);
    }
  };

  const loadConversations = async () => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/conversations?user_id=${userId}`
      );
      const data = await response.json();
      if (data.success) {
        setConversations(data.conversations);
      }
    } catch (error) {
      console.error("Error loading conversations:", error);
    }
  };

  const saveConversation = async (conversation) => {
    try {
      const method = conversation.id ? "PUT" : "POST";
      const url = conversation.id
        ? `${API_BASE_URL}/conversations/${conversation.id}`
        : `${API_BASE_URL}/conversations`;

      const response = await fetch(url, {
        method,
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          ...conversation,
          user_id: userId,
        }),
      });

      const data = await response.json();
      return data.success ? data.conversation : null;
    } catch (error) {
      console.error("Error saving conversation:", error);
      return null;
    }
  };

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => {
    fetchModels();
    loadConversations();
  }, []);

  const createNewConversation = async () => {
    // Don't create new chat if current chat is empty (no messages)
    if (currentConversation && messages.length === 0) {
      return;
    }

    const newConversation = {
      title: "New Conversation",
      model: selectedModel,
    };

    const savedConversation = await saveConversation(newConversation);
    if (savedConversation) {
      await loadConversations(); // Reload conversations to get the updated list
      setCurrentConversation(savedConversation);
      setMessages([]);
    }
  };

  const deleteConversation = async (conversationId) => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/conversations/${conversationId}`,
        {
          method: "DELETE",
        }
      );

      if (response.ok) {
        await loadConversations(); // Reload conversations list

        // If the deleted conversation was the current one, clear it
        if (currentConversation && currentConversation.id === conversationId) {
          setCurrentConversation(null);
          setMessages([]);
        }
      } else {
        alert("Failed to delete conversation");
      }
    } catch (error) {
      console.error("Error deleting conversation:", error);
      alert("Error deleting conversation");
    }
  };

  const selectConversation = async (conversation) => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/conversations/${conversation.id}`
      );
      const data = await response.json();
      if (data.success) {
        setCurrentConversation(data.conversation);
        setMessages(data.messages);
        setSelectedModel(data.conversation.model_used || selectedModel);
      }
    } catch (error) {
      console.error("Error loading conversation:", error);
      // Fallback to basic conversation data
      setCurrentConversation(conversation);
      setMessages(conversation.messages || []);
      setSelectedModel(conversation.model || selectedModel);
    }
  };

  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage = {
      id: Date.now().toString(),
      role: "user",
      content: inputMessage,
      timestamp: new Date().toISOString(),
    };

    const newMessages = [...messages, userMessage];
    setMessages(newMessages);
    setInputMessage("");
    setIsLoading(true);

    if (currentConversation) {
      // Save user message to database
      try {
        await fetch(
          `${API_BASE_URL}/conversations/${currentConversation.id}/messages`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              role: "user",
              content: inputMessage,
              model: selectedModel,
            }),
          }
        );
      } catch (error) {
        console.error("Error saving user message:", error);
      }

      // Update conversation title if it's the first message
      if (newMessages.length === 1) {
        const updatedConversation = {
          ...currentConversation,
          title: inputMessage.slice(0, 50) + "...",
        };
        await saveConversation(updatedConversation);
        setCurrentConversation(updatedConversation);
      }
    }

    try {
      // Convert messages to OpenAI format
      const openaiMessages = newMessages.map((msg) => ({
        role: msg.role,
        content: msg.content,
      }));

      const response = await fetch(
        `${API_BASE_URL}/chat${
          currentConversation ? `/${currentConversation.id}` : ""
        }`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            model: selectedModel,
            messages: openaiMessages,
            max_tokens: 500,
            temperature: 0.7,
          }),
        }
      );

      const data = await response.json();

      if (data.choices && data.choices.length > 0) {
        // OpenAI-compatible response format
        const assistantContent = data.choices[0].message.content;

        const assistantMessage = {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: assistantContent,
          timestamp: new Date().toISOString(),
        };

        const finalMessages = [...newMessages, assistantMessage];
        setMessages(finalMessages);

        if (currentConversation) {
          // Save assistant message to database
          try {
            await fetch(
              `${API_BASE_URL}/conversations/${currentConversation.id}/messages`,
              {
                method: "POST",
                headers: {
                  "Content-Type": "application/json",
                },
                body: JSON.stringify({
                  role: "assistant",
                  content: assistantContent,
                  model: selectedModel,
                  tokens_used: data.usage?.total_tokens,
                }),
              }
            );
          } catch (error) {
            console.error("Error saving assistant message:", error);
          }
        }
      } else if (data.success && data.response) {
        // Fallback for custom response format
        const assistantMessage = {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: data.response,
          timestamp: new Date().toISOString(),
        };

        const finalMessages = [...newMessages, assistantMessage];
        setMessages(finalMessages);

        if (currentConversation) {
          // Save assistant message to database
          try {
            await fetch(
              `${API_BASE_URL}/conversations/${currentConversation.id}/messages`,
              {
                method: "POST",
                headers: {
                  "Content-Type": "application/json",
                },
                body: JSON.stringify({
                  role: "assistant",
                  content: data.response,
                  model: selectedModel,
                  tokens_used: data.usage?.total_tokens,
                }),
              }
            );
          } catch (error) {
            console.error("Error saving assistant message:", error);
          }
        }
      } else {
        const errorMessage = {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: `Error: ${data.error || "Something went wrong"}`,
          timestamp: new Date().toISOString(),
          isError: true,
        };
        setMessages([...newMessages, errorMessage]);
      }
    } catch (error) {
      console.error("Error sending message:", error);
      const errorMessage = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: "Sorry, I encountered an error. Please try again.",
        timestamp: new Date().toISOString(),
        isError: true,
      };
      setMessages([...newMessages, errorMessage]);
    }

    setIsLoading(false);
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const handleSuggestionClick = (suggestion) => {
    setInputMessage(suggestion);
  };

  const handlePullModel = async (modelId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/models/pull/${modelId}`, {
        method: "POST",
      });
      const data = await response.json();
      if (data.success) {
        alert(`Model ${modelId} download started successfully!`);
        // Refresh models list
        fetchModels();
      } else {
        alert(`Failed to download model: ${data.message}`);
      }
    } catch (error) {
      console.error("Error pulling model:", error);
      alert("Error downloading model");
    }
  };

  const handleStopModel = async (modelId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/models/stop/${modelId}`, {
        method: "POST",
      });
      const data = await response.json();
      if (data.success) {
        alert(`Model ${modelId} stopped successfully!`);
        // Refresh models list
        fetchModels();
      } else {
        alert(`Failed to stop model: ${data.message}`);
      }
    } catch (error) {
      console.error("Error stopping model:", error);
      alert("Error stopping model");
    }
  };

  return (
    <div className="app">
      <LeftSidebar
        conversations={conversations}
        currentConversation={currentConversation}
        onNewChat={createNewConversation}
        onSelectConversation={selectConversation}
        onDeleteConversation={deleteConversation}
        showSidebar={showLeftSidebar}
      />

      <ChatArea
        messages={messages}
        inputMessage={inputMessage}
        onInputChange={setInputMessage}
        onSendMessage={sendMessage}
        onKeyPress={handleKeyPress}
        selectedModel={selectedModel}
        onModelChange={setSelectedModel}
        models={models}
        isLoading={isLoading}
        onSuggestionClick={handleSuggestionClick}
        onToggleLeftSidebar={() => setShowLeftSidebar(!showLeftSidebar)}
        onToggleRightSidebar={() => setShowRightSidebar(!showRightSidebar)}
      />

      <RightSidebar
        models={models}
        selectedModel={selectedModel}
        onModelSelect={setSelectedModel}
        showSidebar={showRightSidebar}
        onPullModel={handlePullModel}
        onStopModel={handleStopModel}
      />
    </div>
  );
}

export default App;
