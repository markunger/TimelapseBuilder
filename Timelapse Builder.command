#!/bin/zsh
cd "${0:A:h}"
PYTHON="/Library/Frameworks/Python.framework/Versions/3.12/bin/python3"
[ -x "$PYTHON" ] || PYTHON="python3"
"$PYTHON" gui.py
exit_status=$?
if [ $exit_status -ne 0 ]; then
  echo ""
  echo "TimelapseBuilder exited with an error (see above)."
  read -n 1 -s -r -p "Press any key to close this window..."
fi
