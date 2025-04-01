import os
import sys
from pathlib import Path

from PyQt6 import QtWidgets as qtw

import cli.cli as cli
from fluxrun_cli import FluxRunCli
from fluxrun_gui import FluxRunGUI


def main(args):
    abspath = Path(os.path.abspath(__file__)).parent  # directory of bico.py
    os.chdir(abspath)
    wd = os.getcwd()
    print(f"Working directory: {wd}")

    # Run FLUXRUN w/o GUI
    if args.folder:
        days = args.days if args.days else None
        fluxruncli = FluxRunCli(folder=args.folder, days=days)
        fluxruncli.run()

    # Run FLUXRUN with GUI
    if args.gui:
        app = qtw.QApplication(sys.argv)
        fluxrungui = FluxRunGUI()
        fluxrungui.show()
        app.exec()

    else:
        print("Please add arg how FLUXRUN should be executed. Add '-h' for help.")


if __name__ == '__main__':
    args = cli.get_args()
    args = cli.validate_args(args)
    main(args)
