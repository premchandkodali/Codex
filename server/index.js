const express = require("express");
const cors = require("cors");
const mongoose = require("mongoose");
const path = require('path');

// Load environment variables from .env in the current directory
require('dotenv').config({ path: path.join(__dirname, '.env') });

// Log environment variables (for debugging, remove in production)
console.log('Environment variables loaded:');
console.log('- MONGO_URI:', process.env.MONGO_URI ? 'Set' : 'Not set');
console.log('- JWT_SECRET:', process.env.JWT_SECRET ? 'Set' : 'Not set');

// Check required environment variables
if (!process.env.JWT_SECRET) {
  console.error('FATAL ERROR: JWT_SECRET is not defined.');
  process.exit(1);
}

// Import routes
const authRoutes = require("./routes/auth");

// Initialize express app
const app = express();

// Middleware
app.use(cors());
app.use(express.json());

// Request logging middleware
app.use((req, res, next) => {
  console.log(`${new Date().toISOString()} - ${req.method} ${req.url}`);
  next();
});

// Database connection
const MONGODB_URI = process.env.MONGO_URI || 'mongodb://localhost:27017/Codex';

console.log('Connecting to MongoDB...');

mongoose.connect(MONGODB_URI)
  .then(() => console.log('✅ Connected to MongoDB'))
  .catch(err => {
    console.error('❌ MongoDB connection error:', err.message);
    process.exit(1);
  });

// Event listeners for MongoDB connection
mongoose.connection.on('error', err => {
  console.error('❌ MongoDB connection error:', err.message);
});

mongoose.connection.on('disconnected', () => {
  console.log('ℹ️  MongoDB disconnected');
});

// Routes
app.use("/api/auth", authRoutes);

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'ok', mongo: mongoose.connection.readyState === 1 });
});

// Error handling middleware
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({ error: 'Something went wrong!' });
});

// Start server
const PORT = process.env.PORT || 5000;
const server = app.listen(PORT, () => {
  console.log(`🚀 Server running on port ${PORT}`);
  console.log(`🔗 MongoDB URI: ${MONGODB_URI}`);
});

// Handle unhandled promise rejections
process.on('unhandledRejection', (err) => {
  console.error('Unhandled Rejection:', err);
  server.close(() => process.exit(1));
});
