import React, { useState } from "react";

const RightSidebar = ({
  downloadedModels = [],
  availableModels = [],
  runningModels = [],
  allModels = [],
  selectedModel,
  onModelSelect,
  showSidebar,
  onPullModel,
  onStopModel,
}) => {
  const [activeSection, setActiveSection] = useState("models");

  if (!showSidebar) return null;

  // For demo purposes, split models into downloaded and available

  return (
    <div className="sidebar right-sidebar">
      {/* Section Tabs */}
      <div className="sidebar-tabs">
        <button
          className={`sidebar-tab ${
            activeSection === "models" ? "active" : ""
          }`}
          onClick={() => setActiveSection("models")}
        >
          Models
        </button>
        <button
          className={`sidebar-tab ${
            activeSection === "training" ? "active" : ""
          }`}
          onClick={() => setActiveSection("training")}
        >
          Training
        </button>
        <button
          className={`sidebar-tab ${
            activeSection === "system" ? "active" : ""
          }`}
          onClick={() => setActiveSection("system")}
        >
          System
        </button>
      </div>

      {/* Models Section */}
      {activeSection === "models" && (
        <div className="sidebar-content">
          {/* Current Model Selection */}
          <div className="sidebar-section">
            <h3>Active Model</h3>
            <div className="current-model">
              <select
                value={selectedModel}
                onChange={(e) => onModelSelect(e.target.value)}
                className="model-select"
              >
                {downloadedModels.map((model, index) => (
                  <option key={index} value={model.id || model.name || model}>
                    {model.name || model.id || model}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Downloaded Models */}
          <div className="sidebar-section">
            <h3>Downloaded Models ({downloadedModels.length})</h3>
            <div className="models-list">
              {downloadedModels.length > 0 ? (
                downloadedModels.map((model, index) => (
                  <div
                    key={index}
                    className={`model-item downloaded ${
                      selectedModel === (model.id || model.name || model)
                        ? "active"
                        : ""
                    }`}
                    onClick={() =>
                      onModelSelect(model.id || model.name || model)
                    }
                  >
                    <div className="model-info">
                      <div className="model-name">
                        {model.name || model.id || model}
                      </div>
                      <div className="model-type">{model.type || "text"}</div>
                    </div>
                    <div className="model-status">
                      <span
                        className={`status-dot ${
                          (runningModels || []).some(
                            (r) =>
                              ((r.id || r.rawId || r.name || "") + "").replace(
                                /:/g,
                                "-"
                              ) ===
                              ((model.id || model.name || model) + "").replace(
                                /:/g,
                                "-"
                              )
                          )
                            ? "online"
                            : "offline"
                        }`}
                      ></span>
                      <button
                        className="model-action-btn"
                        onClick={(e) => {
                          e.stopPropagation();
                          onStopModel &&
                            onStopModel(model.id || model.name || model);
                        }}
                        title="Stop model"
                      >
                        ⏹️
                      </button>
                    </div>
                  </div>
                ))
              ) : (
                <p className="no-models">No downloaded models</p>
              )}
            </div>
          </div>

          {/* Available Models to Download */}
          <div className="sidebar-section">
            <h3>Available Models ({availableModels.length})</h3>
            <div className="models-list">
              {availableModels.length > 0 ? (
                availableModels.map((model, index) => (
                  <div key={index} className="model-item available">
                    <div className="model-info">
                      <div className="model-name">
                        {model.name || model.id || model}
                      </div>
                      <div className="model-type">{model.type || "text"}</div>
                      <div className="model-size">{model.size || "2.1 GB"}</div>
                    </div>
                    <button
                      className="download-btn"
                      onClick={() =>
                        onPullModel &&
                        onPullModel(model.id || model.name || model)
                      }
                      title="Download model"
                    >
                      ⬇️
                    </button>
                  </div>
                ))
              ) : (
                <p className="no-models">No additional models available</p>
              )}
            </div>
          </div>
          {/* All Models (complete catalog) */}
          <div className="sidebar-section">
            <h3>All Models ({allModels.length})</h3>
            <div className="models-list">
              {allModels.length > 0 ? (
                allModels.map((model, index) => (
                  <div key={index} className="model-item available">
                    <div className="model-info">
                      <div className="model-name">
                        {model.name || model.id || model}
                      </div>
                      <div className="model-type">{model.type || "text"}</div>
                      <div className="model-size">{model.file_size || ""}</div>
                    </div>
                    <button
                      className="download-btn"
                      onClick={() =>
                        onPullModel &&
                        onPullModel(model.id || model.name || model)
                      }
                      title="Download model"
                    >
                      ⬇️
                    </button>
                  </div>
                ))
              ) : (
                <p className="no-models">No catalog models available</p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Training Section */}
      {activeSection === "training" && (
        <div className="sidebar-content">
          <div className="sidebar-section">
            <h3>Training Jobs</h3>
            <div className="training-status">
              <p>No active training jobs</p>
              <button className="sidebar-btn small">Start Training</button>
            </div>
          </div>

          <div className="sidebar-section">
            <h3>RAG Systems</h3>
            <div className="rag-status">
              <p>No active RAG systems</p>
              <button className="sidebar-btn small">Create RAG</button>
            </div>
          </div>
        </div>
      )}

      {/* System Section */}
      {activeSection === "system" && (
        <div className="sidebar-content">
          <div className="sidebar-section">
            <h3>System Status</h3>
            <div className="status-indicators">
              <div className="status-item">
                <span className="status-dot online"></span>
                Foundry Local: Connected
              </div>
              <div className="status-item">
                <span className="status-dot online"></span>
                Database: Connected
              </div>
              <div className="status-item">
                <span className="status-dot online"></span>
                API: Healthy
              </div>
            </div>
          </div>

          <div className="sidebar-section">
            <h3>Performance</h3>
            <div className="performance-metrics">
              <div className="metric">
                <span className="metric-label">Memory Usage:</span>
                <span className="metric-value">2.3 GB</span>
              </div>
              <div className="metric">
                <span className="metric-label">Active Models:</span>
                <span className="metric-value">{downloadedModels.length}</span>
              </div>
              <div className="metric">
                <span className="metric-label">Conversations:</span>
                <span className="metric-value">12</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default RightSidebar;
