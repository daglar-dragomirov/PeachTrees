#!/bin/bash
cd /tmp/fable_out
python3 c1_table.py > c1.log 2>&1
python3 c1_table.py V > c1V.log 2>&1
python3 b8_frontier.py > b8.log 2>&1
python3 b4_crossfit.py > b4.log 2>&1
python3 b1_semvote.py > b1.log 2>&1
python3 b3_optimism.py > b3.log 2>&1
echo CHAIN_DONE > chain1.done
