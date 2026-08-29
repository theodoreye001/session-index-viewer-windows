# Windows Step 3.5 validation

This step fixes Codex visualization images referenced from session text as local
`file:///.../.codex/visualizations/...` URLs. Browsers block those URLs when the
viewer itself is served from `http://127.0.0.1:7333`.

The server now rewrites those URLs to:

```text
/api/codex-visualization?path=<relative-path>
```

and serves the image from the current user's `~/.codex/visualizations` directory.

## Security boundary

The endpoint accepts relative paths only and resolves them below:

```text
~/.codex/visualizations
```

It rejects:

- absolute paths
- `..` traversal
- paths that resolve outside the visualization root
- missing files
- unsupported file types
- files larger than 25 MiB
- SVG files

Allowed image formats are PNG, JPEG, WebP, GIF, and BMP. Responses include
`X-Content-Type-Options: nosniff` and `Cross-Origin-Resource-Policy: same-origin`.

## Windows validation

Update the branch and run the complete test suite:

```powershell
git pull
py -m unittest discover -s tests -v
```

Because the backend changed, restart the viewer:

```powershell
# stop the existing server with Ctrl+C, then
py server.py
```

Open:

```text
http://127.0.0.1:7333
```

Find a Codex session whose last reply contains a visualization image. The image
should render inside the card. In browser DevTools, its `src` should begin with:

```text
/api/codex-visualization?path=
```

The original absolute Windows path should no longer be exposed to the browser as
a `file:///` image source.

## Regression checks

Also confirm:

1. Codex and Claude session lists still load.
2. Codex Resume still opens Windows Terminal and resumes the selected session.
3. A request such as `/api/codex-visualization?path=../secret.png` returns 404.
