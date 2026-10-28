"""Turn a trading video into a storyboard: screenshots in sync with what is said.

    python scripts/video_digest.py VIDEO.mp4 --out research/videos/<name> [--subs VIDEO.vtt] [--model small]

Steps:
  1. transcript with timestamps: from a subtitle file (--subs, .vtt/.srt) if given, else speech-to-text
     on the audio (faster-whisper, runs on the CPU);
  2. screenshots: one at every scene change (a new chart, a zoom, a drawing appearing) and at least one
     every --every seconds, so nothing on screen is missed;
  3. sync: each screenshot gets the words spoken while it is on screen (word timestamps; with --subs, per line).
Output in --out: frames/*.jpg, transcript.txt (with [mm:ss] stamps), storyboard.md (screenshot + text).

Needs: pip install imageio-ffmpeg faster-whisper  (ffmpeg comes with imageio-ffmpeg).
"""
import argparse
import re
import subprocess
from pathlib import Path


def ffmpeg():
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def mmss(t):
    return f"{int(t // 60):02d}:{int(t % 60):02d}"


def read_subs(path):
    """[(start, end, text)] from .vtt or .srt; duplicate rolling captions are merged."""
    txt = Path(path).read_text(encoding="utf-8", errors="replace")
    stamp = r"(\d{1,2}:)?\d{2}:\d{2}[.,]\d{3}"
    out = []
    for block in re.split(r"\n\s*\n", txt):
        m = re.search(rf"({stamp})\s*-->\s*({stamp})", block)
        if not m:
            continue
        def sec(s):
            p = s.replace(",", ".").split(":")
            return sum(float(x) * 60 ** i for i, x in enumerate(reversed(p)))
        lines = [re.sub(r"<[^>]+>", "", l).strip() for l in block.splitlines()[block.splitlines().index(
            next(l for l in block.splitlines() if "-->" in l)) + 1:]]
        text = " ".join(l for l in lines if l)
        if text and (not out or text != out[-1][2]):
            out.append((sec(m.group(1)), sec(m.group(3)), text))
    return out


def transcribe(video, model):
    from faster_whisper import WhisperModel
    wm = WhisperModel(model, device="cpu", compute_type="int8")
    segs, info = wm.transcribe(str(video), vad_filter=True, word_timestamps=True)
    segs = list(segs)
    words = [(w.start, w.end, w.word.strip()) for s in segs for w in (s.words or [])]
    return [(s.start, s.end, s.text.strip()) for s in segs], words, info.language


def frames(video, out, every, threshold):
    """Scene-change frames plus one every `every` s; returns [(time, path)]."""
    fdir = out / "frames"
    fdir.mkdir(parents=True, exist_ok=True)
    vf = (f"select='gt(scene,{threshold})+isnan(prev_selected_t)+gte(t-prev_selected_t,{every})',"
          "scale='min(1280,iw)':-2,showinfo")
    r = subprocess.run([ffmpeg(), "-hide_banner", "-i", str(video), "-vf", vf, "-vsync", "vfr", "-q:v", "3",
                        str(fdir / "f_%05d.jpg")], capture_output=True, text=True)
    times = [float(x) for x in re.findall(r"pts_time:([0-9.]+)", r.stderr)]
    files = sorted(fdir.glob("f_*.jpg"))
    res = []
    for t, f in zip(times, files):
        new = fdir / f"t_{int(t // 60):02d}m{int(t % 60):02d}s_{f.stem[2:]}.jpg"
        f.rename(new)
        res.append((t, new))
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--out", required=True)
    ap.add_argument("--subs", default=None, help="subtitle file (.vtt/.srt) instead of speech-to-text")
    ap.add_argument("--model", default="small", help="faster-whisper model: tiny, base, small, medium")
    ap.add_argument("--every", type=float, default=20.0, help="at least one screenshot every N seconds")
    ap.add_argument("--scene", type=float, default=0.25, help="scene-change sensitivity (lower = more shots)")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    if a.subs:
        segs, lang = read_subs(a.subs), "subs"
        words = segs  # subtitle lines are the smallest unit we have
    else:
        segs, words, lang = transcribe(a.video, a.model)
    (out / "transcript.txt").write_text("\n".join(f"[{mmss(s)}] {t}" for s, _, t in segs), encoding="utf-8")

    shots = frames(a.video, out, a.every, a.scene)
    md = [f"# Storyboard: {Path(a.video).name}", "",
          f"{len(shots)} screenshots, {len(segs)} transcript segments (source: {lang}).", ""]
    for i, (t, f) in enumerate(shots):
        t_next = shots[i + 1][0] if i + 1 < len(shots) else float("inf")
        t0 = 0.0 if i == 0 else t  # words before the first screenshot belong to it
        said = " ".join(txt for s, _, txt in words if t0 <= s < t_next)
        md += [f"## [{mmss(t)}]", "", f"![{mmss(t)}](frames/{f.name})", "", said or "_(niets gezegd)_", ""]
    (out / "storyboard.md").write_text("\n".join(md), encoding="utf-8")
    print(f"{len(shots)} screenshots, {len(segs)} segments -> {out / 'storyboard.md'}")


if __name__ == "__main__":
    main()
