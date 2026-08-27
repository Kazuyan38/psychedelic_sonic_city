"""
沈黙する都市庭園 - サウンドループ作曲
BPM144 / 20小節 / 約33.3秒。絶対tick方式(TrackBuilder)。
セクション: dormant(静寂) -> growth(acid+sub) -> peak(supersaw+FMベース+グリッチ) -> silence(全休符) -> collapse(断片化して消える)
このセクション構成そのものが「沈黙する都市庭園」の物語構造(生成→過密→沈黙→崩壊)と一致する。
"""
import random
from mido import Message, MetaMessage, MidiFile, MidiTrack

# ---- 冒頭定数ブロック ----
TPB = 480
BEAT = TPB
EIGHTH = TPB // 2
SIXTEENTH = TPB // 4
THIRTYSECOND = TPB // 8
BAR = TPB * 4
BPM = 144
BARS = 20
TEMPO = int(60_000_000 / BPM)
DURATION_S = BARS * 4 * 60 / BPM
OUT_MID = r"C:\Users\gener\psychedelic_sonic_city\assets\sonic_city_loop.mid"

random.seed(20260828)

CH_ACID, PROG_ACID = 0, 81          # Lead 2 (sawtooth) - 303風レゾナンスの代替
CH_PAD_A, PROG_PAD = 1, 89          # Pad 2 (warm) - スーパーソウ層1
CH_PAD_B, _ = 4, PROG_PAD           # スーパーソウ層2(+detune)
CH_PAD_C, _ = 5, PROG_PAD           # スーパーソウ層3(-detune)
CH_SUB, PROG_SUB = 2, 38            # Synth Bass 1
CH_FM, PROG_FM = 3, 87              # Lead 8 (bass+lead) - FM/歪みベース
CH_DRUMS = 9                        # GM ドラム

KICK, SNARE, CLAP, CHH, OHH, CRASH, REV_CYM = 36, 38, 39, 42, 46, 49, 55

# サイケデリックな旋法: フリジアン寄り(暗い緊張感) ルート A(57)
ROOT = 57  # A3
SCALE = [0, 1, 3, 5, 7, 8, 10]  # Phrygian


def deg(step, octave_offset=0):
    o, i = divmod(step, len(SCALE))
    return ROOT + SCALE[i] + 12 * (o + octave_offset)


class TrackBuilder:
    def __init__(self):
        self.notes = []
        self.ccs = []
        self.pbs = []
        self.programs = {}

    def _t(self, beat):
        return int(round(beat * TPB))

    def set_program(self, ch, prog):
        self.programs[ch] = prog

    def add_note(self, abs_beat, note, dur_beats, velocity, ch):
        note = max(0, min(127, int(note)))
        velocity = max(1, min(127, int(velocity)))
        self.notes.append((self._t(abs_beat), self._t(abs_beat + dur_beats), note, velocity, ch))

    def add_chord(self, abs_beat, notes, dur_beats, velocity, ch, arpeggio=False, arp_ticks=30):
        if not arpeggio:
            for n in notes:
                self.add_note(abs_beat, n, dur_beats, velocity, ch)
        else:
            base = self._t(abs_beat)
            for i, n in enumerate(notes):
                on = base + i * arp_ticks
                off = self._t(abs_beat + dur_beats)
                self.notes.append((on, off, max(0, min(127, n)), velocity, ch))

    def add_pitchbend(self, abs_beat, value, ch):
        self.pbs.append((self._t(abs_beat), value, ch))

    def add_cc(self, abs_beat, cc, val, ch):
        self.ccs.append((self._t(abs_beat), cc, val, ch))

    def to_track(self):
        events = []
        for on, off, n, v, ch in self.notes:
            events.append((on, 1, 'note_on', n, v, ch))
            events.append((off, 0, 'note_off', n, 0, ch))
        for tick, cc, val, ch in self.ccs:
            events.append((tick, 2, 'control_change', cc, val, ch))
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
            elif kind == 'control_change':
                track.append(Message('control_change', control=a, value=b, time=dt, channel=ch))
            elif kind == 'pitchwheel':
                track.append(Message('pitchwheel', pitch=a, time=dt, channel=ch))
            prev = tick
        return track


def build_acid(tb):
    """303風の刻みアルペジオ。bar3から入り、bar17以降は断片化して消える。"""
    pattern = [0, 3, 2, 5, 3, 7, 2, 5, 0, 3, 5, 8, 3, 7, 5, 2]
    for bar in range(BARS):
        b0 = bar * 4
        if bar < 2:
            continue  # dormant: 完全静寂
        if bar in (12, 13):
            continue  # silence section: 完全休符
        density = 1.0
        if bar >= 16:
            density = max(0.15, 1.0 - (bar - 15) * 0.22)  # collapse: 徐々に間引く
        for i, step in enumerate(pattern):
            if random.random() > density:
                continue
            beat = b0 + i * (SIXTEENTH / TPB)
            note = deg(step, octave_offset=1)
            vel = 78 + (18 if i % 4 == 0 else 0) + random.randint(-8, 8)
            tb.add_note(beat, note, SIXTEENTH / TPB * 0.85, vel, CH_ACID)


def build_pad(tb):
    """デチューン3層スーパーソウ。bar7で入り、bar14の沈黙で切れる。"""
    tb.add_pitchbend(0, 0, CH_PAD_A)
    tb.add_pitchbend(0, int(8192 * 0.12), CH_PAD_B)
    tb.add_pitchbend(0, -int(8192 * 0.12), CH_PAD_C)
    progressions = [
        [deg(0, 1), deg(2, 1), deg(4, 1), deg(6, 1)],
        [deg(3, 1), deg(5, 1), deg(0, 2), deg(2, 2)],
        [deg(1, 1), deg(3, 1), deg(5, 1), deg(0, 2)],
    ]
    bar = 6
    while bar < 20:
        if bar in (12, 13):
            bar += 2
            continue
        chord = progressions[(bar // 2) % len(progressions)]
        vel = 62 if bar < 12 else (95 if bar < 18 else 50)
        dur = 4 * 0.98
        for ch in (CH_PAD_A, CH_PAD_B, CH_PAD_C):
            for n in chord:
                tb.add_note(bar, n, dur, vel + random.randint(-4, 4), ch)
        bar += 2


def build_sub(tb):
    """サブベース。bar3から。休符区間で消える。"""
    for bar in range(BARS):
        if bar < 2 or bar in (12, 13):
            continue
        root = deg(0, -1)
        vel = 100 if bar in range(6, 18) else 80
        tb.add_note(bar, root, 3.9, vel, CH_SUB)


def build_fm_bass(tb):
    """FM/歪みベース。ピーク区間(bar7-11)と崩壊区間(bar16-19)の一部にだけ噛ませる。"""
    for bar in range(7, 12):
        for i in [0, 1.5, 2, 3]:
            note = deg(random.choice([0, 3, 5]), -1)
            tb.add_note(bar + i, note, 0.4, 105 + random.randint(-6, 10), CH_FM)
    for bar in [16, 17]:
        tb.add_note(bar, deg(0, -1), 0.6, 70, CH_FM)


def build_drums(tb):
    """グリッチ多用のドラム。bar7からスタッター強め、bar12-13は完全休符。"""
    for bar in range(BARS):
        if bar < 2 or bar in (12, 13):
            continue
        b0 = bar
        glitch_zone = bar in (10, 11, 17, 18)
        # kick
        for beat in [0, 1, 2, 3] if bar >= 6 else [0, 2]:
            tb.add_note(b0 + beat, KICK, 0.12, 118, CH_DRUMS)
        # snare/clap on 2 & 4
        for beat in [1, 3]:
            tb.add_note(b0 + beat, SNARE, 0.12, 100, CH_DRUMS)
            if bar >= 12:
                tb.add_note(b0 + beat, CLAP, 0.1, 60, CH_DRUMS)
        # hihat 16分、グリッチ区間はスタッター(32分連打)
        step = THIRTYSECOND / TPB if glitch_zone else SIXTEENTH / TPB
        n = 32 if glitch_zone else 16
        for i in range(n):
            beat = b0 + i * step
            is_open = (i % 8 == 7) and not glitch_zone
            note = OHH if is_open else CHH
            vel = 55 + random.randint(-10, 10) + (15 if i % 4 == 0 else 0)
            if glitch_zone and random.random() < 0.35:
                continue  # ビットクラッシュ的な欠落
            tb.add_note(beat, note, step * 0.7, vel, CH_DRUMS)
        if bar == 6 or bar == 15:
            tb.add_note(b0, CRASH, 1.0, 110, CH_DRUMS)
        if bar == 14:
            tb.add_note(b0, REV_CYM, 2.0, 90, CH_DRUMS)  # silence明けの再出現合図


def main():
    mid = MidiFile(ticks_per_beat=TPB)

    meta = MidiTrack()
    meta.append(MetaMessage('set_tempo', tempo=TEMPO, time=0))
    meta.append(MetaMessage('time_signature', numerator=4, denominator=4, time=0))
    meta.append(MetaMessage('track_name', name='SilentGardenCity_Meta', time=0))
    mid.tracks.append(meta)

    builders = {}
    for ch, prog in [
        (CH_ACID, PROG_ACID), (CH_PAD_A, PROG_PAD), (CH_PAD_B, PROG_PAD),
        (CH_PAD_C, PROG_PAD), (CH_SUB, PROG_SUB), (CH_FM, PROG_FM),
    ]:
        tb = TrackBuilder()
        tb.set_program(ch, prog)
        builders[ch] = tb

    drum_tb = TrackBuilder()
    builders[CH_DRUMS] = drum_tb

    build_acid(builders[CH_ACID])
    build_pad(builders[CH_PAD_A])  # pad builder writes to CH_PAD_A/B/C via its own tb (shared below)
    build_sub(builders[CH_SUB])
    build_fm_bass(builders[CH_FM])
    build_drums(builders[CH_DRUMS])

    # build_pad は3チャンネル分をまとめて1つのTrackBuilderに積む設計に変更
    # (上のbuilders[CH_PAD_A]を共有バッファとして使う)
    for ch, prog in [(CH_ACID, PROG_ACID), (CH_PAD_A, PROG_PAD), (CH_SUB, PROG_SUB), (CH_FM, PROG_FM)]:
        track = builders[ch].to_track()
        name_track = MidiTrack()
        name_track.append(MetaMessage('track_name', name=f'ch{ch}', time=0))
        name_track.append(Message('program_change', program=prog, time=0, channel=ch))
        if ch == CH_PAD_A:
            name_track.append(Message('program_change', program=prog, time=0, channel=CH_PAD_B))
            name_track.append(Message('program_change', program=prog, time=0, channel=CH_PAD_C))
        for msg in track:
            name_track.append(msg)
        mid.tracks.append(name_track)

    drum_track_final = MidiTrack()
    drum_track_final.append(MetaMessage('track_name', name='drums', time=0))
    for msg in builders[CH_DRUMS].to_track():
        drum_track_final.append(msg)
    mid.tracks.append(drum_track_final)

    mid.save(OUT_MID)
    print(f"saved: {OUT_MID}")
    print(f"duration ~= {DURATION_S:.1f}s  bpm={BPM}  bars={BARS}")


if __name__ == "__main__":
    main()
