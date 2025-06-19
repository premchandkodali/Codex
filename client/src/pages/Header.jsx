import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, LogOut } from 'lucide-react';
import './Header.css';

const Header = ({ showBack = true, showLogout = true }) => {
  const navigate = useNavigate();

  const handleBack = () => {
    navigate('/mainpage');
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/');
  };

  return (
    <nav className="header-bar">
      {showBack && (
        <button className="header-back-btn" onClick={handleBack}>
          <ArrowLeft size={18} />
          Back
        </button>
      )}
      {showLogout && (
        <button className="header-logout-btn" onClick={handleLogout}>
          <LogOut size={16} />
          Logout
        </button>
      )}
    </nav>
  );
};

export default Header;