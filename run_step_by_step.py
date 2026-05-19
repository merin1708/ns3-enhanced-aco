#!/usr/bin/env python3
"""
run_step_by_step.py
====================
Runs each (algorithm, nNodes) combination one at a time.
Saves results to sim_results.json immediately after EACH run.
Can be safely interrupted and re-run — already-completed combos are SKIPPED.
"""

import subprocess
import json
import os
import re
import sys

ALGOS      = ["BASIC_ACO", "EHACORP", "ACO_DE_ONLY", "EACO_DE"]
NODE_COUNTS = [50, 100, 150, 200, 250]
SEEDS       = [1]   # Single seed — keeps each combo to ~3 min
RESULTS_FILE = "sim_results.json"

# ─── Load any existing partial results ───────────────────────────────────────
if os.path.exists(RESULTS_FILE):
    with open(RESULTS_FILE) as f:
        results = json.load(f)
    print(f"✅  Loaded existing results from {RESULTS_FILE}")
else:
    results = {}

def save_results():
    with open(RESULTS_FILE, "w") as f:
        json.dump(results, f, indent=2)
    print(f"    💾  Saved → {RESULTS_FILE}")

def run_sim(algo, nNodes, seed):
    cmd = [
        "./ns3", "run",
        f"aco-test --nNodes={nNodes} --algo={algo}",
        "--", f"--RngRun={seed}"
    ]
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT,
                                      timeout=600, text=True)
    except subprocess.TimeoutExpired:
        print(f"    ⚠️  TIMEOUT for {algo} nNodes={nNodes} seed={seed}")
        return None, None, None
    except subprocess.CalledProcessError as e:
        out = e.output

    pdr   = re.search(r'FINAL PDR.*?:\s*([\d.]+)', out)
    delay = re.search(r'Avg Delay\s*:\s*([\d.]+)', out)
    thrpt = re.search(r'Throughput\s*:\s*([\d.]+)', out)

    pdr   = float(pdr.group(1))   if pdr   else 0.0
    delay = float(delay.group(1)) if delay else 0.0
    thrpt = float(thrpt.group(1)) if thrpt else 0.0
    return pdr, delay, thrpt

# ─── Main loop ────────────────────────────────────────────────────────────────
total = len(ALGOS) * len(NODE_COUNTS)
done  = 0

for algo in ALGOS:
    if algo not in results:
        results[algo] = {
            "nNodes": NODE_COUNTS,
            "pdr":    [None] * len(NODE_COUNTS),
            "delay":  [None] * len(NODE_COUNTS),
            "thrpt":  [None] * len(NODE_COUNTS),
        }

    for idx, nNodes in enumerate(NODE_COUNTS):
        done += 1

        # Skip if already computed
        if results[algo]["pdr"][idx] is not None:
            print(f"[{done}/{total}] ⏭️   SKIP  {algo:12s}  nNodes={nNodes}  "
                  f"(already have PDR={results[algo]['pdr'][idx]:.2f}%)")
            continue

        print(f"\n[{done}/{total}] ▶️   Running {algo:12s}  nNodes={nNodes}  "
              f"(seeds {SEEDS}) ...", flush=True)

        pdr_sum = delay_sum = thrpt_sum = 0.0
        valid = 0
        for seed in SEEDS:
            print(f"    seed={seed} ... ", end="", flush=True)
            p, d, t = run_sim(algo, nNodes, seed)
            if p is not None:
                print(f"PDR={p:.2f}%  Delay={d:.1f}ms  Tput={t:.5f}Mbps")
                pdr_sum   += p
                delay_sum += d
                thrpt_sum += t
                valid += 1
            else:
                print("FAILED")

        if valid > 0:
            results[algo]["pdr"][idx]   = round(pdr_sum   / valid, 4)
            results[algo]["delay"][idx] = round(delay_sum / valid, 4)
            results[algo]["thrpt"][idx] = round(thrpt_sum / valid, 6)
        else:
            results[algo]["pdr"][idx]   = 0.0
            results[algo]["delay"][idx] = 0.0
            results[algo]["thrpt"][idx] = 0.0

        print(f"    → avg PDR={results[algo]['pdr'][idx]:.4f}%  "
              f"Delay={results[algo]['delay'][idx]:.2f}ms  "
              f"Tput={results[algo]['thrpt'][idx]:.6f}Mbps")
        save_results()

print("\n" + "="*55)
print("  ALL DONE — generating graphs...")
print("="*55)
subprocess.run(["python3", "compare_4algo_real.py"])
print("\n✅  Graph saved → compare_4algo_real_graphs.png")
