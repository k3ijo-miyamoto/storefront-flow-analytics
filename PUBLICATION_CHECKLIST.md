# Publication Checklist

Use this repository as code plus a minimal anonymized artifact.

Safe to publish:

- `.gitignore`
- `README.md`
- `pyproject.toml`
- `src/`
- `tests/`
- `configs/bytetrack_storefront.yaml`
- `docs/`

Do not publish:

- `data/raw/`
- `data/processed/`
- `outputs/`
- Real-store ROI configs under `configs/*.yaml`
- Local planning/spec documents that mention real stores

Before publishing:

```bash
rg -n "<real-store-name-regex>" \
  README.md .gitignore pyproject.toml src tests public_artifact configs/bytetrack_storefront.yaml
```

The command should return no matches.

For a browser-viewable report on GitHub:

1. Push the repository.
2. Open repository Settings.
3. Open Pages.
4. Set the source to the main branch and `/docs`.
5. Open `https://k3ijo-miyamoto.github.io/storefront-flow-analytics/`.

If this is an existing git repository and sensitive files were already tracked, `.gitignore` alone is not enough. Remove them from the index before pushing:

```bash
git rm --cached -r data outputs
git rm --cached mall_storefront_behavior_analytics_SPEC.md
git rm --cached configs/*.yaml
git add configs/bytetrack_storefront.yaml
```
