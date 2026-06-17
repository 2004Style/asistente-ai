#!/usr/bin/env python3
"""
Seeds the database or memory with initial data for testing.
"""
import os
import sys
import sqlite3
import json
from pathlib import Path

# Add root folder to sys.path
root = Path(__file__).parent.parent.parent.resolve()
sys.path.insert(0, str(root))

def main():
    print("Seeding database and notes...")
    
    notes_dir = root / "data" / "notes"
    notes_dir.mkdir(parents=True, exist_ok=True)
    
    notes = {
        "todo.md": "# Tareas Pendientes\n- [x] Configurar entorno virtual\n- [ ] Probar el asistente en Hyprland\n- [ ] Añadir soporte para voz offline",
        "ideas.md": "# Ideas para RBot\n1. Añadir recordatorios basados en la geolocalización.\n2. Crear una extensión de Chrome para enviar texto directamente."
    }
    
    for filename, content in notes.items():
        note_path = notes_dir / filename
        with open(note_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Created note: {filename}")
        
    db_dir = root / "data" / "db"
    db_dir.mkdir(parents=True, exist_ok=True)
    db_path = db_dir / "assistant.db"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            tool_calls TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            metadata TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vector_store_items (
            id TEXT PRIMARY KEY,
            vector TEXT NOT NULL,
            text TEXT NOT NULL,
            metadata TEXT
        )
    """)
    
    memories = [
        ("El usuario prefiere el editor de texto Neovim para programar en Python.", {"category": "preferences"}),
        ("La clave API de desarrollo se almacena en el archivo .env de forma local.", {"category": "security"}),
        ("RBot es un asistente de escritorio modular y seguro.", {"category": "general"})
    ]
    
    cursor.execute("DELETE FROM memories")
    for content, meta in memories:
        cursor.execute(
            "INSERT INTO memories (content, metadata) VALUES (?, ?)",
            (content, json.dumps(meta))
        )
        doc_id = str(cursor.lastrowid)
        
        val = hash(content)
        vector = []
        for _ in range(1536):
            val = (val * 1103515245 + 12345) & 0x7fffffff
            vector.append(float(val) / float(0x7fffffff) * 2.0 - 1.0)
        cursor.execute(
            "INSERT OR REPLACE INTO vector_store_items (id, vector, text, metadata) VALUES (?, ?, ?, ?)",
            (doc_id, json.dumps(vector), content, json.dumps(meta))
        )
        
    messages = [
        ("default", "user", "Hola, quién eres?", None),
        ("default", "assistant", "Hola! Soy rbot, tu asistente personal de escritorio. ¿En qué te puedo ayudar hoy?", None)
    ]
    
    cursor.execute("DELETE FROM messages")
    for sess_id, role, content, tc in messages:
        cursor.execute(
            "INSERT INTO messages (session_id, role, content, tool_calls) VALUES (?, ?, ?, ?)",
            (sess_id, role, content, tc)
        )
        
    conn.commit()
    conn.close()
    
    print("Database seeding completed successfully.")

if __name__ == "__main__":
    main()
