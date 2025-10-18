import os
import sys
from pathlib import Path

from PyQt6 import QtWidgets as qtw

from . import fluxrun_cli
from . import fluxrun_gui
from .cli import cli

print(f"{__file__}")


def main(args):
    abspath = Path(os.path.abspath(__file__)).parent  # directory of bico.py
    os.chdir(abspath)
    wd = os.getcwd()
    print(f"Working directory: {wd}")

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
