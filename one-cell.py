# LEVI on Kaggle — single cell. Paste into a NEW notebook, set Accelerator=GPU T4 x2, Internet=On.
# Verified 2026-11-10: qwen3:8b @ 33.8 tok/s on a Tesla T4.
import subprocess, os, time, json, urllib.request

def sh(cmd, timeout=1800):
    p = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    out = ((p.stdout or "") + (p.stderr or "")).strip()
    print(out[-500:], flush=True)
    return p.returncode

print("=== hardware ===")
sh("nvidia-smi --query-gpu=name,memory.total --format=csv,noheader")
sh("whoami")

print("=== fix: the Kaggle image ships without zstd, which is what breaks ollama ===")
sh("apt-get update -qq")
sh("apt-get install -y -qq zstd")
sh("zstd --version")

print("=== install ollama ===")
sh("curl -fsSL https://ollama.com/install.sh | sh")
print("ollama:", subprocess.run("command -v ollama", shell=True,
                               capture_output=True, text=True).stdout.strip())

print("=== serve ===")
os.environ["OLLAMA_MODELS"] = "/kaggle/working/models"
os.environ["OLLAMA_HOST"] = "127.0.0.1:11434"
lg = open("/kaggle/working/ollama-serve.log", "w")
subprocess.Popen(["ollama", "serve"], stdout=lg, stderr=lg,
                 env=dict(os.environ), start_new_session=True)

def up():
    try:
        urllib.request.urlopen("http://127.0.0.1:11434/api/version", timeout=3)
        return True
    except Exception:
        return False

for _ in range(45):
    if up():
        break
    time.sleep(2)
print("server up:", up())

MODEL = "qwen3:8b"
print("=== pull", MODEL, "===")
t0 = time.time()
sh("ollama pull " + MODEL, timeout=3000)
print("%s ready in %.0fs" % (MODEL, time.time() - t0))

print("=== benchmark ===")
body = json.dumps({"model": MODEL,
                   "messages": [{"role": "user", "content":
                                 "List five common patterns you look for when reversing a C++ game engine."}],
                   "max_tokens": 300}).encode()
req = urllib.request.Request("http://127.0.0.1:11434/v1/chat/completions",
                             data=body, headers={"Content-Type": "application/json"})
t0 = time.time()
res = json.loads(urllib.request.urlopen(req, timeout=900).read())
el = time.time() - t0
n = res["usage"]["completion_tokens"]
print("RESULT: %d tokens in %.1fs -> %.1f tok/s" % (n, el, n / el))
sh("nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader")
