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
    ├── version.json           # PBIR定義バージョン（必須。無いとDesktopで開けない）
    ├── report.json
    └── pages/                 # P1〜P11（分析7 + ツールチップ2 + 明細2）
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
- `装置`・`工程`・`製品`・`デバイス種別` はCanon/Nikon両ビューの値を
  DISTINCT統合したディメンション（スライサー1本で両ファクトを絞るため。K-06）。
  DB側にマスタ表が見つかれば参照先をそちらへ切り替える（I-007）
- OPERATION / LOT_ID / WAFER_ID のスライサーはファクト列を直接使用する
  （LotとWaferは装置メーカーをまたいで同一値にならない運用のため）
- `日付` テーブルは「今日を基準に2年前の1月1日〜1年後」をMで動的生成する
  （K-07。範囲固定による日付切れを防止）
- `比較軸` はフィールドパラメーター（装置 / 製品 / 工程の切替。K-12）。
  フィールドパラメーターはPower BIの仕様上計算テーブルでのみ実現できるため、
  例外的に計算テーブルとする（リレーションは持たない）

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
4. `日付` `装置` `工程` `製品` `デバイス種別` はDual/Importのまま運用する（複合モデル）
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
| AGA SX/SY/MX/MY/TX/TY 平均 | CANON | P1 低次補正成分トレンド（V-06） |
| SEPA/SAME SMAG・SROT・SHIFTのX/Y 平均（12本） | CANON | P3 Shot別補正値（V-03） |
| OFSETX/Y・SCALX/Y・ROTX/Y 平均 | NIKON | P4 トレンド（V-06） |
| OFSETX/Y・SCALX/Y・ROTX/Y 平均±3σ 表示（6本） | NIKON | P4 KPIカード（X/Y別） |
| SHOT OFSET/SCAL/ROTのX/Y 平均・SHOTFAC02〜06のX/Y 平均 | NIKON | P6 Shot補正成分バー（V-28） |

今後の追加予定: 共分散楕円用の位置ごとVx/Vy/Cxy（V-22/V-23）、
移動平均・前期間比較（V-08）、しきい値超過フラグ（V-07）。

## 3. レポート設計

- ページはP1〜P7（要件4.2と同じ構成）。レイアウトは `dashboard_mockup.pptx` を正とし、
  モックの配置を1280×720pxのページ座標に写像して実装済み
- テーマは `themes/theme.json` をDesktopの「テーマの参照」から適用する

### 3.1 実装状態（ビジュアル）

各ページ共通: 左レールにスライサー8本
（期間=日付[Date]の範囲指定、DEVICE_TYPE、OPERATION、EQPID=装置、
LOT_ID、WAFER_ID、PROCESS、PRODUCT。ファクト列はページの対象ビュー側を使用）。

| ページ | 標準ビジュアル（実装済み） | Denebプレースホルダー |
|---|---|---|
| P1 | KPIカード4（計測値X/Y±3σ・判定0率・Wafer数）、V-06トレンド2面（シフト／倍率+回転）、V-30計測値トレンド、V-09マトリックス、V-04判定比率バー | V-01箱ひげ |
| P2 | — | V-12平均ベクトル場（装置×OPERATION小マルチ） |
| P3 | V-03 Shot別補正値3面（SMAG/SROT/SHIFT、SEPA+SAMEの4系列） | V-11/V-25/V-27/V-22/V-26 |
| P4 | KPIカード6（成分X/Y別±3σ）、V-06トレンド3面（OFSET/SCAL/ROT）、V-09マトリックス | V-02箱ひげ |
| P5 | — | V-18補正前Shot配列（小マルチ） |
| P6 | V-28 Shot補正成分バー（線形6+SHOTFAC10） | V-14/V-18 |
| P7 | — | V-19/V-23/V-21/V-29 |
| P8/P9 | ツールチップページ（Canon/Nikon。320×240、カード5枚） | — |
| P10/P11 | 明細ページ（Canon/Nikon。ドリルスルー専用、上位1,000行制限） | — |

ツールチップ・明細ページの補足（K-11）:

- P8/P9はツールチップ用バインド済み（ビューモードでは非表示）。
  **各ビジュアルへの割り当てはDesktopで行う**
  （ビジュアルの書式 → ツールチップ → レポートページ → P8またはP9を選択）
- P10/P11はP3/P6と同じくEQPID・LOT_ID・OPERATIONを受けるドリルスルー先。
  明細テーブルにはVisualTopNフィルター（上位1,000行）を設定済み。
  上限値の妥当性はDesktopでの表示確認時に調整する
- P1/P4の比較軸スライサー（フィールドパラメーター）で、
  マトリックスの行と判定比率のカテゴリを装置 / 製品 / 工程に切り替えられる（K-12）。
  トレンドの凡例切替は「1グラフ1メジャー」への再構成が必要なため、
  Desktopでの調整フェーズで判断する

補足:

- V-06の6成分小マルチは、単位が混在するため標準折れ線を
  単位グループごとに分割して実装した（P1: nm系とppm/µrad系の2面、P4: 3面）
- V-09のマトリックス色スケール（条件付き書式）はDesktop側で設定する
- Denebプレースホルダーはテキストボックスで位置を確保しており、
  記載の手順（Deneb挿入 → フィールド設定 → `deneb/*.json` 貼り付け）で置き換える

### 3.3 スライサー同期とドリルスルー

スライサー同期（全56本に `syncGroup` 設定済み）:

| グループ | 対象ページ | 内容 |
|---|---|---|
| 期間・装置・DEVICE_TYPE・PROCESS・PRODUCT | 全7ページ | ディメンション列のため全ページで選択を共有（K-06） |
| 比較軸 | P1/P4 | フィールドパラメーターの選択を共有（K-12） |
| OPERATION / LOT_ID / WAFER_ID の各 _Canon | P1/P2/P3/P7 | CANON列のスライサー |
| 同 _Nikon | P4/P5/P6 | NIKON列のスライサー |

期間スライサーの既定値（K-03）:

- 全ページの期間スライサーは**相対日付モード**で、既定の選択状態として
  「直近7日（今日を含む）」を保存済み。ファイルを開いた直後のクエリは
  直近7日分に絞られ、全期間スキャンがVerticaへ飛ぶことを防ぐ
- 期間はその後スライサーで自由に変更できる（過去N日 / 週 / 月など）
- **既定のN日を変える方法**: Desktopでいずれかのページの期間スライサーの
  日数を変更 → 同期グループ「期間」で全ページへ反映 → 保存すると
  それが新しい既定になる（JSON上は各 `pXSlicerDate/visual.json` の
  `"Amount"` が該当。値は負数で、-7 = 直近7日）

ドリルスルー（P3・P6が受け側。`pageBinding` + ページフィルターで定義）:

- P3（Canon詳細）: 装置[EQPID]・CANON[LOT_ID]・CANON[OPERATION] を受け取る
- P6（Nikon詳細）: 装置[EQPID]・NIKON[LOT_ID]・NIKON[OPERATION] を受け取る
- 両ページ左上に「戻る」ボタン（actionButton、Back動作）を配置
- 発生元はフィールドが一致するデータ点の右クリック（P1のマトリックス等。
  P2/P5のDeneb実装枠は、Denebへの置き換え後に右クリックからのドリルスルーが有効になる）

### 3.2 ビジュアル数の目安（8個以下）について

P1/P4はモックアップ準拠でカード含め9〜10個になっている。
カード・スライサーはクエリ負荷が小さいため当面許容し、
ページロード3秒を超える場合はカードの統合・トレンドの集約で削減する。

## 4. Deneb設計

### 4.1 採否理由（Power BI開発ルール準拠）

| 可視化 | 標準ビジュアルでの実現性 | 判断 |
|---|---|---|
| ベクトル場（矢印）V-11/V-12 | 不可（散布図に矢印なし） | Deneb採用 |
| 共分散楕円 V-22/V-23 | 不可 | Deneb採用 |
| 補正前Shot配列 V-26/V-18 | 不可 | Deneb採用 |
| Shot枠つきヒートマップ V-25/V-27 | 標準散布図では枠不可 | Deneb採用 |
| 箱ひげ図 V-01/V-02/V-21/V-29 | 不可（標準に箱ひげ図がないため） | Deneb採用 |
| トレンド・バー・マトリックス・カード | 可能 | 標準ビジュアル |

- DenebはAppSourceの**認定版**を使用する
- 定義は `deneb/*.json` を正とし、修正時はDenebエディタへ貼り付けて反映する

### 4.2 グラフごとの定義（1ビジュアル = 1ファイル）

ファイル名は「ページ_可視化ID_内容」。**フィールド名はモデルの実際の
列名・メジャー名に一致**させており、レポートの実装枠に記載のフィールドを
名前どおりDenebの「値」へ追加すれば動く構成にしている。
各ファイルの `usermeta.datasetFields` が必要フィールドの正である。

| ファイル | 対象 | 備考 |
|---|---|---|
| [p1_v01_box_measxy_by_operation.json](deneb/p1_v01_box_measxy_by_operation.json) | V-01 計測値箱ひげ | X/Y成分を2面並置 |
| [p2_v12_mean_vector_field.json](deneb/p2_v12_mean_vector_field.json) | V-12 平均ベクトル場俯瞰 | 装置×OPERATIONのfacet。枠サイズはOPERATIONから自動判定 |
| [p3_v11_vector_map.json](deneb/p3_v11_vector_map.json) | V-11 計測値ベクトル | 矢印倍率・Shot枠サイズのスライダー付き |
| [p3_v25_heatmap_xy.json](deneb/p3_v25_heatmap_xy.json) | V-25 X/Yヒートマップ | 2面並置、発散配色（0中心） |
| [p3_v27_heatmap_veclen.json](deneb/p3_v27_heatmap_veclen.json) | V-27 ベクトル長ヒートマップ | viridis配色 |
| [p3_v22_covariance_ellipse.json](deneb/p3_v22_covariance_ellipse.json) | V-22 面内共分散楕円 | 分散・共分散はE[X²]−E[X]²等でDeneb側計算。Wafer数3未満非表示 |
| [p3_v26_shot_array_canon.json](deneb/p3_v26_shot_array_canon.json) | V-26 補正前Shot配列（Canon） | SEPA+SAME合成。符号はI-009 |
| [p4_v02_box_corrxy_by_operation.json](deneb/p4_v02_box_corrxy_by_operation.json) | V-02 補正量箱ひげ | X/Y成分を2面並置 |
| [p5_v18_shot_array_grid.json](deneb/p5_v18_shot_array_grid.json) | V-18 補正前Shot配列俯瞰（Nikon） | 装置×OPERATIONのfacet。符号はI-009 |
| [p6_v14_corr_vector_map.json](deneb/p6_v14_corr_vector_map.json) | V-14 補正点ベクトル | OFSET/SCAL/ROTをドロップダウン切替 |
| [p6_v18_shot_array_wafer.json](deneb/p6_v18_shot_array_wafer.json) | V-18 補正前Shot配列（Wafer単位） | 符号はI-009 |
| [p7_v19_stack_vector.json](deneb/p7_v19_stack_vector.json) | V-19 スタック平均ベクトル | 全体/方向1/方向2の3面。全体は点数重み付き合成 |
| [p7_v23_stack_ellipse.json](deneb/p7_v23_stack_ellipse.json) | V-23 スタック共分散楕円 | 同上の3面構成 |
| [p7_v21_box_by_mark.json](deneb/p7_v21_box_by_mark.json) | V-21 Mark位置別箱ひげ | x軸=Mark番号 |
| [p7_v29_box_by_direction.json](deneb/p7_v29_box_by_direction.json) | V-29 方向別箱ひげ | 全体/方向1/方向2（行を複製して3区分化） |

実装時の注意:

- **座標の単位**: `SHOTINFO_PosX/Y` は nm（spec内で1/1,000,000してmm化）、
  `MARKINFO_POSX/Y` と `CORRDATA_POSX/Y` は mm（変換なし）。
  この換算はspec側で実装済みのため、フィールドを名前どおり渡せばよい
- 計測値・補正量は**メジャー（平均）で渡す**。重複データはPower BI側の
  グループ化で自動的に平均される（要件4.4の重複平均ルールと整合）
- Denebへ渡す行数を絞る（必須フィルター + Wafer選択）。
  DirectQueryではビジュアルごとの行数上限（既定30,000行）にも注意する
- 矢印・楕円・誇張の倍率はスライダーで調整可能。実データで既定値を見直す
- 全15ファイルはVega-Lite v5公式スキーマで検証済み。
  フィールド名はモデル定義との一致を機械照合済み

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
- I-009（逆算の符号規約）: p3_v26 / p5_v18 / p6_v18 の各Shot配列specの変位式に反映
