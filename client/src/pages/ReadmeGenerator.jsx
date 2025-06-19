import React, { useState } from "react";
import Header from "./Header";
import "./ReadmeGenerator.css";

const ReadmeGenerator = () => {
  const [githubUrl, setGithubUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [readmeContent, setReadmeContent] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [step, setStep] = useState("input");

  const isValidGitHubUrl = (url) => {
    const githubUrlRegex =
      /^https?:\/\/(www\.)?github\.com\/[a-zA-Z0-9_.-]+\/[a-zA-Z0-9_.-]+\/?$/;
    return githubUrlRegex.test(url);
  };

  const generateReadme = async () => {
    if (!githubUrl.trim()) {
      setError("Please enter a GitHub repository URL");
      return;
    }
    if (!isValidGitHubUrl(githubUrl)) {
      setError("Please enter a valid GitHub repository URL");
      return;
    }
    setLoading(true);
    setError("");
    setSuccess("");
    setStep("generating");
    try {
      const response = await fetch("/api/readme-gen/generate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ githubUrl: githubUrl.trim() }),
      });
      const data = await response.json();
      if (!data.success) {
        setError(data.error || "Failed to generate README");
        setStep("input");
        return;
      }
      setReadmeContent(data.data.readme_content);
      setStep("complete");
      setSuccess("README generated successfully!");
    } catch (err) {
      console.error("Error generating README:", err);
      setError("Failed to generate README. Please try again.");
      setStep("input");
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(readmeContent);
      setSuccess("README copied to clipboard!");
      setTimeout(() => setSuccess(""), 3000);
    } catch (err) {
      setError(`Failed to copy to clipboard: ${err.message}`);
    }
  };

  const downloadReadme = () => {
    const blob = new Blob([readmeContent], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "README.md";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    setSuccess("README downloaded successfully!");
    setTimeout(() => setSuccess(""), 3000);
  };

  const resetGenerator = () => {
    setGithubUrl("");
    setReadmeContent("");
    setError("");
    setSuccess("");
    setStep("input");
  };

  return (
    <div className="readmegen-outer-bg">
      <Header />
      <div className="readmegen-container">
        <div className="header">
          <h1>README Generator</h1>
          <p>Transform any GitHub repository into a professional README.md using AI</p>
        </div>

        {error && <div className="alert error">{error}</div>}
        {success && <div className="alert success">{success}</div>}

        {step === "input" && (
          <div className="card" style={{ textAlign: "left" }}>
            <div className="form-group" style={{ textAlign: "left" }}>
              <label>GitHub Repository URL</label>
              <input
                type="url"
                value={githubUrl}
                onChange={(e) => setGithubUrl(e.target.value)}
                placeholder="https://github.com/username/repository-name"
                disabled={loading}
              />
            </div>
            <div style={{ display: "flex", gap: "1rem", marginTop: "1rem" }}>
              <button
                onClick={generateReadme}
                disabled={loading}
                style={{ padding: '0.5rem 1rem' }}
              >
                {loading ? (
                  <>
                    <span className="spinner"></span> Generating README...
                  </>
                ) : (
                  "Generate README"
                )}
              </button>
            </div>
          </div>
        )}

        {step === "generating" && (
          <div className="card center">
            <div className="loader"></div>
            <h2>Generating Your README...</h2>
            <p>Please wait while we analyze your code.</p>
          </div>
        )}

        {step === "complete" && readmeContent && (
          <div className="card">
            <h2>README Generated Successfully!</h2>
            <div className="actions">
              <button onClick={copyToClipboard}>Copy</button>
              <button onClick={downloadReadme}>Download</button>
              <button onClick={resetGenerator}>New README</button>
            </div>
            <div className="preview-container">
              <pre className="preview">{readmeContent}</pre>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ReadmeGenerator;