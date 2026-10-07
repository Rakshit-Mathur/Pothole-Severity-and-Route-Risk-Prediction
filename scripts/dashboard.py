import argparse

import yaml

from phelmet.server import create_app


ap = argparse.ArgumentParser()
ap.add_argument("--db", default="data/road_log.db")
ap.add_argument("--port", type=int, default=5000)
args = ap.parse_args()
cfg = yaml.safe_load(open("config.yaml", encoding="utf-8"))
create_app(args.db, cfg["storage"]["score_penalty_per_risk_km"]).run(port=args.port, debug=False)
