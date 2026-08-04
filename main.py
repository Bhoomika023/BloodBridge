"""Entry point for BloodBridge."""
import logging

from __init__ import __version__
from gui.dashboard import Dashboard


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
    logging.info("Starting BloodBridge %s", __version__)
    app = Dashboard()
    app.mainloop()


if __name__ == '__main__':
    main()
