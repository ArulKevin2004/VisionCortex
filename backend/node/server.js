const express = require('express');
const { spawn } = require('child_process');
const cors = require('cors');
const path = require('path');
const fs = require('fs');

const app = express();
app.use(cors());
app.use(express.json());

// Define the backend directory
const backendPath = path.resolve('/Users/arulkevin/Desktop/Github/VisionCortex/backend/register.py', '..');
console.log('Backend path:', backendPath);

// Verify Python executable exists
const pythonPath = '/Users/arulkevin/Desktop/Github/VisionCortex/backend/.venv/bin/python3';
if (!fs.existsSync(pythonPath)) {
    console.error('Python executable not found at:', pythonPath);
} else {
    console.log('Python executable found at:', pythonPath);
}

// Common environment for all Python processes to suppress Continuity Camera warning
const pythonEnv = {
    ...process.env,
    NSCameraUseContinuityCameraDeviceType: 'NO'  // Suppress Continuity Camera warning
};

// API to trigger face registration
app.post('/api/register', (req, res) => {
    const { name } = req.body;
    if (!name) {
        return res.status(400).json({ error: 'Name is required' });
    }
    console.log('Calling register.py with name:', name);

    const scriptPath = path.resolve(backendPath, 'register.py');
    
    const child = spawn(pythonPath, [scriptPath, name], { cwd: backendPath, env: pythonEnv });

    let output = '';
    let errorOutput = '';

    child.stdout.on('data', (data) => {
        output += data.toString();
        console.log('Python output:', data.toString());
    });

    child.stderr.on('data', (data) => {
        errorOutput += data.toString();
        console.error('Python stderr:', data.toString());
    });

    child.on('error', (err) => {
        console.error('Spawn error:', err);
        return res.status(500).json({ error: 'Registration failed: ' + err.message });
    });

    child.on('close', (code) => {
        if (res.headersSent) return; // Prevent sending multiple responses
        if (code === 0) {
            res.json({ message: `Face registered for ${name}`, output });
        } else {
            res.status(500).json({ error: `Registration failed with code ${code}: ${errorOutput}` });
        }
    });
});

// API to trigger face recognition
app.get('/api/recognize', (req, res) => {
    console.log('Calling recognize.py');

    const scriptPath = path.resolve(backendPath, 'recognize.py');
    const child = spawn(pythonPath, [scriptPath], { cwd: backendPath, env: pythonEnv });

    let output = '';
    let errorOutput = '';

    child.stdout.on('data', (data) => {
        output += data.toString();
        console.log('Python output:', data.toString());
    });

    child.stderr.on('data', (data) => {
        errorOutput += data.toString();
        console.error('Python stderr:', data.toString());
    });

    child.on('error', (err) => {
        console.error('Spawn error:', err);
        return res.status(500).json({ error: 'Recognition failed: ' + err.message });
    });

    child.on('close', (code) => {
        if (res.headersSent) return; // Prevent sending multiple responses
        if (code === 0) {
            res.json({ message: 'Recognition started', output });
        } else {
            res.status(500).json({ error: `Recognition failed with code ${code}: ${errorOutput}` });
        }
    });
});

// API to handle chat queries
app.post('/api/chat', (req, res) => {
    const { message } = req.body;
    if (!message) {
        return res.status(400).json({ error: 'Message is required' });
    }
    console.log('Calling rag_engine.py with message:', message);

    const scriptPath = path.resolve(backendPath, 'rag_engine.py');
    const child = spawn(pythonPath, [scriptPath, message], { cwd: backendPath, env: pythonEnv });

    let output = '';
    let errorOutput = '';

    child.stdout.on('data', (data) => {
        output += data.toString();
        console.log('Python output:', data.toString());
    });

    child.stderr.on('data', (data) => {
        errorOutput += data.toString();
        console.error('Python stderr:', data.toString());
    });

    child.on('error', (err) => {
        console.error('Spawn error:', err);
        return res.status(500).json({ error: 'Chat query failed: ' + err.message });
    });

    child.on('close', (code) => {
        if (res.headersSent) return; // Prevent sending multiple responses
        if (code === 0) {
            res.json({ message: output.trim() });
        } else {
            res.status(500).json({ error: `Chat query failed with code ${code}: ${errorOutput}` });
        }
    });
});

app.listen(5001, () => console.log('Server running on http://localhost:5001'));