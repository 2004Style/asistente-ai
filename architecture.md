# AI Assistant

ai-assistant/
├── README.md
├── pyproject.toml
├── .gitignore
├── .env.example            # Variables secretas (API keys, tokens, etc.)
│
├── configs/                # Configuraciones YAML cargadas al iniciar
│   ├── app.yml             # Nombre, idioma, puertos, UI por defecto, etc.
│   ├── llm.yml             # Proveedores y modelos LLM (OpenAI, Ollama, etc.)
│   ├── voice.yml           # STT/TTS, wake word, micrófono/altavoz.
│   ├── memory.yml          # Límite de contexto y almacenamiento.
│   ├── security.yml        # Roles, permisos y políticas de confirmación.
│   ├── platforms.yml       # Descripción de distros y escritorios soportados.
│   └── tools.yml           # Habilitar o deshabilitar herramientas globalmente.
│
├── app/                    # Arranque del asistente
│   ├── main.py             # Punto de entrada; invoca al daemon.
│   ├── bootstrap.py        # Registra herramientas, memoria, LLM, visión.
│   ├── container.py        # Inyección de dependencias.
│   ├── lifecycle.py        # Estados de inicio/parada del proceso.
│   └── config/
│       ├── loader.py       # Carga YAML y variables de entorno.
│       ├── schema.py       # Esquemas Pydantic de configuración.
│       └── env.py          # Variables sensibles (ej. .env).
│
├── core/                   # Lógica de orquestación y dominio
│   ├── assistant.py        # Orquestador principal (decide qué hacer).
│   ├── agent.py            # Descomposición de tareas.
│   ├── planner.py          # Planificador de acciones complejas.
│   ├── executor.py         # Ejecuta herramientas, maneja confirmaciones.
│   ├── state_manager.py    # Estados conversacionales (sleeping, speaking, etc.).
│   ├── context.py          # Memoria de corto plazo y resúmenes.
│   ├── events.py           # Bus de eventos internos.
│   └── prompts/
│       ├── system.yml
│       ├── tools.yml
│       └── safety.yml
│
├── host/                   # Adaptadores de plataforma (renombrado de platform/)
│   ├── detector.py         # Detecta OS/distro/escritorio (instalador).
│   ├── profile.py          # Guarda la plataforma detectada.
│   ├── registry.py         # Activa adaptadores según platforms.yml.
│   └── adapters/
│       ├── linux/
│       │   ├── distros/
│       │   │   ├── arch.py
│       │   │   ├── debian.py
│       │   │   └── fedora.py
│       │   ├── desktops/
│       │   │   ├── gnome.py
│       │   │   ├── kde.py
│       │   │   └── hyprland.py
│       │   └── package_managers.py
│       ├── windows/
│       │   ├── base.py
│       │   ├── powershell.py
│       │   └── win32.py
│       └── macos/
│           ├── base.py
│           ├── applescript.py
│           └── shortcuts.py
│
├── llm/                    # Proveedores y modelos de lenguaje
│   ├── base.py
│   ├── router.py
│   ├── message.py
│   ├── providers/
│   │   ├── openai.py
│   │   ├── openrouter.py
│   │   ├── gemini.py
│   │   ├── anthropic.py
│   │   ├── ollama.py
│   │   └── local.py
│   └── models/
│       ├── capabilities.py  # Capacidades de cada modelo
│       └── pricing.py       # Precios (datos actualizables)
│
├── voice/                  # Audio: STT, TTS y wake words
│   ├── manager.py
│   ├── stt/
│   │   ├── base.py
│   │   ├── vosk.py
│   │   ├── whisper_local.py
│   │   ├── faster_whisper.py
│   │   └── gemini_stt.py
│   ├── tts/
│   │   ├── base.py
│   │   ├── piper.py
│   │   ├── edge_tts.py
│   │   ├── elevenlabs.py
│   │   └── gemini_tts.py
│   └── wakeword/
│       ├── base.py
│       └── openwakeword.py
│
├── vision/                 # Cámara y visión por computador
│   ├── manager.py
│   ├── camera.py
│   ├── screen.py
│   └── detectors/
│       ├── yolov8.py
│       ├── clip.py
│       └── …
│
├── memory/                 # Memoria y persistencia
│   ├── manager.py
│   ├── short_term.py
│   ├── long_term.py
│   ├── summarizer.py
│   ├── embeddings.py
│   └── stores/
│       ├── sqlite.py
│       ├── chroma.py
│       ├── qdrant.py
│       └── filesystem.py
│
├── tools/                  # Herramientas disponibles para el asistente
│   ├── registry.py
│   ├── base.py
│   ├── manifest.py         # Define el contrato común de cada herramienta.
│   ├── web/
│   │   ├── manifest.yml
│   │   └── actions/
│   │       ├── search.py
│   │       ├── open_tab.py
│   │       ├── close_tab.py
│   │       └── …           # Otras acciones de navegación.
│   ├── keyboard/
│   │   ├── manifest.yml
│   │   └── actions/
│   │       ├── type_text.py
│   │       ├── press_key.py
│   │       └── shortcut.py
│   ├── mouse/
│   │   ├── manifest.yml
│   │   └── actions/
│   │       ├── move.py
│   │       ├── click.py
│   │       └── scroll.py
│   ├── window/
│   │   ├── manifest.yml
│   │   └── actions/
│   │       ├── list_windows.py
│   │       ├── focus.py
│   │       ├── close.py
│   │       └── move_resize.py
│   ├── workspace/
│   │   ├── manifest.yml
│   │   └── actions/
│   │       ├── switch_workspace.py
│   │       └── list_workspaces.py
│   ├── applications/
│   │   ├── manifest.yml
│   │   └── actions/
│   │       ├── open_app.py
│   │       ├── close_app.py
│   │       └── list_apps.py
│   ├── files/
│   │   ├── manifest.yml
│   │   └── actions/
│   │       ├── read_file.py
│   │       ├── write_file.py
│   │       ├── move_file.py
│   │       ├── copy_file.py
│   │       └── delete_file.py
│   ├── terminal/
│   │   ├── manifest.yml
│   │   └── actions/
│   │       ├── run_command.py
│   │       ├── run_in_background.py
│   │       └── kill_process.py
│   └── notes/
│       ├── manifest.yml
│       └── actions/
│           ├── create_note.py
│           ├── list_notes.py
│           └── delete_note.py
│
├── automation/             # Trabajos en segundo plano y recordatorios
│   ├── scheduler.py
│   ├── tasks_queue.py
│   ├── jobs.py
│   └── reminders.py
│
├── security/               # Seguridad y auditoría
│   ├── permissions.py
│   ├── policy.py
│   ├── sandbox.py
│   ├── confirmation.py
│   └── audit.py
│
├── interfaces/             # Interfaces de usuario
│   ├── voice_controller.py  # Coordina STT y TTS.
│   ├── web_ui/
│   │   ├── hud.html        # Panel de chat y estado del asistente.
│   │   ├── hud.js          # Conexión con WebSocket/HTTP.
│   │   ├── config.html     # UI de configuración.
│   │   ├── config.js
│   │   └── assets/         # Íconos, imágenes, etc.
│   └──                     # La captura de cámara/pantalla se gestiona en vision/
│
├── runtime/                # Componente de ejecución permanente (daemon)
│   ├── daemon.py          # Orquesta FastAPI, scheduler, voice, etc.
│   ├── health.py          # Endpoint de salud /healthz.
│   ├── instance_lock.py   # Evita ejecutar varias instancias.
│   ├── signals.py         # Manejo de SIGTERM, SIGINT, cancelación.
│   ├── shutdown.py        # Apagado controlado.
│   └── paths.py           # Rutas dinámicas y temporales.
│
├── services/               # Abstracción del gestor de servicios
│   ├── manager.py         # Define los comandos genéricos start/stop/etc.
│   ├── base.py
│   ├── systemd.py         # Implementa start/stop usando systemd.
│   ├── windows_service.py # Implementación para Windows.
│   └── launchd.py         # Implementación para macOS.
│
├── cli/                    # Línea de comandos para el usuario
│   ├── main.py
│   └── commands/
│       ├── run.py         # Ejecuta el asistente en primer plano.
│       ├── start.py       # Inicia el servicio como daemon.
│       ├── stop.py        # Detiene el servicio.
│       ├── restart.py
│       ├── status.py
│       ├── install.py     # Instala los archivos de servicio.
│       └── logs.py        # Visualiza registros.
│
├── packaging/              # Archivos de instalación por OS
│   ├── systemd/
│   │   └── rbot.service   # Unidad de systemd (Type=simple:contentReference[oaicite:1]{index=1})
│   ├── windows/
│   │   └── service.xml    # Definición para Windows Service.
│   └── macos/
│       └── com.rbot.assistant.plist
│
├── data/
│   ├── runtime/host-profile.json # Perfil de plataforma detectada.
│   ├── db/                # Bases de datos (SQLite, etc.)
│   ├── logs/              # Registros rotados.
│   ├── memories/          # Almacenamiento de memoria vectorial.
│   ├── models/            # Modelos entrenados localmente.
│   └── cache/             # Archivos temporales.
│
├── scripts/               # Scripts de mantenimiento
│   ├── install.sh         # Detecta sistema y actualiza platforms.yml.
│   ├── install.py         # Alternativa en Python.
│   ├── detect_system.py   # Detección de OS/distro/escritorio.
│   ├── dev.py             # Entorno de desarrollo.
│   └── seed.py            # Población inicial de datos.
│
├── tests/                 # Pruebas unitarias y de integración
│   ├── test_core.py
│   ├── test_host.py       # Sustituye a test_platform
│   ├── test_llm.py
│   ├── test_tools.py
│   ├── test_memory.py
│   ├── test_vision.py
│   └── test_runtime.py    # Valida el daemon.
└── (otros archivos y documentación)