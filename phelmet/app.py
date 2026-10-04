import argparse

from .config import load_cfg


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.yaml")
    args = ap.parse_args()
    cfg = load_cfg(args.config)
    print("phelmet scaffold ready", cfg["camera"]["width"])


if __name__ == "__main__":
    main()
