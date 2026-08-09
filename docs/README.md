# Storefront Behavior Analytics Public Artifact

English | [日本語](#日本語)

This folder contains a minimal anonymized artifact for sharing.

Open `index.html` in a browser to view the full report with the embedded debug video. GitHub Markdown may not reliably play local MP4 files inline, so the README links to the video file rather than depending on inline playback.

Included:

- `index.html`: bilingual EN/JP analytics report for `Store A`
- `figures/store_a_behavior_debug_h264.mp4`: anonymized debug video with ROIs, tracks, detection boxes, and entry counter
- `figures/store_a_anonymized_check.jpg`: sample frame used to confirm masking
- `configs/store_a_anonymized.yaml`: anonymized ROI and privacy-mask configuration

Debug video:

```text
figures/store_a_behavior_debug_h264.mp4
```

Summary observations:

Open `index.html` in a browser to view the full bilingual report, including KPI cards, the funnel, statistical uncertainty, facade-zone matrix, metric definitions, entry tracks, and the anonymized debug video.

The sample shows `227` observed passers in the configured Traffic ROI, `86` facade exposures, and `16` entries. The observed entry rate is therefore `16 / 227 = 7.0%`. With a Beta-Binomial model, the posterior mean is `7.4%` and the 95% credible interval is `4.4% - 11.1%`. This range is more useful than the point estimate alone: in a short clip, the underlying entry tendency should be read as a band of plausible values rather than a fixed number.

The observed exposure rate is `86 / 227 = 37.9%`. The posterior mean is `38.0%` and the 95% credible interval is `31.8% - 44.4%`. In this sample, a substantial minority of passers entered the storefront contact area, but most passers still continued through the traffic area without measurable facade contact. This makes the ROI definition important: widening the Traffic ROI increases the denominator and makes the rate more conservative.

The facade-zone matrix is best read as a path-analysis aid, not a causal attribution model. The entrance-adjacent zone naturally dominates last-touch signals because customers must pass near the entrance to enter. The more interesting signal is upstream first-touch: window zones away from the entrance can still become the first recorded facade contact before an eventual entry. That suggests the facade may work as a distributed attention surface, while the entrance area acts as the final conversion point.

The strongest practical takeaway is methodological. A single, short, handheld storefront clip can produce a useful diagnostic workflow: define traffic/contact/entrance regions, stabilize the footage, track people, inspect entry events, quantify uncertainty, and review facade-zone paths. The result should not be used as a definitive store performance evaluation. It is better framed as an anonymized analytics demo and a hypothesis generator for longer, better-controlled observation.

Not included:

- Raw videos
- Unmasked debug images or videos
- Per-person track CSVs
- Store-name-bearing metrics, stats, or historical reports

Notes:

- The report intentionally uses `Store A` instead of a real store name.
- The video masks storefront signs and visible in-window brand text.
- People remain visible at low resolution. The artifact is intended as an anonymized analytics demo, not an evaluation of a specific real-world store.

## 日本語

このフォルダには、共有用の最小限の匿名化済みアーティファクトが含まれています。

デバッグ動画込みの完全なレポートは、ブラウザで `index.html` を開くと確認できます。GitHubのMarkdownではローカルMP4がREADME内で安定してインライン再生されるとは限らないため、READMEでは動画ファイルへのリンクとして案内しています。

含まれるもの:

- `index.html`: `Store A` の日英切替分析レポート
- `figures/store_a_behavior_debug_h264.mp4`: ROI、軌跡、検出枠、入店カウンターを含む匿名化デバッグ動画
- `figures/store_a_anonymized_check.jpg`: マスキング確認用のサンプルフレーム
- `configs/store_a_anonymized.yaml`: 匿名化済みROI・プライバシーマスク設定

デバッグ動画:

```text
figures/store_a_behavior_debug_h264.mp4
```

含まれないもの:

- raw動画
- 未マスクのデバッグ画像・動画
- 個人単位のトラックCSV
- 店舗名を含むメトリクス、統計、過去レポート

注記:

- レポートでは実店舗名ではなく `Store A` を使用しています。
- 動画では店舗看板とウィンドウ内のブランド文字をマスクしています。
- 人物は低解像度で写っています。このアーティファクトは特定の実店舗を評価するものではなく、匿名化した分析デモとして扱います。

## 所見

詳細な分析結果は、ブラウザで `index.html` を開くと確認できます。KPI、ファネル、統計的不確実性、ファサード分割マトリックス、メトリクス定義、入店トラック、匿名化デバッグ動画を含む日英切替レポートになっています。

このサンプルでは、Traffic ROI内の観測通行者が `227`、ファサード接触が `86`、入店が `16` でした。したがって観測された入店率は `16 / 227 = 7.0%` です。Beta-Binomialモデルでは、事後平均は `7.4%`、95%信用区間は `4.4% - 11.1%` です。短い動画では一点の率だけを見るより、「真の入店傾向はこの程度の幅であり得る」と読むほうが自然です。

観測された接触率は `86 / 227 = 37.9%` です。事後平均は `38.0%`、95%信用区間は `31.8% - 44.4%` です。このサンプルでは、通行者の一定割合が店頭接触領域に入っていますが、多くの人はTraffic ROIを通過するだけで、ファサード接触までは至っていません。そのため、Traffic ROIをどこまで広く取るかが結果に大きく影響します。今回の定義は分母を広めに取っているため、率はやや保守的に出ます。

ファサード分割は、売場・ウィンドウの効果を断定するものではなく、入店前の経路を読むための補助線として見るのが適切です。入口近傍領域のlast-touchが強く出るのは、入店者が入口前を通る以上、定義上かなり自然です。むしろ見る価値があるのは、入口から離れたウィンドウ領域が入店者の初回接触点になっている点です。これは、ファサード全体が注意を拾い、最終的に入口周辺で回収する、という仮説につながります。

この分析で一番意味があるのは、特定店舗の良し悪しを評価することではなく、店頭行動分析のワークフローが成立することを示せた点です。ROIを定義し、手ブレを補正し、人物を追跡し、入店イベントを目視確認し、統計的不確実性を付け、ファサード別の接触経路を見る。この一連の流れは、より長時間・複数日・固定カメラの観測に拡張すれば、店舗設計やファサード改善の仮説検証に使える可能性があります。
