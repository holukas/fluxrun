import os
from pathlib import Path

import fluxrun

abspath = Path(os.path.abspath(__file__)).parent  # directory of start_fluxrun.py
os.chdir(abspath)
wd = os.getcwd()
print(f"Working directory: {wd}")
fluxrun.main()
