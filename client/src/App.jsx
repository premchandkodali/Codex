import { Routes, Route } from 'react-router-dom'
import Login from './pages/Login'
import Signup from './pages/Signup'
import Dashboard from './pages/Dashboard'
import PrivateRoute from './components/PrivateRoute'
import ReadmeGenerator from './pages/ReadmeGenerator'
import MainPage from './pages/MainPage'
import FileToFileSummarizer from './pages/FileToFileSummarizer';

import './App.css';

function App() {
  return (
    <Routes>
      <Route path="/" element={<Login />} />
      <Route path="/signup" element={<Signup />} />
      <Route path="/dashboard" element={
        <PrivateRoute>
          <Dashboard />
        </PrivateRoute>
      } />
       <Route path="/readme-gen" element={
        <PrivateRoute>
          <ReadmeGenerator />
        </PrivateRoute>
      } />
        <Route path="/mainpage" element={
        <PrivateRoute>
          <MainPage />
        </PrivateRoute>
      } />
        <Route path="/file-to-file" element={
        <PrivateRoute>
          <FileToFileSummarizer />
        </PrivateRoute>
      } />

      
    </Routes>
  )
}

export default App
