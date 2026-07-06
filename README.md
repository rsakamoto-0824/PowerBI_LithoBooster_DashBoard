# PowerBI LithoBooster DashBoard

## 何をするものか

半導体製造の露光工程で、LithoBoosterが収集したアライメント計測結果と
Shotごとの補正制御値を可視化するPower BIダッシュボード。
Verticaデータベースの `sys_emas` スキーマにある2ビュー（Canon用 / Nikon用）に
DirectQueryで接続する。

- 要件: [requirements.md](requirements.md)
- 設計: [design.md](design.md)
- ビュー定義: [sys_emas.md](sys_emas.md)
- 課題: [issues.md](issues.md)
- 画面イメージ: `dashboard_mockup.pptx`
- 改善提案: [improvement_report.html](improvement_report.html)（ブラウザで開く）

## 実行方法

1. Power BI Desktop（Windows）でプレビュー機能
   「Power BI プロジェクト (.pbip) の保存オプション」「PBIR形式」を有効化する
2. `LithoBooster.pbip` を開く
3. パラメーター `SampleDataFolder` を自分のPCの `sample_data/` フォルダーの
   絶対パス（末尾 `\` つき）に変更してデータを更新する
4. 開発中はダミーCSV（Import）。本番はVertica DirectQueryへ切替
   （手順は [design.md](design.md) の2.3参照）
5. DB接続時の資格情報はDesktop側で入力する（資格情報はファイルに保存しない）

## 必要な環境

- Power BI Desktop（PBIP / TMDL / PBIRのプレビュー機能を有効化）
- Vertica ODBCドライバー（Verticaコネクタの利用に必要）
- `sys_emas` スキーマへの参照権限を持つDBアカウント
- Power BI Service公開時はOn-premises Data Gateway（ゲートウェイ側にもVertica ODBCドライバーが必要）

## サンプルデータ（ダミー）

`sample_data/` に、ビュー定義と同じ列構成のダミーデータCSVがある。
Vertica接続前のレポート開発・動作確認用で、**実データは一切含まない**。

- [generate_sample_data.py](sample_data/generate_sample_data.py) — 生成スクリプト（Python 3.14以上、標準ライブラリのみ）
- `V_EQP_WAFER_LITHOBOOSTER_CANON_sample.csv` — Canonビュー相当（8 Lot、約48,000行、約19MB）
- `V_EQP_WAFER_LITHOBOOSTER_NIKON_sample.csv` — Nikonビュー相当（8 Lot、約8,800行、約4MB）

データの形式は実データのサンプル（xlsx）に合わせている:

- LOT_ID: `5AW975B82.01` 形式（WAFER_IDは「.」より前 + `-` + Wafer番号2桁）
- 装置: `ML01MF` / `ML02MF` / `ML03MF` の3台に、Lotをランダムに割り当て
- PROCESS / OPERATION: `RDH_PR`/`RDH-MLF` と `MSR_PR`/`MSR-MLF` の2ペア
- OPERATIONごとにShotレイアウトが異なる:
  - `RDH-MLF`: 96 Shot/Wafer、4 Mark/Shot
  - `MSR-MLF`: 114 Shot/Wafer、6 Mark/Shot（グリッド原点もRDHから数mmズレる）
- Wafer数: 1Lotあたり3〜25枚のランダム（最大25枚/Lot）
- 計測日時: 2026/6/29〜7/4 の期間にランダム（Lot単位）

再生成する場合:

```bash
cd sample_data
python3 generate_sample_data.py
```

## 注意事項

- DirectQuery専用。データのImport・実データのCSVエクスポートはコミット禁止
- `.pbi/cache.abf` と `.pbi/localSettings.json` はコミットしない（.gitignore登録）
- リポジトリはPrivateのまま運用する
- mainへ直接コミットせず、ブランチ → PR → 確認 → マージの手順に従う
