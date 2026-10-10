#!/usr/bin/env bash
set -euo pipefail
# Run on the Beelink. All files and logs stay under ~/jevalloc.
cd "$HOME/jevalloc"
case "${1:-start}" in
 start)
  if test -f model-server.pid && kill -0 "$(cat model-server.pid)" 2>/dev/null; then exit 0; fi
  nohup ./llama.cpp/build-vk/bin/llama-server -m models/Clef-Flash-Q8_0.gguf --host 127.0.0.1 --port 8765 -ngl 99 -t 4 -tb 4 -c 4096 -b 4096 -ub 4096 --parallel 1 > model-server.log 2>&1 </dev/null &
  echo $! > model-server.pid ;;
 stop) if test -f model-server.pid; then kill "$(cat model-server.pid)"; fi ;;
 *) exit 2 ;;
esac
