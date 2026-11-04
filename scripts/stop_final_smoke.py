"""Interrupt only this task's smoke launcher; never stop the user's project01 app."""
from pathlib import Path
import os
import signal

scripts={'/mnt/c/DATA/assign/scripts/run_tieuluanfinal.py','/mnt/c/DATA/assign/tieuluanfinal/scripts/serve_final.py'}
matches=[]
for process in Path('/proc').iterdir():
    if not process.name.isdigit():continue
    try:args=(process/'cmdline').read_bytes().decode().split('\0')
    except (OSError,UnicodeError):continue
    if scripts.intersection(args) and '--worker' not in args and '--port' in args and args[args.index('--port')+1]=='8040':
        matches.append(int(process.name))
if len(matches)!=1:raise RuntimeError(f'Expected one owned smoke launcher, found {matches}')
os.kill(matches[0],signal.SIGINT)
print('Stopped owned smoke launcher',matches[0])
