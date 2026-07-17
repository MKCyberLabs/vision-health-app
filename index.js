const express = require('express');
const multer = require('multer');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const app = express();
const port = process.env.PORT || 3000;

app.set('trust proxy', 1);
app.disable('x-powered-by');
app.use((req, res, next) => {
    res.setHeader('X-Content-Type-Options', 'nosniff');
    res.setHeader('X-Frame-Options', 'DENY');
    res.setHeader('X-XSS-Protection', '1; mode=block');
    res.setHeader('Content-Security-Policy', "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com; style-src 'self' 'unsafe-inline'; img-src 'self' blob: data:; connect-src 'self'");
    res.setHeader('Strict-Transport-Security', 'max-age=31536000; includeSubDomains');
    next();
});

app.use(express.json());
app.use(express.static('public'));

const rateLimitMap = new Map();
const RATE_LIMIT_WINDOW = 15 * 60 * 1000; // 15 minutes
const MAX_REQUESTS = 100;

// Prevent memory leaks by periodically cleaning up expired IPs
setInterval(() => {
    const now = Date.now();
    for (const [ip, limitData] of rateLimitMap.entries()) {
        if (now > limitData.resetTime) {
            rateLimitMap.delete(ip);
        }
    }
}, RATE_LIMIT_WINDOW);

app.use((req, res, next) => {
    if (req.path === '/analyze' || req.path === '/reply') {
        const ip = req.ip;
        const now = Date.now();
        const limitData = rateLimitMap.get(ip) || { count: 0, resetTime: now + RATE_LIMIT_WINDOW };

        if (now > limitData.resetTime) {
            limitData.count = 1;
            limitData.resetTime = now + RATE_LIMIT_WINDOW;
        } else {
            limitData.count++;
        }

        rateLimitMap.set(ip, limitData);

        if (limitData.count > MAX_REQUESTS) {
            return res.status(429).json({ error: "Too many requests, please try again later." });
        }
    }
    next();
});

const upload = multer({
    dest: 'temp/',
    limits: { fileSize: 5 * 1024 * 1024 }, // 5MB limit
    fileFilter: (req, file, cb) => {
        if (!file.mimetype.startsWith('image/')) {
            return cb(new Error('INVALID_FILE_TYPE'), false);
        }
        cb(null, true);
    }
});
const GEMINI_API_URL = process.env.GEMINI_API_URL || 'http://172.17.0.1:5000';

// Asynchronous file cleanup to avoid blocking the event loop
const cleanupFileAsync = (filePath) => {
    fs.unlink(filePath, (unlinkErr) => {
        if (unlinkErr && unlinkErr.code !== 'ENOENT') {
            console.error(`Failed to cleanup file ${filePath}:`, unlinkErr);
        }
    });
};

app.post('/analyze', upload.single('image'), async (req, res) => {
    if (!req.file) return res.status(400).json({ error: "No image file provided." });

    const imagePath = req.file.path;
    const weight = req.body.weight || "";

    if (typeof weight !== 'string' || weight.length > 50) {
        if (imagePath) cleanupFileAsync(imagePath);
        return res.status(400).json({ error: "Invalid weight format or length." });
    }

    let prompt = "Analyze this food image and provide a health matrix: calories, protein, fiber, fats, and a description.";
    if (weight) prompt += ` The portion size/weight is: ${weight}.`;
    prompt += ` Image reference path: ${path.resolve(imagePath)}`;

    console.log(`Sending ask request to Flask API at ${GEMINI_API_URL}/ask for image: ${imagePath}`);

    try {
        if (process.env.USE_MOCK_API === 'true') {
            console.log(`[MOCK] Returning mock response for /analyze`);
            const mockData = require('./mocks/askResponse.json');
            // Clean up the image since we didn't send it to backend
            fs.unlink(imagePath, (err) => {
                if (err && err.code !== 'ENOENT') console.error(`Failed to delete ${imagePath}:`, err);
            });
            return res.json({
                status: mockData.status,
                result: mockData.result
            });
        }

        const response = await fetch(`${GEMINI_API_URL}/ask`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: prompt,
                image_path: imagePath
            })
        });

        if (!response.ok) {
            const errorText = await response.text();
            if (imagePath) cleanupFileAsync(imagePath); // ⚡ Bolt Optimization: Non-blocking async file cleanup
            return res.status(response.status).json({
                status: "error",
                message: errorText || `Flask API returned status ${response.status}`
            });
        }

        const data = await response.json();
        if (data.status === "needs_approval") {
            return res.json({
                status: "needs_approval",
                sessionId: data.session_id,
                message: data.message
            });
        } else if (data.status === "success") {
            return res.json({
                status: "success",
                result: data.response
            });
        } else {
            if (imagePath) cleanupFileAsync(imagePath); // ⚡ Bolt Optimization: Non-blocking async file cleanup
            return res.status(500).json({
                status: "error",
                message: data.message || "Unknown response format from Flask API"
            });
        }
    } catch (err) {
        if (imagePath) cleanupFileAsync(imagePath); // ⚡ Bolt Optimization: Non-blocking async file cleanup
        console.error("Error communicating with Flask API:", err);
        return res.status(500).json({
            status: "error",
            message: `Failed to connect to Flask API: ${err.message}`
        });
    }
});

app.post('/reply', async (req, res) => {
    const { sessionId, answer } = req.body;
    if (!sessionId) return res.status(400).json({ error: "Session ID is required." });
    if (typeof answer !== 'string' || !['y', 'n'].includes(answer.toLowerCase())) {
        return res.status(400).json({ error: "Invalid answer. Must be 'y' or 'n'." });
    }

    console.log(`Sending reply to Flask API at ${GEMINI_API_URL}/reply for session: ${sessionId}`);

    try {
        if (process.env.USE_MOCK_API === 'true') {
            console.log(`[MOCK] Returning mock response for /reply`);
            const mockData = require('./mocks/replyResponse.json');
            return res.json({
                status: mockData.status,
                result: mockData.result
            });
        }

        const response = await fetch(`${GEMINI_API_URL}/reply`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: sessionId,
                answer: answer
            })
        });

        if (!response.ok) {
            const errorText = await response.text();
            return res.status(response.status).json({
                status: "error",
                message: errorText || `Flask API returned status ${response.status}`
            });
        }

        const data = await response.json();
        if (data.status === "needs_approval") {
            return res.json({
                status: "needs_approval",
                sessionId: data.session_id,
                message: data.message
            });
        } else if (data.status === "success") {
            return res.json({
                status: "success",
                result: data.response
            });
        } else {
            return res.status(500).json({
                status: "error",
                message: data.message || "Unknown response format from Flask API"
            });
        }
    } catch (err) {
        console.error("Error communicating with Flask API during reply:", err);
        return res.status(500).json({
            status: "error",
            message: `Failed to connect to Flask API: ${err.message}`
        });
    }
});

app.use((err, req, res, next) => {
    console.error('Unhandled error:', err.message);
    if (err instanceof multer.MulterError && err.code === 'LIMIT_FILE_SIZE') {
        return res.status(413).json({ error: "File too large. Maximum size is 5MB." });
    }
    if (err.message === 'INVALID_FILE_TYPE') {
        return res.status(400).json({ error: "Invalid file type. Only images are allowed." });
    }
    res.status(500).json({ error: "An internal server error occurred." });
});

app.listen(port, '0.0.0.0', () => {
    console.log(`Vision Health App running on port ${port}`);
});
