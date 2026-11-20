#!/bin/bash
cd /tmp/fable_out
python3 b6_rules_final.py V > b6V.log 2>&1
python3 b6_rules_final.py > b6.log 2>&1
python3 d1_tables.py > d1.log 2>&1
python3 b8_frontier.py > b8.log 2>&1
python3 c2_judgecost.py > c2.log 2>&1
python3 c4_judge_est.py > c4.log 2>&1
python3 c5_retryadj.py > c5.log 2>&1
python3 c1_table.py V > c1V.log 2>&1
python3 c1_table.py > c1.log 2>&1
python3 b4_crossfit.py > b4.log 2>&1
python3 c3_bird.py > c3.log 2>&1
python3 b2_signals.py > b2.log 2>&1
python3 b3_optimism.py > b3.log 2>&1
python3 a1_baseline.py > a1.log 2>&1
python3 a3_patterns.py > a3.log 2>&1
python3 b1_semvote.py > b1.log 2>&1
python3 b7_sc.py > b7.log 2>&1
echo CHAIN_DONE > chain2.done
