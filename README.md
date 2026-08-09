# Mall Storefront Behavior Analytics

English | [日本語](#日本語)

Anonymous behavior analytics for storefront videos.

The app analyzes pedestrian flow around a storefront using manually configured ROIs, person detection, tracking, and aggregate behavior metrics. It can generate bilingual EN/JP reports with anonymized videos.

![Storefront flow analytics tracking preview](docs/figures/store_a_tracking_thumbnail.jpg)

## Demo Results

| Metric | Result |
|---|---:|
| Passers | 227 |
| Facade exposures | 86 |
| Entries | 16 |
| Entry rate | 7.0% |
| Entry rate 95% credible interval | 4.4% - 11.1% |
| Exposure rate | 37.9% |
| Exposure rate 95% credible interval | 31.8% - 44.4% |

View the full bilingual report:

- GitHub Pages: enable Pages from `/docs`, then open `https://<owner>.github.io/<repository>/`
- Local file: open `docs/index.html` in a browser
- Debug video file: `docs/figures/store_a_behavior_debug_h264.mp4`

GitHub's repository README shows this preview image and summary table directly on the repository top page. The full HTML report and embedded video are best viewed through GitHub Pages or by opening the local HTML file.

## Public Artifact

The shareable anonymized sample is in:

```text
docs/index.html
```

Open this HTML file in a browser to view the full results. The richer written observations are in `docs/README.md`.

Debug video:

```text
docs/figures/store_a_behavior_debug_h264.mp4
```

GitHub Markdown may not reliably play local MP4 files inline. Use `docs/index.html` for the browser-viewable report with the embedded debug video, or open the MP4 file directly.

It includes:

- Aggregate storefront metrics
- Beta-Binomial uncertainty summaries
- Facade-zone analysis
- An anonymized debug video with storefront-name masks
- Metric definitions in English and Japanese
- Summary observations written as an anonymized method demonstration

The repository intentionally excludes raw videos, unmasked outputs, and store-name-bearing intermediate files through `.gitignore`.

## Development

Install the package in editable mode, then run tests:

```bash
pip install -e .
pytest -q
```

Analyze a video with an anonymized config:

```bash
env PYTHONPATH=src python -m mallflow.cli analyze \
  --config configs/store_a.yaml \
  --sample-fps 10 \
  --detector yolo \
  --tracker bytetrack \
  --output-dir outputs/store_a
```

Create a report:

```bash
env PYTHONPATH=src python -m mallflow.cli report \
  --metrics outputs/store_a/metrics/store_a_metrics.yaml \
  --tracks outputs/store_a/tracks/store_a_tracks.csv \
  --display-name "Store A" \
  --output outputs/reports/store_a_report.html
```

Create or update ROI annotations:

```bash
env PYTHONPATH=src python -m mallflow.cli annotate \
  --video data/raw/store_a.mp4 \
  --store STORE_A \
  --output configs/store_a.yaml \
  --display-width 1400 \
  --time 60
```

Annotation controls:

- Click polygon points for `Traffic ROI`, then press Space or Enter.
- Click polygon points for `Interest ROI`, then press Space or Enter.
- Click polygon points for `Entrance ROI`, then press `S` to save.
- Use `U` or Backspace to undo the current step.
- Use `Q` or Esc to cancel.
- Use `+` and `-` to resize the annotation window.

## 日本語

店頭動画を対象にした、匿名化前提の行動分析ツールです。

手動で設定したROI、人物検出、トラッキング、集計メトリクスを使って、店舗前の歩行者動線を分析します。匿名化済み動画を含む日英切替レポートも生成できます。

## デモ結果

| 指標 | 結果 |
|---|---:|
| 通行者 | 227 |
| ファサード接触 | 86 |
| 入店 | 16 |
| 入店率 | 7.0% |
| 入店率 95%信用区間 | 4.4% - 11.1% |
| 接触率 | 37.9% |
| 接触率 95%信用区間 | 31.8% - 44.4% |

詳細な日英切替レポートを見る方法:

- GitHub Pages: `/docs` からPagesを有効化し、`https://<owner>.github.io/<repository>/` を開く
- ローカルファイル: `docs/index.html` をブラウザで開く
- デバッグ動画ファイル: `docs/figures/store_a_behavior_debug_h264.mp4`

GitHubのリポジトリトップページでは、このREADMEのプレビュー画像とサマリーテーブルが直接表示されます。HTMLレポートと埋め込み動画は、GitHub PagesまたはローカルHTMLで見るのが確実です。

## 公開用アーティファクト

共有用の匿名化済みサンプルは以下にあります。

```text
docs/index.html
```

分析結果の本体は、このHTMLをブラウザで開くと確認できます。より詳しい所見は `docs/README.md` に記載しています。

デバッグ動画:

```text
docs/figures/store_a_behavior_debug_h264.mp4
```

GitHubのMarkdownでは、ローカルMP4がREADME内で安定してインライン再生されるとは限りません。デバッグ動画込みで見る場合は `docs/index.html` をブラウザで開くか、MP4ファイルを直接開いてください。

含まれるもの:

- 店頭集計メトリクス
- Beta-Binomialによる不確実性の要約
- ファサード分割分析
- 店舗名をマスクした匿名化デバッグ動画
- 英語・日本語のメトリクス定義
- 匿名化された手法デモとしての所見

raw動画、未マスク出力、店舗名を含む中間ファイルは `.gitignore` で除外しています。

## 開発

編集可能モードでインストールし、テストを実行します。

```bash
pip install -e .
pytest -q
```

匿名化された設定で動画を分析します。

```bash
env PYTHONPATH=src python -m mallflow.cli analyze \
  --config configs/store_a.yaml \
  --sample-fps 10 \
  --detector yolo \
  --tracker bytetrack \
  --output-dir outputs/store_a
```

レポートを作成します。

```bash
env PYTHONPATH=src python -m mallflow.cli report \
  --metrics outputs/store_a/metrics/store_a_metrics.yaml \
  --tracks outputs/store_a/tracks/store_a_tracks.csv \
  --display-name "Store A" \
  --output outputs/reports/store_a_report.html
```

ROIアノテーションを作成・更新します。

```bash
env PYTHONPATH=src python -m mallflow.cli annotate \
  --video data/raw/store_a.mp4 \
  --store STORE_A \
  --output configs/store_a.yaml \
  --display-width 1400 \
  --time 60
```

アノテーション操作:

- `Traffic ROI` の多角形点をクリックし、SpaceまたはEnterを押します。
- `Interest ROI` の多角形点をクリックし、SpaceまたはEnterを押します。
- `Entrance ROI` の多角形点をクリックし、`S` で保存します。
- `U` またはBackspaceで現在のステップを戻します。
- `Q` またはEscでキャンセルします。
- `+` と `-` で表示サイズを調整します。
