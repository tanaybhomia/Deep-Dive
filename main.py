#!/usr/bin/env python3
import sys
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from deepdive.application import DeepDiveApplication


def main():
    app = DeepDiveApplication()
    return app.run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())
