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

// Timeout for CLI responses (3 minutes)
const CLI_TIMEOUT_MS = 180000;

function handleCliInteraction(child, sessionId, imagePath, res) {
    let outputBuffer = '';
    let responded = false;

    // Set a timeout so requests don't hang forever
    const timeout = setTimeout(() => {
        if (!responded) {
            responded = true;
            child.kill();
            if (fs.existsSync(imagePath)) fs.unlinkSync(imagePath);
            delete activeSessions[sessionId];
            res.status(504).json({
                status: "error",
                message: "CLI timed out after 3 minutes. The AI may be overloaded."
            });
        }
    }, CLI_TIMEOUT_MS);

    // Capture BOTH stdout and stderr — agy writes output to stderr
    child.stdout.on('data', (data) => {
        outputBuffer += data.toString();
    });

    child.stderr.on('data', (data) => {
        outputBuffer += data.toString();

        // Check if the CLI is asking for permission/approval
        if (/proceed\? \[y\/n\]/i.test(outputBuffer) || /yes\/no/i.test(outputBuffer)) {
            if (!responded) {
                responded = true;
                clearTimeout(timeout);
                activeSessions[sessionId] = { child, imagePath };
                return res.json({
                    status: "needs_approval",
                    sessionId: sessionId,
                    message: outputBuffer.trim()
                });
            }
        }
    });

    child.on('close', (code) => {
        clearTimeout(timeout);
        if (responded) return; // Already sent a response (approval prompt or timeout)
        responded = true;

        if (fs.existsSync(imagePath)) fs.unlinkSync(imagePath);
        delete activeSessions[sessionId];

        if (code === 0) {
            res.json({ status: "success", result: outputBuffer.trim() });
        } else {
            res.status(500).json({
                status: "error",
                message: outputBuffer.trim() || `CLI exited with code ${code}`
            });
        }
    });

    child.on('error', (err) => {
        clearTimeout(timeout);
        if (responded) return;
        responded = true;

        if (fs.existsSync(imagePath)) fs.unlinkSync(imagePath);
        delete activeSessions[sessionId];
        res.status(500).json({ status: "error", message: err.message });
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

    console.log(`[${sessionId}] Spawning agy CLI for image: ${imagePath}`);

    const child = spawn('/root/.local/bin/agy', ['-p', prompt, '--dangerously-skip-permissions'], {
        env: { ...process.env, HOME: '/root' }
    });

    handleCliInteraction(child, sessionId, imagePath, res);
});

app.post('/reply', (req, res) => {
    const { sessionId, answer } = req.body;
    if (!sessionId || !activeSessions[sessionId]) return res.status(404).json({ error: "Session expired or invalid." });

    const { child, imagePath } = activeSessions[sessionId];
    child.stdin.write(`${answer}\n`);

    // Re-attach handlers for the continued interaction
    let outputBuffer = '';
    let responded = false;

    const timeout = setTimeout(() => {
        if (!responded) {
            responded = true;
            child.kill();
            if (fs.existsSync(imagePath)) fs.unlinkSync(imagePath);
            delete activeSessions[sessionId];
            res.status(504).json({ status: "error", message: "CLI timed out." });
        }
    }, CLI_TIMEOUT_MS);

    child.stdout.on('data', (data) => {
        outputBuffer += data.toString();
    });

    child.stderr.on('data', (data) => {
        outputBuffer += data.toString();
    });

    child.on('close', (code) => {
        clearTimeout(timeout);
        if (responded) return;
        responded = true;

        if (fs.existsSync(imagePath)) fs.unlinkSync(imagePath);
        delete activeSessions[sessionId];

        if (code === 0) {
            res.json({ status: "success", result: outputBuffer.trim() });
        } else {
            res.status(500).json({
                status: "error",
                message: outputBuffer.trim() || `CLI exited with code ${code}`
            });
        }
    });

    child.on('error', (err) => {
        clearTimeout(timeout);
        if (responded) return;
        responded = true;

        if (fs.existsSync(imagePath)) fs.unlinkSync(imagePath);
        delete activeSessions[sessionId];
        res.status(500).json({ status: "error", message: err.message });
    });
});

app.listen(port, '0.0.0.0', () => {
    console.log(`Vision Health App running on port ${port}`);
});
