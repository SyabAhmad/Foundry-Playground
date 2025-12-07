import React, { useEffect, useState } from "react";
import { LeftSidebar, RightSidebar, ChatArea } from "../components";
import api from "../api/api";

const MainApp = () => {
  const [conversations, setConversations] = useState([]);
  const [currentConversation, setCurrentConversation] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [models, setModels] = useState([]);
  const [availableModels, setAvailableModels] = useState([]);
  const [allModels, setAllModels] = useState([]);
  const [selectedModel, setSelectedModel] = useState("");
  const [showLeftSidebar, setShowLeftSidebar] = useState(true);
  const [showRightSidebar, setShowRightSidebar] = useState(true);
  const userId = "demo-user";

  const fetchModels = async () => {
    try {
      const resp = await api.getModels();
      let modelsList =
        resp.success && Array.isArray(resp.models) ? resp.models : [];
      setModels(
        modelsList.map((m) => ({
          ...(typeof m === "string" ? { id: m, name: m } : m),
          id: ((typeof m === "string" ? m : m.id || m.name || "") || "")
            .toString()
            .replace(/:/g, "-"),
        }))
      );
      if (modelsList.length > 0 && !selectedModel) {
        setSelectedModel(
          (modelsList[0].id || modelsList[0]).toString().replace(/:/g, "-")
        );
      }

      // Pullable models
      const pull = await api.getPullableModels();
      if (pull.success && Array.isArray(pull.models)) {
        const downloadedIds = (modelsList || []).map((m) =>
          ((m.id || m.name || "") + "").replace(/:/g, "-")
        );
        const filtered = pull.models.filter((m) => {
          const id = (m.id || m.name || "") + "";
          return !downloadedIds.includes(id.replace(/:/g, "-"));
        });
        setAvailableModels(filtered);
        if (
          (!modelsList || modelsList.length === 0) &&
          pull.models.length > 0 &&
          !selectedModel
        ) {
          setSelectedModel(
            (pull.models[0].id || pull.models[0]).toString().replace(/:/g, "-")
          );
        }
      } else {
        setAvailableModels([]);
      }

      try {
        const allResp = await api.getAllModels();
        if (allResp.success && Array.isArray(allResp.models)) {
          setAllModels(
            allResp.models.map((m) => ({
              ...(typeof m === "string" ? { id: m, name: m } : m),
              id: ((typeof m === "string" ? m : m.id || m.name || "") || "")
                .toString()
                .replace(/:/g, "-"),
            }))
          );
        } else setAllModels([]);
      } catch (e) {
        setAllModels([]);
      }
    } catch (err) {
      console.error("Error fetching models:", err);
    }
  };

  const loadConversations = async () => {
    try {
      const response = await api.getConversations(userId);
      if (response.success) setConversations(response.conversations);
    } catch (err) {
      console.error("Error loading conversations:", err);
    }
  };

  useEffect(() => {
    fetchModels();
    loadConversations();
  }, []);

  const saveConversation = async (conversation) => {
    try {
      let response;
      if (conversation.id) {
        response = await api.updateConversation(conversation.id, {
          ...conversation,
          user_id: userId,
        });
      } else {
        response = await api.createConversation({
          ...conversation,
          user_id: userId,
        });
      }
      return response.success ? response.conversation : null;
    } catch (err) {
      console.error("Error saving conversation:", err);
      return null;
    }
  };

  // Rest of logic (selecting conv, sending messages, pulling models, etc.)
  const createNewConversation = async () => {
    if (currentConversation && messages.length === 0) return;
    const newConversation = { title: "New Conversation", model: selectedModel };
    const saved = await saveConversation(newConversation);
    if (saved) {
      await loadConversations();
      setCurrentConversation(saved);
      setMessages([]);
    }
  };

  const deleteConversation = async (conversationId) => {
    try {
      const result = await api.deleteConversation(conversationId);
      if (result.ok) {
        await loadConversations();
        if (currentConversation && currentConversation.id === conversationId) {
          setCurrentConversation(null);
          setMessages([]);
        }
      } else {
        alert("Failed to delete conversation");
      }
    } catch (err) {
      console.error("Error deleting conversation:", err);
      alert("Error deleting conversation");
    }
  };

  const selectConversation = async (conversation) => {
    try {
      const data = await api.getConversation(conversation.id);
      if (data.success) {
        setCurrentConversation(data.conversation);
        setMessages(data.messages);
        setSelectedModel(data.conversation.model_used || selectedModel);
      }
    } catch (err) {
      console.error("Error loading conversation:", err);
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
      try {
        await api.postConversationMessage(currentConversation.id, {
          role: "user",
          content: inputMessage,
          model: selectedModel,
        });
      } catch (err) {
        console.error("Error saving user message:", err);
      }

      if (newMessages.length === 1) {
        const updated = {
          ...currentConversation,
          title: inputMessage.slice(0, 50) + "...",
        };
        const saved = await saveConversation(updated);
        if (saved) setCurrentConversation(saved);
      }
    }

    try {
      const openaiMessages = newMessages.map((m) => ({
        role: m.role,
        content: m.content,
      }));
      const data = await api.chat(
        currentConversation ? currentConversation.id : null,
        {
          model: selectedModel,
          messages: openaiMessages,
          max_tokens: 500,
          temperature: 0.7,
        }
      );

      if (data.choices && data.choices.length > 0) {
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
          try {
            await api.postConversationMessage(currentConversation.id, {
              role: "assistant",
              content: assistantContent,
              model: selectedModel,
              tokens_used: data.usage?.total_tokens,
            });
          } catch (err) {
            console.error("Error saving assistant message:", err);
          }
        }
      } else if (data.success && data.response) {
        const assistantMessage = {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: data.response,
          timestamp: new Date().toISOString(),
        };
        const finalMessages = [...newMessages, assistantMessage];
        setMessages(finalMessages);
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
    } catch (err) {
      console.error("Error sending message:", err);
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

  const handlePullModel = async (modelId) => {
    try {
      const response = await api.pullModel(modelId);
      if (response.success) {
        alert(`Model ${modelId} download started successfully!`);
        await fetchModels();
      } else
        alert(
          `Failed to download model: ${response.message || response.details}`
        );
    } catch (err) {
      console.error("Error pulling model:", err);
      alert("Error downloading model");
    }
  };

  const handleStopModel = async (modelId) => {
    try {
      const response = await api.stopModel(modelId);
      if (response.success) {
        alert(`Model ${modelId} stopped successfully!`);
        await fetchModels();
      } else
        alert(`Failed to stop model: ${response.message || response.details}`);
    } catch (err) {
      console.error("Error stopping model:", err);
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
        onKeyPress={(e) => {
          if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
          }
        }}
        selectedModel={selectedModel}
        onModelChange={setSelectedModel}
        models={models}
        isLoading={isLoading}
        onSuggestionClick={(s) => setInputMessage(s)}
        onToggleLeftSidebar={() => setShowLeftSidebar(!showLeftSidebar)}
        onToggleRightSidebar={() => setShowRightSidebar(!showRightSidebar)}
      />

      <RightSidebar
        downloadedModels={models}
        availableModels={availableModels}
        allModels={allModels}
        selectedModel={selectedModel}
        onModelSelect={setSelectedModel}
        showSidebar={showRightSidebar}
        onPullModel={handlePullModel}
        onStopModel={handleStopModel}
      />
    </div>
  );
};

export default MainApp;
