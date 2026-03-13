#!/usr/bin/env python3
"""
  ██████╗██╗  ██╗ █████╗ ████████╗
 ██╔════╝██║  ██║██╔══██╗╚══██╔══╝
 ██║     ███████║███████║   ██║   
 ██║     ██╔══██║██╔══██║   ██║   
 ╚██████╗██║  ██║██║  ██║   ██║   
  ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝  
  terminal chatbot via groq
"""

import os
import sys
import json
import urllib.request
import urllib.error

# ── Load .env if present ──────────────────────────────────────────────────────
_env = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(_env):
    with open(_env) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip("\r"))

# ── ANSI colors ───────────────────────────────────────────────────────────────
GREEN   = "\033[32m"
CYAN    = "\033[36m"
RED     = "\033[31m"
YELLOW  = "\033[33m"
DIM     = "\033[2m"
BOLD    = "\033[1m"
RESET   = "\033[0m"

# ── Config ────────────────────────────────────────────────────────────────────
API_URL  = "https://api.groq.com/openai/v1/chat/completions"
MODEL    = os.getenv("CHAT_MODEL", "llama-3.1-8b-instant")
API_KEY  = os.getenv("GROQ_API_KEY", "")

SYSTEM_PROMPT = os.getenv(
    "CHAT_SYSTEM",
    "You are a sharp, concise assistant. No fluff. Answer directly."
)

# ── Helpers ───────────────────────────────────────────────────────────────────
def banner():
    print(f"{GREEN}{__doc__}{RESET}")
    print(f"{DIM}  model : {MODEL}")
    print(f"  type  : /help for commands, Ctrl+C to quit{RESET}\n")

def help_text():
    print(f"""
{YELLOW}commands:{RESET}
  /help        show this message
  /clear       clear conversation history
  /model       show current model
  /models      list available models
  /quit        exit
""")

def free_models():
    print(f"""
{YELLOW}groq free models:{RESET}
  llama-3.1-8b-instant     (default, very fast)
  llama-3.3-70b-versatile  (smarter, still fast)
  llama-3.1-70b-versatile  (solid all-rounder)
  mixtral-8x7b-32768       (long context)
  gemma2-9b-it             (google gemma)

{DIM}set with CHAT_MODEL=<model-name> in .env{RESET}
""")

def stream_response(messages: list) -> str:
    """Send request and stream the response token by token."""
    if not API_KEY:
        print(f"{RED}error: GROQ_API_KEY not set.{RESET}")
        print(f"{DIM}  get a free key at console.groq.com{RESET}\n")
        return ""

    payload = json.dumps({
        "model": MODEL,
        "messages": messages,
        "stream": True,
    }).encode()

    req = urllib.request.Request(
        API_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (compatible; chat-cli/1.0)",
        },
        method="POST",
    )

    full_reply = ""
    print(f"\n{BOLD}{CYAN}ai{RESET} {DIM}>{RESET} ", end="", flush=True)

    try:
        with urllib.request.urlopen(req) as resp:
            for raw_line in resp:
                line = raw_line.decode("utf-8").strip()
                if not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if data == "[DONE]":
                    break
                try:
                    chunk = json.loads(data)
                    delta = chunk["choices"][0]["delta"].get("content", "")
                    if delta:
                        print(f"{BOLD}{delta}{RESET}", end="", flush=True)
                        full_reply += delta
                except (json.JSONDecodeError, KeyError, IndexError):
                    continue

    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"\n{RED}http error {e.code}: {body}{RESET}")
    except urllib.error.URLError as e:
        print(f"\n{RED}connection error: {e.reason}{RESET}")

    print()
    return full_reply

# ── Main loop ─────────────────────────────────────────────────────────────────
def main():
    banner()

    history = [{"role": "system", "content": SYSTEM_PROMPT}]

    while True:
        try:
            user_input = input(f"\n{BOLD}{GREEN}you{RESET} {DIM}>{RESET} ").strip()
        except (KeyboardInterrupt, EOFError):
            print(f"\n{DIM}bye.{RESET}")
            sys.exit(0)

        if not user_input:
            continue

        if user_input.startswith("/"):
            cmd = user_input.lower()
            if cmd in ("/quit", "/exit", "/q"):
                print(f"{DIM}bye.{RESET}")
                sys.exit(0)
            elif cmd == "/help":
                help_text()
            elif cmd == "/clear":
                history = [{"role": "system", "content": SYSTEM_PROMPT}]
                print(f"{DIM}history cleared.{RESET}\n")
            elif cmd == "/model":
                print(f"{DIM}model: {MODEL}{RESET}\n")
            elif cmd == "/models":
                free_models()
            else:
                print(f"{RED}unknown command. type /help{RESET}\n")
            continue

        history.append({"role": "user", "content": user_input})
        reply = stream_response(history)
        if reply:
            history.append({"role": "assistant", "content": reply})
        print()

if __name__ == "__main__":
    main()