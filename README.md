# ASCII Diamond Ring

A real-time software 3D ring animation rendered as dense ASCII in a 1100×1000 window. A 200×150 character grid is rasterized from triangle meshes for the ring band, brilliant-cut diamond, gallery rail, and four prongs. The ring turns continuously through 360° (about one lap every 15 seconds at default speed). A perspective camera, depth buffer, fixed and moving lights, drifting particles, moving orbit glints, and a pulsing diamond flare shade the characters. The image comes from the 3D scene rather than a pre-made picture.

## Run

Requires Python 3.10 or newer.

```powershell
python -m pip install -r requirements.txt
python diamond_ring.py
```

The animation opens in a 1100×1000 window and automatically plays the included song on loop. The lower corner shows the current rotation, particle count, and visible ASCII character count. Close the window or press `Esc` to exit. To use the terminal renderer, run `python diamond_ring.py --terminal` and press `Ctrl+C` to stop.

## Options

```powershell
python diamond_ring.py --quality 3 --speed 0.7 --fps 24
python diamond_ring.py --no-color --terminal
```

- `--quality 1|2|3`: particle density (default `2`).
- `--speed VALUE`: motion speed multiplier (default `1.0`).
- `--fps VALUE`: target frame rate, capped at 60 (default `20`; actual rate depends on the computer).
- `--terminal`: render in the terminal instead of the square window.
- `--no-color`: use monochrome output in terminal mode.
