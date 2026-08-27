"""
sonic_city_loop.mid -> events.json 変換
AR側(JS)はこのJSONだけを読んで、音の合成(Web Audio)と建築生成の両方を駆動する。
MIDIファイル自体はWeb Audio再生には使わず、mido側の「絶対tick設計」をそのまま
イベントの時刻(秒)に変換して引き継ぐのが目的。
"""
import json
import mido

SRC = r"C:\Users\gener\psychedelic_sonic_city\assets\sonic_city_loop.mid"
DST = r"C:\Users\gener\psychedelic_sonic_city\assets\events.json"

# チャンネル -> 役割(JS側の音色/生成マッピングと1対1対応)
CH_ROLE = {
    0: "acid",       # 旋律 -> 建築の輪郭・高さ
    1: "pad",        # 和声(層1) -> 色相・材質
    4: "pad",        # 和声(層2, +detune)
    5: "pad",        # 和声(層3, -detune)
    2: "sub",         # 低域 -> 地面/地下構造の揺れ
    3: "fm",          # 歪みベース -> 金属建築/裂け目
    9: "drum",        # リズム -> 増殖・点滅周期/グリッチ
}

DRUM_NAME = {36: "kick", 38: "snare", 39: "clap", 42: "chh", 46: "ohh", 49: "crash", 55: "revcym"}

SILENCE_GAP_BEATS = 1.5  # これ以上、全チャンネル無音が続いたら"silence"イベント


def main():
    mid = mido.MidiFile(SRC)
    tpb = mid.ticks_per_beat
    tempo = 500000  # デフォルト、set_tempoで更新

    # 全トラックをマージして絶対tickのイベント列にする
    abs_events = []
    for track in mid.tracks:
        t = 0
        for msg in track:
            t += msg.time
            abs_events.append((t, msg))
    abs_events.sort(key=lambda e: e[0])

    events = []
    active_notes = {}  # (ch,note) -> on_tick
    last_sound_tick = 0
    cur_tempo = tempo

    def tick_to_sec(tick):
        # テンポ一定(このループはテンポ変更なし)前提の単純換算
        return mido.tick2second(tick, tpb, cur_tempo)

    max_tick = 0
    for tick, msg in abs_events:
        max_tick = max(max_tick, tick)
        if msg.type == 'set_tempo':
            cur_tempo = msg.tempo
            continue
        if msg.type not in ('note_on', 'note_off'):
            continue
        ch = msg.channel
        role = CH_ROLE.get(ch)
        if role is None:
            continue

        is_on = (msg.type == 'note_on' and msg.velocity > 0)
        if is_on:
            active_notes[(ch, msg.note)] = tick
            last_sound_tick = tick
            ev = {
                "t": round(tick_to_sec(tick), 4),
                "type": role,
                "channel": ch,
                "note": msg.note,
                "velocity": msg.velocity,
            }
            if role == "drum":
                ev["drum"] = DRUM_NAME.get(msg.note, "hit")
            events.append(ev)
        else:
            key = (ch, msg.note)
            on_tick = active_notes.pop(key, None)
            if on_tick is not None:
                events.append({
                    "t": round(tick_to_sec(tick), 4),
                    "type": "note_off",
                    "channel": ch,
                    "note": msg.note,
                })

    # 無音区間を検出して silence イベントを挿入
    note_on_events = sorted([e for e in events if e["type"] != "note_off"], key=lambda e: e["t"])
    gap_thresh_sec = mido.tick2second(int(SILENCE_GAP_BEATS * tpb), tpb, cur_tempo)
    silences = []
    for i in range(1, len(note_on_events)):
        gap = note_on_events[i]["t"] - note_on_events[i - 1]["t"]
        if gap >= gap_thresh_sec:
            silences.append({
                "t": round(note_on_events[i - 1]["t"] + 0.05, 4),
                "type": "silence",
                "duration": round(gap - 0.1, 4),
            })
    events.extend(silences)
    events.sort(key=lambda e: e["t"])

    duration_sec = round(tick_to_sec(max_tick) + 1.0, 3)

    out = {
        "bpm": 144,
        "duration": duration_sec,
        "role_map": {
            "acid": "melody -> 建築の輪郭/高さ, 蛇行する道",
            "pad": "harmony -> 色相/材質/背景グラデーション",
            "sub": "低域 -> 地面の揺れ/地下構造",
            "fm": "歪み -> 金属建築/裂け目/グリッチ演出",
            "drum": "リズム -> 増殖周期/点滅/粒子",
            "silence": "沈黙 -> 彩度低下/停止/崩壊",
        },
        "events": events,
    }
    with open(DST, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(f"saved: {DST}")
    print(f"events: {len(events)}  duration: {duration_sec}s  silences: {len(silences)}")


if __name__ == "__main__":
    main()
