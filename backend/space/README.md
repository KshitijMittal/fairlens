---
title: FairLens API
emoji: ⚖️
colorFrom: indigo
colorTo: blue
sdk: gradio
sdk_version: 6.31.0
python_version: 3.12
app_file: app.py
pinned: false
---

The FairLens analysis API (M0). It runs the three bundled samples through the real
engine and serves the result over HTTPS; the web app is deployed separately.

The SDK must stay on Gradio 6.x: Gradio 5 requires `pandas<3`, and the engine pins
`pandas==3.1.0`.
