#!/usr/bin/env bash
# run_all_algos.sh
# Runs ns-3 ACO simulation for all 4 algorithm types × 5 node counts × 3 seeds,
# averages results, writes sim_results.json, then regenerates graphs.

PROTO_CC="src/aco/model/aco-routing-protocol.cc"
RESULTS_JSON="${RESULTS_FILE:-sim_results.json}"
NODE_COUNTS=(50 100 150 200 250)   # 5 test points
ALGOS=("BASIC_ACO" "EHACORP" "ACO_DE_ONLY" "EACO_DE")
SEEDS=(1 2 3)                      # 3 seeds per run for averaging

echo "=================================================="
echo "  ACO 4-Algorithm Automated Benchmark (3-seed avg)"
echo "=================================================="

# ------------------------------------------------------------------
# 1. Build once
# ------------------------------------------------------------------
echo "Building simulation..."
./ns3 build

if [ $? -ne 0 ]; then
    echo "BUILD FAILED — aborting."
    exit 1
fi

# ------------------------------------------------------------------
# 2. Accumulate results
# ------------------------------------------------------------------
echo "{" > $RESULTS_JSON

FIRST_ALGO=true
for ALGO in "${ALGOS[@]}"; do

    echo ""
    echo ">>> Running simulations for: $ALGO"

    PDR_LIST=""
    DELAY_LIST=""
    THRPT_LIST=""
    FIRST_NODE=true

    for N in "${NODE_COUNTS[@]}"; do
        echo -n "  nNodes=$N  "

        PDR_SUM=0
        DELAY_SUM=0
        THRPT_SUM=0
        VALID_RUNS=0

        for SEED in "${SEEDS[@]}"; do
            # --RngRun is the correct ns-3 global argument to vary random runs
            OUTPUT=$(./ns3 run "aco-test --nNodes=$N --algo=$ALGO" -- --RngRun=$SEED 2>&1)

            PDR=$(echo "$OUTPUT"    | grep "FINAL PDR"   | grep -oP '[0-9]+\.?[0-9]*' | head -1)
            DELAY=$(echo "$OUTPUT"  | grep "Avg Delay"   | grep -oP '[0-9]+\.?[0-9]*' | head -1)
            THRPT=$(echo "$OUTPUT"  | grep "Throughput"  | grep -oP '[0-9]+\.?[0-9]*' | head -1)

            PDR=${PDR:-0}
            DELAY=${DELAY:-0}
            THRPT=${THRPT:-0}

            PDR_SUM=$(echo "$PDR_SUM + $PDR" | bc -l)
            DELAY_SUM=$(echo "$DELAY_SUM + $DELAY" | bc -l)
            THRPT_SUM=$(echo "$THRPT_SUM + $THRPT" | bc -l)
            VALID_RUNS=$((VALID_RUNS + 1))

            echo -n "seed${SEED}:${PDR}%  "
        done

        # Average over seeds
        NUM_SEEDS=${#SEEDS[@]}
        AVG_PDR=$(echo "scale=4; $PDR_SUM / $NUM_SEEDS" | bc -l)
        AVG_DELAY=$(echo "scale=4; $DELAY_SUM / $NUM_SEEDS" | bc -l)
        AVG_THRPT=$(echo "scale=6; $THRPT_SUM / $NUM_SEEDS" | bc -l)

        echo "  → avg PDR=${AVG_PDR}% Delay=${AVG_DELAY}ms Tput=${AVG_THRPT}Mbps"

        if [ "$FIRST_NODE" = true ]; then
            PDR_LIST="$AVG_PDR"
            DELAY_LIST="$AVG_DELAY"
            THRPT_LIST="$AVG_THRPT"
            FIRST_NODE=false
        else
            PDR_LIST="$PDR_LIST, $AVG_PDR"
            DELAY_LIST="$DELAY_LIST, $AVG_DELAY"
            THRPT_LIST="$THRPT_LIST, $AVG_THRPT"
        fi
    done

    # Comma before second+ algo
    if [ "$FIRST_ALGO" = false ]; then
        echo "," >> $RESULTS_JSON
    fi
    FIRST_ALGO=false

    cat >> $RESULTS_JSON <<JSON
  "${ALGO}": {
    "nNodes": [$(IFS=', '; echo "${NODE_COUNTS[*]}")],
    "pdr":    [$PDR_LIST],
    "delay":  [$DELAY_LIST],
    "thrpt":  [$THRPT_LIST]
  }
JSON

done

echo "" >> $RESULTS_JSON
echo "}" >> $RESULTS_JSON

echo ""
echo "=================================================="
echo "  All runs complete! Results in: $RESULTS_JSON"
echo "  Regenerating graphs..."
echo "=================================================="
python3 compare_4algo_real.py

# The python script will read the env vars and print the saved filename.
echo "DONE."
