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
const activeSessions = {};

function handleCliInteraction(child, sessionId, imagePath, res) {
    let outputBuffer = '';

    child.stdout.on('data', (data) => {
        const text = data.toString();
        outputBuffer += text;

        if (/proceed\? \[y\/n\]/i.test(text) || /yes\/no/i.test(text)) {
            activeSessions[sessionId] = { child, imagePath };
            return res.json({
                status: "needs_approval",
                sessionId: sessionId,
                message: outputBuffer.trim()
            });
        }
    });

    child.on('close', (code) => {
        if (activeSessions[sessionId] && !res.writableEnded) return;
        if (fs.existsSync(imagePath)) fs.unlinkSync(imagePath);
        delete activeSessions[sessionId];

        if (code === 0) {
            res.json({ status: "success", result: outputBuffer.trim() });
        } else {
            res.status(500).json({ status: "error", message: `CLI exited with code ${code}` });
        }
    });

    child.on('error', (err) => {
        if (fs.existsSync(imagePath)) fs.unlinkSync(imagePath);
        delete activeSessions[sessionId];
        if (!res.writableEnded) res.status(500).json({ status: "error", message: err.message });
    });
}

app.post('/analyze', upload.single('image'), (req, res) => {
    if (!req.file) return res.status(400).json({ error: "No image file provided." });

    const imagePath = req.file.path;
    const weight = req.body.weight || "";
    const sessionId = uuidv4();

    let prompt = "Analyze this food image and provide a health matrix: calories, protein, fiber, fats, and a description.";
    if (weight) prompt += ` The portion size/weight is: ${weight}.`;
    prompt += ` Image reference path: ${path.resolve(imagePath)}`;

    const child = spawn('/root/.local/bin/agy', ['-p', prompt, '--dangerously-skip-permissions']);
    handleCliInteraction(child, sessionId, imagePath, res);
});

app.post('/reply', (req, res) => {
    const { sessionId, answer } = req.body;
    if (!sessionId || !activeSessions[sessionId]) return res.status(404).json({ error: "Session expired or invalid." });

    const { child, imagePath } = activeSessions[sessionId];
    child.stdin.write(`${answer}\n`);
    handleCliInteraction(child, sessionId, imagePath, res);
});

app.listen(port, '0.0.0.0', () => {
    console.log(`Vision Health App running on port ${port}`);
});
