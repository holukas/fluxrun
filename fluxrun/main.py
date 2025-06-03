import os
import sys
from pathlib import Path

from PyQt6 import QtWidgets as qtw

from . import fluxrun_cli
from . import fluxrun_gui
from .cli import cli

# todo testing
print(f"{__file__}")


# todo wrong imports
# todo now solved? with adjusted batch script that sets script dir it seems to work correctly
# todo batch script:
# :: Activate the conda environment required for the script
# call C:\Users\nopan\miniconda3\Scripts\activate.bat C:\Users\nopan\miniconda3\envs\fluxrun
#
# :: Change directory to the parent of 'fluxrun'
# set SCRIPT_DIR=%~dp0
# cd "%SCRIPT_DIR%"
#
# :: Execute the script as a module
# :: This tells Python to look for the 'fluxrun' package in the current directory
# call python -m fluxrun.main -g
#
# :: Optional: Deactivate the conda environment if you don't need it active afterward
# :: call conda deactivate

# Imports for some reason from script origin folder, should be from testfolder "del":
#   F:\TMP\del\fluxrun\cli\cli.py
#   F:\TMP\del\fluxrun\gui\mainwindow.py
#   todo F:\Sync\luhk_work\20 - CODING\23 - FLUX\fluxrun\fluxrun\fluxrun_gui.py
#   todo F:\Sync\luhk_work\20 - CODING\23 - FLUX\fluxrun\fluxrun\fluxrun_cli.py
#   Working directory: F:\TMP\del\fluxrun
#   F:\TMP\del\\fluxrun\main.py

def main(args):
    abspath = Path(os.path.abspath(__file__)).parent  # directory of bico.py
    os.chdir(abspath)
    wd = os.getcwd()
    print(f"Working directory: {wd}")

    # todo testing
    print(f"{__file__}")

    # Run FLUXRUN w/o GUI
    # Example: main.py -f F:\Sync\luhk_work\CURRENT\FRU_rECord_test\with_cli -d 2
    if args.folder:
        days = args.days if args.days else None
        _fluxruncli = fluxrun_cli.FluxRunCli(folder=args.folder, days=days)
        # _fluxruncli = fluxruncli(folder=args.folder, days=days)
        _fluxruncli.run()

    # Run FLUXRUN with GUI
    if args.gui:
        app = qtw.QApplication(sys.argv)
        _fluxrungui = fluxrun_gui.FluxRunGUI()
        # _fluxrungui = fluxrungui()
        _fluxrungui.show()
        app.exec()

    else:
        print("Please add arg how fluxrun should be executed. Add '-h' for help.")


if __name__ == '__main__':
    args = cli.get_args()
    args = cli.validate_args(args)
    main(args)
