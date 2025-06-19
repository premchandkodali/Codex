const router = require("express").Router();
const User = require("../models/User");
const bcrypt = require("bcrypt");
const jwt = require("jsonwebtoken");

// Signup
router.post("/signup", async (req, res) => {
  try {
    if (!req.body.username || !req.body.password || !req.body.email) {
      return res.status(400).json({ error: "Missing required fields" });
    }
    
    // Check if user already exists
    const existingUser = await User.findOne({ username: req.body.username });
    if (existingUser) {
      return res.status(400).json({ error: "Username already exists" });
    }

    const hashed = await bcrypt.hash(req.body.password, 10);
    const user = new User({ 
      username: req.body.username,
      email: req.body.email,
      password: hashed 
    });
    
    await user.save();
    res.status(201).json({ message: "User created successfully" });
  } catch (error) {
    console.error("Signup error:", error);
    res.status(500).json({ error: "Error creating user" });
  }
});

// Login
router.post("/login", async (req, res) => {
  try {
    if (!req.body.username || !req.body.password) {
      return res.status(400).json({ error: "Username and password are required" });
    }

    const user = await User.findOne({ username: req.body.username });
    
    if (!user) {
      return res.status(401).json({ error: "Invalid username or password" });
    }

    const isMatch = await bcrypt.compare(req.body.password, user.password);
    if (!isMatch) {
      return res.status(401).json({ error: "Invalid username or password" });
    }

    if (!process.env.JWT_SECRET) {
      console.error("JWT_SECRET is not set");
      return res.status(500).json({ error: "Server configuration error" });
    }

    const token = jwt.sign({ id: user._id }, process.env.JWT_SECRET, { expiresIn: '1h' });
    res.json({ 
      token,
      user: {
        id: user._id,
        username: user.username,
        email: user.email
      }
    });
  } catch (error) {
    console.error("Login error:", error);
    res.status(500).json({ error: "Error during login" });
  }
});

// JWT verification middleware
function verifyToken(req, res, next) {
  const authHeader = req.headers.authorization;
  if (!authHeader || !authHeader.startsWith('Bearer ')) return res.status(401).json({ msg: "No token" });
  const token = authHeader.split(' ')[1];
  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    req.user = decoded;
    next();
  } catch (err) {
    res.status(401).json({ msg: "Token invalid" });
  }
}

// Get current user info (/me)
router.get('/me', verifyToken, async (req, res) => {
  try {
    const user = await User.findById(req.user.id).select('username email');
    if (!user) return res.status(404).json({ msg: "User not found" });
    res.json({ username: user.username, email: user.email });
  } catch (err) {
    res.status(500).json({ msg: "Server error" });
  }
});

module.exports = router;