# ── LEVI: paste this into ONE cell, then Shift+Enter ──────────────────────
import os, subprocess, sys, time

def sh(c, out=False):
    r = subprocess.run(c, shell=True, capture_output=True, text=True)
    return r.stdout.strip() if out else r

# 1. hardware check — stops here if no GPU
print("cores:", os.cpu_count(), "| ram:", sh("free -g|awk '/Mem:/{print $2}'", True), "GB")
gpu = sh("nvidia-smi --query-gpu=name,memory.total --format=csv,noheader", True)
print("GPU:", gpu or "NONE")
if not gpu:
    sys.exit("STOP: no GPU. Right sidebar -> Session options -> Accelerator -> GPU T4 x2")

# 2. secrets (ignore if you haven't added them yet)
try:
    from kaggle_secrets import UserSecretsClient
    _u = UserSecretsClient()
    for _k in ("GITHUB_TOKEN", "LEVI_SYNC_REPO", "GROQ_API_KEY"):
        try: os.environ[_k] = _u.get_secret(_k)
        except Exception: pass
except Exception: pass
print("GITHUB_TOKEN:", "set" if os.environ.get("GITHUB_TOKEN") else "MISSING")

# 3. install + serve ollama
if not os.path.exists("/usr/local/bin/ollama"):
    print(sh("curl -fsSL https://ollama.com/install.sh | sh", True)[-400:])
os.environ["OLLAMA_MODELS"] = "/kaggle/working/.ollama"
subprocess.Popen("nohup ollama serve > /kaggle/working/ollama.log 2>&1 &", shell=True)
for i in range(40):
    time.sleep(1)
    if sh("curl -s --max-time 2 http://127.0.0.1:11434/api/tags").returncode == 0:
        print("server up in", i + 1, "s"); break
else:
    sys.exit("ollama did not start — see /kaggle/working/ollama.log")

# 4. model
MODEL = "qwen3:8b"
print(sh(f"ollama pull {MODEL}", True)[-300:])

# 5. speed test — the number that decides everything
t0, out = time.time(), sh(
    f"""curl -s http://127.0.0.1:11434/v1/chat/completions -H 'Content-Type: application/json' """
    f"""-d '{{"model":"{MODEL}","messages":[{{"role":"user","content":"List five things to check when reversing a C++ game engine."}}],"max_tokens":300}}'""", True)
el = time.time() - t0
import json
try:
    n = json.loads(out)["usage"]["completion_tokens"]
    print(f"\n>>> {n} tokens in {el:.1f}s = {n/el:.1f} tok/s")
    print(f">>> 4.6M-token corpus would take ~{4600000/max(n/el,0.1)/3600:.1f} hours of generation")
except Exception:
    print(out[:400])

print("\nDone. Next: attach your zip as a Dataset, then re-run cells 6-8 of")
print("the notebook at github.com/AmbitiousBoyII14/levi-kit")
