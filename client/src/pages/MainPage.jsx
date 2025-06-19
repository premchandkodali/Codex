import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FileText, Code, Settings, LogOut } from 'lucide-react';
import axios from 'axios';
import './MainPage.css';

const MainPage = () => {
  const navigate = useNavigate();
  const [username, setUsername] = useState('');

  useEffect(() => {
    const fetchUser = async () => {
      try {
        const token = localStorage.getItem('token');
        if (!token) {
          navigate('/');
          return;
        }
        const res = await axios.get('http://localhost:5000/api/auth/me', {
          headers: { Authorization: `Bearer ${token}` },
        });
        setUsername(res.data.username);
      } catch (err) {
        setUsername('');
        navigate('/');
      }
    };
    fetchUser();
  }, [navigate]);

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/');
  };

  const handleReadmeGenerator = () => {
    navigate('/readme-gen');
  };

  const handleCodeBase = () => {
    navigate('/dashboard');
  };

  const handleFiletoFile = () => {
    navigate('/file-to-file');
  };

  return (
    <div className="mainpage-container">
      <nav className="mainpage-header-bar">
        <div className="mainpage-welcome">
          {username && (
            <span>
              Welcome <b>{username.toUpperCase()}</b> !!
            </span>
          )}
        </div>
        <button className="mainpage-logout-btn" onClick={handleLogout}>
          <LogOut size={16} />
          Logout
        </button>
      </nav>

      <div className="mainpage-content-outer">
        <div className="mainpage-header">
          <h1>Welcome to Codex - Your Repomate</h1>
          <p>Choose your development tool to get started</p>
        </div>

        <div className="mainpage-content">
          <div className="circle-buttons-container">
            <div className="circle-button" onClick={handleReadmeGenerator}>
              <div className="circle-icon">
                <FileText size={40} />
              </div>
              <h3>README Generator</h3>
              <p>Create professional README files for your GitHub repositories</p>
            </div>
            <div className="circle-button" onClick={handleCodeBase}>
              <div className="circle-icon">
                <Code size={40} />
              </div>
              <h3>Codebase Q & A</h3>
              <p>Ask any question about your repo and get instant explanations</p>
            </div>
            <div className="circle-button" onClick={handleFiletoFile}>
              <div className="circle-icon">
                <Settings size={40} />
              </div>
              <h3>File to File Summary</h3>
              <p>Get key file summaries from your repo with a download option</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MainPage;