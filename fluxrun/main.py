import os
import sys
from pathlib import Path

from PyQt6 import QtWidgets as qtw

import cli.cli as cli
from fluxrun import fluxruncli
from fluxrun import fluxrungui


def main(args):
    abspath = Path(os.path.abspath(__file__)).parent  # directory of bico.py
    os.chdir(abspath)
    wd = os.getcwd()
    print(f"Working directory: {wd}")

    # Run FLUXRUN w/o GUI
    if args.folder:
        days = args.days if args.days else None
        _fluxruncli = fluxruncli(folder=args.folder, days=days)
        _fluxruncli.run()

    # Run FLUXRUN with GUI
    if args.gui:
        app = qtw.QApplication(sys.argv)
        _fluxrungui = fluxrungui()
        _fluxrungui.show()
        app.exec()

    else:
        print("Please add arg how fluxrun should be executed. Add '-h' for help.")


if __name__ == '__main__':
    args = cli.get_args()
    args = cli.validate_args(args)
    main(args)
