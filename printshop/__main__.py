"""Allow ``python -m printshop ...`` to invoke the CLI."""

from printshop.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
