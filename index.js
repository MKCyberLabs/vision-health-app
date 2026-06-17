const express = require('express');
const multer = require('multer');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
const { v4: uuidv4 } = require('uuid');

const app = express();
const port = process.env.PORT || 3000;

app.use(express.json());
app.use(express.static('public'));

const upload = multer({ dest: 'temp/' });
const GEMINI_API_URL = process.env.GEMINI_API_URL || 'http://172.17.0.1:5000';

app.post('/analyze', upload.single('image'), async (req, res) => {
    if (!req.file) return res.status(400).json({ error: "No image file provided." });

    const imagePath = req.file.path;
    const weight = req.body.weight || "";

    let prompt = "Analyze this food image and provide a health matrix: calories, protein, fiber, fats, and a description.";
    if (weight) prompt += ` The portion size/weight is: ${weight}.`;
    prompt += ` Image reference path: ${path.resolve(imagePath)}`;

    console.log(`Sending ask request to Flask API at ${GEMINI_API_URL}/ask for image: ${imagePath}`);

    try {
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
            if (fs.existsSync(imagePath)) fs.unlinkSync(imagePath);
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
            if (fs.existsSync(imagePath)) fs.unlinkSync(imagePath);
            return res.status(500).json({
                status: "error",
                message: data.message || "Unknown response format from Flask API"
            });
        }
    } catch (err) {
        if (fs.existsSync(imagePath)) fs.unlinkSync(imagePath);
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

    console.log(`Sending reply to Flask API at ${GEMINI_API_URL}/reply for session: ${sessionId}`);

    try {
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

app.listen(port, '0.0.0.0', () => {
    console.log(`Vision Health App running on port ${port}`);
});
