"""PyInstaller entry script for CanTraceDiag.exe (see cantracediag.desktop)."""

import multiprocessing
import sys

from cantracediag.desktop import main

if __name__ == "__main__":
    multiprocessing.freeze_support()
    sys.exit(main())
