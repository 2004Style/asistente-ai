// Connect to the assistant WebSocket server
const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
const wsUrl = `${wsProtocol}//${window.location.host}/ws`;

let socket;
const reconnectInterval = 3000;
let currentConfirmId = null;

// UI State Mapping
const STATE = {
  current: "waiting",
  config: {
    waiting: {
      color: "#4a5568",
      name: "ESPERA",
      ringSpeed: 4,
      pulseSpeed: 3,
    },
    speaking: {
      color: "#00ff88",
      name: "HABLANDO",
      ringSpeed: 2,
      pulseSpeed: 0.6,
    },
    listening: {
      color: "#ffaa00",
      name: "ESCUCHANDO",
      ringSpeed: 1.5,
      pulseSpeed: 0.3,
    },
    processing: {
      color: "#aa66ff",
      name: "PROCESANDO",
      ringSpeed: 0.8,
      pulseSpeed: 0.2,
    },
    error: {
      color: "#ff3355",
      name: "ERROR",
      ringSpeed: 0.3,
      pulseSpeed: 0.1,
    },
  },
};

// DOM Elements
const coreContainer = document.getElementById("coreContainer");
const userPanel = document.getElementById("userPanel");
const jarvisPanel = document.getElementById("jarvisPanel");
const chatInput = document.getElementById("chatInput");
const btnSend = document.getElementById("btnSend");

// Modal Elements
const confirmModal = document.getElementById("confirmModal");
const modalText = document.getElementById("modalText");
const btnConfirm = document.getElementById("btnConfirm");
const btnDeny = document.getElementById("btnDeny");

// Config Overlay Elements
const configPanel = document.getElementById("configPanel");
const configBtn = document.getElementById("configBtn");
const configClose = document.getElementById("configClose");
const configForm = document.getElementById("configForm");
const statusMsg = document.getElementById("statusMsg");

// Mode buttons
const coreModeBtn = document.getElementById("coreModeBtn");
const cameraModeBtn = document.getElementById("cameraModeBtn");

// Window Buttons
const minimizeBtn = document.getElementById("minimizeBtn");
const closeBtn = document.getElementById("closeBtn");

function connect() {
    socket = new WebSocket(wsUrl);

    socket.onopen = () => {
        logConsole("Conectado al servidor de rbot.", "success");
        setUiState("waiting");
    };

    socket.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            handleServerMessage(data);
        } catch (err) {
            console.error("Error parsing message:", err);
        }
    };

    socket.onclose = () => {
        setUiState("error");
        logConsole("Conexión perdida. Reconectando en 3s...", "error");
        setTimeout(connect, reconnectInterval);
    };

    socket.onerror = (error) => {
        console.error("WebSocket error:", error);
    };
}

function handleServerMessage(data) {
    // 1. Handle Assistant State
    if (data.type === "state") {
        mapAndSetState(data.state);
    }

    // 2. Handle Final Chat Response
    else if (data.type === "response") {
        appendMessage("assistant", data.content);
    }

    // 3. Handle System Events (Tool executions / approvals)
    else if (data.type === "event") {
        const eventType = data.event;
        const eventData = data.data;

        if (eventType === "state_changed") {
            mapAndSetState(eventData.new_state);
        }
        else if (eventType === "voice_listening_success") {
            appendMessage("user", eventData.text);
        }
        else if (eventType === "voice_speaking_start") {
            appendMessage("assistant", eventData.text);
        }
        else if (eventType === "tool_start") {
            const toolName = eventData.tool || "tool";
            logConsole(`Ejecutando: '${toolName}'`, "action");
            spawnProcess(toolName);
        }
        else if (eventType === "tool_success") {
            logConsole(`Herramienta '${eventData.tool}' finalizada.`, "success");
            
            // Return back to main core mode so user can see the projected results card in full size
            if (["inspect_camera", "inspect_screen"].includes(eventData.tool)) {
                setActiveMode("core");
            }
            
            const result = eventData.result;
            if (result && typeof result === "object") {
                const imagePath = result.path || result.image_path || result.image?.path || result.preview_path || result.capture?.path;
                const url = result.url || result.link || result.source_url || result.web_url || result.product_url || result.search_url;
                
                const isVisualTool = ["inspect_screen", "inspect_camera", "web_search"].includes(eventData.tool) ||
                                     ["research", "product", "shopping", "search"].includes(String(result.visual_intent || "").toLowerCase());
                                     
                let isImageShown = false;
                if (imagePath && (result.display_image === true || isVisualTool || url)) {
                    let previewUrl = imagePath;
                    if (!/^https?:\/\//i.test(imagePath)) {
                        previewUrl = `/api/preview?path=${encodeURIComponent(imagePath)}&t=${Date.now()}`;
                    }
                    window.showImage(previewUrl, url);
                    isImageShown = true;
                }
                
                // Check if file was created or downloaded
                const filePath = result.file_path || result.output_path || result.project_path || result.dest_path || result.project_dir;
                if (filePath && !isImageShown) {
                    showFileCard(filePath, result.filename);
                }
            }
        }
        else if (eventType === "tool_error") {
            logConsole(`Error en '${eventData.tool}': ${eventData.error}`, "error");
        }
        else if (eventType === "tool_denied") {
            logConsole(`Ejecución denegada para '${eventData.tool}'.`, "error");
        }
        else if (eventType === "tool_pending_confirmation") {
            logConsole(`Confirmación requerida para '${eventData.tool}'`, "action");
            showConfirmationModal(eventData);
        }
        else if (eventType === "tool_confirmation_resolved") {
            logConsole(`Confirmación resuelta: ${eventData.approved ? 'APROBADA' : 'RECHAZADA'}`, eventData.approved ? "success" : "error");
            if (currentConfirmId === eventData.confirm_id) {
                currentConfirmId = null;
                confirmModal.style.display = "none";
            }
        }
        else if (eventType === "reminder_triggered") {
            logConsole(`RECORDATORIO: ${eventData.message}`, "action");
        }
        // Handle UI Commands broadcasted from Python
        else if (eventType === "ui_command") {
            handleVoiceUiCommand(eventData.action);
        }
    }
}

// Map Python daemon states to frontend core states
function mapAndSetState(daemonState) {
    let mapped = "waiting";
    switch(daemonState) {
        case "idle":
            mapped = "waiting";
            break;
        case "listening":
            mapped = "listening";
            break;
        case "speaking":
            mapped = "speaking";
            break;
        case "thinking":
        case "planning":
        case "executing":
            mapped = "processing";
            break;
        case "error":
            mapped = "error";
            break;
        default:
            mapped = "waiting";
    }
    setUiState(mapped);
}

function setUiState(state) {
    STATE.current = state;
    const cfg = STATE.config[state];
    const root = document.documentElement;
    root.style.setProperty("--state-color", cfg.color);
    root.style.setProperty("--state-glow", cfg.color + "88");
    root.style.setProperty("--ring-speed", cfg.ringSpeed + "s");
    root.style.setProperty("--pulse-speed", cfg.pulseSpeed + "s");

    if (coreContainer) {
        coreContainer.className = "core-container " + state;
    }
}

// Log line into Assistant Panel Console style
function logConsole(message, type = "info") {
    const icon = type === "success" ? "✔" : type === "error" ? "✘" : type === "action" ? "⚡" : "ℹ";
    appendMessage("assistant", `[${icon}] ${message}`);
}

// Append Chat bubble to respective side panels
function appendMessage(sender, text) {
    const bubble = document.createElement("div");
    bubble.className = `msg ${sender === 'assistant' ? 'jarvis' : ''}`;
    bubble.textContent = (sender === 'user' ? '▸ ' : '◆ ') + text;
    
    if (sender === 'user') {
        if (userPanel) {
            userPanel.appendChild(bubble);
            userPanel.scrollTop = userPanel.scrollHeight;
        }
    } else {
        if (jarvisPanel) {
            jarvisPanel.appendChild(bubble);
            jarvisPanel.scrollTop = jarvisPanel.scrollHeight;
        }
    }
}

// Send Message handler
function sendMessage() {
    const text = chatInput.value.trim();
    if (!text) return;

    appendMessage("user", text);
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({
            message: text,
            session_id: "default"
        }));
        chatInput.value = "";
    } else {
        logConsole("No se pudo enviar el mensaje: Conexión cerrada.", "error");
    }
}

// Confirmation Modal operations
function showConfirmationModal(data) {
    currentConfirmId = data.confirm_id;
    modalText.innerHTML = `
        El asistente solicita autorización para ejecutar la herramienta: <br>
        <strong>${data.tool}</strong> <br><br>
        Parámetros: <br>
        <code>${JSON.stringify(data.arguments)}</code> <br><br>
        Nivel de seguridad: <strong style="color: var(--amber)">${data.level}</strong>
    `;
    confirmModal.style.display = "flex";
}

function closeConfirmationModal(approved) {
    if (!currentConfirmId) return;

    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({
            type: "confirmation_response",
            confirm_id: currentConfirmId,
            approved: approved
        }));
        logConsole(`Confirmación enviada: ${approved ? 'APROBADA' : 'RECHAZADA'}`, approved ? "success" : "error");
    }
    
    currentConfirmId = null;
    confirmModal.style.display = "none";
}

// Voice Command Handler
function handleVoiceUiCommand(action) {
    logConsole(`Comando de UI recibido: ${action}`, "success");
    switch(action) {
        case "open_config":
            window.location.href = "/config_page";
            break;
        case "close_config":
            window.location.href = "/hud";
            break;
        case "open_hud":
            // Focus window or bring it up if possible
            break;
        case "close_hud":
            window.close();
            break;
        case "show_camera":
            setActiveMode("camera");
            break;
        case "hide_camera":
            setActiveMode("core");
            break;
        case "show_screen":
            setActiveMode("screen");
            break;
        case "hide_screen":
            setActiveMode("core");
            break;
        case "start_demo":
            startStateDemo();
            break;
        case "stop_demo":
            stopStateDemo();
            break;
    }
}

// ========== PARTICLES SYSTEM ==========
const canvas = document.getElementById("coreCanvas");
const ctx = canvas.getContext("2d");
let particles = [];
let animFrame;

function resizeCanvas() {
    if (canvas) {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    }
}
resizeCanvas();
window.addEventListener("resize", () => {
    resizeCanvas();
    if (imageDisplay.classList.contains("active")) positionImageCard();
    const fileDisplay = document.getElementById("fileDisplay");
    if (fileDisplay && fileDisplay.classList.contains("active")) positionFileCard();
});

class Particle {
    constructor() {
        this.reset();
    }
    reset() {
        const section = document.getElementById("coreSection");
        const rect = section.getBoundingClientRect();
        this.x = rect.left + rect.width / 2 + (Math.random() - 0.5) * 200;
        this.y = rect.top + rect.height / 2 + (Math.random() - 0.5) * 200;
        this.size = Math.random() * 2 + 1;
        this.speedX = (Math.random() - 0.5) * 2;
        this.speedY = (Math.random() - 0.5) * 2;
        this.life = 1;
        this.decay = 0.002 + Math.random() * 0.005;
    }
    update() {
        this.x += this.speedX;
        this.y += this.speedY;
        this.life -= this.decay;
        if (this.life <= 0) this.reset();
    }
    draw() {
        const cfg = STATE.config[STATE.current];
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
        ctx.fillStyle =
            cfg.color +
            Math.floor(this.life * 80)
                .toString(16)
                .padStart(2, "0");
        ctx.fill();
        ctx.shadowBlur = 10;
        ctx.shadowColor = cfg.color;
    }
}

for (let i = 0; i < 50; i++) particles.push(new Particle());

function animateParticles() {
    if (!ctx) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    const isProcessing = STATE.current === "processing";
    const isError = STATE.current === "error";
    const particleCount = isProcessing ? 150 : isError ? 100 : 50;

    while (particles.length < particleCount) particles.push(new Particle());
    while (particles.length > particleCount) particles.pop();

    particles.forEach((p) => {
        p.update();
        p.draw();
    });
    animFrame = requestAnimationFrame(animateParticles);
}
animateParticles();

// ========== PROCESS NODES ==========
const processOrbit = document.getElementById("processOrbit");
let processNodes = [];
let processAnimFrame;

function spawnProcess(toolName) {
    if (!processOrbit) return;
    const angle = Math.random() * Math.PI * 2;
    const radius = 100 + Math.random() * 60;
    const cleanedName = toolName.substring(0, 15).toUpperCase();

    const node = document.createElement("div");
    node.className = "process-node active";

    const core = document.createElement("div");
    core.className = "node-core";
    node.appendChild(core);

    const ring = document.createElement("div");
    ring.className = "node-ring";
    node.appendChild(ring);

    const label = document.createElement("div");
    label.className = "node-label";
    label.textContent = cleanedName;
    node.appendChild(label);

    processOrbit.appendChild(node);

    const trail = document.createElement("div");
    trail.className = "process-node trail";
    processOrbit.appendChild(trail);

    processNodes.push({
        el: node,
        trail,
        angle,
        radius,
        speed: 0.008 + Math.random() * 0.012,
        life: 250 + Math.random() * 150,
        maxLife: 400,
    });
}

function animateProcesses() {
    processNodes.forEach((n, i) => {
        n.angle += n.speed;
        n.life--;
        const progress = n.life / n.maxLife;
        const r = n.radius * (0.6 + progress * 0.4);
        const x = Math.cos(n.angle) * r;
        const y = Math.sin(n.angle) * r;
        n.el.style.transform = `translate(${160 + x}px, ${160 + y}px)`;

        const opacity = Math.min(1, progress * 3) * 0.85;
        n.el.style.opacity = opacity;
        n.el.style.zIndex = progress > 0.5 ? 5 : 3;

        const tx = Math.cos(n.angle - n.speed * 5) * r;
        const ty = Math.sin(n.angle - n.speed * 5) * r;
        n.trail.style.transform = `translate(${160 + tx}px, ${160 + ty}px)`;
        n.trail.style.opacity = opacity * 0.3;

        if (n.life <= 0) {
            n.el.remove();
            n.trail.remove();
            processNodes.splice(i, 1);
        }
    });

    processAnimFrame = requestAnimationFrame(animateProcesses);
}
animateProcesses();

// ========== CAMERA/SCREEN MODE AND WEBCAM ==========
let cameraStream = null;
let isCameraMode = false;
let isScreenMode = false;
let cameraTransitioning = false;
let cameraUploadInterval = null;

function startCameraUpload() {
    if (cameraUploadInterval) return;
    
    const captureCanvas = document.createElement("canvas");
    const captureCtx = captureCanvas.getContext("2d");
    
    cameraUploadInterval = setInterval(async () => {
        const video = document.getElementById("cameraFeed");
        if (!isCameraMode || !cameraStream || !video || video.paused || video.ended) {
            stopCameraUpload();
            return;
        }
        
        try {
            // Downscale for network efficiency
            captureCanvas.width = 640;
            captureCanvas.height = 480;
            captureCtx.drawImage(video, 0, 0, 640, 480);
            
            // Compress as JPEG to minimize payload size
            const dataUrl = captureCanvas.toDataURL("image/jpeg", 0.7);
            
            await fetch("/api/camera_frame", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ image: dataUrl })
            });
        } catch (e) {
            console.warn("Error uploading camera frame to daemon:", e);
        }
    }, 1000); // 1 FPS upload rate is optimal
}

function stopCameraUpload() {
    if (cameraUploadInterval) {
        clearInterval(cameraUploadInterval);
        cameraUploadInterval = null;
    }
}

function cleanCameraStream() {
    stopCameraUpload();
    if (cameraStream) {
        try {
            cameraStream.getTracks().forEach((t) => t.stop());
        } catch (e) {
            console.warn("Error stopping camera tracks:", e);
        }
        cameraStream = null;
    }
    const video = document.getElementById("cameraFeed");
    if (video) {
        video.srcObject = null;
    }
}

async function toggleVisionMode(mode) {
    // Clear any active transitions to prevent UI locks on rapid changes
    if (window.cameraViewTimeout) clearTimeout(window.cameraViewTimeout);
    if (window.feedTimeout) clearTimeout(window.feedTimeout);
    if (window.lockTimeout) clearTimeout(window.lockTimeout);
    cameraTransitioning = true;

    const core = document.getElementById("coreContainer");
    const sideLeft = document.getElementById("sidebarLeft");
    const sideRight = document.getElementById("sidebarRight");
    const cameraView = document.getElementById("cameraView");
    const video = document.getElementById("cameraFeed");
    const screenFeed = document.getElementById("screenFeed");

    // Release camera immediately on transition to prevent locks
    cleanCameraStream();

    if (mode === "camera" || mode === "screen") {
        // Position core in bottom-right corner
        const rect = core.getBoundingClientRect();
        const cx = rect.left + rect.width / 2;
        const cy = rect.top + rect.height / 2;

        const margin = 40;
        const scale = 0.35;
        const sw = rect.width * scale;
        const sh = rect.height * scale;
        const tx = window.innerWidth - margin - sw / 2;
        const ty = window.innerHeight - margin - sh / 2;
        const dx = tx - cx;
        const dy = ty - cy;

        // Animate sidebars
        if (sideLeft) {
            sideLeft.style.opacity = "0";
            sideLeft.style.pointerEvents = "none";
        }
        if (sideRight) {
            sideRight.style.opacity = "0";
            sideRight.style.pointerEvents = "none";
        }

        core.style.transform = `translate(${dx}px, ${dy}px) scale(${scale})`;
        window.cameraViewTimeout = setTimeout(() => cameraView.classList.add("active"), 100);

        if (mode === "camera") {
            if (screenFeed) screenFeed.style.display = "none";
            if (video) video.style.display = "block";

            // Turn on camera feed
            window.feedTimeout = setTimeout(async () => {
                try {
                    cameraStream = await navigator.mediaDevices.getUserMedia({
                        video: {
                            facingMode: "user",
                            width: { ideal: 1280 },
                            height: { ideal: 720 },
                        },
                    });
                    video.srcObject = cameraStream;
                    startCameraUpload();
                } catch (e) {
                    console.warn("Camera not available:", e);
                    logConsole("No se pudo iniciar el stream de la cámara.", "error");
                }
            }, 300);
        } else {
            // Screen Mode
            if (video) {
                video.style.display = "none";
                video.srcObject = null;
            }
            if (screenFeed) {
                screenFeed.style.display = "block";
                screenFeed.src = "";
            }

            // Trigger screen capture on the backend and render it
            window.feedTimeout = setTimeout(async () => {
                logConsole("Capturando pantalla...", "action");
                try {
                    const res = await fetch("/api/screenshot", { method: "POST" });
                    if (!res.ok) throw new Error("Failed to capture screen");
                    const result = await res.json();
                    if (result.path && screenFeed) {
                        screenFeed.src = `/api/preview?path=${encodeURIComponent(result.path)}&t=${Date.now()}`;
                        logConsole("Captura de pantalla lista.", "success");
                    } else {
                        logConsole("No se pudo obtener la captura de pantalla.", "error");
                    }
                } catch (e) {
                    console.error("Screenshot error:", e);
                    logConsole("Error al capturar pantalla.", "error");
                }
            }, 300);
        }

        window.lockTimeout = setTimeout(() => { cameraTransitioning = false; }, 900);
    } else {
        cameraView.classList.remove("active");

        window.feedTimeout = setTimeout(() => {
            if (video) video.srcObject = null;
            if (screenFeed) screenFeed.style.display = "none";
        }, 400);

        core.style.transform = "";

        window.cameraViewTimeout = setTimeout(() => {
            if (sideLeft) {
                sideLeft.style.opacity = "1";
                sideLeft.style.pointerEvents = "auto";
            }
            if (sideRight) {
                sideRight.style.opacity = "1";
                sideRight.style.pointerEvents = "auto";
            }
        }, 400); // 400ms aligns with core transform transition back

        window.lockTimeout = setTimeout(() => { cameraTransitioning = false; }, 900);
    }
}

function setActiveMode(mode) {
    document.querySelectorAll(".mockup-mode-btn").forEach((b) => {
        b.classList.toggle("active", b.dataset.mode === mode);
    });
    isCameraMode = mode === "camera";
    isScreenMode = mode === "screen";
    
    if (!isCameraMode) {
        stopCameraUpload();
    }
    
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({
            type: "ui_action",
            action: "set_active_mode",
            mode: mode
        }));
    }
    
    toggleVisionMode(mode);
}

// ========== IMAGE PROJECTOR ==========
const imageDisplay = document.getElementById("imageDisplay");
const imageCard = document.getElementById("imageCard");
const imgPlaceholder = document.getElementById("imgPlaceholder");
const imgClose = document.getElementById("imgClose");
const imgWebBtn = document.getElementById("imgWebBtn");
const connectorBeam = document.getElementById("connectorBeam");
const beamCanvas = document.getElementById("beamCanvas");
const beamCtx = beamCanvas.getContext("2d");
let currentImageUrl = "";
let beamAnim = null;

function positionImageCard() {
    const core = document.getElementById("coreContainer");
    const cr = core.getBoundingClientRect();
    const gap = 14;
    const cardW = Math.min(270, window.innerWidth * 0.8);

    imageCard.style.width = cardW + "px";
    imageCard.style.maxWidth = "";

    let left = cr.left - cardW - gap;
    let top = cr.top - cardW * 0.5 - gap;

    left = Math.max(10, Math.min(left, window.innerWidth - cardW - 10));
    top = Math.max(56, Math.min(top, window.innerHeight - cardW * 0.6));

    imageCard.style.left = left + "px";
    imageCard.style.top = top + "px";
}

function drawBeam() {
    const core = document.getElementById("coreContainer");
    const cr = core.getBoundingClientRect();
    const cx = cr.left + cr.width / 2;
    const cy = cr.top + cr.height / 2;

    const cardR = imageCard.getBoundingClientRect();
    const fromX = cardR.right;
    const fromY = cardR.bottom;

    const dx = cx - fromX;
    const dy = cy - fromY;
    const len = Math.sqrt(dx * dx + dy * dy);
    const angle = Math.atan2(dy, dx);

    const pad = 40;
    connectorBeam.style.left = fromX - pad + "px";
    connectorBeam.style.top = fromY - pad + "px";
    connectorBeam.style.width = len + pad * 2 + "px";
    connectorBeam.style.height = pad * 2 + "px";

    beamCanvas.width = len + pad * 2;
    beamCanvas.height = pad * 2;

    const bCtx = beamCtx;
    bCtx.clearRect(0, 0, beamCanvas.width, beamCanvas.height);
    bCtx.save();
    bCtx.translate(pad, pad);
    bCtx.rotate(angle);

    // Main line
    bCtx.beginPath();
    bCtx.moveTo(0, 0);
    bCtx.lineTo(len, 0);
    bCtx.strokeStyle = `rgba(0, 212, 255, 0.15)`;
    bCtx.lineWidth = 1;
    bCtx.setLineDash([4, 6]);
    bCtx.stroke();

    // Glow
    bCtx.beginPath();
    bCtx.moveTo(0, 0);
    bCtx.lineTo(len, 0);
    bCtx.strokeStyle = `rgba(0, 212, 255, ${0.04 + Math.sin(Date.now() / 500) * 0.02})`;
    bCtx.lineWidth = 3;
    bCtx.setLineDash([]);
    bCtx.shadowBlur = 10;
    bCtx.shadowColor = "rgba(0,212,255,0.2)";
    bCtx.stroke();

    // Data pulses
    const pulsePos = (Date.now() % 1500) / 1500;
    bCtx.beginPath();
    bCtx.arc(len * pulsePos, 0, 2, 0, Math.PI * 2);
    bCtx.fillStyle = `rgba(0, 212, 255, ${0.6 + Math.sin(pulsePos * Math.PI) * 0.3})`;
    bCtx.shadowBlur = 15;
    bCtx.shadowColor = "rgba(0,212,255,0.6)";
    bCtx.fill();

    bCtx.restore();
}

function startBeamAnimation() {
    connectorBeam.classList.add("active");
    function frame() {
        drawBeam();
        beamAnim = requestAnimationFrame(frame);
    }
    beamAnim = requestAnimationFrame(frame);
}

function stopBeamAnimation() {
    if (beamAnim) {
        cancelAnimationFrame(beamAnim);
        beamAnim = null;
    }
    connectorBeam.classList.remove("active");
}

window.showImage = function (url, webUrl) {
    currentImageUrl = webUrl || url;
    imgPlaceholder.innerHTML = `<img src="${url}" alt="Visualización">`;
    positionImageCard();
    
    // Trigger animations reset
    imageCard.style.animation = "none";
    imgPlaceholder.style.animation = "none";
    imageCard.offsetHeight; // Reflow
    imageCard.style.animation = "";
    imgPlaceholder.style.animation = "";
    
    imageDisplay.classList.add("active");
    setTimeout(positionImageCard, 50);
    startBeamAnimation();
};

function closeImageDisplay() {
    imageDisplay.classList.remove("active");
    stopBeamAnimation();
}

// ========== CONFIGURATION PANEL OVERLAY LOGIC ==========
async function loadConfig() {
    try {
        const res = await fetch("/config");
        if (!res.ok) throw new Error("Failed to load config");
        const data = await res.json();
        
        // Populate inputs
        document.getElementById("llmProvider").value = data.llm.provider;
        document.getElementById("llmModel").value = data.llm.model;
        document.getElementById("llmTemp").value = data.llm.temperature;
        document.getElementById("llmApiKey").value = data.llm.api_key || "";
        
        document.getElementById("minPermission").value = data.security.min_permission_level;
        document.getElementById("requireConfirm").checked = data.security.require_confirmation;
        
        document.getElementById("appName").value = data.app.name;
        document.getElementById("shortTermLimit").value = data.memory.short_term_limit;
    } catch (err) {
        showConfigStatus("Error loading config: " + err.message, "error");
    }
}

async function saveConfig(event) {
    event.preventDefault();
    
    const payload = {
        llm: {
            provider: document.getElementById("llmProvider").value,
            model: document.getElementById("llmModel").value,
            temperature: parseFloat(document.getElementById("llmTemp").value),
            api_key: document.getElementById("llmApiKey").value
        },
        security: {
            min_permission_level: document.getElementById("minPermission").value,
            require_confirmation: document.getElementById("requireConfirm").checked
        },
        app: {
            name: document.getElementById("appName").value
        },
        memory: {
            short_term_limit: parseInt(document.getElementById("shortTermLimit").value)
        }
    };
    
    try {
        const res = await fetch("/config", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        });
        
        if (!res.ok) throw new Error("Failed to save configuration");
        showConfigStatus("Configuración guardada correctamente.", "success");
    } catch (err) {
        showConfigStatus("Error al guardar la configuración: " + err.message, "error");
    }
}

function showConfigStatus(text, type) {
    statusMsg.textContent = text;
    statusMsg.style.display = "block";
    if (type === "success") {
        statusMsg.style.background = "rgba(0, 255, 136, 0.15)";
        statusMsg.style.border = "1px solid var(--green)";
        statusMsg.style.color = "var(--green)";
    } else {
        statusMsg.style.background = "rgba(255, 51, 85, 0.15)";
        statusMsg.style.border = "1px solid var(--red)";
        statusMsg.style.color = "var(--red)";
    }
    
    setTimeout(() => {
        statusMsg.style.display = "none";
    }, 4000);
}

function showConfigPanel() {
    loadConfig();
    configPanel.style.display = "flex";
    setTimeout(() => {
        configPanel.classList.add("active");
    }, 10);
}

function hideConfigPanel() {
    configPanel.classList.remove("active");
    setTimeout(() => {
        configPanel.style.display = "none";
    }, 300);
}

// ========== SYSTEM MONITOR METRICS POLLING ==========
const cpuValue = document.getElementById("cpuValue");
const gpuValue = document.getElementById("gpuValue");
const ramValue = document.getElementById("ramValue");
const netValue = document.getElementById("netValue");

// Natural variations helper
function getSysNoise(val, min, max, delta) {
    let nv = val + (Math.random() - 0.5) * delta * 2;
    return Math.max(min, Math.min(max, nv));
}

let mockCpu = 15;
let mockGpu = 8;
let mockRam = 4.2;
let mockNet = 25;

async function pollSystemStats() {
    try {
        const res = await fetch("/stats");
        if (res.ok) {
            const data = await res.json();
            cpuValue.textContent = Math.round(data.cpu) + "%";
            ramValue.textContent = data.ram.toFixed(1) + " GB";
            
            if (data.gpu) {
                gpuValue.textContent = Math.round(data.gpu.util) + "%";
            } else {
                mockGpu = getSysNoise(mockGpu, 2, 25, 2);
                gpuValue.textContent = Math.round(mockGpu) + "%";
            }
            
            mockNet = getSysNoise(mockNet, 5, 80, 5);
            netValue.textContent = mockNet.toFixed(0) + " Mbps";
            return;
        }
    } catch (e) {
        // Fallback silently to mock loop below
    }

    // Mock stats fallback if server stat endpoint is degraded
    mockCpu = getSysNoise(mockCpu, 8, 70, 8);
    mockGpu = getSysNoise(mockGpu, 2, 25, 2);
    mockRam = getSysNoise(mockRam, 3.8, 6.2, 0.1);
    mockNet = getSysNoise(mockNet, 5, 80, 5);

    cpuValue.textContent = Math.round(mockCpu) + "%";
    gpuValue.textContent = Math.round(mockGpu) + "%";
    ramValue.textContent = mockRam.toFixed(1) + " GB";
    netValue.textContent = mockNet.toFixed(0) + " Mbps";
}
setInterval(pollSystemStats, 2000);
pollSystemStats();

// ========== STATE DEMO FUNCTIONALITY ==========
let demoInterval = null;
function startStateDemo() {
    if (demoInterval) return;
    const states = ["waiting", "speaking", "listening", "processing", "error"];
    let i = 0;
    demoInterval = setInterval(() => {
        setUiState(states[i]);
        i = (i + 1) % states.length;
    }, 2500);
    logConsole("Modo de demostración de estados activado.", "success");
}

function stopStateDemo() {
    if (demoInterval) {
        clearInterval(demoInterval);
        demoInterval = null;
        setUiState("waiting");
        logConsole("Modo de demostración de estados detenido.", "success");
    }
}

// ========== EVENT LISTENERS ==========
btnSend.addEventListener("click", sendMessage);
chatInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") sendMessage();
});

btnConfirm.addEventListener("click", () => closeConfirmationModal(true));
btnDeny.addEventListener("click", () => closeConfirmationModal(false));

configBtn.addEventListener("click", () => {
    window.location.href = "/config_page";
});

coreModeBtn.addEventListener("click", () => setActiveMode("core"));
cameraModeBtn.addEventListener("click", () => setActiveMode("camera"));
const screenModeBtn = document.getElementById("screenModeBtn");
if (screenModeBtn) {
    screenModeBtn.addEventListener("click", () => setActiveMode("screen"));
}

imgClose.addEventListener("click", closeImageDisplay);
imageDisplay.addEventListener("click", (e) => {
    if (e.target === imageDisplay) closeImageDisplay();
});
imgWebBtn.addEventListener("click", () => {
    if (currentImageUrl) window.open(currentImageUrl, "_blank");
});

// Demo buttons in mockup bar
document.getElementById("imgDemoBtn").addEventListener("click", () => {
    window.showImage(
        "https://picsum.photos/seed/rbot-proj/800/450",
        "https://picsum.photos/seed/rbot-proj/800/450"
    );
});
document.getElementById("procDemoBtn").addEventListener("click", () => {
    spawnProcess("PROC-DEMO");
});

// Window Control actions
minimizeBtn.addEventListener("click", () => {
    logConsole("HUD minimizado.", "info");
    // Send to background
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({ type: "ui_action", action: "minimize" }));
    }
});
closeBtn.addEventListener("click", () => {
    window.close();
});

// 3D Tilt Hover effect on Core Section
const coreSection = document.getElementById("coreSection");
coreSection.addEventListener("mousemove", (e) => {
    if (isCameraMode || cameraTransitioning) return;
    const rect = coreContainer.getBoundingClientRect();
    const cx = rect.left + rect.width / 2;
    const cy = rect.top + rect.height / 2;
    const dx = (e.clientX - cx) / rect.width;
    const dy = (e.clientY - cy) / rect.height;
    coreContainer.style.transform = `perspective(800px) rotateY(${dx * 12}deg) rotateX(${-dy * 12}deg)`;
});

coreSection.addEventListener("mouseleave", () => {
    if (isCameraMode || cameraTransitioning) return;
    coreContainer.style.transform = "perspective(800px) rotateY(0deg) rotateX(0deg)";
});

// ========== FILE CARD FLOATING OPERATIONS ==========
let currentFilePath = null;
const fileDisplay = document.getElementById("fileDisplay");
const fileCard = document.getElementById("fileCard");
const fileConnectorBeam = document.getElementById("fileConnectorBeam");
const fileBeamCanvas = document.getElementById("fileBeamCanvas");
const fileBeamCtx = fileBeamCanvas.getContext("2d");
let fileBeamAnim = null;

function positionFileCard() {
    const core = document.getElementById("coreContainer");
    const cr = core.getBoundingClientRect();
    const gap = 14;
    const cardW = Math.min(270, window.innerWidth * 0.8);

    fileCard.style.width = cardW + "px";
    fileCard.style.maxWidth = "";

    // Position on the right side of the core
    let left = cr.right + gap;
    let top = cr.top - cardW * 0.5 - gap;

    left = Math.max(10, Math.min(left, window.innerWidth - cardW - 10));
    top = Math.max(56, Math.min(top, window.innerHeight - cardW * 0.6));

    fileCard.style.left = left + "px";
    fileCard.style.top = top + "px";
}

function drawFileBeam() {
    const core = document.getElementById("coreContainer");
    const cr = core.getBoundingClientRect();
    const cx = cr.left + cr.width / 2;
    const cy = cr.top + cr.height / 2;

    const cardR = fileCard.getBoundingClientRect();
    const fromX = cardR.left;
    const fromY = cardR.bottom;

    const dx = cx - fromX;
    const dy = cy - fromY;
    const len = Math.sqrt(dx * dx + dy * dy);
    const angle = Math.atan2(dy, dx);

    const pad = 40;
    fileConnectorBeam.style.left = fromX - pad + "px";
    fileConnectorBeam.style.top = fromY - pad + "px";
    fileConnectorBeam.style.width = len + pad * 2 + "px";
    fileConnectorBeam.style.height = pad * 2 + "px";

    fileBeamCanvas.width = len + pad * 2;
    fileBeamCanvas.height = pad * 2;

    const bCtx = fileBeamCtx;
    bCtx.clearRect(0, 0, fileBeamCanvas.width, fileBeamCanvas.height);
    bCtx.save();
    bCtx.translate(pad, pad);
    bCtx.rotate(angle);

    // Main line (green theme)
    bCtx.beginPath();
    bCtx.moveTo(0, 0);
    bCtx.lineTo(len, 0);
    bCtx.strokeStyle = `rgba(0, 255, 136, 0.15)`;
    bCtx.lineWidth = 1;
    bCtx.setLineDash([4, 6]);
    bCtx.stroke();

    // Glow
    bCtx.beginPath();
    bCtx.moveTo(0, 0);
    bCtx.lineTo(len, 0);
    bCtx.strokeStyle = `rgba(0, 255, 136, ${0.04 + Math.sin(Date.now() / 500) * 0.02})`;
    bCtx.lineWidth = 3;
    bCtx.setLineDash([]);
    bCtx.shadowBlur = 10;
    bCtx.shadowColor = "rgba(0,255,136,0.2)";
    bCtx.stroke();

    // Data pulses
    const pulsePos = (Date.now() % 1500) / 1500;
    bCtx.beginPath();
    bCtx.arc(len * pulsePos, 0, 2, 0, Math.PI * 2);
    bCtx.fillStyle = `rgba(0, 255, 136, ${0.6 + Math.sin(pulsePos * Math.PI) * 0.3})`;
    bCtx.shadowBlur = 15;
    bCtx.shadowColor = "rgba(0,255,136,0.6)";
    bCtx.fill();

    bCtx.restore();
}

function startFileBeamAnimation() {
    fileConnectorBeam.classList.add("active");
    function frame() {
        drawFileBeam();
        fileBeamAnim = requestAnimationFrame(frame);
    }
    fileBeamAnim = requestAnimationFrame(frame);
}

function stopFileBeamAnimation() {
    if (fileBeamAnim) {
        cancelAnimationFrame(fileBeamAnim);
        fileBeamAnim = null;
    }
    fileConnectorBeam.classList.remove("active");
}

function showFileCard(filePath, filename) {
    if (!filePath) return;
    
    currentFilePath = filePath;
    
    if (!filename) {
        filename = filePath.split(/[/\\]/).pop();
    }
    
    document.getElementById("fileModalName").textContent = filename;
    document.getElementById("fileModalPath").textContent = filePath;
    
    const ext = filename.split('.').pop().toLowerCase();
    const iconEl = document.getElementById("fileModalIcon");
    
    iconEl.className = "fas ";
    let color = "#00ff88"; // green default
    
    if (ext === "pdf") {
        iconEl.classList.add("fa-file-pdf");
        color = "#ff5c5c";
    } else if (["docx", "doc", "odt"].includes(ext)) {
        iconEl.classList.add("fa-file-word");
        color = "#3b82f6";
    } else if (["xlsx", "xls", "ods", "csv"].includes(ext)) {
        iconEl.classList.add("fa-file-excel");
        color = "#10b981";
    } else if (["zip", "tar", "gz", "rar", "7z"].includes(ext)) {
        iconEl.classList.add("fa-file-archive");
        color = "#f59e0b";
    } else if (["py", "sh", "js", "go", "rs", "json", "yml", "yaml", "html", "css", "c", "h"].includes(ext)) {
        iconEl.classList.add("fa-file-code");
        color = "#00d4ff";
    } else if (["png", "jpg", "jpeg", "webp", "gif", "bmp"].includes(ext)) {
        iconEl.classList.add("fa-file-image");
        color = "#a855f7";
    } else if (!ext || ext === filename.toLowerCase()) {
        iconEl.classList.add("fa-folder-open");
        color = "#eab308";
    } else {
        iconEl.classList.add("fa-file-alt");
        color = "#ffffff";
    }
    
    iconEl.style.color = color;
    iconEl.style.filter = `drop-shadow(0 0 10px ${color}80)`;
    
    positionFileCard();

    fileCard.style.animation = "none";
    fileCard.offsetHeight; // Reflow
    fileCard.style.animation = "";

    fileDisplay.classList.add("active");
    setTimeout(positionFileCard, 50);
    startFileBeamAnimation();
}

function closeFileCard() {
    currentFilePath = null;
    fileDisplay.classList.remove("active");
    stopFileBeamAnimation();
}

function handleFileView() {
    if (!currentFilePath) return;
    
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({
            type: "ui_action",
            action: "open_file",
            path: currentFilePath
        }));
    }
    
    closeFileCard();
}

document.getElementById("btnFileView").addEventListener("click", handleFileView);
document.getElementById("btnFileClose").addEventListener("click", closeFileCard);

// Initialize WebSocket connection
connect();
