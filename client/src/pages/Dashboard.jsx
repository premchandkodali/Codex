import { useState, useEffect } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import Header from './Header';
import './Dashboard.css';

function Dashboard() {
  const [repoUrl, setRepoUrl] = useState('');
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [branches, setBranches] = useState([]);
  const [selectedBranch, setSelectedBranch] = useState('');
  const [isLoadingBranches, setIsLoadingBranches] = useState(false);
  const [isAsking, setIsAsking] = useState(false);
  const [error, setError] = useState('');

  const token = localStorage.getItem('token');

  useEffect(() => {
    setBranches([]);
    setSelectedBranch('');
    setAnswer('');
    setError('');

    const delayDebounce = setTimeout(() => {
      if (repoUrl.startsWith('https://github.com/')) {
        fetchBranches();
      }
    }, 600);

    return () => clearTimeout(delayDebounce);
    // eslint-disable-next-line
  }, [repoUrl]);

  const fetchBranches = async () => {
    if (!repoUrl) {
      setError('Please enter a repository URL first');
      return;
    }

    setIsLoadingBranches(true);
    setError('');
    try {
      const response = await axios.post('http://localhost:5001/api/branches', {
        repoUrl
      }, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });

      if (response.data.branches && response.data.branches.length > 0) {
        setBranches(response.data.branches);
        const defaultBranch = response.data.branches.find(b => b.name === 'main') ||
                              response.data.branches.find(b => b.name === 'master') ||
                              response.data.branches[0];
        setSelectedBranch(defaultBranch.name);
      } else {
        setError('No branches found for this repository');
      }
    } catch (error) {
      setError(error.response?.data?.error || 'Failed to fetch branches. Please check the repository URL and try again.');
    } finally {
      setIsLoadingBranches(false);
    }
  };

  const askQuestion = async () => {
    if (!repoUrl || !question || !selectedBranch) {
      setError('Please enter a repository URL, select a branch, and enter your question.');
      return;
    }

    setIsAsking(true);
    setError('');
    try {
      const response = await axios.post('http://localhost:5001/ask', {
        repoUrl,
        branch: selectedBranch,
        question
      }, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });

      setAnswer(response.data.answer);
    } catch (error) {
      setError(error.response?.data?.error || 'Something went wrong. Please try again later.');
    } finally {
      setIsAsking(false);
    }
  };

  return (
    <div className="dashboard-bg">
      <Header />
      <div className="dashboard-container">
        <div className="dashboard-title">
          <h1>🔍 GitHub Repo Q&A Dashboard</h1>
          <p>Ask AI-powered questions about any public GitHub repository</p>
        </div>

        <div className="dashboard-card">
          <label htmlFor="repo-url">GitHub Repository URL</label>
          <input
            id="repo-url"
            type="text"
            className="dashboard-input"
            placeholder="https://github.com/username/repository"
            value={repoUrl}
            onChange={(e) => setRepoUrl(e.target.value)}
            disabled={isLoadingBranches || isAsking}
            autoComplete="off"
          />

          {isLoadingBranches && (
            <div className="dashboard-loading-branches">
              Loading branches...
            </div>
          )}

          {branches.length > 0 && (
            <>
              <label htmlFor="branch-select">Select Branch</label>
              <select
                id="branch-select"
                className="dashboard-select"
                value={selectedBranch}
                onChange={(e) => setSelectedBranch(e.target.value)}
                disabled={isAsking}
              >
                {branches.map((branch) => (
                  <option key={branch.name} value={branch.name}>
                    {branch.name} {branch.protected ? '🔒' : ''} ({branch.commit_sha})
                  </option>
                ))}
              </select>
            </>
          )}

          <label htmlFor="repo-question">Your Question</label>
          <textarea
            id="repo-question"
            className="dashboard-textarea"
            placeholder="Ask a question about this repository..."
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            disabled={!selectedBranch || isAsking}
            minLength={3}
            autoComplete="off"
          />

          <button
            className="dashboard-ask-btn"
            onClick={askQuestion}
            disabled={!selectedBranch || !question.trim() || isAsking}
          >
            {isAsking ? 'Processing...' : 'Ask Question'}
            {isAsking && <span className="spinner"></span>}
          </button>

          {error && (
            <div className="dashboard-error">
              {error}
            </div>
          )}
        </div>

        {answer && (
          <div className="dashboard-answer">
            <h3>Answer:</h3>
            <div className="markdown">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{answer}</ReactMarkdown>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default Dashboard;