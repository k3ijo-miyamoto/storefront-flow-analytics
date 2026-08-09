from __future__ import annotations

import argparse

from mallflow.analysis import analyze_video
from mallflow.annotation import run_roi_editor


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="mallflow")
    subparsers = parser.add_subparsers(dest="command", required=True)

    annotate = subparsers.add_parser("annotate", help="Create ROI YAML from a video frame.")
    annotate.add_argument("--video", required=True)
    annotate.add_argument("--store", required=True)
    annotate.add_argument("--output", help="Path to write the ROI YAML config.")
    annotate.add_argument("--display-width", type=int, default=1400, help="Width of the annotation window.")
    annotate.add_argument("--time", type=float, default=0.0, help="Video timestamp in seconds to use for annotation.")
    annotate.add_argument("--entrance-mode", choices=["roi", "line"], default="roi")
    annotate.add_argument("--only", choices=["traffic_roi", "interest_roi", "entrance_roi"], help="Only edit one ROI and preserve the rest of the existing config.")

    analyze = subparsers.add_parser("analyze", help="Analyze a storefront video.")
    analyze.add_argument("--config", required=True)
    analyze.add_argument("--output-dir", default="outputs")
    analyze.add_argument("--sample-fps", type=float, default=1.0)
    analyze.add_argument("--detector-width", type=int, default=960)
    analyze.add_argument("--detector", choices=["hog", "yolo"], default="hog")
    analyze.add_argument("--tracker", choices=["centroid", "bytetrack"], default="centroid")
    analyze.add_argument("--tracker-config", default="bytetrack.yaml")
    analyze.add_argument("--model", help="Model path for --detector yolo.")
    analyze.add_argument("--confidence", type=float, default=0.25)
    analyze.add_argument("--device", help="Ultralytics device, e.g. 0, cuda:0, or cpu.")
    analyze.add_argument("--start", type=float)
    analyze.add_argument("--end", type=float)
    analyze.add_argument("--max-frames", type=int)

    compare = subparsers.add_parser("compare", help="Compare store-level track CSV files.")
    compare.add_argument("track_csv", nargs="+")

    debug_frame = subparsers.add_parser("debug-frame", help="Save a frame with ROI overlays.")
    debug_frame.add_argument("--config", required=True)
    debug_frame.add_argument("--time", type=float, required=True)
    debug_frame.add_argument("--output", required=True)
    debug_frame.add_argument("--track-points", help="Optional track point CSV to overlay trajectories.")
    debug_frame.add_argument("--window", type=float, default=8.0, help="Seconds before/after --time for trajectory overlay.")

    debug_video = subparsers.add_parser("debug-video", help="Save a video clip with ROI and trajectory overlays.")
    debug_video.add_argument("--config", required=True)
    debug_video.add_argument("--track-points", required=True)
    debug_video.add_argument("--start", type=float, required=True)
    debug_video.add_argument("--end", type=float, required=True)
    debug_video.add_argument("--output", required=True)
    debug_video.add_argument("--trail", type=float, default=6.0)
    debug_video.add_argument("--fps", type=float, default=12.0)
    debug_video.add_argument("--width", type=int, default=1280)
    debug_video.add_argument("--boxes", action="store_true", help="Overlay current detection boxes, confidence, and foot points.")
    debug_video.add_argument("--tracks", help="Optional track CSV to overlay cumulative entry counts.")

    report = subparsers.add_parser("report", help="Create a single-store HTML report.")
    report.add_argument("--metrics", required=True)
    report.add_argument("--tracks", required=True)
    report.add_argument("--figure", action="append", default=[])
    report.add_argument("--stats", action="append", default=[], help="Optional beta-binomial stats YAML to include.")
    report.add_argument("--facade", help="Optional facade zone CSV to include.")
    report.add_argument("--display-name", default="Store A", help="Anonymized display name for the report.")
    report.add_argument("--output", required=True)

    stats = subparsers.add_parser("stats", help="Create beta-binomial uncertainty summaries from store metrics.")
    stats.add_argument("--metrics", action="append", required=True)
    stats.add_argument("--metric", choices=["entry", "exposure", "stop"], default="entry")
    stats.add_argument("--samples", type=int, default=100_000)
    stats.add_argument("--seed", type=int, default=42)
    stats.add_argument("--output", required=True)

    facade = subparsers.add_parser("facade", help="Summarize configured facade zones from existing tracks.")
    facade.add_argument("--config", required=True)
    facade.add_argument("--tracks", required=True)
    facade.add_argument("--track-points", required=True)
    facade.add_argument("--output", required=True)

    stabilize = subparsers.add_parser("stabilize", help="Create a camera-stabilized video.")
    stabilize.add_argument("--input", required=True)
    stabilize.add_argument("--output", required=True)
    stabilize.add_argument("--reference-time", type=float, default=54.0)
    stabilize.add_argument("--start", type=float, default=0.0)
    stabilize.add_argument("--end", type=float)
    stabilize.add_argument("--fps", type=float, default=10.0)
    stabilize.add_argument("--width", type=int, default=1280)
    stabilize.add_argument("--feature-width", type=int, default=960)
    stabilize.add_argument("--side-by-side", action="store_true")

    args = parser.parse_args(argv)
    if args.command == "annotate":
        output = run_roi_editor(
            args.video,
            args.store,
            args.output,
            args.display_width,
            args.time,
            args.entrance_mode,
            args.only,
        )
        print(f"Saved ROI config: {output}")
        return 0
    if args.command == "analyze":
        outputs = analyze_video(
            config_path=args.config,
            output_dir=args.output_dir,
            sample_fps=args.sample_fps,
            detector_width=args.detector_width,
            detector_backend=args.detector,
            tracker_backend=args.tracker,
            model_path=args.model,
            confidence_threshold=args.confidence,
            tracker_config=args.tracker_config,
            device=args.device,
            start_s=args.start,
            end_s=args.end,
            max_frames=args.max_frames,
        )
        print(f"Saved track CSV: {outputs['tracks']}")
        print(f"Saved track points CSV: {outputs['track_points']}")
        print(f"Saved metrics: {outputs['metrics']}")
        return 0
    if args.command == "compare":
        print("CSV comparison reporting is planned after track CSV generation is connected.")
        return 0
    if args.command == "debug-frame":
        from mallflow.visualization import save_debug_frame, save_track_debug_frame

        if args.track_points:
            output = save_track_debug_frame(args.config, args.track_points, args.time, args.output, args.window)
        else:
            output = save_debug_frame(args.config, args.time, args.output)
        print(f"Saved debug frame: {output}")
        return 0
    if args.command == "debug-video":
        from mallflow.visualization import save_track_debug_video

        output = save_track_debug_video(
            args.config,
            args.track_points,
            args.start,
            args.end,
            args.output,
            args.trail,
            args.fps,
            args.width,
            args.boxes,
            args.tracks,
        )
        print(f"Saved debug video: {output}")
        return 0
    if args.command == "report":
        from mallflow.visualization import save_store_report

        output = save_store_report(
            args.metrics,
            args.tracks,
            args.figure,
            args.output,
            args.stats,
            args.facade,
            args.display_name,
        )
        print(f"Saved report: {output}")
        return 0
    if args.command == "stats":
        from mallflow.analytics import summarize_beta_binomial

        output = summarize_beta_binomial(args.metrics, args.output, args.metric, args.samples, args.seed)
        print(f"Saved stats summary: {output}")
        return 0
    if args.command == "facade":
        from mallflow.analytics.facade import summarize_facade_zones

        output = summarize_facade_zones(args.config, args.tracks, args.track_points, args.output)
        print(f"Saved facade summary: {output}")
        return 0
    if args.command == "stabilize":
        from mallflow.video import stabilize_video

        output = stabilize_video(
            input_path=args.input,
            output_path=args.output,
            reference_time_s=args.reference_time,
            start_s=args.start,
            end_s=args.end,
            output_fps=args.fps,
            width=args.width,
            feature_width=args.feature_width,
            side_by_side=args.side_by_side,
        )
        print(f"Saved stabilized video: {output}")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
