import { useState } from 'react'
import axios from 'axios'
import { useNavigate } from 'react-router-dom'
import { Eye, EyeOff } from 'lucide-react'
import './Login.css' 

function Login() {
  const [username, setUserName] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const navigate = useNavigate()

  const handleLogin = async () => {
    try {
      const res = await axios.post('http://localhost:5000/api/auth/login', { username, password })
      localStorage.setItem('token', res.data.token)
      navigate('/mainpage')
    } catch (err) {
      alert('Login failed')
    }
  }

  return (
    <div className="login-container">
      <div className="login-form">
        <h2>Login</h2>
        <div className="input-group">
          <input 
            placeholder="Username" 
            value={username} 
            onChange={(e) => setUserName(e.target.value)} 
          />
        </div>
        <div className="input-group password-group">
          <input 
            type={showPassword ? "text" : "password"} 
            placeholder="Password" 
            value={password} 
            onChange={(e) => setPassword(e.target.value)} 
          />
          <button 
            type="button" 
            className="password-toggle"
            onClick={() => setShowPassword(!showPassword)}
          >
            {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
          </button>
        </div>
        <button className="login-btn" onClick={handleLogin}>Login</button>
        <p>Don't have an account? <a href="/signup">Sign up</a></p>
      </div>
    </div>
  )
}

export default Login