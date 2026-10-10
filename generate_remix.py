"""Generate a new original 128 BPM track and copy the approved video untouched."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import random
import secrets
import subprocess
import wave
import numpy as np

ROOT=Path(__file__).resolve().parent
BPM=128
DURATION=15
RATE=44100
BEAT=60/BPM

def synthesize(seed):
    rng=random.Random(seed)
    noise_rng=np.random.default_rng(seed)
    root=rng.choice([53,55,57,59,60,62])
    progressions=[[(0,3),(-4,4),(-2,4),(-5,3)],
                  [(0,3),(-5,3),(-4,4),(-2,4)],
                  [(0,3),(-2,4),(-4,4),(0,3)]]
    progression=rng.choice(progressions)
    phrase=[0]
    tones=[0,2,3,5,7,10,12]
    for _ in range(15):
        possible=[n for n in tones if abs(n-phrase[-1])<=7]
        phrase.append(rng.choice(possible))
    phrase[7]=rng.choice([3,7])
    phrase[15]=0
    bass_pattern=rng.choice([[0,0,7,0],[0,7,0,12],[0,0,3,7]])
    brightness=rng.uniform(.18,.36)
    t=np.arange(RATE*DURATION)/RATE
    beat_pos=np.remainder(t,BEAT)
    step=(t/(BEAT/2)).astype(int)
    note_pos=np.remainder(t,BEAT/2)
    chord_index=(t/(4*BEAT)).astype(int)%4
    chord_offsets=np.array([x[0] for x in progression])[chord_index]
    thirds=np.array([x[1] for x in progression])[chord_index]
    freq=lambda midi:440*2**((midi-69)/12)
    kick=np.sin(2*np.pi*(48*beat_pos+100*.025*(1-np.exp(-beat_pos/.025))))*np.exp(-22*beat_pos)
    bass_offsets=np.array(bass_pattern)[(t/BEAT).astype(int)%4]
    bass_f=freq(root-24+chord_offsets+bass_offsets)
    # Continuous phase avoids clicks when the bass note changes.
    bass_phase=2*np.pi*np.cumsum(bass_f)/RATE
    bass=(np.sin(bass_phase)+.22*np.sin(2*bass_phase))*np.sin(np.pi*beat_pos/BEAT)**2
    melody=np.array(phrase)[step%16]
    lead_f=freq(root+chord_offsets+melody)
    lead_phase=2*np.pi*np.cumsum(lead_f)/RATE
    lead_env=(1-np.exp(-note_pos*120))*np.exp(-note_pos*rng.uniform(7,11))
    lead=(np.sin(lead_phase)+brightness*np.sin(2*lead_phase))*lead_env
    pad=np.zeros_like(t)
    for offset in [np.zeros_like(t),thirds,np.full_like(t,7)]:
        p=2*np.pi*np.cumsum(freq(root+chord_offsets+offset))/RATE
        pad+=np.sin(p)/3
    hat=noise_rng.uniform(-1,1,len(t))*np.exp(-110*note_pos)
    duck=.25+.75*np.minimum(beat_pos/.12,1)
    energy=np.where((t>=5.5)&(t<7.5),.55,1)
    fade=np.minimum(np.minimum(t/.03,(DURATION-t)/.25),1)
    audio=(.42*kick*energy+duck*(.24*bass*energy+.18*lead+.085*pad+.05*hat*energy))*fade
    peak=float(np.max(np.abs(audio)))
    if peak>.90:audio*=.90/peak
    samples=(audio*32767).astype('<i2')
    info={'seed':str(seed),'bpm':BPM,'duration_seconds':DURATION,
          'root_midi':root,'progression':progression,'melody':phrase,
          'bass_pattern':bass_pattern,'lead_brightness':brightness,
          'audio_sha256':hashlib.sha256(samples.tobytes()).hexdigest()}
    return samples,info

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--seed',type=int,help='Optional seed for an exact musical repeat')
    parser.add_argument('--template',type=Path,default=ROOT/'assets/approved_duet.mp4')
    parser.add_argument('--output-dir',type=Path,default=ROOT/'output')
    args=parser.parse_args()
    args.output_dir.mkdir(parents=True,exist_ok=True)
    seed=args.seed if args.seed is not None else secrets.randbits(63)
    samples,info=synthesize(seed)
    audio=args.output_dir/'music.wav'
    with wave.open(str(audio),'wb') as f:
        f.setnchannels(1);f.setsampwidth(2);f.setframerate(RATE)
        f.writeframes(samples.tobytes())
    video=args.output_dir/'ezawa238_reel.mp4'
    subprocess.run(['ffmpeg','-y','-v','error','-i',str(args.template),'-i',str(audio),
        '-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','192k',
        '-t',str(DURATION),'-movflags','+faststart',str(video)],check=True)
    info['template_sha256']=hashlib.sha256(args.template.read_bytes()).hexdigest()
    info['visuals']='approved two-guardian duet, copied without re-encoding'
    (args.output_dir/'music_info.json').write_text(json.dumps(info,ensure_ascii=False,indent=2)+'\n')
    print(f'Generated new music, seed={seed}; preserved approved video: {video}')

if __name__=='__main__':main()
