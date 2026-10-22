"""Render a verified per-track BPM over the template's baked-in title.

Analysis is not verification: measure the supplied audio and resolve half/double
beat ambiguity before passing --bpm. Review the output before queue registration.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
from check_instagram_connection import CheckError


def bpm_text(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 20 <= value <= 400:
        raise CheckError('確認済みBPMは20〜400の数値で指定してください。')
    return f'{value:g}'


def validate_bpm(item):
    """Bind reviewed display and caption to this exact finished video."""
    label = bpm_text(item.get('bpm'))
    if item.get('bpm_verified') is not True or not item.get('bpm_evidence', '').strip():
        raise CheckError('音源のBPM確認記録がないため投稿を停止します。')
    if item.get('bpm_overlay_verified') is not True or item.get('bpm_video_sha256') != item.get('sha256'):
        raise CheckError('この完成動画のBPM表示が確認されていないため投稿を停止します。')
    mentions = re.findall(r'(\d+(?:\.\d+)?)\s*BPM\b', item.get('caption', ''), re.I)
    if not mentions or any(float(x) != float(label) for x in mentions):
        raise CheckError('投稿文と確認済みBPMが一致しないため投稿を停止します。')


def render(source, output, bpm, evidence):
    label = bpm_text(bpm)
    if not evidence.strip():
        raise ValueError('Describe audio measurement and beat verification.')
    if source.resolve() == output.resolve():
        raise ValueError('Output must be a new file.')
    probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height', '-of', 'json', str(source)]))
    stream = probe['streams'][0]
    if (stream['width'], stream['height']) != (1080, 1920):
        raise ValueError('This overlay is calibrated for the approved 1080x1920 template only.')
    # Fully cover the old burned-in line. The statues and frame timing are untouched.
    vf = f"drawbox=x=320:y=228:w=440:h=54:color=black:t=fill,drawtext=text='STONE GROOVE / {label} BPM':fontcolor=white:fontsize=27:x=(w-tw)/2:y=243"
    output.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(['ffmpeg', '-n', '-v', 'error', '-i', str(source), '-map', '0:v:0', '-map', '0:a:0', '-vf', vf, '-c:v', 'libx264', '-crf', '18', '-preset', 'medium', '-pix_fmt', 'yuv420p', '-c:a', 'copy', '-movflags', '+faststart', str(output)], check=True)
    subprocess.run(['ffmpeg', '-v', 'error', '-i', str(output), '-f', 'null', '-'], check=True)
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    metadata = dict(bpm=bpm, bpm_verified=True, bpm_evidence=evidence,
                    bpm_overlay_verified=False, bpm_video_sha256=digest, sha256=digest,
                    caption=f'EZAWA238 | STONE GROOVE / {label} BPM\n#EZAWA238 #Dance #Suno')
    output.with_suffix('.bpm.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2)+'\n')
    return metadata


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--bpm', type=float, required=True)
    parser.add_argument('--evidence', required=True)
    args = parser.parse_args()
    render(args.source, args.output, args.bpm, args.evidence)
    print('Rendered. Inspect beginning/middle/end, then set bpm_overlay_verified=true when registering the queue item.')
