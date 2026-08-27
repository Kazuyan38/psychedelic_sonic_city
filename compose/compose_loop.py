"""
沈黙する都市庭園 - サウンドループ作曲 (3分尺・二波構成)
BPM144 / 108小節 / ちょうど180秒。絶対tick方式(TrackBuilder)。
セクション: dormant -> growth -> peak(第一波) -> silence -> restart -> peak2(第二波・より過密) -> silence2 -> collapse -> end
一回タップで始まり3分間で完結する体験の骨格そのもの。
"""
import random
from mido import Message, MetaMessage, MidiFile, MidiTrack

# ---- 冒頭定数ブロック ----
TPB = 480
BAR = TPB * 4
BPM = 144
BARS = 108
TEMPO = int(60_000_000 / BPM)
DURATION_S = BARS * 4 * 60 / BPM
OUT_MID = r"C:\Users\gener\psychedelic_sonic_city\assets\sonic_city_loop.mid"

random.seed(20260828)

CH_ACID, PROG_ACID = 0, 81
CH_PAD_A, PROG_PAD = 1, 89
CH_PAD_B, CH_PAD_C = 4, 5
CH_SUB, PROG_SUB = 2, 38
CH_FM, PROG_FM = 3, 87
CH_DRUMS = 9

KICK, SNARE, CLAP, CHH, OHH, CRASH, REV_CYM = 36, 38, 39, 42, 46, 49, 55

ROOT = 57  # A3
SCALE = [0, 1, 3, 5, 7, 8, 10]  # Phrygian

# 3分の物語構造: 小節範囲(開始,終了) と名前
SECTIONS = [
    (0, 4, "dormant"),
    (4, 16, "growth"),
    (16, 40, "peak"),
    (40, 44, "silence"),
    (44, 52, "restart"),
    (52, 84, "peak2"),
    (84, 90, "silence2"),
    (90, 104, "collapse"),
    (104, 108, "end"),
]


def section_of(bar):
    for s0, s1, name in SECTIONS:
        if s0 <= bar < s1:
            return name, (bar - s0) / (s1 - s0)
    return "end", 1.0


def deg(step, octave_offset=0):
    o, i = divmod(step, len(SCALE))
    return ROOT + SCALE[i] + 12 * (o + octave_offset)


class TrackBuilder:
    def __init__(self):
        self.notes = []
        self.ccs = []
        self.pbs = []

    def _t(self, beat):
        return int(round(beat * TPB))

    def add_note(self, abs_beat, note, dur_beats, velocity, ch):
        note = max(0, min(127, int(note)))
        velocity = max(1, min(127, int(velocity)))
        self.notes.append((self._t(abs_beat), self._t(abs_beat + dur_beats), note, velocity, ch))

    def add_pitchbend(self, abs_beat, value, ch):
        self.pbs.append((self._t(abs_beat), value, ch))

    def to_track(self):
        events = []
        for on, off, n, v, ch in self.notes:
            events.append((on, 1, 'note_on', n, v, ch))
            events.append((off, 0, 'note_off', n, 0, ch))
        for tick, val, ch in self.pbs:
            events.append((tick, 2, 'pitchwheel', val, 0, ch))
        events.sort(key=lambda e: (e[0], e[1]))
        track, prev = MidiTrack(), 0
        for tick, _, kind, a, b, ch in events:
            dt = tick - prev
            if kind == 'note_on':
                track.append(Message('note_on', note=a, velocity=b, time=dt, channel=ch))
            elif kind == 'note_off':
                track.append(Message('note_off', note=a, velocity=0, time=dt, channel=ch))
            elif kind == 'pitchwheel':
                track.append(Message('pitchwheel', pitch=a, time=dt, channel=ch))
            prev = tick
        return track


ACID_PATTERN = [0, 3, 2, 5, 3, 7, 2, 5, 0, 3, 5, 8, 3, 7, 5, 2]


def acid_density(name, p):
    if name in ("dormant", "silence", "silence2"):
        return 0.0
    if name == "growth":
        return 0.25 + 0.55 * p
    if name == "peak":
        return 0.85 + 0.15 * p
    if name == "restart":
        return 0.25 + 0.45 * p
    if name == "peak2":
        return 0.95
    if name == "collapse":
        return max(0.08, 0.85 - 0.8 * p)
    return 0.0  # end


def build_acid(tb):
    for bar in range(BARS):
        name, p = section_of(bar)
        density = acid_density(name, p)
        if density <= 0:
            continue
        stutter = name == "peak2"
        steps = ACID_PATTERN * (2 if stutter else 1)
        step_len = (TPB / 8 if stutter else TPB / 4) / TPB  # peak2は32分でスタッター
        for i, step in enumerate(steps):
            if random.random() > density:
                continue
            beat = bar * 4 + i * step_len
            if beat >= bar * 4 + 4:
                break
            note = deg(step, octave_offset=1)
            vel = 74 + (18 if i % 4 == 0 else 0) + random.randint(-8, 8)
            if name == "peak2":
                vel = min(127, vel + 10)
            tb.add_note(beat, note, step_len * 0.85, vel, CH_ACID)


PAD_PROGRESSIONS = [
    [deg(0, 1), deg(2, 1), deg(4, 1), deg(6, 1)],
    [deg(3, 1), deg(5, 1), deg(0, 2), deg(2, 2)],
    [deg(1, 1), deg(3, 1), deg(5, 1), deg(0, 2)],
    [deg(6, 0), deg(1, 1), deg(3, 1), deg(5, 1)],
]


def build_pad(tb):
    tb.add_pitchbend(0, 0, CH_PAD_A)
    tb.add_pitchbend(0, int(8192 * 0.12), CH_PAD_B)
    tb.add_pitchbend(0, -int(8192 * 0.12), CH_PAD_C)
    bar = 0
    prog_i = 0
    while bar < BARS:
        name, p = section_of(bar)
        if name in ("dormant", "silence", "silence2", "end"):
            bar += 2
            continue
        chord = PAD_PROGRESSIONS[prog_i % len(PAD_PROGRESSIONS)]
        prog_i += 1
        if name == "growth":
            vel = 50 + int(20 * p)
        elif name == "peak":
            vel = 78 + int(15 * p)
        elif name == "restart":
            vel = 45 + int(25 * p)
        elif name == "peak2":
            vel = 96 + int(20 * p)
        else:  # collapse
            vel = max(30, int(90 * (1 - p)))
        dur = 4 * 0.98
        for ch in (CH_PAD_A, CH_PAD_B, CH_PAD_C):
            for n in chord:
                tb.add_note(bar, n, dur, min(120, vel + random.randint(-4, 4)), ch)
        bar += 2


def build_sub(tb):
    for bar in range(BARS):
        name, p = section_of(bar)
        if name in ("dormant", "silence", "silence2", "end"):
            continue
        root = deg(0, -1)
        vel = {"growth": 82, "peak": 100, "restart": 78, "peak2": 112, "collapse": max(40, int(95 * (1 - p)))}[name]
        tb.add_note(bar, root, 3.9, vel, CH_SUB)


def build_fm_bass(tb):
    for bar in range(BARS):
        name, p = section_of(bar)
        if name in ("peak", "peak2"):
            hits = [0, 1.5, 2, 3] if name == "peak2" else [0, 2]
            for off in hits:
                note = deg(random.choice([0, 3, 5]), -1)
                tb.add_note(bar + off, note, 0.4, 100 + random.randint(-6, 15), CH_FM)
        elif name == "collapse" and random.random() < 0.5:
            tb.add_note(bar, deg(0, -1), 0.6, max(50, int(90 * (1 - p))), CH_FM)
        elif name == "restart" and p > 0.6:
            tb.add_note(bar, deg(3, -1), 0.3, 70, CH_FM)


def build_drums(tb):
    for bar in range(BARS):
        name, p = section_of(bar)
        if name in ("dormant", "silence", "silence2", "end"):
            continue
        b0 = bar
        glitch_zone = name == "peak2" or (name == "peak" and p > 0.85) or (name == "collapse" and p < 0.3)
        kick_beats = [0, 1, 2, 3] if name in ("peak", "peak2") else [0, 2]
        if name == "collapse":
            kick_beats = [0, 2] if p < 0.6 else [0]
        for beat in kick_beats:
            tb.add_note(b0 + beat, KICK, 0.12, 118, CH_DRUMS)
        for beat in [1, 3]:
            if name == "collapse" and p > 0.7:
                continue
            tb.add_note(b0 + beat, SNARE, 0.12, 100, CH_DRUMS)
            if name in ("peak2", "collapse"):
                tb.add_note(b0 + beat, CLAP, 0.1, 55, CH_DRUMS)
        step = (TPB / 8 if glitch_zone else TPB / 4) / TPB
        n = 32 if glitch_zone else 16
        for i in range(n):
            beat = b0 + i * step
            if beat >= b0 + 4:
                break
            is_open = (i % 8 == 7) and not glitch_zone
            note = OHH if is_open else CHH
            vel = 55 + random.randint(-10, 10) + (15 if i % 4 == 0 else 0)
            if glitch_zone and random.random() < 0.35:
                continue
            if name == "collapse" and random.random() > max(0.15, 1 - p):
                continue
            tb.add_note(beat, note, step * 0.7, vel, CH_DRUMS)
        if bar in (16, 52, 90):
            tb.add_note(b0, CRASH, 1.0, 112, CH_DRUMS)
        if bar in (44, 84):
            tb.add_note(b0, REV_CYM, 2.0, 90, CH_DRUMS)


def main():
    mid = MidiFile(ticks_per_beat=TPB)
    meta = MidiTrack()
    meta.append(MetaMessage('set_tempo', tempo=TEMPO, time=0))
    meta.append(MetaMessage('time_signature', numerator=4, denominator=4, time=0))
    meta.append(MetaMessage('track_name', name='SilentGardenCity_Meta', time=0))
    mid.tracks.append(meta)

    tb_acid, tb_pad, tb_sub, tb_fm, tb_drum = (TrackBuilder() for _ in range(5))
    build_acid(tb_acid)
    build_pad(tb_pad)
    build_sub(tb_sub)
    build_fm_bass(tb_fm)
    build_drums(tb_drum)

    for tb, ch, prog, name in [
        (tb_acid, CH_ACID, PROG_ACID, "acid"),
        (tb_pad, CH_PAD_A, PROG_PAD, "pad"),
        (tb_sub, CH_SUB, PROG_SUB, "sub"),
        (tb_fm, CH_FM, PROG_FM, "fm"),
    ]:
        track = MidiTrack()
        track.append(MetaMessage('track_name', name=name, time=0))
        track.append(Message('program_change', program=prog, time=0, channel=ch))
        if ch == CH_PAD_A:
            track.append(Message('program_change', program=prog, time=0, channel=CH_PAD_B))
            track.append(Message('program_change', program=prog, time=0, channel=CH_PAD_C))
        for msg in tb.to_track():
            track.append(msg)
        mid.tracks.append(track)

    drum_track = MidiTrack()
    drum_track.append(MetaMessage('track_name', name='drums', time=0))
    for msg in tb_drum.to_track():
        drum_track.append(msg)
    mid.tracks.append(drum_track)

    mid.save(OUT_MID)
    print(f"saved: {OUT_MID}")
    print(f"duration ~= {DURATION_S:.1f}s  bpm={BPM}  bars={BARS}")


if __name__ == "__main__":
    main()
