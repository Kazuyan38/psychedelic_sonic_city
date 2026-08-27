"""events.json を index_template.html に埋め込み、配布用の index.html を書き出す。"""
import json

ROOT = r"C:\Users\gener\psychedelic_sonic_city"
TEMPLATE = ROOT + r"\index_template.html"
EVENTS = ROOT + r"\assets\events.json"
OUT = ROOT + r"\index.html"


def main():
    with open(EVENTS, "r", encoding="utf-8") as f:
        score = json.load(f)
    with open(TEMPLATE, "r", encoding="utf-8") as f:
        tpl = f.read()
    injected = tpl.replace("/*__EVENTS_JSON__*/", json.dumps(score, ensure_ascii=False))
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(injected)
    print(f"saved: {OUT}  ({len(injected)} chars)")


if __name__ == "__main__":
    main()
