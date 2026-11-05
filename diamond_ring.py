"""A small software 3D renderer for a cinematic ASCII engagement ring."""

from __future__ import annotations

import argparse
import math
import os
import random
import shutil
import sys
import time
from dataclasses import dataclass
from pathlib import Path


Vec3 = tuple[float, float, float]
Triangle = tuple[Vec3, Vec3, Vec3, str]
RAMP = " .,:;irsXA253hMHGS#9B&@"
GOLD = (218, 166, 86)
WHITE = (232, 238, 248)


def add(a: Vec3, b: Vec3) -> Vec3:
    return a[0] + b[0], a[1] + b[1], a[2] + b[2]


def sub(a: Vec3, b: Vec3) -> Vec3:
    return a[0] - b[0], a[1] - b[1], a[2] - b[2]


def scale(a: Vec3, k: float) -> Vec3:
    return a[0] * k, a[1] * k, a[2] * k


def dot(a: Vec3, b: Vec3) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross(a: Vec3, b: Vec3) -> Vec3:
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def normalize(a: Vec3) -> Vec3:
    length = math.sqrt(dot(a, a)) or 1.0
    return scale(a, 1.0 / length)


def rotate_z(p: Vec3, angle: float) -> Vec3:
    c, s = math.cos(angle), math.sin(angle)
    return p[0] * c - p[1] * s, p[0] * s + p[1] * c, p[2]


def rotate_x(p: Vec3, angle: float) -> Vec3:
    c, s = math.cos(angle), math.sin(angle)
    return p[0], p[1] * c - p[2] * s, p[1] * s + p[2] * c


def mesh_torus(major: float = 1.05, tube: float = 0.105, around: int = 112, sides: int = 18, center_z: float = 0.0, horizontal: bool = False) -> list[Triangle]:
    triangles: list[Triangle] = []
    for i in range(around):
        u0, u1 = 2 * math.pi * i / around, 2 * math.pi * (i + 1) / around
        for j in range(sides):
            v0, v1 = 2 * math.pi * j / sides, 2 * math.pi * (j + 1) / sides

            def point(u: float, v: float) -> Vec3:
                radius = major + tube * math.cos(v)
                if horizontal:
                    return radius * math.cos(u), radius * math.sin(u), center_z + tube * math.sin(v)
                return radius * math.cos(u), tube * math.sin(v), center_z + radius * math.sin(u)

            a, b, c, d = point(u0, v0), point(u1, v0), point(u1, v1), point(u0, v1)
            triangles.extend(((a, b, c, "metal"), (a, c, d, "metal")))
    return triangles


def mesh_diamond(sides: int = 12) -> list[Triangle]:
    """Brilliant cut with table, crown, girdle, pavilion, and culet facets."""
    triangles: list[Triangle] = []
    top_z, girdle_z, lower_z, culet_z = 2.02, 1.60, 1.45, 1.00
    table_r, crown_r, girdle_r, pavilion_r = 0.27, 0.46, 0.52, 0.40
    table, girdle, pavilion = [], [], []
    for i in range(sides):
        a = 2 * math.pi * i / sides + math.pi / sides / 2
        girdle.append((girdle_r * math.cos(a), girdle_r * math.sin(a), girdle_z))
        pavilion.append((pavilion_r * math.cos(a), pavilion_r * math.sin(a), lower_z))
        table.append((table_r * math.cos(a), table_r * math.sin(a), top_z))
    table_center: Vec3 = (0, 0, top_z)
    culet: Vec3 = (0, 0, culet_z)
    for i in range(sides):
        n = (i + 1) % sides
        # Table and crown star facets.
        triangles.append((table_center, table[i], table[n], "gem"))
        triangles.extend(((table[i], girdle[i], girdle[n], "gem"), (table[i], girdle[n], table[n], "gem")))
        # Girdle band and pavilion facets split into alternating triangles.
        triangles.append((girdle[i], pavilion[i], girdle[n], "gem"))
        triangles.append((girdle[n], pavilion[i], pavilion[n], "gem"))
        triangles.append((pavilion[i], culet, pavilion[n], "gem"))
    return triangles


def rod(a: Vec3, b: Vec3, radius: float, sides: int = 8, material: str = "metal") -> list[Triangle]:
    axis = normalize(sub(b, a))
    helper = (0.0, 0.0, 1.0) if abs(axis[2]) < 0.9 else (0.0, 1.0, 0.0)
    u, v = normalize(cross(axis, helper)), normalize(cross(axis, normalize(cross(axis, helper))))
    ring_a, ring_b = [], []
    for i in range(sides):
        t = 2 * math.pi * i / sides
        offset = add(scale(u, radius * math.cos(t)), scale(v, radius * math.sin(t)))
        ring_a.append(add(a, offset))
        ring_b.append(add(b, offset))
    result: list[Triangle] = []
    for i in range(sides):
        n = (i + 1) % sides
        result.extend(((ring_a[i], ring_b[i], ring_b[n], material), (ring_a[i], ring_b[n], ring_a[n], material)))
    return result


def build_scene() -> list[Triangle]:
    triangles = mesh_torus(tube=0.13, around=72, sides=12) + mesh_diamond()
    # A slim gallery rail supporting the girdle.
    triangles.extend(mesh_torus(0.37, 0.035, 36, 6, 1.59, horizontal=True))
    # Four tapered prongs rise from the band to hold the girdle.
    for angle in (math.pi / 4, 3 * math.pi / 4, 5 * math.pi / 4, 7 * math.pi / 4):
        x, y = math.cos(angle), math.sin(angle)
        triangles.extend(rod((0.84 * x, 0.84 * y, 0.10), (0.37 * x, 0.37 * y, 1.70), 0.038))
        triangles.extend(rod((0.37 * x, 0.37 * y, 1.64), (0.31 * x, 0.31 * y, 1.79), 0.029))
    return triangles


@dataclass
class Camera:
    distance: float = 5.4
    focal: float = 2.0
    target_z: float = 0.68

    def project(self, p: Vec3, width: int, height: int) -> tuple[float, float, float] | None:
        # Camera looks along +Y; rotating the whole model gives changing views.
        depth = self.distance + p[1]
        if depth < 0.3:
            return None
        f = self.focal * min(width / 2.8, height / 1.4)
        # Terminal cells are taller than they are wide; compensate in vertical projection.
        return width / 2 + p[0] * f / depth, height / 2 - (p[2] - self.target_z) * f * 0.92 / depth, depth


class ParticleSystem:
    def __init__(self, count: int, seed: int = 19) -> None:
        rng = random.Random(seed)
        self.items = []
        for _ in range(count):
            self.items.append([rng.uniform(-2.4, 2.4), rng.uniform(-1.2, 1.2), rng.uniform(-1.5, 2.8),
                               rng.uniform(0.08, 0.32), rng.uniform(0.25, 1.0), rng.random() * 6.28])

    def update(self, dt: float) -> None:
        for p in self.items:
            p[1] += p[3] * dt
            p[0] += math.sin(p[5]) * 0.035 * dt
            p[5] += dt * 0.7
            if p[1] > 1.5:
                p[1] = -1.5


class ASCIIRenderer:
    def __init__(self, quality: int = 1, color: bool = True, columns: int | None = None, rows: int | None = None) -> None:
        self.quality, self.color = quality, color and sys.stdout.isatty()
        self.fixed_dimensions = (columns, rows)
        self.scene = build_scene()
        self.camera = Camera()
        self.particles = ParticleSystem(300 * quality)
        self.frame = 0
        self.started = time.monotonic()

    def dimensions(self) -> tuple[int, int]:
        if self.fixed_dimensions[0] is not None and self.fixed_dimensions[1] is not None:
            return self.fixed_dimensions[0], self.fixed_dimensions[1]
        size = shutil.get_terminal_size((100, 38))
        return max(50, min(150, size.columns)), max(20, min(55, size.lines - 3))

    def render(self, elapsed: float, speed: float) -> str:
        width, height = self.dimensions()
        zbuf = [[float("inf")] * width for _ in range(height)]
        lum = [[0.0] * width for _ in range(height)]
        colors = [[WHITE] * width for _ in range(height)]
        # Cycle through broad and brief edge-on views like the video reference.
        # A steady full turn keeps rotating forever; 24°/s makes one lap take 15 seconds.
        angle = math.radians(35) + elapsed * math.radians(24) * speed
        tilt = math.sin(elapsed * 0.11) * 0.11
        reveal = min(1.0, max(0.0, (elapsed - 0.25) / 4.3))
        sweep_angle = -math.pi + reveal * math.tau if reveal < 1 else (elapsed - 4.55) * 0.55 + math.pi
        key = normalize((-2.8, -3.0, 4.2))
        moving = normalize((2.2 * math.cos(elapsed * 0.9), -2.4, 2.5 + math.sin(elapsed * 0.7)))

        transformed: dict[Vec3, Vec3] = {}
        projected: dict[Vec3, tuple[float, float, float] | None] = {}

        def transform(p: Vec3) -> Vec3:
            cached = transformed.get(p)
            if cached is None:
                cached = rotate_x(rotate_z(p, angle), tilt)
                transformed[p] = cached
            return cached

        def project(p: Vec3) -> tuple[float, float, float] | None:
            if p not in projected:
                projected[p] = self.camera.project(transform(p), width, height)
            return projected[p]

        def plot(x: int, y: int, depth: float, brightness: float, rgb: tuple[int, int, int]) -> None:
            if 0 <= x < width and 0 <= y < height and depth < zbuf[y][x]:
                zbuf[y][x] = depth
                lum[y][x] = max(0.0, min(1.0, brightness))
                colors[y][x] = rgb

        def raster(tri: Triangle) -> None:
            material = tri[3]
            a, b, c = (transform(p) for p in tri[:3])
            normal = normalize(cross(sub(b, a), sub(c, a)))
            center = scale(add(add(a, b), c), 1 / 3)
            view = normalize((0, -1, 0))
            facing = dot(normal, view)
            # Shade both windings; the torus is visible from either side as it turns.
            n = normal if facing >= 0 else scale(normal, -1)
            pa, pb, pc = project(tri[0]), project(tri[1]), project(tri[2])
            if pa is None or pb is None or pc is None:
                return
            minx = max(0, int(min(pa[0], pb[0], pc[0])))
            maxx = min(width - 1, int(max(pa[0], pb[0], pc[0]) + 1))
            miny = max(0, int(min(pa[1], pb[1], pc[1])))
            maxy = min(height - 1, int(max(pa[1], pb[1], pc[1]) + 1))
            area = (pb[1] - pc[1]) * (pa[0] - pc[0]) + (pc[0] - pb[0]) * (pa[1] - pc[1])
            if abs(area) < 1e-7:
                return
            around = (math.atan2(center[2], center[0]) + math.pi) % math.tau / math.tau
            reveal_at = around if material == "metal" else 0.46 + around * 0.48
            reveal_fade = min(1.0, max(0.0, (reveal - reveal_at) / 0.035))
            if reveal_fade <= 0:
                return
            diffuse = max(0.0, dot(n, key)) * 0.68 + max(0.0, dot(n, moving)) * 0.54
            halfv = normalize(add(moving, view))
            spec = max(0.0, dot(n, halfv)) ** (26 if material == "metal" else 12)
            rim = (1 - max(0.0, dot(n, view))) ** 2 * 0.20
            if material == "gem":
                # Each triangular facet gets its own light response and hue.
                facet = (abs(n[0] * 0.31 + n[1] * 0.53 + n[2] * 0.79) % 1.0) * 0.13
                brightness = 0.23 + diffuse * 0.60 + spec * 0.72 + rim + facet
                rgb = (int(138 + 105 * min(1, diffuse + spec)), int(158 + 95 * min(1, diffuse + spec)), 255)
            else:
                brightness = 0.14 + diffuse * 0.70 + spec * 0.92 + rim
                rgb = (int(132 + 112 * min(1, diffuse + spec)), int(142 + 108 * min(1, diffuse + spec)), int(158 + 97 * min(1, diffuse + spec)))
            # A moving light streak sweeps across the metal and gemstone.
            surface_angle = math.atan2(center[2], center[0])
            angle_delta = math.atan2(math.sin(surface_angle - sweep_angle), math.cos(surface_angle - sweep_angle))
            streak = max(0.0, 1 - abs(angle_delta) / 0.11)
            brightness = (brightness + streak * (0.52 if material == "metal" else 0.72)) * reveal_fade
            for y in range(miny, maxy + 1):
                py = y + 0.5
                for x in range(minx, maxx + 1):
                    px = x + 0.5
                    wa = ((pb[1] - pc[1]) * (px - pc[0]) + (pc[0] - pb[0]) * (py - pc[1])) / area
                    wb = ((pc[1] - pa[1]) * (px - pc[0]) + (pa[0] - pc[0]) * (py - pc[1])) / area
                    wc = 1.0 - wa - wb
                    if min(wa, wb, wc) < -0.001:
                        continue
                    depth = wa * pa[2] + wb * pb[2] + wc * pc[2]
                    if depth < zbuf[y][x]:
                        zbuf[y][x] = depth
                        lum[y][x] = max(0.0, min(1.0, brightness))
                        colors[y][x] = rgb

        for triangle in self.scene:
            raster(triangle)

        # Sparse, depth tested dust and gold sparks. The trail pulses softly around the ring.
        for p in self.particles.items:
            x, y, z, velocity, intensity, phase = p
            q = transform((x + math.sin(elapsed * 0.3 + phase) * 0.035, y, z))
            proj = self.camera.project(q, width, height)
            if proj:
                sx, sy = int(proj[0]), int(proj[1])
                if proj[2] < zbuf[sy][sx] if 0 <= sx < width and 0 <= sy < height else False:
                    glow = intensity * (0.3 + 0.7 * (0.5 + 0.5 * math.sin(elapsed * 1.6 + phase))) * min(1, reveal * 2) * 0.32
                    if glow > max(0.16, lum[sy][sx]):
                        lum[sy][sx] = glow
                        colors[sy][sx] = GOLD if intensity < 0.8 else WHITE
        # Two dim, crossing light orbits add the airy loops visible in the reference.
        trail = (0.075 + 0.035 * (0.5 + 0.5 * math.sin(elapsed * 0.8))) * reveal
        for orbit in range(2):
            orbit_points = 420
            head = (elapsed * 0.72 + orbit * math.pi) % math.tau
            for i in range(orbit_points):
                a = i * math.tau / orbit_points
                if orbit == 0:
                    point = (1.62 * math.cos(a), 0.05, 0.85 + 1.05 * math.sin(a))
                else:
                    point = (1.62 * math.cos(a + 0.72), 0.62 * math.sin(a), 0.85 + 1.05 * math.sin(a))
                proj = project(point)
                if proj:
                    sx, sy = int(proj[0]), int(proj[1])
                    angular_distance = math.atan2(math.sin(a - head), math.cos(a - head))
                    orbit_glow = trail + 0.48 * math.exp(-((angular_distance / 0.075) ** 2))
                    if 0 <= sx < width and 0 <= sy < height and proj[2] < zbuf[sy][sx] and orbit_glow > lum[sy][sx]:
                        lum[sy][sx], colors[sy][sx] = orbit_glow, (185, 198, 220)

        # A brief eight-point star flare travels with the diamond table.
        stone = self.camera.project(transform((0.0, 0.0, 2.02)), width, height)
        sparkle = abs(math.sin(elapsed * 2.2)) ** 8 * reveal
        if stone and sparkle > 0.08:
            cx, cy = stone[0], stone[1]
            for ray in range(8):
                ray_angle = ray * math.tau / 8
                length = 11 if ray % 2 == 0 else 7
                for step in range(1, length + 1):
                    sx = int(round(cx + math.cos(ray_angle) * step))
                    sy = int(round(cy + math.sin(ray_angle) * step * 0.72))
                    brightness = sparkle * (1 - step / (length + 1))
                    if 0 <= sx < width and 0 <= sy < height and brightness > lum[sy][sx]:
                        lum[sy][sx], colors[sy][sx] = brightness, WHITE

        lines = []
        self.last_grid: list[list[tuple[str, tuple[int, int, int]]]] = []
        for y in range(height):
            row = []
            grid_row = []
            last = None
            for x in range(width):
                value = lum[y][x]
                # Keep dim lit surfaces as punctuation so fine metal detail survives at high density.
                char = RAMP[min(len(RAMP) - 1, max(1, int(value * (len(RAMP) - 1))))] if value > 0 else " "
                rgb = colors[y][x]
                grid_row.append((char, rgb))
                if self.color and char != " ":
                    if rgb != last:
                        row.append(f"\033[38;2;{rgb[0]};{rgb[1]};{rgb[2]}m")
                        last = rgb
                elif self.color and last is not None:
                    row.append("\033[0m")
                    last = None
                row.append(char)
            if self.color:
                row.append("\033[0m")
            lines.append("".join(row))
            self.last_grid.append(grid_row)
        self.frame += 1
        return "\n".join(lines)


class AnimationController:
    def __init__(self, quality: int, speed: float, fps: int, color: bool) -> None:
        self.renderer = ASCIIRenderer(quality, color)
        self.speed, self.fps = speed, fps

    def run(self) -> None:
        os.system("")  # Enable ANSI processing in Windows terminals.
        sys.stdout.write("\033[2J\033[?25l")
        sys.stdout.flush()
        previous = time.monotonic()
        try:
            while True:
                now = time.monotonic()
                dt = now - previous
                previous = now
                elapsed = now - self.renderer.started
                self.renderer.particles.update(dt)
                frame = self.renderer.render(elapsed, self.speed)
                phase = "LIGHT REVEAL" if elapsed < 4.55 else "SLOW ROTATION"
                status = f"\033[90m   DIAMOND  /  {phase}     {elapsed:05.1f}s     CTRL+C TO EXIT\033[0m"
                sys.stdout.write("\033[H" + frame + "\n" + status + "\033[J")
                sys.stdout.flush()
                time.sleep(max(0, 1 / self.fps - (time.monotonic() - now)))
        except KeyboardInterrupt:
            pass
        finally:
            sys.stdout.write("\033[0m\033[?25h\n")
            sys.stdout.flush()


class PygameAnimationController:
    """Present the dense character grid in a large near-square window."""

    def __init__(self, quality: int, speed: float, fps: int) -> None:
        self.speed, self.fps = speed, fps
        self.renderer = ASCIIRenderer(quality, color=False, columns=200, rows=150)

    def run(self) -> None:
        try:
            import pygame
        except ImportError as exc:
            raise SystemExit("pygame-ce is missing. Install dependencies with: python -m pip install -r requirements.txt") from exc

        pygame.init()
        try:
            pygame.mixer.init()
            song = Path(__file__).resolve().parent / "assets" / "jmsn-love-me-grok-song.mp3"
            pygame.mixer.music.load(str(song))
            pygame.mixer.music.set_volume(0.65)
            pygame.mixer.music.play(loops=-1)
        except (pygame.error, OSError):
            # Audio is optional; a missing device/codec should not block the animation.
            pass
        window = pygame.display.set_mode((1100, 1000))
        pygame.display.set_caption("Diamond Ring · ASCII 3D")
        clock = pygame.time.Clock()
        font = pygame.font.SysFont("Consolas", 7, bold=True)
        hud_font = pygame.font.SysFont("Consolas", 12, bold=True)
        glyph_cache: dict[tuple[str, tuple[int, int, int]], object] = {}
        cell_width, cell_height = 1100 / 200, 1000 / 150
        started = time.monotonic()
        running = True
        try:
            while running:
                dt = clock.tick(self.fps) / 1000.0
                for event in pygame.event.get():
                    if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                        running = False

                elapsed = time.monotonic() - started
                self.renderer.particles.update(dt)
                self.renderer.render(elapsed, self.speed)
                ascii_count = sum(char != " " for row in self.renderer.last_grid for char, _ in row)
                window.fill((0, 0, 0))
                for row_index, row in enumerate(self.renderer.last_grid):
                    y = round(row_index * cell_height)
                    for col_index, (char, color) in enumerate(row):
                        if char != " ":
                            color_key = tuple((int(channel) // 16) * 16 for channel in color)
                            cache_key = (char, color_key)
                            glyph = glyph_cache.get(cache_key)
                            if glyph is None:
                                glyph = pygame.transform.smoothscale(
                                    font.render(char, True, color_key), (round(cell_width), round(cell_height))
                                )
                                glyph_cache[cache_key] = glyph
                            window.blit(glyph, (round(col_index * cell_width), y))
                if elapsed > 0.25:
                    stamp = font.render(f"{elapsed:05.2f}s", True, (105, 100, 108))
                    window.blit(stamp, (1100 - stamp.get_width() - 18, 12))
                    degrees = (35 + elapsed * 24 * self.speed) % 360
                    hud = hud_font.render(
                        f"ROTATION {degrees:05.1f}°   GLINTS {len(self.renderer.particles.items)}   ASCII {ascii_count:,}",
                        True,
                        (105, 100, 108),
                    )
                    window.blit(hud, (18, 1000 - hud.get_height() - 14))
                pygame.display.flip()
        finally:
            if pygame.mixer.get_init():
                pygame.mixer.music.stop()
            pygame.quit()


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a rotating 3D diamond ring in ASCII.")
    parser.add_argument("--quality", type=int, choices=(1, 2, 3), default=2, help="particle density and mesh quality (1–3)")
    parser.add_argument("--speed", type=float, default=1.0, help="rotation speed multiplier")
    parser.add_argument("--fps", type=int, default=20, help="target frames per second")
    parser.add_argument("--no-color", action="store_true", help="force monochrome output")
    parser.add_argument("--terminal", action="store_true", help="render in the terminal instead of the graphical window")
    args = parser.parse_args()
    fps = max(1, min(60, args.fps))
    if args.terminal:
        AnimationController(args.quality, args.speed, fps, not args.no_color).run()
    else:
        PygameAnimationController(args.quality, args.speed, fps).run()


if __name__ == "__main__":
    main()
