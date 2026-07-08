#!/bin/zsh
cd "${0:A:h}"
python3 gui.py
exit_status=$?
if [ $exit_status -ne 0 ]; then
  echo ""
  echo "TimelapseBuilder exited with an error (see above)."
  read -n 1 -s -r -p "Press any key to close this window..."
else
  echo "TimelapseBuilder closed."
fi
