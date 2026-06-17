// Connect to the assistant WebSocket server
const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
const wsUrl = `${wsProtocol}//${window.location.host}/ws`;

let socket;
const reconnectInterval = 3000;

const statusDot = document.getElementById("statusDot");
const statusText = document.getElementById("statusText");
const configForm = document.getElementById("configForm");
const statusMsg = document.getElementById("statusMsg");

// Predefined models per LLM provider
const PROVIDER_MODELS = {
    openai: [
        { value: "gpt-4o-mini", label: "GPT-4o Mini (Recomendado / Rápido)" },
        { value: "gpt-4o", label: "GPT-4o (Alta Capacidad)" },
        { value: "gpt-4-turbo", label: "GPT-4 Turbo" },
        { value: "gpt-3.5-turbo", label: "GPT-3.5 Turbo" },
        { value: "o1-mini", label: "o1 Mini (Razonamiento)" },
        { value: "o1-preview", label: "o1 Preview" }
    ],
    gemini: [
        { value: "gemini-2.5-flash", label: "Gemini 2.5 Flash (Recomendado / Rápido)" },
        { value: "gemini-2.5-pro", label: "Gemini 2.5 Pro (Razonamiento Avanzado)" },
        { value: "gemini-1.5-flash", label: "Gemini 1.5 Flash" },
        { value: "gemini-1.5-pro", label: "Gemini 1.5 Pro" }
    ],
    anthropic: [
        { value: "claude-3-5-sonnet-latest", label: "Claude 3.5 Sonnet (Recomendado)" },
        { value: "claude-3-5-haiku-latest", label: "Claude 3.5 Haiku" },
        { value: "claude-3-opus-latest", label: "Claude 3 Opus" }
    ],
    openrouter: [
        { value: "openrouter/free", label: "Auto Free Router (openrouter/free) [Recomendado Gratis]" },
        { value: "openrouter/auto", label: "Auto Paid Router (openrouter/auto)" },
        { value: "google/gemini-2.5-flash", label: "Gemini 2.5 Flash (Pago)" },
        { value: "google/gemini-2.5-pro", label: "Gemini 2.5 Pro (Pago)" },
        { value: "meta-llama/llama-3.3-70b-instruct:free", label: "Llama 3.3 70B Instruct (Gratis)" },
        { value: "deepseek/deepseek-chat:free", label: "DeepSeek V3 / Chat (Gratis)" },
        { value: "qwen/qwen-2.5-7b-instruct:free", label: "Qwen 2.5 7B Instruct (Gratis)" },
        { value: "qwen/qwen-2.5-coder-32b-instruct:free", label: "Qwen 2.5 Coder 32B (Gratis)" },
        { value: "microsoft/phi-3-medium-128k-instruct:free", label: "Phi 3 Medium 128k (Gratis)" },
        { value: "meta-llama/llama-3-8b-instruct:free", label: "Llama 3 8B Instruct (Gratis)" },
        { value: "gryphe/mythomax-l2-13b:free", label: "MythoMax L2 13B (Gratis)" },
        { value: "meta-llama/llama-3.1-405b-instruct", label: "Llama 3.1 405B" },
        { value: "anthropic/claude-3.5-sonnet", label: "Claude 3.5 Sonnet" },
        { value: "openai/gpt-4o", label: "GPT-4o" },
        { value: "openai/gpt-4o-mini", label: "GPT-4o Mini" }
    ],
    ollama: [
        { value: "llama3", label: "Llama 3" },
        { value: "llama3.1", label: "Llama 3.1" },
        { value: "gemma2", label: "Gemma 2" },
        { value: "mistral", label: "Mistral" },
        { value: "phi3", label: "Phi 3" },
        { value: "qwen2.5", label: "Qwen 2.5" },
        { value: "deepseek-coder", label: "DeepSeek Coder" }
    ],
    local: [
        { value: "local-model", label: "Modelo Local (Por Defecto)" }
    ]
};

// Predefined voices for Microsoft Edge TTS
const EDGE_VOICES = [
    { value: "es-ES-AlvaroNeural", label: "España - Álvaro (Masculino)" },
    { value: "es-ES-ElviraNeural", label: "España - Elvira (Femenino)" },
    { value: "es-MX-JorgeNeural", label: "México - Jorge (Masculino)" },
    { value: "es-MX-DaliaNeural", label: "México - Dalia (Femenino)" },
    { value: "es-US-AlonsoNeural", label: "EEUU - Alonso (Masculino)" },
    { value: "es-US-PalomaNeural", label: "EEUU - Paloma (Femenino)" }
];

// Predefined voices for Google Cloud Text-to-Speech
const GEMINI_VOICES = [
    { value: "es-ES-Neural2-F", label: "España - Neural2-F (Femenino)" },
    { value: "es-ES-Neural2-B", label: "España - Neural2-B (Masculino)" },
    { value: "es-MX-Neural2-A", label: "México - Neural2-A (Femenino)" },
    { value: "en-US-Neural2-F", label: "EEUU - Neural2-F (Femenino)" }
];

// Predefined models for Piper TTS
const PIPER_VOICES = [
    { value: "data/models/es_ES-carlfm-x_low.onnx", label: "España - Carlfm (Masculino)" },
    { value: "data/models/es_ES-davefx-medium.onnx", label: "España - DaveFX (Masculino - Proyecto Go)" },
    { value: "data/models/es_ES-sharvard-medium.onnx", label: "España - SHarvard (Femenino)" }
];

// Predefined voices for Gemini Live (Native Audio)
const GEMINI_LIVE_VOICES = [
    { value: "Charon", label: "Charon (Masculino - Usado en Go)" },
    { value: "Puck", label: "Puck (Masculino)" },
    { value: "Kore", label: "Kore (Femenino)" },
    { value: "Fenrir", label: "Fenrir (Masculino)" },
    { value: "Aoede", label: "Aoede (Femenino)" }
];

function connect() {
    socket = new WebSocket(wsUrl);

    socket.onopen = () => {
        if (statusDot) statusDot.classList.add("connected");
        if (statusText) statusText.textContent = "Conectado";
    };

    socket.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            if (data.type === "event" && data.event === "ui_command") {
                const action = data.data.action;
                // Redirect back to HUD if the voice command tells us to return
                if (action === "open_hud" || action === "close_config") {
                    window.location.href = "/hud";
                }
            }
        } catch (err) {
            console.error("Error parsing message:", err);
        }
    };

    socket.onclose = () => {
        if (statusDot) statusDot.classList.remove("connected");
        if (statusText) statusText.textContent = "Desconectado";
        setTimeout(connect, reconnectInterval);
    };

    socket.onerror = (error) => {
        console.error("WebSocket error:", error);
    };
}

function updateProviderFields(selectedModel = null) {
    const provider = document.getElementById("llmProvider").value;
    const apiKeyGroup = document.getElementById("apiKeyGroup");
    const apiBaseGroup = document.getElementById("apiBaseGroup");
    const apiKeyLabel = document.getElementById("apiKeyLabel");
    const llmApiKey = document.getElementById("llmApiKey");
    const llmApiBase = document.getElementById("llmApiBase");
    
    // Config interface depending on selected provider
    if (provider === "ollama" || provider === "local") {
        apiKeyGroup.style.display = "none";
        apiBaseGroup.style.display = "flex";
        if (provider === "ollama") {
            llmApiBase.placeholder = "http://localhost:11434";
        } else {
            llmApiBase.placeholder = "http://localhost:8000";
        }
    } else {
        apiKeyGroup.style.display = "flex";
        apiBaseGroup.style.display = "none";
        
        // Dynamically adjust label and placeholder to be extremely clear and accurate
        apiKeyLabel.textContent = "API Key del Proveedor (PROVIDER_API_KEY)";
        if (provider === "openai") {
            llmApiKey.placeholder = "sk-proj-xxxxxxxxxxxxxxxxxxxx";
        } else if (provider === "gemini") {
            llmApiKey.placeholder = "AIzaSyxxxxxxxxxxxxxxxxxxxxxx";
        } else if (provider === "anthropic") {
            llmApiKey.placeholder = "sk-ant-xxxxxxxxxxxxxxxxxxxx";
        } else if (provider === "openrouter") {
            llmApiKey.placeholder = "sk-or-v1-xxxxxxxxxxxxxxxxxx";
        }
    }
    
    // Populate model options dropdown
    const modelSelect = document.getElementById("llmModel");
    modelSelect.innerHTML = "";
    
    const models = PROVIDER_MODELS[provider] || [];
    models.forEach(m => {
        const opt = document.createElement("option");
        opt.value = m.value;
        opt.textContent = m.label;
        modelSelect.appendChild(opt);
    });
    
    // Add manual text input option
    const customOpt = document.createElement("option");
    customOpt.value = "custom";
    customOpt.textContent = "Otro (Ingresar manualmente)";
    modelSelect.appendChild(customOpt);
    
    // Set active/loaded model
    if (selectedModel) {
        const found = models.some(m => m.value === selectedModel);
        if (found) {
            modelSelect.value = selectedModel;
            document.getElementById("llmModelManual").style.display = "none";
            document.getElementById("llmModelManual").value = "";
        } else {
            modelSelect.value = "custom";
            document.getElementById("llmModelManual").style.display = "block";
            document.getElementById("llmModelManual").value = selectedModel;
        }
    } else {
        if (models.length > 0) {
            modelSelect.value = models[0].value;
            document.getElementById("llmModelManual").style.display = "none";
            document.getElementById("llmModelManual").value = "";
        } else {
            modelSelect.value = "custom";
            document.getElementById("llmModelManual").style.display = "block";
            document.getElementById("llmModelManual").value = "";
        }
    }
}

function checkManualModel() {
    const modelSelect = document.getElementById("llmModel");
    const modelManual = document.getElementById("llmModelManual");
    if (modelSelect.value === "custom") {
        modelManual.style.display = "block";
    } else {
        modelManual.style.display = "none";
        modelManual.value = "";
    }
}

function updateVoiceFields(selectedSttModel = null, selectedTtsVoice = null, selectedApiKey = null) {
    const stt = document.getElementById("sttProvider").value;
    const tts = document.getElementById("ttsProvider").value;
    
    const voiceExtraRow = document.getElementById("voiceExtraRow");
    const sttModelGroup = document.getElementById("sttModelGroup");
    const ttsVoiceGroup = document.getElementById("ttsVoiceGroup");
    const ttsVoiceLabel = document.getElementById("ttsVoiceLabel");
    const ttsVoiceSelect = document.getElementById("ttsVoiceSelect");
    const ttsVoiceInput = document.getElementById("ttsVoiceInput");
    
    const piperDownloadContainer = document.getElementById("piperDownloadContainer");
    if (piperDownloadContainer) {
        piperDownloadContainer.style.display = "none";
    }
    
    const voskDownloadContainer = document.getElementById("voskDownloadContainer");
    if (voskDownloadContainer) {
        voskDownloadContainer.style.display = "none";
    }
    
    const whisperDownloadContainer = document.getElementById("whisperDownloadContainer");
    if (whisperDownloadContainer) {
        whisperDownloadContainer.style.display = "none";
    }
    
    const voiceKeyRow = document.getElementById("voiceKeyRow");
    const voiceApiKey = document.getElementById("voiceApiKey");
    
    let showExtra = false;
    
    // 1. STT Whisper Model configurations
    if (stt === "whisper_local" || stt === "faster_whisper" || stt === "groq_stt" || stt === "openai_stt") {
        sttModelGroup.style.display = "flex";
        showExtra = true;
        if (selectedSttModel) {
            document.getElementById("sttModel").value = selectedSttModel;
        }
        // Check local model presence if local whisper providers are selected
        if (stt === "whisper_local" || stt === "faster_whisper") {
            const sttModelVal = document.getElementById("sttModel").value;
            checkWhisperModelPresence(stt, sttModelVal);
        }
    } else {
        sttModelGroup.style.display = "none";
        if (stt === "vosk") {
            checkVoskModelPresence();
        }
    }
    
    // Bind change listener on STT model select once
    const sttModelSelect = document.getElementById("sttModel");
    if (sttModelSelect && !sttModelSelect.dataset.listenerBound) {
        sttModelSelect.addEventListener("change", () => {
            const activeStt = document.getElementById("sttProvider").value;
            if (activeStt === "whisper_local" || activeStt === "faster_whisper") {
                checkWhisperModelPresence(activeStt, sttModelSelect.value);
            }
        });
        sttModelSelect.dataset.listenerBound = "true";
    }
    
    // 2. TTS Voice selection and details
    if (tts === "piper") {
        ttsVoiceGroup.style.display = "flex";
        ttsVoiceSelect.style.display = "block";
        ttsVoiceInput.style.display = "none";
        ttsVoiceLabel.textContent = "Modelo de Voz Piper";
        
        // Populate Piper options
        ttsVoiceSelect.innerHTML = "";
        PIPER_VOICES.forEach(v => {
            const opt = document.createElement("option");
            opt.value = v.value;
            opt.textContent = v.label;
            ttsVoiceSelect.appendChild(opt);
        });
        
        // Add manual custom option
        const optCustom = document.createElement("option");
        optCustom.value = "custom";
        optCustom.textContent = "Otro (Ingresar ruta manualmente)";
        ttsVoiceSelect.appendChild(optCustom);
        
        // Bind select value
        if (selectedTtsVoice) {
            const found = PIPER_VOICES.some(v => v.value === selectedTtsVoice);
            if (found) {
                ttsVoiceSelect.value = selectedTtsVoice;
                ttsVoiceInput.value = selectedTtsVoice;
                ttsVoiceInput.style.display = "none";
            } else {
                ttsVoiceSelect.value = "custom";
                ttsVoiceInput.style.display = "block";
                ttsVoiceInput.value = selectedTtsVoice;
            }
        } else {
            ttsVoiceSelect.value = PIPER_VOICES[0].value;
            ttsVoiceInput.value = PIPER_VOICES[0].value;
            ttsVoiceInput.style.display = "none";
        }
        
        // Bind event listeners dynamically once
        if (!ttsVoiceSelect.dataset.listenerBound) {
            ttsVoiceSelect.addEventListener("change", () => {
                const ttsVal = document.getElementById("ttsProvider").value;
                if (ttsVal === "piper") {
                    if (ttsVoiceSelect.value === "custom") {
                        ttsVoiceInput.style.display = "block";
                        ttsVoiceInput.value = "";
                        document.getElementById("piperDownloadContainer").style.display = "none";
                    } else {
                        ttsVoiceInput.style.display = "none";
                        ttsVoiceInput.value = ttsVoiceSelect.value;
                        checkPiperModelPresence(ttsVoiceSelect.value);
                    }
                }
            });
            ttsVoiceSelect.dataset.listenerBound = "true";
        }

        if (!ttsVoiceInput.dataset.listenerBound) {
            ttsVoiceInput.addEventListener("change", () => {
                const ttsVal = document.getElementById("ttsProvider").value;
                if (ttsVal === "piper" && ttsVoiceSelect.value === "custom") {
                    checkPiperModelPresence(ttsVoiceInput.value);
                }
            });
            ttsVoiceInput.dataset.listenerBound = "true";
        }

        // Ensure check for model presence
        const activePath = ttsVoiceSelect.value === "custom" ? ttsVoiceInput.value : ttsVoiceSelect.value;
        checkPiperModelPresence(activePath);
        
        showExtra = true;
    } else if (tts === "edge_tts") {
        ttsVoiceGroup.style.display = "flex";
        ttsVoiceSelect.style.display = "block";
        ttsVoiceInput.style.display = "none";
        ttsVoiceLabel.textContent = "Voz de Microsoft Edge";
        
        // Populate Edge-TTS options
        ttsVoiceSelect.innerHTML = "";
        EDGE_VOICES.forEach(v => {
            const opt = document.createElement("option");
            opt.value = v.value;
            opt.textContent = v.label;
            ttsVoiceSelect.appendChild(opt);
        });
        
        if (selectedTtsVoice) {
            ttsVoiceSelect.value = selectedTtsVoice;
        }
        showExtra = true;
    } else if (tts === "elevenlabs") {
        ttsVoiceGroup.style.display = "flex";
        ttsVoiceSelect.style.display = "none";
        ttsVoiceInput.style.display = "block";
        ttsVoiceLabel.textContent = "ID de Voz de ElevenLabs";
        ttsVoiceInput.placeholder = "21m00Tcm4TlvDq8ikWAM";
        if (selectedTtsVoice !== null && selectedTtsVoice !== undefined) {
            ttsVoiceInput.value = selectedTtsVoice;
        } else {
            ttsVoiceInput.value = "";
        }
        showExtra = true;
    } else if (tts === "gemini_tts") {
        ttsVoiceGroup.style.display = "flex";
        ttsVoiceSelect.style.display = "block";
        ttsVoiceInput.style.display = "none";
        ttsVoiceLabel.textContent = "Voz de Google Cloud TTS";
        
        // Populate Gemini TTS options
        ttsVoiceSelect.innerHTML = "";
        GEMINI_VOICES.forEach(v => {
            const opt = document.createElement("option");
            opt.value = v.value;
            opt.textContent = v.label;
            ttsVoiceSelect.appendChild(opt);
        });
        
        if (selectedTtsVoice) {
            ttsVoiceSelect.value = selectedTtsVoice;
        }
        showExtra = true;
    } else if (tts === "gemini_live") {
        ttsVoiceGroup.style.display = "flex";
        ttsVoiceSelect.style.display = "block";
        ttsVoiceInput.style.display = "none";
        ttsVoiceLabel.textContent = "Voz Nativa de Gemini Live";
        
        // Populate Gemini Live options
        ttsVoiceSelect.innerHTML = "";
        GEMINI_LIVE_VOICES.forEach(v => {
            const opt = document.createElement("option");
            opt.value = v.value;
            opt.textContent = v.label;
            ttsVoiceSelect.appendChild(opt);
        });
        
        if (selectedTtsVoice) {
            // Check if selected voice is supported in Gemini Live list, else default to Charon
            const found = GEMINI_LIVE_VOICES.some(v => v.value === selectedTtsVoice);
            if (found) {
                ttsVoiceSelect.value = selectedTtsVoice;
            } else {
                ttsVoiceSelect.value = "Charon";
            }
        } else {
            ttsVoiceSelect.value = "Charon";
        }
        showExtra = true;
    } else {
        ttsVoiceGroup.style.display = "none";
    }
    
    // Toggle overall extra row visibility
    voiceExtraRow.style.display = showExtra ? "flex" : "none";
    
    // 3. API Key fields depending on voice services (if cloud is selected)
    const isCloudVoice = (stt === "gemini_stt" || stt === "gemini_live" || stt === "groq_stt" || stt === "openai_stt" || stt === "google_stt" || tts === "elevenlabs" || tts === "gemini_tts" || tts === "gemini_live");
    if (isCloudVoice) {
        voiceKeyRow.style.display = "flex";
        if (selectedApiKey !== null && selectedApiKey !== undefined) {
            voiceApiKey.value = selectedApiKey;
        }
    } else {
        voiceKeyRow.style.display = "none";
        voiceApiKey.value = "";
    }
}

async function loadConfig() {
    try {
        const res = await fetch("/config");
        if (!res.ok) throw new Error("Failed to load config");
        const data = await res.json();
        
        // Populate inputs
        document.getElementById("llmProvider").value = data.llm.provider;
        
        // Load provider fields and specific selected model
        updateProviderFields(data.llm.model);
        
        document.getElementById("llmTemp").value = data.llm.temperature;
        document.getElementById("llmApiKey").value = data.llm.api_key || "";
        document.getElementById("llmApiBase").value = data.llm.api_base || "";
        
        document.getElementById("voiceEnabled").checked = data.voice.enabled;
        document.getElementById("voicePTT").checked = data.voice.push_to_talk;
        document.getElementById("sttProvider").value = data.voice.stt_provider;
        document.getElementById("ttsProvider").value = data.voice.tts_provider;
        
        // Dynamically update voice inputs and load values
        updateVoiceFields(data.voice.stt_model, data.voice.tts_voice, data.voice.api_key);

        document.getElementById("minPermission").value = data.security.min_permission_level;
        document.getElementById("requireConfirm").checked = data.security.require_confirmation;
        
        document.getElementById("appName").value = data.app.name;
        document.getElementById("shortTermLimit").value = data.memory.short_term_limit;
    } catch (err) {
        showStatus("Error al cargar la configuración: " + err.message, "error");
    }
}

async function saveConfig(event) {
    event.preventDefault();
    
    const provider = document.getElementById("llmProvider").value;
    const modelSelect = document.getElementById("llmModel");
    const modelManual = document.getElementById("llmModelManual");
    const selectedModel = modelSelect.value === "custom" ? modelManual.value : modelSelect.value;
    
    const stt = document.getElementById("sttProvider").value;
    const tts = document.getElementById("ttsProvider").value;
    
    // Determine the tts_voice based on active selection or input
    let ttsVoice = "";
    if (tts === "edge_tts" || tts === "gemini_tts" || tts === "gemini_live") {
        ttsVoice = document.getElementById("ttsVoiceSelect").value;
    } else if (tts === "piper") {
        const piperSel = document.getElementById("ttsVoiceSelect").value;
        ttsVoice = piperSel === "custom" ? document.getElementById("ttsVoiceInput").value : piperSel;
    } else if (tts === "elevenlabs") {
        ttsVoice = document.getElementById("ttsVoiceInput").value;
    }
    
    const voiceApiKey = document.getElementById("voiceApiKey").value;
    const sttModel = (stt === "whisper_local" || stt === "faster_whisper") 
        ? document.getElementById("sttModel").value 
        : null;
    
    const payload = {
        llm: {
            provider: provider,
            model: selectedModel,
            temperature: parseFloat(document.getElementById("llmTemp").value),
            api_key: document.getElementById("llmApiKey").value,
            api_base: document.getElementById("llmApiBase").value || null
        },
        voice: {
            enabled: document.getElementById("voiceEnabled").checked,
            push_to_talk: document.getElementById("voicePTT").checked,
            stt_provider: stt,
            tts_provider: tts,
            stt_model: sttModel,
            tts_voice: ttsVoice,
            api_key: voiceApiKey
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
        showStatus("Configuración guardada correctamente.", "success");
    } catch (err) {
        showStatus("Error al guardar la configuración: " + err.message, "error");
    }
}

function showStatus(text, type) {
    statusMsg.textContent = text;
    statusMsg.className = `status-message ${type}`;
    statusMsg.style.display = "block";
    
    setTimeout(() => {
        statusMsg.style.display = "none";
    }, 4000);
}

// Event Listeners
configForm.addEventListener("submit", saveConfig);

// Expose functions globally for inline HTML event handlers
window.updateProviderFields = updateProviderFields;
window.checkManualModel = checkManualModel;
window.updateVoiceFields = updateVoiceFields;
window.downloadPiperModel = downloadPiperModel;
window.checkPiperModelPresence = checkPiperModelPresence;
window.downloadVoskModel = downloadVoskModel;
window.checkVoskModelPresence = checkVoskModelPresence;

let piperDownloadInterval = null;
let voskDownloadInterval = null;

async function checkPiperModelPresence(modelPath) {
    const downloadContainer = document.getElementById("piperDownloadContainer");
    const downloadBtn = document.getElementById("btnDownloadPiper");
    const progressDiv = document.getElementById("piperDownloadProgress");
    
    if (!modelPath) {
        downloadContainer.style.display = "none";
        return;
    }
    
    try {
        const res = await fetch(`/voice/check_piper?path=${encodeURIComponent(modelPath)}`);
        if (res.ok) {
            const data = await res.json();
            if (data.exists) {
                downloadContainer.style.display = "none";
            } else {
                downloadContainer.style.display = "block";
                progressDiv.style.display = "none";
                downloadBtn.disabled = false;
                downloadBtn.innerHTML = '<i class="fas fa-download"></i> Descargar Modelo';
            }
        }
    } catch (e) {
        console.error("Error checking Piper model presence:", e);
    }
}

async function downloadPiperModel() {
    const ttsVoiceSelect = document.getElementById("ttsVoiceSelect");
    const ttsVoiceInput = document.getElementById("ttsVoiceInput");
    const modelPath = ttsVoiceSelect.value === "custom" ? ttsVoiceInput.value : ttsVoiceSelect.value;
    
    const downloadBtn = document.getElementById("btnDownloadPiper");
    const progressDiv = document.getElementById("piperDownloadProgress");
    const progressBar = document.getElementById("piperProgressBar");
    const progressText = document.getElementById("piperProgressText");
    
    if (!modelPath) {
        alert("Por favor ingrese o seleccione una ruta de modelo válida.");
        return;
    }
    
    downloadBtn.disabled = true;
    downloadBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Iniciando descarga...';
    progressDiv.style.display = "block";
    progressBar.style.width = "0%";
    progressText.textContent = "Iniciando descarga...";
    
    try {
        const res = await fetch("/voice/download_piper", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ path: modelPath })
        });
        
        if (!res.ok) {
            throw new Error(`Servidor retornó código: ${res.status}`);
        }
        
        if (piperDownloadInterval) clearInterval(piperDownloadInterval);
        
        piperDownloadInterval = setInterval(async () => {
            try {
                const statusRes = await fetch("/voice/download_piper/status");
                if (statusRes.ok) {
                    const statusData = await statusRes.json();
                    
                    if (statusData.status === "downloading") {
                        const percent = statusData.progress;
                        progressBar.style.width = `${percent}%`;
                        progressText.textContent = `Descargando: ${percent}%`;
                        downloadBtn.innerHTML = `<i class="fas fa-spinner fa-spin"></i> Descargando (${percent}%)`;
                    } else if (statusData.status === "completed") {
                        clearInterval(piperDownloadInterval);
                        progressBar.style.width = "100%";
                        progressText.textContent = "¡Descarga completa!";
                        downloadBtn.innerHTML = '<i class="fas fa-check"></i> Descargado';
                        
                        setTimeout(() => {
                            document.getElementById("piperDownloadContainer").style.display = "none";
                            showStatus("Modelo Piper descargado e instalado correctamente.", "success");
                        }, 1500);
                    } else if (statusData.status === "error") {
                        clearInterval(piperDownloadInterval);
                        progressBar.style.width = "0%";
                        progressText.textContent = `Error: ${statusData.error_message}`;
                        downloadBtn.disabled = false;
                        downloadBtn.innerHTML = '<i class="fas fa-download"></i> Reintentar Descarga';
                        showStatus(`Error al descargar: ${statusData.error_message}`, "error");
                    }
                }
            } catch (err) {
                console.error("Error polling download status:", err);
            }
        }, 1000);
        
    } catch (err) {
        downloadBtn.disabled = false;
        downloadBtn.innerHTML = '<i class="fas fa-download"></i> Descargar Modelo';
        progressText.textContent = `Error: ${err.message}`;
        showStatus(`Error de red: ${err.message}`, "error");
    }
}

async function checkVoskModelPresence() {
    const downloadContainer = document.getElementById("voskDownloadContainer");
    const downloadBtn = document.getElementById("btnDownloadVosk");
    const progressDiv = document.getElementById("voskDownloadProgress");
    
    try {
        const res = await fetch("/voice/check_vosk");
        if (res.ok) {
            const data = await res.json();
            if (data.exists) {
                downloadContainer.style.display = "none";
            } else {
                downloadContainer.style.display = "block";
                progressDiv.style.display = "none";
                downloadBtn.disabled = false;
                downloadBtn.innerHTML = '<i class="fas fa-download"></i> Descargar Modelo Vosk (40MB)';
            }
        }
    } catch (e) {
        console.error("Error checking Vosk model presence:", e);
    }
}

async function downloadVoskModel() {
    const downloadBtn = document.getElementById("btnDownloadVosk");
    const progressDiv = document.getElementById("voskDownloadProgress");
    const progressBar = document.getElementById("voskProgressBar");
    const progressText = document.getElementById("voskProgressText");
    
    downloadBtn.disabled = true;
    downloadBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Iniciando descarga...';
    progressDiv.style.display = "block";
    progressBar.style.width = "0%";
    progressText.textContent = "Iniciando descarga...";
    
    try {
        const res = await fetch("/voice/download_vosk", { method: "POST" });
        if (!res.ok) {
            throw new Error(`Servidor retornó código: ${res.status}`);
        }
        
        if (voskDownloadInterval) clearInterval(voskDownloadInterval);
        
        voskDownloadInterval = setInterval(async () => {
            try {
                const statusRes = await fetch("/voice/download_vosk/status");
                if (statusRes.ok) {
                    const statusData = await statusRes.json();
                    if (statusData.status === "downloading") {
                        const percent = statusData.progress;
                        progressBar.style.width = `${percent}%`;
                        progressText.textContent = `Descargando: ${percent}%`;
                        downloadBtn.innerHTML = `<i class="fas fa-spinner fa-spin"></i> Descargando (${percent}%)`;
                    } else if (statusData.status === "completed") {
                        clearInterval(voskDownloadInterval);
                        progressBar.style.width = "100%";
                        progressText.textContent = "¡Descarga completa!";
                        downloadBtn.innerHTML = '<i class="fas fa-check"></i> Descargado';
                        
                        setTimeout(() => {
                            document.getElementById("voskDownloadContainer").style.display = "none";
                            showStatus("Modelo Vosk descargado e instalado correctamente.", "success");
                        }, 1500);
                    } else if (statusData.status === "error") {
                        clearInterval(voskDownloadInterval);
                        progressBar.style.width = "0%";
                        progressText.textContent = `Error: ${statusData.error_message}`;
                        downloadBtn.disabled = false;
                        downloadBtn.innerHTML = '<i class="fas fa-download"></i> Reintentar Descarga';
                        showStatus(`Error al descargar: ${statusData.error_message}`, "error");
                    }
                }
            } catch (err) {
                console.error("Error polling Vosk download status:", err);
            }
        }, 1000);
        
    } catch (err) {
        downloadBtn.disabled = false;
        downloadBtn.innerHTML = '<i class="fas fa-download"></i> Descargar Modelo Vosk (40MB)';
        progressText.textContent = `Error: ${err.message}`;
        showStatus(`Error de red: ${err.message}`, "error");
    }
}

let whisperDownloadInterval = null;

async function checkWhisperModelPresence(provider, model) {
    const downloadContainer = document.getElementById("whisperDownloadContainer");
    const downloadBtn = document.getElementById("btnDownloadWhisper");
    const progressDiv = document.getElementById("whisperDownloadProgress");
    
    if (!downloadContainer) return;
    
    if (!provider || !model) {
        downloadContainer.style.display = "none";
        return;
    }
    
    try {
        const res = await fetch(`/voice/check_whisper?provider=${encodeURIComponent(provider)}&model=${encodeURIComponent(model)}`);
        if (res.ok) {
            const data = await res.json();
            if (data.exists) {
                downloadContainer.style.display = "none";
            } else {
                downloadContainer.style.display = "block";
                progressDiv.style.display = "none";
                downloadBtn.disabled = false;
                const modelLabel = model.toUpperCase();
                const providerLabel = provider === "whisper_local" ? "Whisper Local" : "Faster-Whisper";
                downloadBtn.innerHTML = `<i class="fas fa-download"></i> Descargar Modelo ${modelLabel} para ${providerLabel}`;
            }
        }
    } catch (e) {
        console.error("Error checking Whisper model presence:", e);
    }
}

async function downloadWhisperModel() {
    const provider = document.getElementById("sttProvider").value;
    const model = document.getElementById("sttModel").value;
    
    const downloadBtn = document.getElementById("btnDownloadWhisper");
    const progressDiv = document.getElementById("whisperDownloadProgress");
    const progressBar = document.getElementById("whisperProgressBar");
    const progressText = document.getElementById("whisperProgressText");
    
    if (!provider || !model) {
        alert("Por favor seleccione un proveedor y modelo STT válidos.");
        return;
    }
    
    downloadBtn.disabled = true;
    downloadBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Iniciando descarga...';
    progressDiv.style.display = "block";
    progressBar.style.width = "0%";
    progressText.textContent = "Iniciando descarga...";
    
    try {
        const res = await fetch("/voice/download_whisper", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ provider: provider, model: model })
        });
        
        if (!res.ok) {
            throw new Error(`Servidor retornó código: ${res.status}`);
        }
        
        if (whisperDownloadInterval) clearInterval(whisperDownloadInterval);
        
        whisperDownloadInterval = setInterval(async () => {
            try {
                const statusRes = await fetch("/voice/download_whisper/status");
                if (statusRes.ok) {
                    const statusData = await statusRes.json();
                    
                    if (statusData.status === "downloading") {
                        const percent = statusData.progress;
                        progressBar.style.width = `${percent}%`;
                        progressText.textContent = `Descargando: ${percent}%`;
                        downloadBtn.innerHTML = `<i class="fas fa-spinner fa-spin"></i> Descargando (${percent}%)`;
                    } else if (statusData.status === "completed") {
                        clearInterval(whisperDownloadInterval);
                        progressBar.style.width = "100%";
                        progressText.textContent = "¡Descarga completa!";
                        downloadBtn.innerHTML = '<i class="fas fa-check"></i> Descargado';
                        
                        setTimeout(() => {
                            document.getElementById("whisperDownloadContainer").style.display = "none";
                            showStatus(`Modelo Whisper ${model.toUpperCase()} descargado correctamente.`, "success");
                        }, 1500);
                    } else if (statusData.status === "error") {
                        clearInterval(whisperDownloadInterval);
                        progressBar.style.width = "0%";
                        progressText.textContent = `Error: ${statusData.error_message}`;
                        downloadBtn.disabled = false;
                        downloadBtn.innerHTML = '<i class="fas fa-download"></i> Reintentar Descarga';
                        showStatus(`Error al descargar Whisper: ${statusData.error_message}`, "error");
                    }
                }
            } catch (err) {
                console.error("Error polling Whisper download status:", err);
            }
        }, 1000);
        
    } catch (err) {
        downloadBtn.disabled = false;
        downloadBtn.innerHTML = '<i class="fas fa-download"></i> Descargar Modelo';
        progressText.textContent = `Error: ${err.message}`;
        showStatus(`Error de red: ${err.message}`, "error");
    }
}

window.downloadWhisperModel = downloadWhisperModel;
window.checkWhisperModelPresence = checkWhisperModelPresence;

// Load settings and connect to WS on load
window.addEventListener("DOMContentLoaded", () => {
    loadConfig();
    connect();
});
