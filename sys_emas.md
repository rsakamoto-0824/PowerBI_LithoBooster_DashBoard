# sys_emas スキーマ ビュー定義

- データベース: Vertica
- 「意味（想定）」「単位（想定）」列はダッシュボード開発用の想定であり、
  確定していないものは末尾に「※要確認」を付けている（→ issues.md I-002）
- 座標系の前提: Wafer中心を原点 (0, 0) とする。詳細はOverlay計測 共通ルールに従う

# ビュー定義①（V_EQP_WAFER_LITHOBOOSTER_CANON）

1行 = 1 Wafer × 1 Shot × 1 Mark（MARKINFO_MARKNO単位）

| No | 物理名 | データ型 | 意味（想定） | 単位（想定） |
|---:|---|---|---|---|
| 1 | TEC_KIND | WideString | 技術区分（データ種別の識別子） | - |
| 2 | LOT_ID | WideString | Lot ID | - |
| 3 | WAFER_ID | WideString | Wafer ID | - |
| 4 | WAFER_NO | Largeint | Lot内のWafer番号（1〜25） | - |
| 5 | CREATE_TIME | DateTime | レコード作成日時 | JST |
| 6 | MEASUREMENT_TIME | DateTime | アライメント計測日時 | JST |
| 7 | PROCESS | WideString | 工程 | - |
| 8 | OPERATION | WideString | オペレーション（作業工程コード） | - |
| 9 | PRODUCT | WideString | 製品名 | - |
| 10 | EQPID | WideString | 露光装置の号機ID | - |
| 11 | DEVICE_TYPE | WideString | デバイス種別 | - |
| 12 | CTRL_JOB | WideString | 補正制御ジョブ名 | - |
| 13 | SHOTINFO_SHOTNO | Largeint | Shot番号 | - |
| 14 | SHOTINFO_PosX | Largeint | Shot中心X座標（Wafer中心原点の絶対座標） | nm |
| 15 | SHOTINFO_PosY | Largeint | Shot中心Y座標（Wafer中心原点の絶対座標） | nm |
| 16 | SHOTINFO_DIRECTION | Largeint | 露光スキャン方向（コード値） | - |
| 17 | IS_AGA_SAMPLE_SHOTS | Boolean | AGAサンプルShotかどうかのフラグ | - |
| 18 | MARKINFO_MARKNO | Largeint | Mark番号（通常1Shotあたり4点） | - |
| 19 | MARKINFO_POSX | Float | MarkのX座標（Shot中心からの相対座標） | mm |
| 20 | MARKINFO_POSY | Float | MarkのY座標（Shot中心からの相対座標） | mm |
| 21 | AGA_LINEAR_MX | Float | AGA線形成分: Wafer倍率X | ppm |
| 22 | AGA_LINEAR_MY | Float | AGA線形成分: Wafer倍率Y | ppm |
| 23 | AGA_LINEAR_TX | Float | AGA線形成分: Wafer回転X | µrad |
| 24 | AGA_LINEAR_TY | Float | AGA線形成分: Wafer回転Y | µrad |
| 25 | AGA_LINEAR_SX | Float | AGA線形成分: WaferシフトX | nm |
| 26 | AGA_LINEAR_SY | Float | AGA線形成分: WaferシフトY | nm |
| 27 | AGA_SHOT_MX | Float | AGA Shot成分: Shot倍率X | ppm |
| 28 | AGA_SHOT_MY | Float | AGA Shot成分: Shot倍率Y | ppm |
| 29 | AGA_SHOT_TX | Float | AGA Shot成分: Shot回転X | µrad |
| 30 | AGA_SHOT_TY | Float | AGA Shot成分: Shot回転Y | µrad |
| 31 | PSO_LINEAR_MX | Float | PSO線形成分: 倍率X | ppm |
| 32 | PSO_LINEAR_MY | Float | PSO線形成分: 倍率Y | ppm |
| 33 | PSO_LINEAR_TX | Float | PSO線形成分: 回転X | µrad |
| 34 | PSO_LINEAR_TY | Float | PSO線形成分: 回転Y | µrad |
| 35 | PSO_LINEAR_SX | Float | PSO線形成分: シフトX | nm |
| 36 | PSO_LINEAR_SY | Float | PSO線形成分: シフトY | nm |
| 37 | PSO_LINEAR_3SX | Float | PSO線形成分: 残差3σ（X） | nm |
| 38 | PSO_LINEAR_3SY | Float | PSO線形成分: 残差3σ（Y） | nm |
| 39 | SEPA_SHOTFORM_SMAGX | Float | Shotごとの線形補正（SEPA、Scanner用）: Shot倍率補正X | ppm |
| 40 | SEPA_SHOTFORM_SMAGY | Float | Shotごとの線形補正（SEPA、Scanner用）: Shot倍率補正Y | ppm |
| 41 | SEPA_SHOTFORM_SROTX | Float | Shotごとの線形補正（SEPA、Scanner用）: Shot回転補正X | µrad |
| 42 | SEPA_SHOTFORM_SROTY | Float | Shotごとの線形補正（SEPA、Scanner用）: Shot回転補正Y | µrad |
| 43 | SEPA_SHOTDATA_SHIFTX | Float | Shotごとの線形補正（SEPA、Scanner用）: Shotシフト補正X | nm |
| 44 | SEPA_SHOTDATA_SHIFTY | Float | Shotごとの線形補正（SEPA、Scanner用）: Shotシフト補正Y | nm |
| 45 | SAME_SHOTFORM_SMAGX | Float | Shotごとの線形補正（SAME、Stepper用）: Shot倍率補正X | ppm |
| 46 | SAME_SHOTFORM_SMAGY | Float | Shotごとの線形補正（SAME、Stepper用）: Shot倍率補正Y | ppm |
| 47 | SAME_SHOTFORM_SROTX | Float | Shotごとの線形補正（SAME、Stepper用）: Shot回転補正X | µrad |
| 48 | SAME_SHOTFORM_SROTY | Float | Shotごとの線形補正（SAME、Stepper用）: Shot回転補正Y | µrad |
| 49 | SAME_SHOTDATA_SHIFTX | Float | Shotごとの線形補正（SAME、Stepper用）: Shotシフト補正X | nm |
| 50 | SAME_SHOTDATA_SHIFTY | Float | Shotごとの線形補正（SAME、Stepper用）: Shotシフト補正Y | nm |
| 51 | RAW_DATA_X | Float | アライメント計測結果X（Mark単位） | nm |
| 52 | RAW_DATA_Y | Float | アライメント計測結果Y（Mark単位） | nm |
| 53 | RAW_DATA_STSX | Float | アライメント計測結果X（Mark単位）の判定 | - |
| 54 | RAW_DATA_STSY | Float | アライメント計測結果Y（Mark単位）の判定 | - |
| 55 | ST_TIMESTAMP | DateTime | DB格納日時 | JST |

---

# ビュー定義②（V_EQP_WAFER_LITHOBOOSTER_NIKON）

1行 = 1 Wafer × 1 補正点（CORRDATA_ID単位）

| No | 物理名 | データ型 | 意味（想定） | 単位（想定） |
|---:|---|---|---|---|
| 1 | TEC_KIND | WideString | 技術区分（データ種別の識別子） | - |
| 2 | LOT_ID | WideString | Lot ID | - |
| 3 | WAFER_ID | WideString | Wafer ID | - |
| 4 | WAFER_NO | Largeint | Lot内のWafer番号（1〜25） | - |
| 5 | CREATE_TIME | DateTime | レコード作成日時 | JST |
| 6 | MEASUREMENT_TIME | DateTime | アライメント計測日時 | JST |
| 7 | PROCESS | WideString | 工程 | - |
| 8 | OPERATION | WideString | オペレーション（作業工程コード） | - |
| 9 | PRODUCT | WideString | 製品名 | - |
| 10 | EQPID | WideString | 露光装置の号機ID | - |
| 11 | DEVICE_TYPE | WideString | デバイス種別 | - |
| 12 | CTRL_JOB | WideString | 補正制御ジョブ名 | - |
| 13 | WAFER_OFSETX | Float | Wafer線形成分: オフセット（シフト）X | nm |
| 14 | WAFER_OFSETY | Float | Wafer線形成分: オフセット（シフト）Y | nm |
| 15 | WAFER_SCALX | Float | Wafer線形成分: スケーリング（倍率）X | ppm |
| 16 | WAFER_SCALY | Float | Wafer線形成分: スケーリング（倍率）Y | ppm |
| 17 | WAFER_ROTX | Float | Wafer線形成分: 回転X | µrad |
| 18 | WAFER_ROTY | Float | Wafer線形成分: 回転Y | µrad |
| 19 | SHOT_OFSETX | Float | Shot線形成分: オフセットX | nm |
| 20 | SHOT_OFSETY | Float | Shot線形成分: オフセットY | nm |
| 21 | SHOT_SCALX | Float | Shot線形成分: スケーリング（倍率）X | ppm |
| 22 | SHOT_SCALY | Float | Shot線形成分: スケーリング（倍率）Y | ppm |
| 23 | SHOT_ROTX | Float | Shot線形成分: 回転X | µrad |
| 24 | SHOT_ROTY | Float | Shot線形成分: 回転Y | µrad |
| 25 | CORRDATA_ID | Largeint | 補正点ID（Wafer内の連番） | - |
| 26 | CORRDATA_POSX | Float | 補正点のX座標（Wafer中心原点） | mm |
| 27 | CORRDATA_POSY | Float | 補正点のY座標（Wafer中心原点） | mm |
| 28 | CORRDATA_OFSETX | Float | 補正点ごとの補正量: オフセットX | nm |
| 29 | CORRDATA_OFSETY | Float | 補正点ごとの補正量: オフセットY | nm |
| 30 | CORRDATA_SCALX | Float | 補正点ごとの補正量: スケーリングX | ppm |
| 31 | CORRDATA_SCALY | Float | 補正点ごとの補正量: スケーリングY | ppm |
| 32 | CORRDATA_ROTX | Float | 補正点ごとの補正量: 回転X | µrad |
| 33 | CORRDATA_ROTY | Float | 補正点ごとの補正量: 回転Y | µrad |
| 34 | SHOTFAC02X | Float | Shot内高次補正係数（多項式係数、X方向 2次項） | 次数依存 |
| 35 | SHOTFAC03X | Float | Shot内高次補正係数（X方向 3次項） | 次数依存 ※要確認 |
| 36 | SHOTFAC04X | Float | Shot内高次補正係数（X方向 4次項） | 次数依存 ※要確認 |
| 37 | SHOTFAC05X | Float | Shot内高次補正係数（X方向 5次項） | 次数依存 ※要確認 |
| 38 | SHOTFAC06X | Float | Shot内高次補正係数（X方向 6次項） | 次数依存 ※要確認 |
| 39 | SHOTFAC11Y | Float | Shot内高次補正係数（Y方向 11項） | 次数依存 ※要確認 |
| 40 | SHOTFAC02Y | Float | Shot内高次補正係数（Y方向 2次項） | 次数依存 ※要確認 |
| 41 | SHOTFAC12Y | Float | Shot内高次補正係数（Y方向 12項） | 次数依存 ※要確認 |
| 42 | SHOTFAC03Y | Float | Shot内高次補正係数（Y方向 3次項） | 次数依存 ※要確認 |
| 43 | SHOTFAC13Y | Float | Shot内高次補正係数（Y方向 13項） | 次数依存 ※要確認 |
| 44 | SHOTFAC04Y | Float | Shot内高次補正係数（Y方向 4次項） | 次数依存 ※要確認 |
| 45 | SHOTFAC14Y | Float | Shot内高次補正係数（Y方向 14項） | 次数依存 ※要確認 |
| 46 | SHOTFAC05Y | Float | Shot内高次補正係数（Y方向 5次項） | 次数依存 ※要確認 |
| 47 | SHOTFAC15Y | Float | Shot内高次補正係数（Y方向 15項） | 次数依存 ※要確認 |
| 48 | SHOTFAC06Y | Float | Shot内高次補正係数（Y方向 6次項） | 次数依存 ※要確認 |
| 49 | SHOTFAC20X | Float | Shot内高次補正係数（X方向 20項） | 次数依存 ※要確認 |
| 50 | SHOTFAC20Y | Float | Shot内高次補正係数（Y方向 20項） | 次数依存 ※要確認 |
| 51 | SHOTFAC30X | Float | Shot内高次補正係数（X方向 30項） | 次数依存 ※要確認 |
| 52 | SHOTFAC11X | Float | Shot内高次補正係数（X方向 11項） | 次数依存 ※要確認 |
| 53 | SHOTFAC12X | Float | Shot内高次補正係数（X方向 12項） | 次数依存 ※要確認 |
| 54 | SHOTFAC21Y | Float | Shot内高次補正係数（Y方向 21項） | 次数依存 ※要確認 |
| 55 | ST_TIMESTAMP | DateTime | DB格納日時 | JST |

---

## 用語の想定（要確認）

- **AGA**: アライメント計測（Advanced Global Alignment）。
  Waferの位置ずれを複数のサンプルShotで計測し、線形成分（シフト・倍率・回転）を算出する処理
- **PSO**: Wafer線形補正成分
- **SEPA / SAME**: Shotごとの線形補正値。SEPA = Scanner用補正、SAME = Stepper用補正
- **CORRDATA**: Wafer面内の補正点ごとの補正量（Nikon）
- **SHOTFAC**: Shot内の高次補正の多項式係数（Nikon）
