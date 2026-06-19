#!/bin/zsh
# Wrapper invoked by the launchd job. launchd has a minimal PATH/env, so set everything
# explicitly here. NOTE: if node or python is upgraded, update the two version paths below.
#
# Usage: run.sh [orchestrator args]   e.g.  run.sh --shadow --quiet

export PATH="/Users/victor_he/.nvm/versions/node/v22.22.0/bin:/usr/local/bin:/usr/bin:/bin"
export CLAUDE_BIN="/Users/victor_he/.nvm/versions/node/v22.22.0/bin/claude"
unset ANTHROPIC_API_KEY            # force Max-subscription auth (zero API cost)

PY="/Library/Frameworks/Python.framework/Versions/3.13/bin/python3"
REPO="/Users/victor_he/Projects/option-harvest"

cd "$REPO" || exit 1
echo "===== $(date '+%Y-%m-%d %H:%M:%S %Z') :: run.sh $* ====="
exec "$PY" -m automation.run_history_update "$@"
