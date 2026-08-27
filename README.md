# 沈黙する都市庭園 (Psychedelic Sonic City)

Repo: https://github.com/Kazuyan38/psychedelic_sonic_city
公開URL(GitHub Pages): https://kazuyan38.github.io/psychedelic_sonic_city/

音が建築を生成し、沈黙が都市を崩す、疑似AR作品。自作MIDI(BPM144・3分/108小節)をイベント列に変換し、
Web Audio(電子音全レイヤー: acid303風・デチューンスーパーソウ・サブベース・FM歪みベース・グリッチドラム)と、
カメラ映像+Canvas2D万華鏡演出で同時駆動する。画面を一回タップすると音楽と映像が同時に始まり、
3分間かけて画面全体を覆うまで増殖し、沈黙とともに崩れて終わる。

中心の問い: **音が止まったとき、都市は死ぬのか、それとも別の夢を見始めるのか。**

## 開くには

**スマホでは上の公開URLを直接開けばよい**(GitHub PagesはHTTPS配信なのでカメラ許可が動く)。

`index.html` は完全に単一ファイル完結(events.json はビルド時にインライン埋め込み済み)。
カメラ(`getUserMedia`)は **HTTPS または localhost でしか動かない**ブラウザ仕様のため、
`file://` で直接ダブルクリックしても背景カメラは使えない(暗紫グラデーションにフォールバックはする)。
ローカルで確認する場合は簡易サーバ越しにする。

```
cd C:\Users\gener\psychedelic_sonic_city
python -m http.server 8000
# スマホから http://<このPCのIP>:8000/ にアクセス(同一Wi-Fi内)
```

スマホでカメラ許可・音の許可(タップ)をすると、背景に薄暗い紫のカメラ映像+その上に発光する
万華鏡都市が重なる。「音を許可してはじめる」を一回タップすると、その場で音楽と映像が同時に始まる。
3分間かけて2波の生成(growth→peak→silence→restart→peak2)を経て画面全体を覆い、最後は沈黙→崩壊して終了カードが出る。

## 再生成する場合(音楽を差し替えたいとき)

```
cd compose
python compose_loop.py      # mido でMIDI作曲 -> ../assets/sonic_city_loop.mid
python midi_to_events.py    # MIDI -> ../assets/events.json (音↔建築の対応イベント列)
python build_html.py        # index_template.html に events.json を埋め込み -> ../index.html
```

`compose_loop.py` の冒頭定数(BPM/BARS/ROOT/SCALE)を変えるだけで、別の色彩・別の都市になる。

## 音↔生成の対応表

| MIDIチャンネル | 役割 | 視覚 |
|---|---|---|
| 0 (Acid Lead) | 旋律 | タワーの高さ・輪郭・色相の種 |
| 1,4,5 (Supersaw Pad, ±detune) | 和声 | 都市全体の色相(cityHue)を回転 |
| 2 (Sub Bass) | 低域 | エネルギー(脈動)上昇 |
| 3 (FM Bass) | 歪み | グリッチ演出+大粒子 |
| 9 (Drums) | リズム | kick=脈動, chh/ohh=粒子, snare/clap=フラッシュ, crash/revcym=万華鏡回転+フラッシュ |
| 休符(1.5拍以上) | 沈黙 | 彩度(desat)がグレースケールへ遷移 |

## 安全面の実装済み対策

- 強フラッシュに最小間隔(260ms)のレート制限
- 開始画面に光過敏性の注意書き
- 「低刺激モード」トグル(グリッチ演出・強フラッシュを抑制)
- カメラ映像は端末内処理のみ、外部送信なし
- カメラ/傾きセンサー共に、権限が得られない場合は静止画/暗グラデーションへ自動フォールバック

## 既知の制約(次にやるなら)

- 現状は「疑似AR」(カメラ映像+画面固定の生成物+傾きで視差)であり、WebXR hit-testによる
  床面への正確なワールドアンカリングはしていない。実装するなら `navigator.xr` の
  `XRHitTestSource` を直接使う経路が必要(A-Frame頼みは避けた: バージョン依存のAPIが不確実なため)。
- 建築表現はCanvas2Dの放射状ストローク+万華鏡ミラーリングのみ。3Dメッシュ化はしていない。
- 音源は全てWeb Audio合成(事前レンダリング音声ファイルは使っていない)。端末による音色差が出る。
