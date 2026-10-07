import argparse

from phelmet.server import create_app


ap = argparse.ArgumentParser()
ap.add_argument("--db", default="data/road_log.db")
ap.add_argument("--port", type=int, default=5000)
args = ap.parse_args()
create_app(args.db).run(port=args.port, debug=False)
