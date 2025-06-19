import { useState } from 'react'
import axios from 'axios'
import { useNavigate, Link } from 'react-router-dom'
import { Eye, EyeOff, User, Mail } from 'lucide-react'
import './Signup.css' 

function Signup() {
  const [email, setEmail] = useState('')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const navigate = useNavigate()

  const handleSignup = async () => {
    try {
      await axios.post('http://localhost:5000/api/auth/signup', { username, email, password })
      navigate('/')
    } catch (err) {
      alert('Signup failed')
    }
  }

  return (
    <div className="signup-container">
      <div className="signup-form">
        <h2>Sign Up</h2>
        <div className="input-group">
          <div className="input-icon">
            <User size={20} />
          </div>
          <input 
            placeholder="Username" 
            value={username} 
            onChange={(e) => setUsername(e.target.value)} 
          />
        </div>
        <div className="input-group">
          <div className="input-icon">
            <Mail size={20} />
          </div>
          <input 
            type="email"
            placeholder="Email" 
            value={email} 
            onChange={(e) => setEmail(e.target.value)} 
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
        <button className="signup-btn" onClick={handleSignup}>Sign Up</button>
        <p>Already have an account? <Link to="/">Login</Link></p>
      </div>
    </div>
  )
}

export default Signup