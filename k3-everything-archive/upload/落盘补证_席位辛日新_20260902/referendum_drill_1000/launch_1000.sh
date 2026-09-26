#!/bin/bash
# 千席演练九路点火器——全绝对路径+setsid隔离，规避壳墙#9（&断链）与#10（pkill自匹配）
W=<输出区>/referendum_drill_1000/drill_worker_1000.py
L=<输出区>/referendum_drill_1000
setsid nohup python3 $W deepseek-v4-flash   1  294 > $L/log_v4flash.txt   2>&1 < /dev/null &
setsid nohup python3 $W deepseek-v4-pro   295  491 > $L/log_v4pro.txt     2>&1 < /dev/null &
setsid nohup python3 $W qwen3-30b-a3b     492  621 > $L/log_qwen30b.txt   2>&1 < /dev/null &
setsid nohup python3 $W qwen3-32b         622  736 > $L/log_qwen32b.txt   2>&1 < /dev/null &
setsid nohup python3 $W openpangu-2.0-flash 737 808 > $L/log_panguflash.txt 2>&1 < /dev/null &
setsid nohup python3 $W kimi-平台版本甲         809  858 > $L/log_kimi.txt      2>&1 < /dev/null &
setsid nohup python3 $W glm-5.1           859  907 > $L/log_glm51.txt     2>&1 < /dev/null &
setsid nohup python3 $W glm-5.2           908  955 > $L/log_glm52.txt     2>&1 < /dev/null &
setsid nohup python3 $W openpangu-2.0-pro 956 1000 > $L/log_pangupro.txt  2>&1 < /dev/null &
echo "launched 9 queues at $(date -u +%FT%TZ)"
