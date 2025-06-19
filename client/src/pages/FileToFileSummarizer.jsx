import React, { useState } from "react";
import ReactMarkdown from "react-markdown";
import Header from "./Header";
import "./FileToFileSummarizer.css";

const FileToFileSummarizer = () => {
  const [githubUrl, setGithubUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [summaryContent, setSummaryContent] = useState("");
  const [lastSummarizedUrl, setLastSummarizedUrl] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [step, setStep] = useState("input");

  const isValidGitHubUrl = (url) => {
    const githubUrlRegex =
      /^https?:\/\/(www\.)?github\.com\/[a-zA-Z0-9_.-]+\/[a-zA-Z0-9_.-]+\/?$/;
    return githubUrlRegex.test(url);
  };

  const generateSummary = async () => {
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
      const response = await fetch("/api/file-summary/generate-preview", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ githubUrl: githubUrl.trim() }),
      });
      const data = await response.json();
      if (!data.success) {
        setError(data.error || "Failed to generate summary");
        setStep("input");
        return;
      }
      setSummaryContent(data.data.summary_content);
      setLastSummarizedUrl(githubUrl.trim());
      setStep("complete");
      setSuccess("Summary generated successfully!");
    // eslint-disable-next-line no-unused-vars
    } catch (err) {
      setError("Failed to generate summary. Please try again.");
      setStep("input");
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(summaryContent);
      setSuccess("Summary copied to clipboard!");
      setTimeout(() => setSuccess(""), 3000);
    } catch (err) {
      setError(`Failed to copy to clipboard: ${err.message}`);
    }
  };

  const downloadPDFSummary = async () => {
    if (!lastSummarizedUrl) {
      setError("No summary to download. Please generate a summary first.");
      return;
    }
    setLoading(true);
    setError("");
    setSuccess("");
    try {
      const response = await fetch("/api/file-summary/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ githubUrl: lastSummarizedUrl }),
      });
      if (!response.ok) {
        setError("Failed to generate PDF summary");
        return;
      }
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", "summary.pdf");
      document.body.appendChild(link);
      link.click();
      link.parentNode.removeChild(link);
      setSuccess("PDF summary downloaded successfully!");
      setTimeout(() => setSuccess(""), 3000);
    // eslint-disable-next-line no-unused-vars
    } catch (err) {
      setError("Failed to download PDF summary. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const reset = () => {
    setGithubUrl("");
    setSuccess("");
    setError("");
    setSummaryContent("");
    setLastSummarizedUrl("");
    setStep("input");
  };

  return (
    <div className="readmegen-outer-bg">
      <Header />
      <div className="readmegen-container">
        <div className="header">
          <h1>File-to-File Summarizer</h1>
          <p>Instant GitHub repo summaries.</p>
        </div>

        {error && <div className="alert error">{error}</div>}
        {success && <div className="alert success">{success}</div>}

        {step === "input" && (
          <div className="card" style={{ textAlign: "left" }}>
            <div className="form-group">
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
                type="button"
                onClick={generateSummary}
                disabled={loading}
                style={{ padding: '0.5rem 1rem' }}
              >
                {loading ? (
                  <>
                    <span className="spinner"></span> Generating Summary...
                  </>
                ) : (
                  "Generate Summary"
                )}
              </button>
            </div>
          </div>
        )}

        {step === "generating" && (
          <div className="card center">
            <div className="loader"></div>
            <h2>Generating Your File Summaries...</h2>
            <p>Please wait while we analyze your code.</p>
          </div>
        )}

        {step === "complete" && summaryContent && (
          <div className="card">
            <h2>Summary Generated Successfully!</h2>
            <div className="actions">
              <button
                type="button"
                onClick={copyToClipboard}
                disabled={loading}
              >
                Copy
              </button>
              <button
                type="button"
                onClick={downloadPDFSummary}
                disabled={loading}
              >
                {loading ? "Downloading..." : "Download PDF"}
              </button>
              <button
                type="button"
                onClick={reset}
                disabled={loading}
              >
                Reset
              </button>
            </div>
            <div className="preview-container preview">
              <ReactMarkdown>{summaryContent}</ReactMarkdown>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default FileToFileSummarizer;
