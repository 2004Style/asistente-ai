# Checklist de desarrollo por archivo - AI Assistant

> Hoja de ruta para implementar, revisar y probar la arquitectura del proyecto `ai-assistant`.
>
> Marca una tarea como completada solo cuando el archivo exista, tenga una implementación funcional, incluya manejo de errores y cuente con las pruebas que correspondan.

## Convenciones generales

- [ ] Usar Python 3.12 o una versión definida explícitamente en `pyproject.toml`.
- [ ] Añadir `__init__.py` en todos los directorios que deban funcionar como paquetes Python.
- [ ] Aplicar tipado estático a funciones públicas y modelos de datos.
- [ ] Evitar que el dominio dependa directamente de proveedores, sistemas operativos o interfaces.
- [ ] No almacenar secretos, tokens, contraseñas ni datos privados en el repositorio.
- [ ] Registrar errores con contexto, sin exponer secretos en los logs.
- [ ] Incorporar timeouts, cancelación y reintentos limitados en operaciones externas.
- [ ] Probar primero las acciones destructivas en modo simulado.
- [ ] Mantener compatibilidad progresiva entre Linux, Windows y macOS.

---

## Raíz del proyecto

### `README.md`

- [ ] Explicar el propósito, alcance y estado actual del asistente.
- [ ] Documentar requisitos, instalación, configuración y primera ejecución.
- [ ] Incluir ejemplos de uso por CLI, voz y Web UI.
- [ ] Describir la arquitectura general y enlazar documentación especializada.
- [ ] Añadir instrucciones para ejecutar pruebas y contribuir.

### `pyproject.toml`

- [ ] Definir nombre, versión, descripción, licencia y versión mínima de Python.
- [ ] Separar dependencias principales, opcionales y de desarrollo.
- [ ] Registrar comandos ejecutables para el asistente y la CLI.
- [ ] Configurar formateador, linter, comprobación de tipos y `pytest`.
- [ ] Mantener dependencias con rangos de versiones compatibles.

### `.gitignore`

- [ ] Ignorar entornos virtuales, cachés, compilados y archivos del editor.
- [ ] Ignorar `.env`, logs, bases de datos, modelos y datos temporales.
- [ ] Conservar archivos vacíos necesarios mediante `.gitkeep`.
- [ ] Verificar que `.env.example` y configuraciones de ejemplo sí se versionen.

### `.env.example`

- [ ] Declarar solo nombres de variables y valores ficticios seguros.
- [ ] Agrupar variables por proveedor o subsistema.
- [ ] Indicar cuáles son obligatorias y cuáles opcionales.
- [ ] Incluir endpoints, claves, timeouts y opciones sensibles configurables.
- [ ] Mantenerlo sincronizado con `app/config/env.py`.

---

## Configuración

### `configs/app.yml`

- [ ] Definir nombre, idioma, zona horaria y entorno de ejecución.
- [ ] Configurar host, puertos y tipo de interfaz predeterminada.
- [ ] Incluir niveles de log y rutas lógicas, no rutas rígidas del equipo.
- [ ] Añadir valores predeterminados seguros y comentarios breves.

### `configs/llm.yml`

- [ ] Declarar proveedores habilitados y modelo predeterminado.
- [ ] Configurar modelos de respaldo y reglas de enrutamiento.
- [ ] Definir temperatura, límite de tokens, timeout y reintentos.
- [ ] Referenciar secretos mediante variables de entorno.
- [ ] Permitir capacidades por modelo: texto, visión, audio y herramientas.

### `configs/voice.yml`

- [ ] Seleccionar proveedores STT, TTS y wake word.
- [ ] Configurar idioma, voz, velocidad, dispositivo de entrada y salida.
- [ ] Definir detección de silencio, cancelación y tiempos máximos.
- [ ] Añadir modo local, modo remoto y estrategia de respaldo.

### `configs/memory.yml`

- [ ] Configurar límites de contexto y estrategia de resumen.
- [ ] Definir almacenes de corto y largo plazo.
- [ ] Establecer modelo de embeddings y dimensiones esperadas.
- [ ] Configurar retención, limpieza, privacidad y rutas de almacenamiento.

### `configs/security.yml`

- [ ] Definir roles, capacidades y permisos predeterminados.
- [ ] Clasificar acciones por nivel de riesgo.
- [ ] Establecer qué acciones requieren confirmación.
- [ ] Configurar sandbox, auditoría, límites y rutas permitidas.
- [ ] Aplicar denegación por defecto a operaciones no declaradas.

### `configs/platforms.yml`

- [ ] Modelar sistemas, distribuciones, escritorios y gestores soportados.
- [ ] Registrar capacidades disponibles por plataforma.
- [ ] Permitir que el instalador actualice solo la sección detectada.
- [ ] Validar compatibilidad con `host/profile.py` y `host/registry.py`.

### `configs/tools.yml`

- [ ] Habilitar o deshabilitar herramientas y acciones individualmente.
- [ ] Asociar cada herramienta con permisos y nivel de riesgo.
- [ ] Configurar timeout, concurrencia y límites de uso.
- [ ] Permitir restricciones específicas por plataforma o perfil.

---

## Aplicación y arranque

### `app/main.py`

- [ ] Implementar el punto de entrada asíncrono.
- [ ] Cargar configuración y construir el contenedor.
- [ ] Iniciar el daemon y traducir errores a códigos de salida claros.
- [ ] No contener lógica de negocio.

### `app/bootstrap.py`

- [ ] Registrar LLM, memoria, herramientas, voz, visión y eventos.
- [ ] Resolver implementaciones desde la configuración.
- [ ] Validar dependencias y capacidades antes del arranque.
- [ ] Evitar importaciones opcionales cuando una función esté deshabilitada.

### `app/container.py`

- [ ] Definir el contenedor de dependencias y ciclos de vida.
- [ ] Exponer interfaces, no instancias globales mutables.
- [ ] Permitir sustituir dependencias durante las pruebas.
- [ ] Cerrar correctamente recursos compartidos.

### `app/lifecycle.py`

- [ ] Modelar estados de arranque, ejecución, degradación y apagado.
- [ ] Ejecutar hooks en orden y de forma idempotente.
- [ ] Propagar cancelaciones y errores críticos.
- [ ] Emitir eventos de ciclo de vida.

### `app/config/loader.py`

- [ ] Cargar YAML, variables de entorno y overrides de CLI.
- [ ] Definir precedencia de fuentes de configuración.
- [ ] Resolver rutas de forma portable.
- [ ] Mostrar errores de configuración con la ruta exacta del campo.

### `app/config/schema.py`

- [ ] Crear modelos Pydantic para todos los archivos de `configs/`.
- [ ] Usar enumeraciones y tipos restringidos donde corresponda.
- [ ] Rechazar campos desconocidos en configuraciones críticas.
- [ ] Validar referencias cruzadas entre proveedores, modelos y herramientas.

### `app/config/env.py`

- [ ] Declarar variables sensibles con tipos y alias consistentes.
- [ ] Cargar `.env` solo en entornos permitidos.
- [ ] Proporcionar acceso seguro sin imprimir valores secretos.
- [ ] Verificar sincronización con `.env.example`.

---

## Núcleo de orquestación

### `core/assistant.py`

- [ ] Implementar el flujo principal desde entrada hasta respuesta.
- [ ] Coordinar contexto, agente, ejecución y salida.
- [ ] Gestionar cancelaciones, errores recuperables y respuestas parciales.
- [ ] Emitir eventos y métricas de cada interacción.

### `core/agent.py`

- [ ] Transformar solicitudes en objetivos y tareas manejables.
- [ ] Decidir cuándo responder directamente o utilizar herramientas.
- [ ] Mantener límites de iteración, costo y tiempo.
- [ ] Detectar tareas incompletas y resultados inválidos.

### `core/planner.py`

- [ ] Crear planes estructurados con dependencias y estados.
- [ ] Validar que las acciones propuestas existan en el registro.
- [ ] Permitir replanificación después de fallos o nueva información.
- [ ] Evitar ciclos y planes sin condición de finalización.

### `core/executor.py`

- [ ] Ejecutar acciones con timeout, cancelación y captura de errores.
- [ ] Consultar permisos antes de cada operación.
- [ ] Solicitar confirmación en acciones sensibles.
- [ ] Registrar resultados normalizados y soportar modo simulado.

### `core/state_manager.py`

- [ ] Definir estados válidos y sus transiciones.
- [ ] Proteger cambios concurrentes.
- [ ] Emitir eventos al cambiar de estado.
- [ ] Recuperar un estado coherente después de excepciones.

### `core/context.py`

- [ ] Administrar mensajes, resultados de herramientas y resúmenes.
- [ ] Calcular límites de contexto según el modelo.
- [ ] Recortar información sin perder instrucciones esenciales.
- [ ] Separar contexto temporal de memoria persistente.

### `core/events.py`

- [ ] Definir eventos tipados y un bus desacoplado.
- [ ] Soportar suscripción, cancelación y publicación asíncrona.
- [ ] Aislar fallos de consumidores.
- [ ] Evitar que eventos sensibles terminen sin filtrar en los logs.

### `core/prompts/system.yml`

- [ ] Definir identidad, alcance y comportamiento base.
- [ ] Separar instrucciones estables de datos dinámicos.
- [ ] Incluir variables con nombres claros y valores de respaldo.
- [ ] Versionar cambios relevantes del prompt.

### `core/prompts/tools.yml`

- [ ] Explicar al modelo cuándo y cómo utilizar herramientas.
- [ ] Describir contratos de entrada y salida sin duplicar manifiestos.
- [ ] Incluir reglas para errores, reintentos y confirmaciones.
- [ ] Evitar ejemplos que incentiven acciones destructivas.

### `core/prompts/safety.yml`

- [ ] Definir límites de seguridad y privacidad.
- [ ] Indicar cuándo rechazar, preguntar o solicitar confirmación.
- [ ] Proteger secretos, credenciales y datos personales.
- [ ] Cubrir manipulación de archivos, terminal, red y automatización.

---

## Plataforma anfitriona

### `host/detector.py`

- [ ] Detectar sistema operativo, distribución, versión y arquitectura.
- [ ] Detectar escritorio, sesión gráfica y disponibilidad de comandos.
- [ ] Devolver resultados estructurados con nivel de confianza.
- [ ] Funcionar cuando algunos comandos del sistema no existan.

### `host/profile.py`

- [ ] Definir el esquema serializable del perfil detectado.
- [ ] Guardar el perfil de forma atómica.
- [ ] Incluir fecha, versión del detector y capacidades.
- [ ] Migrar perfiles antiguos sin perder datos válidos.

### `host/registry.py`

- [ ] Registrar adaptadores por plataforma y capacidad.
- [ ] Seleccionar el adaptador compatible desde `platforms.yml`.
- [ ] Informar claramente funciones no soportadas.
- [ ] Permitir adaptadores falsos para pruebas.

### `host/adapters/linux/distros/arch.py`

- [ ] Detectar Arch Linux y derivados.
- [ ] Resolver instalación y consulta de paquetes con `pacman`.
- [ ] Manejar AUR como capacidad opcional y explícita.
- [ ] No ejecutar cambios del sistema sin confirmación.

### `host/adapters/linux/distros/debian.py`

- [ ] Detectar Debian, Ubuntu y derivados.
- [ ] Implementar operaciones mediante `apt`.
- [ ] Diferenciar actualización de índices y actualización de paquetes.
- [ ] Manejar privilegios y errores de bloqueo.

### `host/adapters/linux/distros/fedora.py`

- [ ] Detectar Fedora y sistemas compatibles.
- [ ] Implementar operaciones mediante `dnf`.
- [ ] Normalizar resultados con los otros adaptadores.
- [ ] Manejar repositorios y privilegios de forma segura.

### `host/adapters/linux/desktops/gnome.py`

- [ ] Detectar sesión GNOME en X11 y Wayland.
- [ ] Implementar capacidades mediante APIs o comandos disponibles.
- [ ] Declarar limitaciones de automatización en Wayland.
- [ ] Normalizar ventanas, espacios de trabajo y aplicaciones.

### `host/adapters/linux/desktops/kde.py`

- [ ] Detectar Plasma y su versión.
- [ ] Integrar herramientas de KWin y DBus cuando estén disponibles.
- [ ] Cubrir diferencias entre X11 y Wayland.
- [ ] Devolver errores de capacidad no soportada.

### `host/adapters/linux/desktops/hyprland.py`

- [ ] Detectar la instancia activa de Hyprland.
- [ ] Usar su interfaz IPC para ventanas y workspaces.
- [ ] Escapar argumentos y validar respuestas JSON.
- [ ] Cubrir monitores múltiples y workspaces especiales.

### `host/adapters/linux/package_managers.py`

- [ ] Definir una interfaz común para gestores de paquetes.
- [ ] Normalizar búsqueda, instalación, eliminación y actualización.
- [ ] Detectar privilegios y soportar modo de simulación.
- [ ] Evitar interpolación insegura de comandos.

### `host/adapters/windows/base.py`

- [ ] Definir capacidades base para Windows.
- [ ] Normalizar rutas, procesos, aplicaciones y errores.
- [ ] Detectar edición, versión y arquitectura.
- [ ] Proporcionar comprobaciones de privilegios.

### `host/adapters/windows/powershell.py`

- [ ] Ejecutar PowerShell con argumentos estructurados.
- [ ] Preferir salida JSON para evitar parsing frágil.
- [ ] Aplicar timeout, codificación UTF-8 y límites de salida.
- [ ] Evitar concatenar entradas del usuario en scripts.

### `host/adapters/windows/win32.py`

- [ ] Implementar operaciones de ventanas con APIs Win32.
- [ ] Gestionar identificadores inválidos y ventanas protegidas.
- [ ] Soportar escalado DPI y múltiples monitores.
- [ ] Liberar correctamente recursos nativos.

### `host/adapters/macos/base.py`

- [ ] Definir capacidades base para macOS.
- [ ] Detectar versión, arquitectura y permisos disponibles.
- [ ] Normalizar aplicaciones, rutas y procesos.
- [ ] Informar permisos de accesibilidad faltantes.

### `host/adapters/macos/applescript.py`

- [ ] Ejecutar AppleScript con parámetros validados.
- [ ] Capturar errores y códigos de salida.
- [ ] Escapar valores sin construir scripts inseguros.
- [ ] Solicitar confirmación para acciones sensibles.

### `host/adapters/macos/shortcuts.py`

- [ ] Listar y ejecutar atajos existentes.
- [ ] Validar nombres y entradas antes de invocarlos.
- [ ] Normalizar resultados y errores.
- [ ] Aplicar timeout y cancelación.

---

## Modelos de lenguaje

### `llm/base.py`

- [ ] Definir la interfaz asíncrona común de proveedores.
- [ ] Soportar respuesta normal y streaming.
- [ ] Normalizar uso, costos, errores y finalización.
- [ ] Declarar capacidades y cierre de recursos.

### `llm/router.py`

- [ ] Seleccionar proveedor y modelo según capacidad y configuración.
- [ ] Implementar fallback controlado y circuit breaker.
- [ ] Considerar privacidad, latencia, disponibilidad y costo.
- [ ] Evitar repetir solicitudes no idempotentes automáticamente.

### `llm/message.py`

- [ ] Modelar roles, contenido multimodal y llamadas a herramientas.
- [ ] Validar secuencias de mensajes.
- [ ] Serializar sin perder identificadores ni metadatos.
- [ ] Mantener el modelo independiente del formato de cada proveedor.

### `llm/providers/openai.py`

- [ ] Implementar autenticación y cliente asíncrono.
- [ ] Convertir mensajes, herramientas y respuestas al contrato común.
- [ ] Soportar streaming, uso y errores de límite.
- [ ] Añadir timeout, reintentos seguros y pruebas simuladas.

### `llm/providers/openrouter.py`

- [ ] Implementar cabeceras y endpoint de OpenRouter.
- [ ] Permitir selección dinámica de modelos.
- [ ] Normalizar diferencias de proveedores subyacentes.
- [ ] Capturar costos, disponibilidad y errores de enrutamiento.

### `llm/providers/gemini.py`

- [ ] Adaptar roles, contenido multimodal y funciones.
- [ ] Soportar streaming y metadatos de seguridad.
- [ ] Normalizar límites y motivos de finalización.
- [ ] Manejar credenciales sin exponerlas.

### `llm/providers/anthropic.py`

- [ ] Adaptar mensajes de sistema y bloques de contenido.
- [ ] Implementar herramientas y streaming.
- [ ] Normalizar uso de tokens y errores.
- [ ] Probar secuencias con resultados de herramientas.

### `llm/providers/ollama.py`

- [ ] Detectar disponibilidad del servidor local.
- [ ] Listar modelos instalados y sus capacidades conocidas.
- [ ] Implementar generación, chat y streaming.
- [ ] Manejar descarga ausente, timeout y servidor desconectado.

### `llm/providers/local.py`

- [ ] Definir integración genérica con motores locales.
- [ ] Administrar carga, descarga y consumo de recursos.
- [ ] Limitar concurrencia según CPU, RAM y GPU.
- [ ] Exponer estado y métricas del modelo.

### `llm/models/capabilities.py`

- [ ] Definir capacidades normalizadas por modelo.
- [ ] Registrar contexto, modalidades y soporte de herramientas.
- [ ] Permitir actualización sin cambiar el router.
- [ ] Manejar modelos desconocidos con valores conservadores.

### `llm/models/pricing.py`

- [ ] Modelar precios de entrada, salida, caché y multimedia.
- [ ] Registrar moneda, fecha y fuente de actualización.
- [ ] Calcular estimaciones sin mezclar unidades.
- [ ] Marcar precios desconocidos en vez de asumir cero.

---

## Voz

### `voice/manager.py`

- [ ] Coordinar captura, STT, wake word y TTS.
- [ ] Evitar que el TTS vuelva a activar el micrófono.
- [ ] Gestionar interrupciones, cancelación y selección de dispositivos.
- [ ] Emitir estados para la interfaz.

### `voice/stt/base.py`

- [ ] Definir contrato de transcripción normal y en streaming.
- [ ] Modelar idioma, segmentos, confianza y marcas de tiempo.
- [ ] Soportar cancelación y cierre.
- [ ] Normalizar formatos de audio aceptados.

### `voice/stt/vosk.py`

- [ ] Cargar el modelo configurado de forma perezosa.
- [ ] Convertir audio al formato requerido.
- [ ] Emitir resultados parciales y finales.
- [ ] Manejar modelo ausente y consumo de recursos.

### `voice/stt/whisper_local.py`

- [ ] Integrar Whisper local y selección de dispositivo.
- [ ] Configurar idioma, tarea y precisión.
- [ ] Liberar recursos cuando no se utilice.
- [ ] Medir duración y errores de transcripción.

### `voice/stt/faster_whisper.py`

- [ ] Implementar transcripción eficiente por segmentos.
- [ ] Configurar dispositivo, tipo de cómputo y VAD.
- [ ] Evitar bloquear el event loop.
- [ ] Manejar modelos no descargados.

### `voice/stt/gemini_stt.py`

- [ ] Convertir audio al formato admitido por Gemini.
- [ ] Aplicar límites de tamaño y duración.
- [ ] Normalizar texto, idioma y errores.
- [ ] Solicitar consentimiento cuando el audio salga del equipo.

### `voice/tts/base.py`

- [ ] Definir contrato para síntesis y streaming.
- [ ] Modelar voz, idioma, velocidad y formato.
- [ ] Permitir cancelación inmediata de reproducción.
- [ ] Normalizar datos y metadatos de audio.

### `voice/tts/piper.py`

- [ ] Detectar binario y modelo de voz.
- [ ] Sintetizar sin bloquear el proceso principal.
- [ ] Gestionar archivos temporales de forma segura.
- [ ] Manejar voces no instaladas.

### `voice/tts/edge_tts.py`

- [ ] Listar y validar voces disponibles.
- [ ] Sintetizar con timeout y manejo de red.
- [ ] Aplicar velocidad, tono y volumen.
- [ ] Normalizar la salida al reproductor.

### `voice/tts/elevenlabs.py`

- [ ] Implementar autenticación y selección de voz.
- [ ] Soportar streaming cuando esté disponible.
- [ ] Controlar cuota, timeout y errores de API.
- [ ] No registrar texto privado sin autorización.

### `voice/tts/gemini_tts.py`

- [ ] Implementar síntesis según capacidades configuradas.
- [ ] Validar voz, idioma y formato de salida.
- [ ] Normalizar errores y uso.
- [ ] Proteger credenciales y contenido sensible.

### `voice/wakeword/base.py`

- [ ] Definir contrato de detección por fragmentos de audio.
- [ ] Modelar sensibilidad, estado y eventos.
- [ ] Permitir pausar durante reproducción TTS.
- [ ] Soportar cierre y reinicio del detector.

### `voice/wakeword/openwakeword.py`

- [ ] Cargar modelos de wake word configurados.
- [ ] Procesar audio en ventanas adecuadas.
- [ ] Aplicar umbral, enfriamiento y reducción de falsos positivos.
- [ ] Medir latencia y consumo.

---

## Visión

### `vision/manager.py`

- [x] Coordinar cámara, pantalla y detectores habilitados.
- [x] Gestionar permisos, frecuencia y ciclo de vida.
- [x] Limitar procesamiento para no saturar CPU o GPU.
- [x] Emitir resultados normalizados y auditables.

### `vision/camera.py`

- [x] Enumerar y seleccionar cámaras.
- [x] Capturar frames con resolución y FPS configurables.
- [x] Liberar el dispositivo ante errores o apagado.
- [x] Informar claramente permisos o cámara ocupada.

### `vision/screen.py`

- [x] Capturar pantalla, monitor, región o ventana.
- [x] Soportar escalado y múltiples monitores.
- [x] Adaptarse a restricciones de Wayland, Windows y macOS.
- [x] Evitar persistir capturas sensibles por defecto.

### `vision/detectors/yolov8.py`

- [x] Cargar el modelo y seleccionar dispositivo.
- [x] Normalizar detecciones, clases, confianza y coordenadas.
- [x] Implementar umbrales y NMS configurables.
- [x] Probar imágenes vacías y modelos ausentes.

### `vision/detectors/clip.py`

- [x] Cargar modelo y preprocesador compatibles.
- [x] Generar embeddings de imagen y texto.
- [x] Normalizar similitudes y lotes.
- [x] Gestionar caché y memoria del dispositivo.

### `vision/detectors/<nuevo_detector>.py`

- [ ] Implementar una interfaz común para futuros detectores.
- [ ] Declarar capacidades, modelos y requisitos.
- [ ] Registrar el detector sin modificar el manager.
- [ ] Añadir pruebas y configuración correspondiente.

---

## Memoria

### `memory/manager.py`

- [ ] Coordinar memoria corta, larga, embeddings y resumen.
- [ ] Aplicar políticas de privacidad y retención.
- [ ] Evitar duplicados y manejar concurrencia.
- [ ] Exponer búsqueda, almacenamiento, olvido y estado.

### `memory/short_term.py`

- [ ] Mantener contexto reciente con límites medibles.
- [ ] Priorizar instrucciones y datos relevantes.
- [ ] Expulsar contenido mediante una estrategia definida.
- [ ] Permitir reiniciar una conversación sin borrar memoria larga.

### `memory/long_term.py`

- [ ] Modelar recuerdos, fuentes, fechas y nivel de confianza.
- [ ] Guardar solo información permitida y útil.
- [ ] Implementar actualización, deduplicación y eliminación.
- [ ] Permitir exportar y borrar datos del usuario.

### `memory/summarizer.py`

- [ ] Resumir conversaciones preservando decisiones y pendientes.
- [ ] Evitar convertir suposiciones en hechos.
- [ ] Registrar procedencia y versión del resumen.
- [ ] Tener fallback cuando el LLM no esté disponible.

### `memory/embeddings.py`

- [ ] Definir interfaz para proveedores de embeddings.
- [ ] Validar dimensión y versión del modelo.
- [ ] Procesar lotes, errores y límites.
- [ ] Evitar mezclar vectores incompatibles.

### `memory/stores/sqlite.py`

- [ ] Definir esquema, índices y migraciones.
- [ ] Usar consultas parametrizadas y transacciones.
- [ ] Configurar WAL, concurrencia y copias de seguridad.
- [ ] Cerrar conexiones correctamente.

### `memory/stores/chroma.py`

- [ ] Crear o abrir colecciones de forma idempotente.
- [ ] Guardar metadatos compatibles y filtrables.
- [ ] Implementar inserción, consulta y eliminación.
- [ ] Validar persistencia y versión del cliente.

### `memory/stores/qdrant.py`

- [ ] Configurar cliente local o remoto.
- [ ] Crear colecciones con dimensión y métrica correctas.
- [ ] Implementar filtros, upsert, búsqueda y borrado.
- [ ] Manejar red, autenticación y reintentos seguros.

### `memory/stores/filesystem.py`

- [ ] Definir formato y organización de archivos.
- [ ] Escribir de forma atómica y evitar colisiones.
- [ ] Validar rutas para impedir traversal.
- [ ] Implementar bloqueo y limpieza.

---

## Infraestructura de herramientas

### `tools/registry.py`

- [ ] Descubrir y registrar herramientas habilitadas.
- [ ] Validar nombres únicos, manifiestos y acciones.
- [ ] Filtrar por plataforma, permisos y configuración.
- [ ] Exponer esquemas compatibles con el LLM.

### `tools/base.py`

- [ ] Definir contrato común de herramientas y acciones.
- [ ] Modelar entrada, resultado, error y contexto de ejecución.
- [ ] Incluir timeout, cancelación y nivel de riesgo.
- [ ] Evitar dependencias directas del orquestador.

### `tools/manifest.py`

- [ ] Crear esquemas para cargar y validar `manifest.yml`.
- [ ] Definir nombre, versión, acciones, permisos y plataformas.
- [ ] Validar referencias a clases y esquemas de entrada.
- [ ] Rechazar campos críticos desconocidos.

### Requisitos comunes de todos los `manifest.yml`

- [ ] Definir identificador único, nombre, versión y descripción.
- [ ] Enumerar acciones con esquema de parámetros y resultado.
- [ ] Declarar permisos, riesgo, confirmación y plataformas.
- [ ] Configurar timeout, idempotencia y capacidad de simulación.
- [ ] Validar el manifiesto durante el arranque.

---

## Herramientas web

### `tools/web/manifest.yml`

- [ ] Declarar `search`, `open_tab`, `close_tab` y futuras acciones.
- [ ] Diferenciar navegación de lectura y acciones con efectos externos.
- [ ] Configurar dominios, permisos y límites.

### `tools/web/actions/search.py`

- [ ] Validar consulta, proveedor y cantidad de resultados.
- [ ] Normalizar título, URL, fragmento y fecha.
- [ ] Aplicar timeout, límites y manejo de red.
- [ ] Filtrar URLs peligrosas o no permitidas.

### `tools/web/actions/open_tab.py`

- [ ] Validar URL y protocolos permitidos.
- [ ] Abrir la pestaña mediante el adaptador disponible.
- [ ] Devolver identificador y estado normalizados.
- [ ] Solicitar confirmación para esquemas o destinos sensibles.

### `tools/web/actions/close_tab.py`

- [ ] Validar el identificador de la pestaña.
- [ ] Evitar cerrar pestañas fuera del contexto autorizado.
- [ ] Manejar pestañas ya cerradas de forma idempotente.
- [ ] Devolver el resultado verificable.

### `tools/web/actions/<nueva_accion>.py`

- [ ] Definir propósito y nivel de riesgo.
- [ ] Implementar entrada y salida tipadas.
- [ ] Añadirla al manifiesto y al registro.
- [ ] Incorporar pruebas de permisos y errores.

---

## Herramientas de teclado

### `tools/keyboard/manifest.yml`

- [ ] Declarar escritura, pulsación y atajos.
- [ ] Marcar escritura automática como acción confirmable según contexto.
- [ ] Definir plataformas y limitaciones de sesión gráfica.

### `tools/keyboard/actions/type_text.py`

- [ ] Validar longitud y contenido del texto.
- [ ] Soportar velocidad de escritura y cancelación.
- [ ] Evitar escribir secretos en ventanas no verificadas.
- [ ] Devolver caracteres enviados y resultado.

### `tools/keyboard/actions/press_key.py`

- [ ] Normalizar nombres y códigos de tecla.
- [ ] Validar compatibilidad con la plataforma.
- [ ] Liberar modificadores incluso después de un error.
- [ ] Limitar repeticiones accidentales.

### `tools/keyboard/actions/shortcut.py`

- [ ] Parsear combinaciones de forma estructurada.
- [ ] Validar modificadores y teclas.
- [ ] Bloquear atajos críticos sin confirmación.
- [ ] Garantizar liberación de todas las teclas.

---

## Herramientas de ratón

### `tools/mouse/manifest.yml`

- [ ] Declarar movimiento, clic y desplazamiento.
- [ ] Definir coordenadas, monitor y botones permitidos.
- [ ] Clasificar dobles clics y clics destructivos.

### `tools/mouse/actions/move.py`

- [ ] Validar coordenadas absolutas o relativas.
- [ ] Considerar escalado y múltiples monitores.
- [ ] Soportar duración y cancelación.
- [ ] Evitar posiciones fuera del área válida.

### `tools/mouse/actions/click.py`

- [ ] Validar botón, cantidad y posición opcional.
- [ ] Aplicar una pausa segura entre clics.
- [ ] Solicitar confirmación en contextos sensibles.
- [ ] Devolver la posición final y el resultado.

### `tools/mouse/actions/scroll.py`

- [ ] Normalizar dirección y magnitud.
- [ ] Limitar desplazamientos extremos.
- [ ] Soportar ejes vertical y horizontal.
- [ ] Comprobar compatibilidad del adaptador.

---

## Herramientas de ventanas

### `tools/window/manifest.yml`

- [ ] Declarar listado, enfoque, cierre y redimensionamiento.
- [ ] Definir identificadores de ventana portables.
- [ ] Marcar `close` como acción con posible pérdida de datos.

### `tools/window/actions/list_windows.py`

- [ ] Listar título, aplicación, identificador y workspace.
- [ ] Filtrar ventanas internas o sensibles cuando corresponda.
- [ ] Normalizar datos entre plataformas.
- [ ] Manejar permisos insuficientes.

### `tools/window/actions/focus.py`

- [ ] Validar que la ventana exista.
- [ ] Activar workspace y ventana cuando sea necesario.
- [ ] Verificar el enfoque después de la acción.
- [ ] Informar restricciones del compositor.

### `tools/window/actions/close.py`

- [ ] Diferenciar cierre normal y terminación forzada.
- [ ] Solicitar confirmación cuando pueda perderse trabajo.
- [ ] Verificar que la ventana haya cerrado.
- [ ] Evitar terminar procesos no autorizados.

### `tools/window/actions/move_resize.py`

- [ ] Validar posición, tamaño y monitor.
- [ ] Respetar dimensiones mínimas y área visible.
- [ ] Considerar escalado y decoraciones.
- [ ] Verificar geometría final.

---

## Herramientas de workspaces

### `tools/workspace/manifest.yml`

- [ ] Declarar listado y cambio de workspace.
- [ ] Definir soporte por escritorio y sistema.
- [ ] Normalizar identificadores y nombres.

### `tools/workspace/actions/switch_workspace.py`

- [ ] Validar destino existente o política de creación.
- [ ] Ejecutar mediante el adaptador del escritorio.
- [ ] Verificar el workspace activo.
- [ ] Manejar escritorios sin esta capacidad.

### `tools/workspace/actions/list_workspaces.py`

- [ ] Listar identificador, nombre, monitor y estado.
- [ ] Marcar workspace activo y especial.
- [ ] Normalizar diferencias entre escritorios.
- [ ] Devolver una lista vacía válida si no hay soporte.

---

## Herramientas de aplicaciones

### `tools/applications/manifest.yml`

- [ ] Declarar apertura, cierre y listado de aplicaciones.
- [ ] Definir alias, identificadores y permisos.
- [ ] Clasificar cierres forzados como acción sensible.

### `tools/applications/actions/open_app.py`

- [ ] Resolver la aplicación sin ejecutar texto como shell.
- [ ] Validar argumentos y archivos asociados.
- [ ] Evitar duplicados cuando se solicite una sola instancia.
- [ ] Devolver PID o identificador verificable.

### `tools/applications/actions/close_app.py`

- [ ] Diferenciar solicitud de cierre y terminación.
- [ ] Validar identidad del proceso.
- [ ] Solicitar confirmación para terminación forzada.
- [ ] Verificar el resultado.

### `tools/applications/actions/list_apps.py`

- [ ] Listar aplicaciones instaladas o en ejecución según el filtro.
- [ ] Normalizar nombre, ID, ruta y estado.
- [ ] Evitar exponer argumentos sensibles de procesos.
- [ ] Manejar fuentes específicas de cada sistema.

---

## Herramientas de archivos

### `tools/files/manifest.yml`

- [ ] Declarar lectura, escritura, movimiento, copia y eliminación.
- [ ] Definir raíces permitidas y límites de tamaño.
- [ ] Marcar sobrescritura y eliminación como acciones sensibles.

### `tools/files/actions/read_file.py`

- [ ] Resolver y validar la ruta real.
- [ ] Limitar tamaño y detectar archivos binarios.
- [ ] Manejar codificación y errores de permisos.
- [ ] Evitar leer rutas fuera del ámbito autorizado.

### `tools/files/actions/write_file.py`

- [ ] Validar ruta, contenido y tamaño.
- [ ] Escribir de forma atómica.
- [ ] Controlar creación, anexado y sobrescritura.
- [ ] Solicitar confirmación antes de reemplazar datos.

### `tools/files/actions/move_file.py`

- [ ] Validar origen y destino.
- [ ] Manejar movimientos entre sistemas de archivos.
- [ ] Definir política de colisiones.
- [ ] Intentar restaurar el estado ante un fallo parcial.

### `tools/files/actions/copy_file.py`

- [ ] Validar origen, destino y espacio disponible.
- [ ] Preservar metadatos solo cuando se solicite.
- [ ] Verificar integridad en copias críticas.
- [ ] Definir política de sobrescritura.

### `tools/files/actions/delete_file.py`

- [ ] Resolver la ruta y bloquear rutas protegidas.
- [ ] Preferir papelera cuando la plataforma lo permita.
- [ ] Requerir confirmación para borrado permanente.
- [ ] Registrar qué se eliminó sin guardar su contenido.

---

## Herramientas de terminal

### `tools/terminal/manifest.yml`

- [ ] Declarar ejecución normal, segundo plano y terminación.
- [ ] Definir comandos, directorios y entornos permitidos.
- [ ] Marcar privilegios, red y cambios destructivos como sensibles.

### `tools/terminal/actions/run_command.py`

- [ ] Ejecutar argumentos sin shell cuando sea posible.
- [ ] Validar comando, directorio y variables de entorno.
- [ ] Aplicar timeout y límites de salida.
- [ ] Capturar stdout, stderr y código de salida por separado.

### `tools/terminal/actions/run_in_background.py`

- [ ] Crear un identificador persistente del trabajo.
- [ ] Capturar estado y logs con límites.
- [ ] Evitar procesos huérfanos.
- [ ] Permitir consulta y cancelación posterior.

### `tools/terminal/actions/kill_process.py`

- [ ] Validar PID e identidad del proceso.
- [ ] Intentar terminación gradual antes de forzar.
- [ ] Proteger procesos críticos y ajenos.
- [ ] Verificar que el proceso haya terminado.

---

## Herramientas de notas

### `tools/notes/manifest.yml`

- [ ] Declarar creación, listado y eliminación de notas.
- [ ] Definir formato, almacenamiento y permisos.
- [ ] Marcar eliminación permanente como confirmable.

### `tools/notes/actions/create_note.py`

- [ ] Validar título, contenido, etiquetas y longitud.
- [ ] Generar identificador único y marcas de tiempo.
- [ ] Evitar duplicados accidentales.
- [ ] Guardar de forma atómica.

### `tools/notes/actions/list_notes.py`

- [ ] Permitir filtros por texto, fecha y etiquetas.
- [ ] Paginar resultados.
- [ ] No devolver contenido completo cuando solo se necesita un resumen.
- [ ] Ordenar de forma determinista.

### `tools/notes/actions/delete_note.py`

- [ ] Validar el identificador.
- [ ] Preferir archivado o papelera.
- [ ] Solicitar confirmación para eliminación permanente.
- [ ] Ser idempotente cuando la nota ya no exista.

---

## Automatización

### `automation/scheduler.py`

- [ ] Programar tareas únicas y recurrentes.
- [ ] Usar zona horaria explícita.
- [ ] Recuperar tareas después de un reinicio.
- [ ] Evitar ejecuciones duplicadas.

### `automation/tasks_queue.py`

- [ ] Implementar cola, prioridad, estado e intentos.
- [ ] Aplicar backoff y límite de reintentos.
- [ ] Soportar cancelación y trabajos idempotentes.
- [ ] Manejar recuperación de tareas bloqueadas.

### `automation/jobs.py`

- [ ] Definir el modelo de trabajo y su ciclo de vida.
- [ ] Validar payload, permisos y ejecutor.
- [ ] Guardar resultados, errores y marcas de tiempo.
- [ ] Versionar el esquema para migraciones.

### `automation/reminders.py`

- [ ] Crear, modificar, listar y cancelar recordatorios.
- [ ] Interpretar fechas con zona horaria.
- [ ] Entregar notificaciones por interfaces disponibles.
- [ ] Evitar avisos duplicados después de reinicios.

---

## Seguridad

### `security/permissions.py`

- [ ] Definir permisos atómicos y roles.
- [ ] Evaluar sujeto, acción, recurso y contexto.
- [ ] Aplicar denegación por defecto.
- [ ] Probar escalamiento y combinaciones de roles.

### `security/policy.py`

- [ ] Cargar y evaluar reglas desde configuración.
- [ ] Resolver conflictos con precedencia explícita.
- [ ] Devolver decisión y motivo auditable.
- [ ] Permitir políticas específicas por plataforma.

### `security/sandbox.py`

- [ ] Definir aislamiento disponible por sistema.
- [ ] Restringir archivos, procesos, red y recursos.
- [ ] Fallar de forma cerrada si el aislamiento requerido no existe.
- [ ] Probar escapes y rutas simbólicas.

### `security/confirmation.py`

- [ ] Generar solicitudes claras con acción, alcance y riesgo.
- [ ] Asociar cada confirmación a una acción exacta y con caducidad.
- [ ] Evitar reutilizar respuestas para acciones diferentes.
- [ ] Soportar aprobación, rechazo y timeout.

### `security/audit.py`

- [ ] Registrar actor, acción, decisión, resultado y fecha.
- [ ] Redactar secretos y datos sensibles.
- [ ] Proteger integridad y rotación de registros.
- [ ] Permitir consultas y exportación controlada.

---

## Interfaces

### `interfaces/voice_controller.py`

- [ ] Conectar eventos de voz con el asistente.
- [ ] Coordinar escucha, procesamiento, habla e interrupción.
- [ ] Evitar solapamiento de audio.
- [ ] Exponer estados y errores a otras interfaces.

### `interfaces/web_ui/hud.html`

- [ ] Crear panel accesible de chat, estado y actividad.
- [ ] Incluir estados vacío, conectado, procesando y error.
- [ ] Mantener diseño adaptable a escritorio y móvil.
- [ ] Evitar insertar contenido del modelo como HTML sin sanitizar.

### `interfaces/web_ui/hud.js`

- [ ] Conectar mediante WebSocket y HTTP.
- [ ] Implementar reconexión con backoff.
- [ ] Renderizar mensajes y eventos de forma segura.
- [ ] Gestionar envío, cancelación y errores.

### `interfaces/web_ui/config.html`

- [ ] Crear formularios por sección de configuración.
- [ ] Mostrar validación, valores heredados y cambios pendientes.
- [ ] Ocultar secretos y permitir reemplazarlos sin revelarlos.
- [ ] Incluir estados de guardado y error.

### `interfaces/web_ui/config.js`

- [ ] Cargar y guardar configuración mediante la API.
- [ ] Validar antes de enviar.
- [ ] No conservar secretos en almacenamiento del navegador.
- [ ] Avisar cuándo un cambio requiere reinicio.

### `interfaces/web_ui/assets/`

- [ ] Añadir iconos, imágenes, fuentes o sonidos realmente utilizados.
- [ ] Optimizar tamaños y formatos.
- [ ] Mantener licencias y atribuciones.
- [ ] Eliminar recursos huérfanos.

---

## Runtime y daemon

### `runtime/daemon.py`

- [ ] Orquestar API, scheduler, voz, eventos y asistente.
- [ ] Iniciar componentes en orden y comprobar disponibilidad.
- [ ] Gestionar fallos parciales y estado degradado.
- [ ] Ejecutar apagado controlado.

### `runtime/health.py`

- [ ] Implementar `/healthz` para vida y disponibilidad.
- [ ] Comprobar componentes críticos sin operaciones costosas.
- [ ] Devolver estado estructurado y códigos HTTP correctos.
- [ ] No revelar secretos ni detalles internos sensibles.

### `runtime/instance_lock.py`

- [ ] Impedir múltiples instancias sobre el mismo perfil.
- [ ] Guardar PID e identidad de proceso de forma segura.
- [ ] Detectar y limpiar locks obsoletos.
- [ ] Funcionar en los tres sistemas soportados.

### `runtime/signals.py`

- [ ] Capturar SIGINT y SIGTERM donde existan.
- [ ] Traducir señales a cancelación coordinada.
- [ ] Evitar registrar handlers incompatibles.
- [ ] Mantener handlers pequeños y no bloqueantes.

### `runtime/shutdown.py`

- [ ] Cerrar entradas y dejar de aceptar tareas.
- [ ] Cancelar o finalizar trabajos según política.
- [ ] Cerrar audio, cámara, red, bases y logs.
- [ ] Aplicar timeout global y registrar recursos pendientes.

### `runtime/paths.py`

- [ ] Resolver rutas de configuración, datos, caché y logs por OS.
- [ ] Permitir overrides explícitos.
- [ ] Crear directorios con permisos apropiados.
- [ ] Evitar depender del directorio actual.

---

## Gestión de servicios

### `services/manager.py`

- [ ] Detectar el gestor de servicios disponible.
- [ ] Exponer instalación, inicio, parada, reinicio, estado y logs.
- [ ] Validar privilegios antes de ejecutar.
- [ ] Normalizar resultados entre plataformas.

### `services/base.py`

- [ ] Definir la interfaz común del gestor.
- [ ] Modelar estados y resultados.
- [ ] Declarar capacidades opcionales.
- [ ] Facilitar implementaciones falsas para pruebas.

### `services/systemd.py`

- [ ] Instalar la unidad en la ubicación correcta.
- [ ] Ejecutar `daemon-reload` cuando corresponda.
- [ ] Implementar start, stop, restart, status y logs.
- [ ] Soportar servicio de usuario y del sistema según configuración.

### `services/windows_service.py`

- [ ] Instalar y eliminar el servicio de Windows.
- [ ] Implementar control y consulta de estado.
- [ ] Configurar cuenta, recuperación y logs.
- [ ] Manejar privilegios administrativos.

### `services/launchd.py`

- [ ] Instalar el plist en la ubicación adecuada.
- [ ] Implementar carga, descarga, reinicio y estado.
- [ ] Diferenciar LaunchAgent y LaunchDaemon.
- [ ] Validar el plist antes de activarlo.

---

## CLI

### `cli/main.py`

- [ ] Crear el grupo principal de comandos.
- [ ] Configurar salida, nivel de detalle y códigos de error.
- [ ] Cargar solo dependencias necesarias por comando.
- [ ] Mostrar ayuda útil y consistente.

### `cli/commands/run.py`

- [ ] Ejecutar el asistente en primer plano.
- [ ] Permitir overrides de host, puerto e interfaz.
- [ ] Mostrar errores de arranque legibles.
- [ ] Propagar interrupciones al ciclo de apagado.

### `cli/commands/start.py`

- [ ] Iniciar el servicio mediante `services/manager.py`.
- [ ] Detectar si ya está activo.
- [ ] Informar el estado final.
- [ ] Manejar privilegios insuficientes.

### `cli/commands/stop.py`

- [ ] Solicitar detención controlada.
- [ ] Esperar con timeout configurable.
- [ ] Evitar éxito falso si el servicio sigue activo.
- [ ] Ofrecer forzado solo con confirmación.

### `cli/commands/restart.py`

- [ ] Encadenar parada e inicio con verificación.
- [ ] Conservar errores de ambas fases.
- [ ] Esperar disponibilidad después del arranque.
- [ ] Evitar reinicios concurrentes.

### `cli/commands/status.py`

- [ ] Mostrar estado del servicio y health check.
- [ ] Incluir PID, duración y componentes relevantes.
- [ ] Soportar salida humana y JSON.
- [ ] Diferenciar detenido, iniciando, activo y degradado.

### `cli/commands/install.py`

- [ ] Detectar plataforma y gestor de servicios.
- [ ] Generar o copiar archivos con rutas correctas.
- [ ] Validar configuración antes de instalar.
- [ ] Soportar reinstalación idempotente.

### `cli/commands/logs.py`

- [ ] Mostrar logs recientes o en seguimiento.
- [ ] Permitir filtros por nivel y componente.
- [ ] Limitar volumen y redactar secretos.
- [ ] Adaptarse al gestor de servicios.

---

## Empaquetado por sistema

### `packaging/systemd/rbot.service`

- [ ] Definir `Type=simple`, usuario, directorio y `ExecStart`.
- [ ] Configurar reinicio, variables y dependencias.
- [ ] Aplicar endurecimiento compatible con las funciones requeridas.
- [ ] Enviar logs al destino configurado.
- [ ] Eliminar cualquier texto residual como `contentReference`.

### `packaging/windows/service.xml`

- [ ] Definir identificador, nombre, ejecutable y argumentos.
- [ ] Configurar logs, reinicio y directorio de trabajo.
- [ ] Referenciar rutas instaladas, no rutas de desarrollo.
- [ ] Validar con el wrapper de servicio elegido.

### `packaging/macos/com.rbot.assistant.plist`

- [ ] Definir `Label`, argumentos, directorio y entorno.
- [ ] Configurar `RunAtLoad`, `KeepAlive` y logs.
- [ ] Usar rutas válidas para el tipo de servicio.
- [ ] Validar sintaxis antes de instalar.

---

## Datos y almacenamiento

### `data/runtime/host-profile.json`

- [ ] Generarlo automáticamente; no editarlo manualmente.
- [ ] Validarlo contra el esquema de `host/profile.py`.
- [ ] Escribirlo de forma atómica.
- [ ] Excluir datos identificables que no sean necesarios.

### `data/db/`

- [ ] Guardar bases locales y migraciones aplicadas.
- [ ] Ignorar archivos de datos en Git.
- [ ] Añadir política de backup, restauración y corrupción.
- [ ] Aplicar permisos restrictivos.

### `data/logs/`

- [ ] Configurar rotación, retención y tamaño máximo.
- [ ] Separar logs generales y auditoría cuando corresponda.
- [ ] Redactar secretos.
- [ ] Mantener un `.gitkeep` si se necesita conservar la carpeta.

### `data/memories/`

- [ ] Separar datos por usuario o perfil.
- [ ] Implementar exportación y eliminación.
- [ ] Proteger datos sensibles en reposo.
- [ ] Ignorar el contenido en Git.

### `data/models/`

- [ ] Organizar modelos por proveedor, nombre y versión.
- [ ] Guardar metadatos, licencia y checksum.
- [ ] Verificar integridad antes de cargar.
- [ ] Evitar versionar archivos pesados.

### `data/cache/`

- [ ] Definir claves, expiración y límites de tamaño.
- [ ] Permitir limpieza sin perder datos esenciales.
- [ ] Manejar escrituras interrumpidas.
- [ ] Ignorar el contenido en Git.

---

## Scripts

### `scripts/install.sh`

- [ ] Usar modo estricto y manejo claro de errores.
- [ ] Detectar sistema sin modificarlo antes de confirmar.
- [ ] Instalar dependencias y archivos de servicio de forma idempotente.
- [ ] Actualizar `platforms.yml` mediante una herramienta estructurada.
- [ ] Proporcionar opción de simulación y desinstalación documentada.

### `scripts/install.py`

- [ ] Ofrecer alternativa portable al instalador shell.
- [ ] Reutilizar detector y gestor de servicios.
- [ ] Validar versión de Python y dependencias.
- [ ] Implementar rollback de pasos críticos.

### `scripts/detect_system.py`

- [ ] Ejecutar `host/detector.py` desde línea de comandos.
- [ ] Mostrar salida humana y JSON.
- [ ] No cambiar el sistema.
- [ ] Usar códigos de salida coherentes.

### `scripts/dev.py`

- [ ] Preparar servicios y configuración de desarrollo.
- [ ] Iniciar componentes con recarga cuando corresponda.
- [ ] Verificar puertos y dependencias.
- [ ] Cerrar procesos hijos al terminar.

### `scripts/seed.py`

- [ ] Crear datos iniciales mínimos y no sensibles.
- [ ] Ser idempotente.
- [ ] Permitir seleccionar entorno o conjunto de datos.
- [ ] Impedir ejecución accidental en producción.

---

## Pruebas

### `tests/test_core.py`

- [ ] Probar planificación, ejecución, estados y contexto.
- [ ] Cubrir respuestas directas, uso de herramientas y replanificación.
- [ ] Simular errores, timeout y cancelación.
- [ ] Verificar límites de iteraciones.

### `tests/test_host.py`

- [ ] Probar detección con fixtures de cada plataforma.
- [ ] Probar registro y selección de adaptadores.
- [ ] Cubrir plataformas incompletas o no soportadas.
- [ ] No depender del sistema real de CI.

### `tests/test_llm.py`

- [ ] Probar normalización de mensajes y respuestas.
- [ ] Simular streaming, límites, timeout y fallback.
- [ ] Verificar selección por capacidades.
- [ ] Evitar llamadas reales en pruebas unitarias.

### `tests/test_tools.py`

- [ ] Validar todos los manifiestos.
- [ ] Probar registro, permisos y confirmaciones.
- [ ] Cubrir entradas inválidas y acciones no soportadas.
- [ ] Ejecutar acciones destructivas solo sobre recursos temporales.

### `tests/test_memory.py`

- [ ] Probar memoria corta, resumen y deduplicación.
- [ ] Probar cada store con contrato compartido.
- [ ] Verificar borrado, privacidad y migraciones.
- [ ] Cubrir embeddings incompatibles.

### `tests/test_vision.py`

- [ ] Probar cámara y pantalla mediante mocks o archivos de muestra.
- [ ] Validar formato de detecciones.
- [ ] Cubrir modelo ausente y dispositivo no disponible.
- [ ] Marcar pruebas de GPU como opcionales.

### `tests/test_runtime.py`

- [ ] Probar arranque y apagado completos.
- [ ] Verificar `/healthz` en estados sano y degradado.
- [ ] Probar instance lock y señales.
- [ ] Confirmar que no queden tareas ni recursos abiertos.

---

## Archivos adicionales recomendados

### `LICENSE`

- [ ] Elegir una licencia compatible con dependencias y objetivos.
- [ ] Añadir el texto completo y el año correcto.
- [ ] Referenciarla desde `README.md` y `pyproject.toml`.

### `CHANGELOG.md`

- [ ] Registrar cambios por versión.
- [ ] Separar añadidos, cambios, correcciones y seguridad.
- [ ] Mantener una sección de cambios no publicados.

### `CONTRIBUTING.md`

- [ ] Documentar entorno, estilo, pruebas y flujo de contribución.
- [ ] Explicar cómo añadir proveedores, herramientas y adaptadores.
- [ ] Incluir requisitos de seguridad y revisión.

### `SECURITY.md`

- [ ] Explicar cómo reportar vulnerabilidades de forma privada.
- [ ] Indicar versiones soportadas y tiempos esperados de respuesta.
- [ ] No pedir que vulnerabilidades activas se publiquen como issues.

### `docs/architecture.md`

- [ ] Documentar componentes, dependencias y límites.
- [ ] Incluir diagramas de arranque, interacción y ejecución de herramientas.
- [ ] Registrar decisiones arquitectónicas importantes.

### `docs/tool-development.md`

- [ ] Explicar contrato, manifiesto, permisos y pruebas de una herramienta.
- [ ] Incluir una herramienta mínima de ejemplo.
- [ ] Documentar versionado y compatibilidad.

### `docs/platform-support.md`

- [ ] Mantener una matriz de funciones por OS y escritorio.
- [ ] Registrar limitaciones conocidas de Wayland y permisos del sistema.
- [ ] Indicar cómo validar un nuevo adaptador.

### `.pre-commit-config.yaml`

- [ ] Ejecutar formato, lint y comprobaciones básicas antes de guardar cambios.
- [ ] Detectar secretos y archivos excesivamente grandes.
- [ ] Mantener versiones de hooks actualizadas.

### `Dockerfile`

- [ ] Crear una imagen mínima para componentes compatibles.
- [ ] Ejecutar con usuario no root.
- [ ] Separar construcción y ejecución.
- [ ] No incluir secretos ni datos locales.

### `docker-compose.yml`

- [ ] Levantar solo dependencias de desarrollo necesarias.
- [ ] Configurar health checks, volúmenes y redes.
- [ ] Usar variables de entorno seguras.
- [ ] Evitar publicar servicios innecesariamente.

---

## Criterios de finalización por módulo

Un módulo puede considerarse completado cuando:

- [ ] Todos sus archivos principales están implementados.
- [ ] Sus configuraciones son validadas por esquemas.
- [ ] Sus errores se traducen al contrato común.
- [ ] Sus recursos se cierran durante cancelación y apagado.
- [ ] Sus acciones sensibles pasan por permisos y confirmación.
- [ ] Cuenta con pruebas unitarias y, cuando corresponde, de integración.
- [ ] Está documentado en la matriz de capacidades.
- [ ] Funciona sin obligar a instalar proveedores opcionales deshabilitados.

## Orden recomendado de implementación

- [ ] **Fase 1:** raíz, configuración, `app/`, `runtime/` y logging.
- [ ] **Fase 2:** contratos de `llm/`, `tools/`, `memory/` y `security/`.
- [ ] **Fase 3:** un proveedor LLM local y uno remoto.
- [ ] **Fase 4:** herramientas no destructivas: notas, lectura y listado.
- [ ] **Fase 5:** permisos, confirmaciones, auditoría y sandbox.
- [ ] **Fase 6:** herramientas de escritorio y adaptadores Linux.
- [ ] **Fase 7:** voz, visión y memoria vectorial.
- [ ] **Fase 8:** automatización, Web UI y servicio permanente.
- [ ] **Fase 9:** Windows, macOS, empaquetado e instaladores.
- [ ] **Fase 10:** pruebas end-to-end, endurecimiento y documentación final.

## Validación final del proyecto

- [ ] La instalación parte de un entorno limpio.
- [ ] El asistente arranca, responde y se apaga sin errores.
- [ ] Una dependencia opcional ausente no impide iniciar módulos no relacionados.
- [ ] Las acciones destructivas siempre requieren la política adecuada.
- [ ] Los secretos no aparecen en logs, errores, prompts ni auditorías.
- [ ] Las rutas funcionan fuera del directorio del repositorio.
- [ ] El daemon evita instancias duplicadas.
- [ ] Los datos del usuario se pueden exportar y eliminar.
- [ ] Las pruebas pasan en los sistemas declarados como compatibles.
- [ ] La documentación coincide con el comportamiento implementado.
