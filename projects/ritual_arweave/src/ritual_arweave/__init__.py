from ritual_arweave.cli import cli


def main() -> int:
    from nicelog import setup_logging  # type: ignore

    setup_logging()
    cli()
    return 0
