# Build the browser version of the games

Editing a game does **not** change its browser version. The games under
`web/` and the site under `docs/` are generated copies, so after changing a
game you have to rebuild.

## The one command you normally want

```bash
sh tools/deploy.sh                          # all games
sh tools/deploy.sh bowling-2                # just one, much faster
sh tools/deploy.sh bowling-2 "fixed score"  # with your own commit message
```

`deploy.sh` does the whole trip: rebuild -> `git commit` -> `git push`. GitHub
Pages then redraws the site at
<https://levmelah-ship-it.github.io/python-games/> within a minute or two.
If the page still shows the old version, reload without cache (Ctrl+Shift+R).

To rebuild without publishing:

```bash
sh tools/rebuild.sh              # all games
sh tools/rebuild.sh bowling-2    # just one, much faster
```

That runs four steps, which can also be run on their own:

```bash
python3 tools/stage.py          # web/<slug>/main.py  + its images
sh tools/build_all.sh           # pygbag -> web/<slug>/build/web/
python3 tools/publish.py        # copy the builds into docs/
python3 tools/generate_site.py  # docs/index.html
```

`docs/` is what GitHub Pages serves. Everything else is regenerated, which is
why `web/` and `build/` are in `.gitignore`. Publishing by hand is the last two
steps of `deploy.sh`:

```bash
git add -A && git commit -m "update games" && git push
```

The site is at <https://levmelah-ship-it.github.io/python-games/> once GitHub
Pages is pointed at branch `main`, folder `/docs`
(repository Settings -> Pages).

## What each script does

| script | job |
| --- | --- |
| `convert.py` | Rewrites one game for the browser. Finds the main loop (the `while` holding `pygame.event.get`), puts `await asyncio.sleep(0)` at the top of it, turns every function on the call path into `async def`, adds the matching `await`s, wraps the entry point in `asyncio.run`, and installs a fallback font because a browser has no system fonts. The original game file is never touched. |
| `stage.py` | Runs `convert.py` over every game in `manifest.tsv` and copies the images each one needs. |
| `publish.py` | Copies each finished build into `docs/<slug>/` and writes `playable.txt`. |
| `generate_site.py` | Writes `docs/index.html` from `manifest.tsv`, `playable.txt` and `native.tsv`. |
| `rebuild.sh` | Runs the four scripts above in order. |
| `deploy.sh` | Runs `rebuild.sh`, then commits and pushes to GitHub. |

## The two tables

- `manifest.tsv` — one row per browser game: source file, URL slug, title,
  and the asset files to copy as `source>destination`, separated by `;`.
  Add a row here to put another pygame game on the site.
- `native.tsv` — the games that cannot run in a browser (ursina, Panda3D,
  tkinter, turtle, PySide6). They appear on the site as source links only.

## Before the first publish

`generate_site.py` has a `REPO_URL` near the top, still set to `USERNAME`.
Change it to the real repository address, or the source links will be dead.

## Testing locally: never use the word "localhost"

Serve `docs/` with any static server, then open it as **`http://127.0.0.1:<port>/`**.
Opening the very same server as `http://localhost:<port>/` gives a grey screen and
nothing else, because pygbag's loader contains this:

```python
elif platform.window.location.href.startswith("http://localhost:8"):
    rewritecdn = "http://localhost:8000/cdn/"
```

Any `http://localhost:8…` address switches pygbag into development mode, where it
stops downloading the Python runtime from the real CDN and looks for a local copy
on port 8000 instead. With a plain `python3 -m http.server` there is nothing there,
so `pygame_ce` never loads, `import pygame` yields an empty stub, and the first line
that touches `pygame.font` raises `AttributeError: module 'pygame' has no attribute
'font'`. `127.0.0.1` does not match that string, so the real CDN is used.

This only ever affects local testing. A real domain, GitHub Pages included, is not
`localhost` and never enters that mode.

To see what actually went wrong inside a game, append `#debug` to its URL:
`http://127.0.0.1:8222/bowling-2/#debug` opens a console with the Python traceback.

## Checking a conversion without a browser

A converted `main.py` is ordinary async Python, so it also runs on the desktop:

```bash
cd web/<slug>
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy PYTHONWARNINGS=always \
  timeout 8 python3 main.py
```

Exit code 124 means it was still running when the timeout hit, which is what
you want. A `RuntimeWarning: coroutine ... was never awaited` means a call to
an async function is missing its `await`.
