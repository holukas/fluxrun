# USED FOR SETUPTOOLS BUT CURRENTLY NOT WORKING

import os
import sys
from pathlib import Path

from PyQt5 import QtWidgets as qtw

# from fluxrun import FluxRun
import fluxrun

def main():
    abspath = Path(os.path.abspath(__file__)).parent  # Directory of this file
    os.chdir(abspath)
    wd = os.getcwd()
    print(f"Working directory: {wd}")
    app = qtw.QApplication(sys.argv)
    fr = fluxrun.FluxRun()
    fr.show()
    app.exec_()


if __name__ == '__main__':
    main()
