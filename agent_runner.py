import requests
import json
import os

OLLAMA_URL = "http://localhost:11434/api/generate"
RESTORE_API_URL = "http://127.0.0.1:8001/api/v1/execute-transactional-tool"

def query_ollama(prompt: str, model: str = "llama3") -> str:
    """Sends a prompt to the local Ollama instance."""
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=30)
        response.raise_for_status()
        return response.json().get("response", "")
    except Exception as e:
        return f"Error connecting to Ollama: {str(e)}"

def run_agent_workflow():
    target_file = "sample.txt"
    
    # Initialize a secure starting state
    with open(target_file, "w") as f:
        f.write("INITIAL_BASE_CONFIG_v1")

    print(f"[*] Initialized target file '{target_file}' with content: {open(target_file).read()}")
    print("[*] Prompting local Ollama model to execute a transactional tool call...")

    # Define a tool execution payload simulating an agent action
    # We will test a normal successful write first, then a failing one to show self-correction.
    
    test_payloads = [
        {
            "tool_name": "file_editor",
            "arguments": {"write_data": "UPDATED_CONFIG_v2", "file_path": target_file},
            "target_path": target_file,
            "description": "Standard update workflow"
        },
        {
            "tool_name": "file_editor",
            "arguments": {"command": "fail", "file_path": target_file},
            "target_path": target_file,
            "description": "Simulated failure workflow triggering rollback"
        }
    ]

    for i, payload in enumerate(test_payloads, 1):
        print(f"\n--- Running Agent Step {i}: {payload['description']} ---")
        
        # Ask Ollama to review the intent before firing
        ollama_prompt = f"An AI agent is about to execute tool '{payload['tool_name']}' with arguments {payload['arguments']}. Provide a 1-sentence safety validation commentary."
        commentary = query_ollama(ollama_prompt)
        print(f"[Ollama Safety Check]: {commentary.strip()}")

        # Execute through ResilientRestore middleware API
        try:
            response = requests.post(RESTORE_API_URL, json={
                "tool_name": payload["tool_name"],
                "arguments": payload["arguments"],
                "target_path": payload["target_path"]
            })
            
            result = response.json()
            if response.status_code == 200:
                print(f"[ResilientRestore Status]: COMMITTED 🟢 (Tx ID: {result.get('transaction_id')})")
                print(f"[File Current Content]: {open(target_file).read()}")
            else:
                print(f"[ResilientRestore Status]: ROLLED BACK 🔴 (Tx ID: {result.get('detail', {}).get('transaction_id')})")
                print(f"[Error Reason]: {result.get('detail', {}).get('reason')}")
                print(f"[File Restored Content]: {open(target_file).read()}")
                
                # Self-healing feedback loop simulation with Ollama
                print("\n[Self-Healing Loop]: Asking Ollama to analyze failure and suggest corrective action...")
                fix_prompt = f"The tool execution failed with error: {result.get('detail', {}).get('reason')}. Suggest a corrected argument payload to safely achieve the objective."
                fix_suggestion = query_ollama(fix_prompt)
                print(f"[Ollama Remediation Advice]:\n{fix_suggestion.strip()}")

        except requests.exceptions.ConnectionError:
            print("[Error]: Could not connect to ResilientRestore server. Make sure `python server.py` is running on port 8001!")
            break

if __name__ == "__main__":
    run_agent_workflow()