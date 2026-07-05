# LithoBooster ダッシュボード 基本設計・詳細設計

要件は [requirements.md](requirements.md) を正とする。
本書はPBIPプロジェクト（データモデル・レポート・Deneb）の設計を記述する。

## 1. プロジェクト構成

```text
LithoBooster.pbip              # Power BI Desktopで開くエントリファイル
LithoBooster.SemanticModel/    # セマンティックモデル（TMDL）
├── definition/
│   ├── database.tmdl
│   ├── model.tmdl
│   ├── expressions.tmdl       # SampleDataFolder パラメーター
│   ├── relationships.tmdl
│   └── tables/
│       ├── CANON.tmdl         # ファクト（Canonビュー）+ メジャー
│       ├── NIKON.tmdl         # ファクト（Nikonビュー）+ メジャー
│       ├── 日付.tmdl          # 日付ディメンション（Power Query生成）
│       └── 装置.tmdl          # 装置ディメンション（両ビューからDISTINCT）
LithoBooster.Report/           # レポート定義（PBIR）
└── definition/
    ├── report.json
    └── pages/                 # P1〜P7の空ページ（雛形）
themes/theme.json              # テーマ（モックアップと同じ配色）
deneb/*.json                   # Deneb（Vega-Lite）定義
```

## 2. データモデル設計

### 2.1 スタースキーマ

```text
日付 (1) ──< CANON (＊)        日付 (1) ──< NIKON (＊)
装置 (1) ──< CANON (＊)        装置 (1) ──< NIKON (＊)
```

- リレーションはすべて多対一・単方向
- ファクトの `計測日`（Power Queryで `MEASUREMENT_TIME` から生成した日付型列）と
  `日付[Date]` を関連付ける
- `装置` はCanon/Nikon両ビューのEQPIDを統合したディメンション
  （スライサーを1つで共用するため）
- DEVICE_TYPE / OPERATION / PROCESS / PRODUCT のスライサーは、
  当面ファクト列を直接使用する（値種類が少ないため。
  パフォーマンス問題が出たらディメンション化する）

### 2.2 開発時データソース（現状の雛形）

- パラメーター `SampleDataFolder` のフォルダーからダミーCSVをImportモードで読む
- 初回オープン時に `SampleDataFolder` を各自の環境のパスに変更する
  （例: `C:\LithoBooster\sample_data\`。リポジトリの `sample_data/` を指す）

### 2.3 本番切替（Vertica DirectQuery）手順

1. 接続情報（サーバー・ポート・DB名）を確定する（issues.md I-001b）
2. 各ファクトテーブルのパーティションのMソースを以下の形に置き換える

```text
let
    Source = Vertica.Database("<サーバー>:<ポート>", "<DB名>"),
    View = Source{[Schema = "sys_emas", Item = "V_EQP_WAFER_LITHOBOOSTER_CANON"]}[Data],
    AddMeasureDate = Table.AddColumn(View, "計測日", each Date.From([MEASUREMENT_TIME]), type date)
in
    AddMeasureDate
```

3. テーブルのストレージモードを `directQuery` に変更する
   （TMDLでは `partition ... mode: directQuery`）
4. `日付` `装置` はDual/Importのまま運用する（複合モデル）
5. 資格情報はDesktop / ゲートウェイ側で設定し、ファイルには保存しない

### 2.4 メジャー設計

命名は「対象 + 統計量」。すべて名前付きメジャー（インライン式禁止）。

| メジャー | テーブル | 用途 |
|---|---|---|
| 計測値X/Y 平均・3σ・RMS | CANON | トレンド・KPI |
| 計測値X/Y 平均±3σ 表示 | CANON | KPIカードの表示文字列（V-10） |
| ベクトル長 平均 | CANON | V-27ヒートマップ等 |
| Wafer数 / Lot数 / 測定点数 | CANON | KPI・件数ガード |
| 判定0率X | CANON | V-04（0/1の意味はI-002確認後にラベル確定） |
| 補正量X/Y 平均・3σ・平均±3σ 表示 | NIKON | P4 KPIカード |
| Wafer数 N / Lot数 N / 補正点数 | NIKON | KPI |

今後の追加予定: 共分散楕円用の位置ごとVx/Vy/Cxy（V-22/V-23）、
移動平均・前期間比較（V-08）、しきい値超過フラグ（V-07）。

## 3. レポート設計

- ページはP1〜P7（要件4.2と同じ構成）。雛形では空ページのみ作成済み
- レイアウトは `dashboard_mockup.pptx` を正とする
- テーマは `themes/theme.json` をDesktopの「テーマの参照」から適用する
- ビジュアル実装の順序（推奨）: P1/P4（標準ビジュアルのみ）→ P2/P3 →
  P5/P6/P7（Deneb中心）

## 4. Deneb設計

### 4.1 採否理由（Power BI開発ルール準拠）

| 可視化 | 標準ビジュアルでの実現性 | 判断 |
|---|---|---|
| ベクトル場（矢印）V-11/V-12 | 不可（散布図に矢印なし） | Deneb採用 |
| 共分散楕円 V-22/V-23 | 不可 | Deneb採用 |
| 補正前Shot配列 V-26/V-18 | 不可 | Deneb採用 |
| Shot枠つきヒートマップ V-25/V-27 | 標準散布図では枠不可 | Deneb採用 |
| トレンド・箱ひげ・バー・カード | 可能 | 標準ビジュアル |

- DenebはAppSourceの**認定版**を使用する
- 定義は `deneb/*.json` を正とし、修正時はDenebエディタへ貼り付けて反映する

### 4.2 雛形として用意した定義

| ファイル | 対象 | 状態 |
|---|---|---|
| [v11_vector_map.json](deneb/v11_vector_map.json) | V-11計測値ベクトル（V-12はfacet追加で流用） | 雛形。フィールド名の対応をDeneb側で設定 |
| [v22_covariance_ellipse.json](deneb/v22_covariance_ellipse.json) | V-22/V-23共分散楕円 | 雛形。Vx/Vy/CxyはDAXメジャーで供給 |
| [v26_shot_array.json](deneb/v26_shot_array.json) | V-26/V-18補正前Shot配列 | 雛形。逆算式の符号はI-009確認後に確定 |

実装時の注意:

- Denebへ渡す行数を絞る（必須フィルター + Wafer選択）。
  DirectQueryではビジュアルごとの行数上限（既定30,000行）にも注意する
- 楕円のnm→mm換算係数と誇張倍率は実データで調整する

## 5. 検証手順（Windows / Power BI Desktop）

1. Power BI Desktop（2024年以降のバージョン）で
   オプション → プレビュー機能 →「Power BI プロジェクト (.pbip) の保存オプション」
   と「レポートの拡張メタデータ形式（PBIR）」を有効化して再起動
2. `LithoBooster.pbip` を開く
3. パラメーター `SampleDataFolder` を自分のPCの `sample_data/` フォルダーの
   絶対パスに変更（末尾に `\` を付ける）→ データの更新
4. モデルビューでリレーション（日付・装置 → CANON/NIKON）を確認
5. テーマ `themes/theme.json` を適用
6. 保存すると `.pbi/` 配下にローカルファイルが生成されるが、
   `.gitignore` 済みのためコミットされない

※ この雛形は手書きのため、Desktopのバージョンによっては開く際に
スキーマ差分のエラーが出る可能性がある。その場合はエラーメッセージを
共有してもらえれば修正する（最終手段: Desktopで新規PBIP保存 →
本雛形のtables/*.tmdlとメジャーを移植する）。

## 6. 課題との対応

- I-001b（接続情報）: 確定後に 2.3 の手順で切替
- I-002（単位・判定の意味）: メジャーの単位ラベル・判定0率の名称に反映
- I-009（逆算の符号規約）: v26_shot_array.json の変位式に反映
