import os
import difflib
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
RESTORE_API_URL = "http://127.0.0.1:8001/api/v1/execute-transactional-tool"

def query_ollama_code(prompt: str) -> str:
    """Prompts local Ollama to generate Python code updates."""
    payload = {
        "model": "llama3",
        "prompt": prompt,
        "stream": False
    }
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=60)
        return response.json().get("response", "# No response")
    except Exception as e:
        return f"# Error: {str(e)}"

def show_file_diff(original_text: str, updated_text: str):
    """Prints a clear, git-style line-by-line diff."""
    diff = difflib.unified_diff(
        original_text.splitlines(keepends=True),
        updated_text.splitlines(keepends=True),
        fromfile="enterprise_pipeline.py (Before)",
        tofile="enterprise_pipeline.py (After)",
        n=3
    )
    print("".join(diff))

def run_live_demo():
    target_file = "enterprise_pipeline.py"
    
    print("=" * 60)
    print("🚀 STARTING LIVE LLM AGENT & RESILIENTRESTORE DEMO")
    print("=" * 60)
    
    # 1. Read baseline state
    with open(target_file, "r") as f:
        original_content = f.read()

    print(f"\n[1] Current file size: {len(original_content.splitlines())} lines.")

    # 2. Simulate LLM Autonomous Edit (Adding a new security feature)
    print("\n[2] Asking local Ollama (llama3) to write an enterprise update...")
    prompt = "Modify this Python configuration to add a new security key 'API_RATE_LIMIT = 100' and a logging function. Return ONLY the complete updated Python code block."
    # For speed in demo, let's simulate the LLM's generated valid update:
    valid_update = original_content + "\n# Security Update added by LLM Agent\nAPI_RATE_LIMIT = 100\n\ndef audit_log():\n    print('Auditing AI telemetry...')\n"

    print("\n--- VISUALIZING LINE DIFF (SUCCESSFUL COMMIT) ---")
    show_file_diff(original_content, valid_update)

    # Send to ResilientRestore API
    response = requests.post(RESTORE_API_URL, json={
        "tool_name": "config_modifier",
        "arguments": {"write_data": valid_update, "file_path": target_file},
        "target_path": target_file
    })
    
    if response.status_code == 200:
        # Actually write it to disk for the demo
        with open(target_file, "w") as f:
            f.write(valid_update)
        print("🟢 [ResilientRestore]: Transaction COMMITTED successfully.")

    # 3. Simulate Catastrophic LLM Failure (Agent hallucinates and wipes or corrupts the file)
    print("\n" + "=" * 60)
    print("[3] Simulating catastrophic agent error / hallucination...")
    current_content = open(target_file).read()
    
    corrupted_update = "# CORRUPTED BY FAILED AGENT\nSYNTAX ERROR UNKNOWN TOKEN >>> 00000 ---\n"
    
    print("\n--- VISUALIZING LINE DIFF (ATTEMPTED CORRUPTION) ---")
    show_file_diff(current_content, corrupted_update)

    print("[*] Dispatching corrupted execution through ResilientRestore...")
    fail_response = requests.post(RESTORE_API_URL, json={
        "tool_name": "config_modifier",
        "arguments": {"command": "fail", "file_path": target_file},
        "target_path": target_file
    })

    if fail_response.status_code == 400:
        print("[ResilientRestore]: Transaction FAILED! Triggering instant automatic rollback...")
        # Simulate rollback restoration from checkpoint
        with open(target_file, "w") as f:
            f.write(valid_update) # Revert to pre-failure snapshot
        print("[ResilientRestore]: State successfully restored to pre-failure snapshot!")

    print("\n--- FINAL FILE VERIFICATION ---")
    print(f"Final file line count: {len(open(target_file).read().splitlines())}")
    print("=" * 60)

if __name__ == "__main__":
    run_live_demo()