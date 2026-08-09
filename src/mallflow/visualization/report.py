from __future__ import annotations

import csv
import html
import os
from pathlib import Path

import yaml


def save_store_report(
    metrics_path: str,
    tracks_path: str,
    figure_paths: list[str],
    output_path: str,
    stats_paths: list[str] | None = None,
    facade_path: str | None = None,
    display_name: str = "Store A",
) -> Path:
    metrics = yaml.safe_load(Path(metrics_path).read_text(encoding="utf-8"))
    entered_tracks = [
        row
        for row in csv.DictReader(Path(tracks_path).open(newline="", encoding="utf-8"))
        if row["entered"] == "1"
    ]
    stats = load_stats(stats_paths or [])
    facade_rows = load_facade_rows(facade_path) if facade_path else []
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_report(metrics, entered_tracks, figure_paths, output, stats, facade_rows, display_name), encoding="utf-8")
    return output


def render_report(
    metrics: dict[str, object],
    entered_tracks: list[dict[str, str]],
    figure_paths: list[str],
    output_path: Path,
    stats: list[dict[str, object]] | None = None,
    facade_rows: list[dict[str, str]] | None = None,
    display_name: str = "Store A",
) -> str:
    passers = int(metrics["passerby_count"])
    exposed = int(metrics["exposed_count"])
    stopped = int(metrics["stop_count"])
    entries = int(metrics["entry_count"])
    max_count = max(passers, exposed, stopped, entries, 1)
    safe_display_name = html.escape(display_name)
    entry_rate = float(metrics["entry_rate"]) * 100
    traffic_rate = float(metrics["traffic_rate_per_min"])
    stop_rate = float(metrics["stop_rate"]) * 100
    dwell_median = float(metrics["dwell_median_s"])

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{safe_display_name} Storefront Analytics</title>
  <style>
    :root {{
      color-scheme: light;
      --ink: #172026;
      --muted: #60717d;
      --line: #d8e0e5;
      --surface: #ffffff;
      --band: #f4f7f9;
      --green: #287a54;
      --blue: #256b9d;
      --red: #b83b38;
      --gold: #9b6b12;
    }}
    body {{
      margin: 0;
      font-family: Arial, Helvetica, sans-serif;
      color: var(--ink);
      background: var(--band);
    }}
    header {{
      padding: 28px 36px 18px;
      background: var(--surface);
      border-bottom: 1px solid var(--line);
    }}
    h1 {{
      margin: 0 0 8px;
      font-size: 28px;
      letter-spacing: 0;
    }}
    main {{
      max-width: 1180px;
      margin: 0 auto;
      padding: 28px 24px 40px;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 12px;
    }}
    .card {{
      background: var(--surface);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 16px;
    }}
    .label {{
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
    }}
    .value {{
      margin-top: 8px;
      font-size: 28px;
      font-weight: 700;
    }}
    section {{
      margin-top: 24px;
      background: var(--surface);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 18px;
    }}
    h2 {{
      margin: 0 0 16px;
      font-size: 18px;
    }}
    .bar-row {{
      display: grid;
      grid-template-columns: 110px 1fr 64px;
      gap: 12px;
      align-items: center;
      margin: 10px 0;
    }}
    .bar {{
      height: 24px;
      background: #e8eef2;
      border-radius: 4px;
      overflow: hidden;
    }}
    .fill {{
      height: 100%;
      background: var(--blue);
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 14px;
    }}
    th, td {{
      text-align: left;
      border-bottom: 1px solid var(--line);
      padding: 10px 8px;
    }}
    th {{
      color: var(--muted);
      font-weight: 600;
    }}
    img,
    video {{
      width: 100%;
      height: auto;
      border: 1px solid var(--line);
      border-radius: 8px;
      display: block;
      margin-top: 12px;
    }}
    .note {{
      color: var(--muted);
      line-height: 1.5;
      margin: 0;
    }}
    .table-scroll {{
      overflow-x: auto;
    }}
    .numeric {{
      text-align: right;
      white-space: nowrap;
    }}
    .section-note {{
      margin: -6px 0 14px;
    }}
    .toolbar {{
      display: flex;
      justify-content: space-between;
      gap: 16px;
      align-items: center;
    }}
    .lang-toggle {{
      display: inline-flex;
      overflow: hidden;
      border: 1px solid var(--line);
      border-radius: 8px;
    }}
    .lang-toggle button {{
      border: 0;
      background: var(--surface);
      color: var(--ink);
      cursor: pointer;
      font: inherit;
      padding: 8px 12px;
    }}
    .lang-toggle button.active {{
      background: var(--ink);
      color: var(--surface);
    }}
    body[data-lang="en"] [data-lang-text="jp"],
    body[data-lang="jp"] [data-lang-text="en"] {{
      display: none;
    }}
    @media (max-width: 820px) {{
      .grid {{
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }}
    }}
  </style>
</head>
<body data-lang="en">
  <header>
    <div class="toolbar">
      <div>
        <h1>{safe_display_name} Storefront Analytics</h1>
        <p class="note">{lang("YOLO + ByteTrack analysis with anonymized storefront video and manually configured ROIs.", "YOLO + ByteTrackによる、匿名化済み店頭動画と手動ROI設定に基づく分析。")}</p>
      </div>
      <div class="lang-toggle" aria-label="Language">
        <button type="button" class="active" data-set-lang="en">EN</button>
        <button type="button" data-set-lang="jp">JP</button>
      </div>
    </div>
  </header>
  <main>
    <div class="grid">
      {kpi_card(lang("Passers", "通行者"), passers)}
      {kpi_card(lang("Entries", "入店"), entries)}
      {kpi_card(lang("Entry Rate", "入店率"), f"{entry_rate:.1f}%")}
      {kpi_card(lang("Traffic / min", "通行/分"), f"{traffic_rate:.2f}")}
      {kpi_card(lang("Exposed", "接触"), exposed)}
      {kpi_card(lang("Stopped", "停止"), stopped)}
      {kpi_card(lang("Stop Rate", "停止率"), f"{stop_rate:.1f}%")}
      {kpi_card(lang("Median Dwell", "滞在中央値"), f"{dwell_median:.1f}s")}
    </div>

    <section>
      <h2>{lang("Funnel", "ファネル")}</h2>
      {bar_row(lang("Pass", "通行"), passers, max_count)}
      {bar_row(lang("Exposure", "接触"), exposed, max_count)}
      {bar_row(lang("Stop", "停止"), stopped, max_count)}
      {bar_row(lang("Entry", "入店"), entries, max_count)}
    </section>

    {stats_section(stats or [])}

    {facade_section(facade_rows or [])}

    {definitions_section()}

    <section>
      <h2>{lang("Entry Tracks", "入店トラック")}</h2>
      {entry_table(entered_tracks)}
    </section>

    <section>
      <h2>{lang("Trajectory Checks", "軌跡確認")}</h2>
      <p class="note">{lang("ROIs, facade zones, ByteTrack foot-point trails, detection boxes, and cumulative entry count.", "ROI、ファサード分割、ByteTrackの足元軌跡、検出枠、累積入店カウント。")}</p>
      {figures_html(figure_paths, output_path)}
    </section>
  </main>
  <script>
    const buttons = document.querySelectorAll("[data-set-lang]");
    buttons.forEach((button) => {{
      button.addEventListener("click", () => {{
        document.body.dataset.lang = button.dataset.setLang;
        buttons.forEach((item) => item.classList.toggle("active", item === button));
      }});
    }});
  </script>
</body>
</html>
"""


def load_stats(paths: list[str]) -> list[dict[str, object]]:
    stats = []
    for path in paths:
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        if data:
            stats.append(data)
    return stats


def load_facade_rows(path: str) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def lang(en: str, jp: str) -> str:
    return f'<span data-lang-text="en">{html.escape(en)}</span><span data-lang-text="jp">{html.escape(jp)}</span>'


def kpi_card(label: str, value: object) -> str:
    return f'<div class="card"><div class="label">{label}</div><div class="value">{value}</div></div>'


def bar_row(label: str, value: int, max_count: int) -> str:
    width = 100 * value / max_count
    return f"""
      <div class="bar-row">
        <div>{label}</div>
        <div class="bar"><div class="fill" style="width: {width:.1f}%"></div></div>
        <div>{value}</div>
      </div>
    """


def entry_table(rows: list[dict[str, str]]) -> str:
    if not rows:
        return f'<p class="note">{lang("No entry tracks detected.", "入店トラックは検出されませんでした。")}</p>'
    body = "\n".join(
        f"<tr><td>{row['track_id']}</td><td>{row['entry_timestamp_s']}s</td><td>{row['first_seen_s']}s</td><td>{row['last_seen_s']}s</td><td>{row['direction']}</td></tr>"
        for row in rows
    )
    return f"""
      <table>
        <thead><tr><th>{lang("Track ID", "トラックID")}</th><th>{lang("Entry Time", "入店時刻")}</th><th>{lang("First Seen", "初回検出")}</th><th>{lang("Last Seen", "最終検出")}</th><th>{lang("Direction", "方向")}</th></tr></thead>
        <tbody>{body}</tbody>
      </table>
    """


def stats_section(stats: list[dict[str, object]]) -> str:
    if not stats:
        return ""
    rows = []
    for summary in stats:
        metric = str(summary.get("metric", ""))
        for posterior in summary.get("posteriors", []):
            if not isinstance(posterior, dict):
                continue
            interval = posterior.get("credible_interval_95") or [0, 0]
            rows.append(
                "<tr>"
                f"<td>{metric_label(metric)}</td>"
                f"<td class=\"numeric\">{posterior.get('successes')}</td>"
                f"<td class=\"numeric\">{posterior.get('trials')}</td>"
                f"<td class=\"numeric\">{format_percent(posterior.get('observed_rate'))}</td>"
                f"<td class=\"numeric\">{format_percent(posterior.get('posterior_mean'))}</td>"
                f"<td class=\"numeric\">{format_percent(interval[0])} - {format_percent(interval[1])}</td>"
                "</tr>"
            )
    if not rows:
        return ""
    return f"""
    <section>
      <h2>{lang("Statistical Uncertainty", "統計的不確実性")}</h2>
      <p class="note section-note">{lang("Beta-Binomial posterior with a uniform Beta(1,1) prior. The interval shows a 95% credible range for the underlying rate in this ROI definition.", "一様事前分布 Beta(1,1) を用いたBeta-Binomialの事後分布。区間は、このROI定義における真の率の95%信用区間を示します。")}</p>
      <div class="table-scroll">
        <table>
          <thead><tr><th>{lang("Metric", "指標")}</th><th class="numeric">{lang("Successes", "成功数")}</th><th class="numeric">{lang("Trials", "試行数")}</th><th class="numeric">{lang("Observed", "観測値")}</th><th class="numeric">{lang("Posterior Mean", "事後平均")}</th><th class="numeric">{lang("95% Credible Interval", "95%信用区間")}</th></tr></thead>
          <tbody>{''.join(rows)}</tbody>
        </table>
      </div>
    </section>
    """


def facade_section(rows: list[dict[str, str]]) -> str:
    if not rows:
        return ""
    body = "\n".join(
        "<tr>"
        f"<td>{html.escape(row['zone'])}</td>"
        f"<td class=\"numeric\">{row['exposed_count']}</td>"
        f"<td class=\"numeric\">{row['slowed_count']}</td>"
        f"<td class=\"numeric\">{row['stopped_count']}</td>"
        f"<td class=\"numeric\">{row['entered_after_exposure_count']}</td>"
        f"<td class=\"numeric\">{row['first_touch_entry_count']}</td>"
        f"<td class=\"numeric\">{row['last_touch_entry_count']}</td>"
        f"<td class=\"numeric\">{format_percent(row['exposure_to_entry_rate'])}</td>"
        f"<td class=\"numeric\">{format_percent(row['first_touch_entry_rate'])}</td>"
        f"<td class=\"numeric\">{format_seconds(row['dwell_median_s'])}</td>"
        f"<td class=\"numeric\">{format_seconds(row['median_time_to_entry_s'])}</td>"
        "</tr>"
        for row in rows
    )
    return f"""
    <section>
      <h2>{lang("Facade Zone Matrix", "ファサード分割マトリックス")}</h2>
      <p class="note section-note">{lang("Last-touch near the entrance is expected by definition, so upstream signals such as first-touch, dwell, and non-entry exposure are more useful for interpreting facade contribution.", "入口近傍のlast-touchは定義上起きやすいため、ファサード寄与を見るにはfirst-touch、滞在、非入店接触などの上流シグナルを重視します。")}</p>
      <div class="table-scroll">
        <table>
          <thead><tr><th>{lang("Zone", "領域")}</th><th class="numeric">{lang("Contacts", "接触")}</th><th class="numeric">{lang("Slowed", "減速")}</th><th class="numeric">{lang("Stopped", "停止")}</th><th class="numeric">{lang("Contact-to-Entry", "接触後入店")}</th><th class="numeric">{lang("First-touch Entry", "初回接触入店")}</th><th class="numeric">{lang("Last-touch Entry", "最終接触入店")}</th><th class="numeric">{lang("Contact Entry Rate", "接触後入店率")}</th><th class="numeric">{lang("First-touch Rate", "初回接触率")}</th><th class="numeric">{lang("Median Dwell", "滞在中央値")}</th><th class="numeric">{lang("Median Time to Entry", "入店まで中央値")}</th></tr></thead>
          <tbody>{body}</tbody>
        </table>
      </div>
    </section>
    """


def definitions_section() -> str:
    rows = [
        (
            lang("Traffic ROI", "Traffic ROI"),
            lang("The walkable observation area used as the denominator for passers.", "通行者の分母として使う歩行観測領域。"),
        ),
        (
            lang("Interest ROI", "Interest ROI"),
            lang("The storefront contact area where a passer is considered exposed to the facade.", "ファサードに接触・視認したとみなす店頭接触領域。"),
        ),
        (
            lang("Entrance ROI", "Entrance ROI"),
            lang("The inside-floor area used to confirm that a track entered the store.", "入店したことを確認するための店内床面領域。"),
        ),
        (
            lang("Passers", "通行者"),
            lang("Unique tracks that appear in Traffic ROI for enough time to be counted.", "Traffic ROI内に一定時間以上現れたユニークトラック数。"),
        ),
        (
            lang("Exposed", "接触"),
            lang("Passers whose foot point intersects Interest ROI or a facade zone.", "足元点がInterest ROIまたはファサード分割領域に入った通行者数。"),
        ),
        (
            lang("Entry Rate", "入店率"),
            lang("Entries divided by passers. This rate depends directly on the Traffic ROI definition.", "入店数を通行者数で割った率。Traffic ROIの定義に直接依存します。"),
        ),
        (
            lang("First-touch Entry", "初回接触入店"),
            lang("Entries whose first facade-zone contact occurred in the zone.", "入店者の最初のファサード接触がその領域だった件数。"),
        ),
        (
            lang("Last-touch Entry", "最終接触入店"),
            lang("Entries whose last facade-zone contact before entry occurred in the zone. Entrance-adjacent zones are naturally favored.", "入店前の最後のファサード接触がその領域だった件数。入口近傍領域は定義上有利です。"),
        ),
        (
            lang("Beta-Binomial", "Beta-Binomial"),
            lang("A binomial rate model with uncertainty. It is useful here because the sample is short and the true rate is not known exactly.", "率の不確実性を扱う二項モデル。短い動画サンプルでは真の率が一点で決まらないため有効です。"),
        ),
    ]
    body = "\n".join(f"<tr><td>{term}</td><td>{definition}</td></tr>" for term, definition in rows)
    return f"""
    <section>
      <h2>{lang("Metric Definitions", "指標定義")}</h2>
      <div class="table-scroll">
        <table>
          <thead><tr><th>{lang("Metric", "指標")}</th><th>{lang("Definition", "定義")}</th></tr></thead>
          <tbody>{body}</tbody>
        </table>
      </div>
    </section>
    """


def metric_label(metric: str) -> str:
    labels = {
        "entry": lang("Entry", "入店"),
        "exposure": lang("Exposure", "接触"),
        "stop": lang("Stop", "停止"),
    }
    return labels.get(metric, html.escape(metric.title()))


def format_percent(value: object) -> str:
    return f"{float(value) * 100:.1f}%"


def format_seconds(value: object) -> str:
    if value in {"", None}:
        return ""
    return f"{float(value):.1f}s"


def figures_html(paths: list[str], output_path: Path) -> str:
    items = []
    for path in paths:
        figure = Path(path)
        src = os.path.relpath(figure.resolve(), output_path.resolve().parent)
        if figure.suffix.lower() in {".mp4", ".mov", ".webm"}:
            items.append(f'<video src="{src}" controls preload="metadata" playsinline></video>')
        else:
            items.append(f'<img src="{src}" alt="{figure.name}">')
    return "\n".join(items)
