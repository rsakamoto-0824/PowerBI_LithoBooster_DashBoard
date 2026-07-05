"""LithoBoosterビューのダミーデータCSVを生成するスクリプト。

sys_emas.md のビュー定義（Canon / Nikon）に合わせた列構成で、
Power BIダッシュボード開発用のダミーデータを作成する。
実データは一切含まない（LOT名・装置名はすべて架空の形式）。

実行方法:
    python3 generate_sample_data.py

出力:
    V_EQP_WAFER_LITHOBOOSTER_CANON_sample.csv
    V_EQP_WAFER_LITHOBOOSTER_NIKON_sample.csv
"""

import csv
import math
import random
from datetime import datetime, timedelta
from pathlib import Path

# ---------------------------------------------------------------
# 定数（生成条件）
# ---------------------------------------------------------------
RANDOM_SEED = 20260705

OUTPUT_DIR = Path(__file__).parent
CANON_CSV_NAME = "V_EQP_WAFER_LITHOBOOSTER_CANON_sample.csv"
NIKON_CSV_NAME = "V_EQP_WAFER_LITHOBOOSTER_NIKON_sample.csv"

# 日時（JST想定）。ダッシュボードの既定フィルター「直近7日」に収まる範囲で、
# Lotの計測開始時刻をこの期間内にランダムに割り当てる
MEASUREMENT_PERIOD_START = datetime(2026, 6, 29, 0, 0, 0)
MEASUREMENT_PERIOD_HOURS = 138  # 6/29 00:00 〜 7/4 18:00
DATETIME_FORMAT = "%Y/%m/%d %H:%M:%S"
WAFER_INTERVAL_MINUTES = 4      # Wafer1枚あたりの処理間隔
CREATE_DELAY_MINUTES = 2        # 計測 → レコード作成までの遅れ
STORE_DELAY_MINUTES = 5         # 計測 → DB格納までの遅れ

# Wafer / Shot条件（Overlay計測 共通ルール準拠）
WAFER_RADIUS_MM = 150.0         # 有効半径。150mm以上の測定点は除外
SHOT_CENTER_MAX_RADIUS_MM = 145.0  # Shot中心がこの半径内のShotを対象にする
NM_PER_MM = 1_000_000           # Shot座標(nm)変換用

# OPERATIONごとのShotレイアウト定義。
# Shotサイズ（ピッチ）とMark数が異なり、グリッド原点も少しズレる。
# Mark配置はShot中心からの相対座標(mm)
OPERATION_LAYOUTS = {
    "RDH-MLF": {
        "shot_pitch_x_mm": 24.0,
        "shot_pitch_y_mm": 28.0,
        "grid_offset_x_mm": 0.0,
        "grid_offset_y_mm": 0.0,
        "mark_offsets_mm": [       # 4隅の4点
            (1, -10.0, -12.0),
            (2, 10.0, -12.0),
            (3, -10.0, 12.0),
            (4, 10.0, 12.0),
        ],
    },
    "MSR-MLF": {
        "shot_pitch_x_mm": 22.0,
        "shot_pitch_y_mm": 26.0,
        "grid_offset_x_mm": 2.0,   # RDHに対してグリッド原点が少しズレる
        "grid_offset_y_mm": -1.5,
        "mark_offsets_mm": [       # 4隅 + 上下辺中央の6点
            (1, -9.0, -11.0),
            (2, 9.0, -11.0),
            (3, -9.0, 11.0),
            (4, 9.0, 11.0),
            (5, 0.0, -11.0),
            (6, 0.0, 11.0),
        ],
    },
}

# Lot構成。Lotは装置・時刻ともランダムに割り当てる（ランダム測定を想定）
LOTS_PER_VIEW = 8               # 各ビュー（Canon / Nikon）のLot数
WAFER_COUNT_MIN = 3             # 1Lotあたりの最小Wafer数
WAFER_COUNT_MAX = 25            # 1Lotあたりの最大Wafer数（1Lot = 最大25枚）

# 属性値（すべて架空。実データのxlsxサンプルと同じ形式に合わせている）
TEC_KIND = 5
PRODUCT = "NM975"
DEVICE_TYPE = "AADE058_01.00"
EQP_NUMBERS = ["01", "02", "03"]      # 装置は連番3台
EQPID_FORMAT = "ML{number}MF"          # 例: ML01MF
PROCESS_OPERATION_PAIRS = [
    ("RDH_PR", "RDH-MLF"),
    ("MSR_PR", "MSR-MLF"),
]

# LOT_IDの形式: 例 5AW975B82.01（"975"は製品NM975に対応させる）
LOT_ID_FORMAT = "5{letter}W975B{number:02d}.{suffix}"
LOT_LETTER_CHOICES = "AB"
LOT_SUFFIX_CHOICES = "123456789ABCDEF"  # 末尾は "0"+英数1文字（例: .01, .0F）

# Shotスキャン方向のコード値（0 / 1 / 2 の3値）
DIRECTION_EVERY_8TH_SHOT = 8    # Shot番号が8の倍数の偶数Shotをコード2にする

# ばらつきの大きさ（ダミーデータの見た目を決めるだけの値）
SHIFT_SIGMA_NM = 15.0           # シフト・オフセット成分
MAG_SIGMA_PPM = 0.5             # 倍率・スケーリング成分
ROT_SIGMA_URAD = 0.5            # 回転成分
SHOT_COMP_SIGMA = 0.8           # Shot成分（ppm / µrad）
SHOT_SHIFT_SIGMA_NM = 3.0       # Shotシフト補正
RESIDUAL_NOISE_SIGMA_NM = 3.0   # 計測残差のランダムノイズ
CORR_NOISE_SIGMA_NM = 2.0       # Nikon補正点のランダムノイズ
SHOTFAC_SIGMA = 0.001           # 高次補正係数
PSO_3SIGMA_MIN_NM = 3.0
PSO_3SIGMA_MAX_NM = 9.0
AGA_SAMPLE_SHOT_COUNT = 12      # AGAサンプルShot数

# 計測判定（RAW_DATA_STSX/Y）。0の割合とX/Y判定が食い違う割合
# （0/1の意味は未確定。issues.md I-002参照。分布は実データサンプルに合わせた）
STS_ZERO_RATE = 0.26
STS_XY_MISMATCH_RATE = 0.03

random.seed(RANDOM_SEED)


# ---------------------------------------------------------------
# 共通処理
# ---------------------------------------------------------------
def build_shot_layout(layout):
    """OPERATIONごとのレイアウト定義から、Shot中心座標(mm)の一覧を作る。

    Shot番号は下から上・左から右の順に振る。
    """
    pitch_x = layout["shot_pitch_x_mm"]
    pitch_y = layout["shot_pitch_y_mm"]
    shots = []
    shot_no = 1
    y_count = int(WAFER_RADIUS_MM / pitch_y) + 1
    x_count = int(WAFER_RADIUS_MM / pitch_x) + 1
    for iy in range(-y_count, y_count + 1):
        center_y = (iy + 0.5) * pitch_y + layout["grid_offset_y_mm"]
        for ix in range(-x_count, x_count + 1):
            center_x = (ix + 0.5) * pitch_x + layout["grid_offset_x_mm"]
            radius = math.hypot(center_x, center_y)
            if radius <= SHOT_CENTER_MAX_RADIUS_MM:
                shots.append((shot_no, center_x, center_y))
                shot_no += 1
    return shots


def build_layouts_by_operation():
    """OPERATION名 →（Shot一覧, Mark配置）の対応表を作る。"""
    return {
        operation: (build_shot_layout(layout), layout["mark_offsets_mm"])
        for operation, layout in OPERATION_LAYOUTS.items()
    }


def format_time(base, offset_minutes):
    return (base + timedelta(minutes=offset_minutes)).strftime(DATETIME_FORMAT)


def new_lot_id(used_lot_ids):
    """実データと同じ形式のLOT_IDを重複しないように作る。"""
    while True:
        lot_id = LOT_ID_FORMAT.format(
            letter=random.choice(LOT_LETTER_CHOICES),
            number=random.randint(0, 99),
            suffix="0" + random.choice(LOT_SUFFIX_CHOICES),
        )
        if lot_id not in used_lot_ids:
            used_lot_ids.add(lot_id)
            return lot_id


def build_lot_plans(used_lot_ids):
    """1ビュー分のLot計画（ID・装置・工程・計測開始時刻・Wafer数）を作る。

    Lotがどの装置でいつ測定されたかはランダムに割り当てる。
    """
    plans = []
    for _ in range(LOTS_PER_VIEW):
        eqp_number = random.choice(EQP_NUMBERS)
        process, operation = random.choice(PROCESS_OPERATION_PAIRS)
        start_offset_minutes = random.randint(0, MEASUREMENT_PERIOD_HOURS * 60)
        plans.append({
            "lot_id": new_lot_id(used_lot_ids),
            "eqpid": EQPID_FORMAT.format(number=eqp_number),
            "process": process,
            "operation": operation,
            "wafer_count": random.randint(WAFER_COUNT_MIN, WAFER_COUNT_MAX),
            "start_time": MEASUREMENT_PERIOD_START
            + timedelta(minutes=start_offset_minutes),
        })
    # 計測時刻順に並べる（DBに格納された順のイメージ）
    plans.sort(key=lambda p: p["start_time"])
    return plans


def wafer_id_of(lot_id, wafer_no):
    """WAFER_ID = LOT_IDの「.」より前 + "-" + Wafer番号2桁。"""
    return f"{lot_id.split('.')[0]}-{wafer_no:02d}"


def shot_direction(shot_no):
    """スキャン方向コード（0 / 1 / 2）を作る。

    奇数Shotは1、偶数Shotは原則0、8の倍数のShotだけ2にする。
    """
    if shot_no % 2 == 1:
        return 1
    if shot_no % DIRECTION_EVERY_8TH_SHOT == 0:
        return 2
    return 0


def measurement_status_pair():
    """計測判定（STSX, STSY）を作る。X/Yはほぼ同じ値になる。"""
    sts_x = 0 if random.random() < STS_ZERO_RATE else 1
    sts_y = sts_x
    if random.random() < STS_XY_MISMATCH_RATE:
        sts_y = 1 - sts_x
    return sts_x, sts_y


# ---------------------------------------------------------------
# Canonビュー生成
# ---------------------------------------------------------------
CANON_HEADER = [
    "TEC_KIND", "LOT_ID", "WAFER_ID", "WAFER_NO", "CREATE_TIME",
    "MEASUREMENT_TIME", "PROCESS", "OPERATION", "PRODUCT", "EQPID",
    "DEVICE_TYPE", "CTRL_JOB", "SHOTINFO_SHOTNO", "SHOTINFO_PosX",
    "SHOTINFO_PosY", "SHOTINFO_DIRECTION", "IS_AGA_SAMPLE_SHOTS",
    "MARKINFO_MARKNO", "MARKINFO_POSX", "MARKINFO_POSY",
    "AGA_LINEAR_MX", "AGA_LINEAR_MY", "AGA_LINEAR_TX", "AGA_LINEAR_TY",
    "AGA_LINEAR_SX", "AGA_LINEAR_SY",
    "AGA_SHOT_MX", "AGA_SHOT_MY", "AGA_SHOT_TX", "AGA_SHOT_TY",
    "PSO_LINEAR_MX", "PSO_LINEAR_MY", "PSO_LINEAR_TX", "PSO_LINEAR_TY",
    "PSO_LINEAR_SX", "PSO_LINEAR_SY", "PSO_LINEAR_3SX", "PSO_LINEAR_3SY",
    "SEPA_SHOTFORM_SMAGX", "SEPA_SHOTFORM_SMAGY",
    "SEPA_SHOTFORM_SROTX", "SEPA_SHOTFORM_SROTY",
    "SEPA_SHOTDATA_SHIFTX", "SEPA_SHOTDATA_SHIFTY",
    "SAME_SHOTFORM_SMAGX", "SAME_SHOTFORM_SMAGY",
    "SAME_SHOTFORM_SROTX", "SAME_SHOTFORM_SROTY",
    "SAME_SHOTDATA_SHIFTX", "SAME_SHOTDATA_SHIFTY",
    "RAW_DATA_X", "RAW_DATA_Y", "RAW_DATA_STSX", "RAW_DATA_STSY",
    "ST_TIMESTAMP",
]


def canon_wafer_params():
    """Wafer1枚分の線形成分・補正値（Wafer内で一定の値）を作る。"""
    return {
        "aga_mx": random.gauss(0, MAG_SIGMA_PPM),
        "aga_my": random.gauss(0, MAG_SIGMA_PPM),
        "aga_tx": random.gauss(0, ROT_SIGMA_URAD),
        "aga_ty": random.gauss(0, ROT_SIGMA_URAD),
        "aga_sx": random.gauss(0, SHIFT_SIGMA_NM),
        "aga_sy": random.gauss(0, SHIFT_SIGMA_NM),
        "aga_shot_mx": random.gauss(0, SHOT_COMP_SIGMA),
        "aga_shot_my": random.gauss(0, SHOT_COMP_SIGMA),
        "aga_shot_tx": random.gauss(0, SHOT_COMP_SIGMA),
        "aga_shot_ty": random.gauss(0, SHOT_COMP_SIGMA),
        "pso_mx": random.gauss(0, MAG_SIGMA_PPM),
        "pso_my": random.gauss(0, MAG_SIGMA_PPM),
        "pso_tx": random.gauss(0, ROT_SIGMA_URAD),
        "pso_ty": random.gauss(0, ROT_SIGMA_URAD),
        "pso_sx": random.gauss(0, SHIFT_SIGMA_NM),
        "pso_sy": random.gauss(0, SHIFT_SIGMA_NM),
        "pso_3sx": random.uniform(PSO_3SIGMA_MIN_NM, PSO_3SIGMA_MAX_NM),
        "pso_3sy": random.uniform(PSO_3SIGMA_MIN_NM, PSO_3SIGMA_MAX_NM),
        "sepa_smagx": random.gauss(0, SHOT_COMP_SIGMA),
        "sepa_smagy": random.gauss(0, SHOT_COMP_SIGMA),
        "sepa_srotx": random.gauss(0, SHOT_COMP_SIGMA),
        "sepa_sroty": random.gauss(0, SHOT_COMP_SIGMA),
        "sepa_shiftx": random.gauss(0, SHOT_SHIFT_SIGMA_NM),
        "sepa_shifty": random.gauss(0, SHOT_SHIFT_SIGMA_NM),
        "same_smagx": random.gauss(0, SHOT_COMP_SIGMA),
        "same_smagy": random.gauss(0, SHOT_COMP_SIGMA),
        "same_srotx": random.gauss(0, SHOT_COMP_SIGMA),
        "same_sroty": random.gauss(0, SHOT_COMP_SIGMA),
        "same_shiftx": random.gauss(0, SHOT_SHIFT_SIGMA_NM),
        "same_shifty": random.gauss(0, SHOT_SHIFT_SIGMA_NM),
    }


def canon_residual_nm(params, pos_x_mm, pos_y_mm):
    """計測点位置での残差(nm)を線形モデル + ノイズで作る。

    ppm × mm = nm、µrad × mm = nm の関係を使う。
    """
    raw_x = (
        params["aga_sx"]
        + params["aga_mx"] * pos_x_mm
        - params["aga_tx"] * pos_y_mm
        + random.gauss(0, RESIDUAL_NOISE_SIGMA_NM)
    )
    raw_y = (
        params["aga_sy"]
        + params["aga_my"] * pos_y_mm
        + params["aga_ty"] * pos_x_mm
        + random.gauss(0, RESIDUAL_NOISE_SIGMA_NM)
    )
    return raw_x, raw_y


def generate_canon_rows(layouts_by_operation, lot_plans):
    rows = []
    for plan in lot_plans:
        shots, mark_offsets = layouts_by_operation[plan["operation"]]
        for wafer_index in range(plan["wafer_count"]):
            wafer_no = wafer_index + 1
            wafer_id = wafer_id_of(plan["lot_id"], wafer_no)
            meas_time = plan["start_time"] + timedelta(
                minutes=WAFER_INTERVAL_MINUTES * wafer_index
            )
            create_time = format_time(meas_time, CREATE_DELAY_MINUTES)
            st_time = format_time(meas_time, STORE_DELAY_MINUTES)
            params = canon_wafer_params()
            sample_shot_nos = set(
                random.sample([s[0] for s in shots], AGA_SAMPLE_SHOT_COUNT)
            )

            for shot_no, shot_x_mm, shot_y_mm in shots:
                for mark_no, mark_x_mm, mark_y_mm in mark_offsets:
                    pos_x_mm = shot_x_mm + mark_x_mm
                    pos_y_mm = shot_y_mm + mark_y_mm
                    # 半径150mm以上の測定点は存在しない前提で除外する
                    if math.hypot(pos_x_mm, pos_y_mm) >= WAFER_RADIUS_MM:
                        continue
                    raw_x, raw_y = canon_residual_nm(params, pos_x_mm, pos_y_mm)
                    sts_x, sts_y = measurement_status_pair()
                    rows.append([
                        TEC_KIND, plan["lot_id"], wafer_id, wafer_no,
                        create_time, meas_time.strftime(DATETIME_FORMAT),
                        plan["process"], plan["operation"], PRODUCT,
                        plan["eqpid"], DEVICE_TYPE,
                        f"CJ_{plan['eqpid']}_{plan['lot_id']}",
                        shot_no,
                        round(shot_x_mm * NM_PER_MM),
                        round(shot_y_mm * NM_PER_MM),
                        shot_direction(shot_no),
                        shot_no in sample_shot_nos,
                        mark_no, mark_x_mm, mark_y_mm,
                        round(params["aga_mx"], 4), round(params["aga_my"], 4),
                        round(params["aga_tx"], 4), round(params["aga_ty"], 4),
                        round(params["aga_sx"], 2), round(params["aga_sy"], 2),
                        round(params["aga_shot_mx"], 4),
                        round(params["aga_shot_my"], 4),
                        round(params["aga_shot_tx"], 4),
                        round(params["aga_shot_ty"], 4),
                        round(params["pso_mx"], 4), round(params["pso_my"], 4),
                        round(params["pso_tx"], 4), round(params["pso_ty"], 4),
                        round(params["pso_sx"], 2), round(params["pso_sy"], 2),
                        round(params["pso_3sx"], 2), round(params["pso_3sy"], 2),
                        round(params["sepa_smagx"], 4),
                        round(params["sepa_smagy"], 4),
                        round(params["sepa_srotx"], 4),
                        round(params["sepa_sroty"], 4),
                        round(params["sepa_shiftx"], 2),
                        round(params["sepa_shifty"], 2),
                        round(params["same_smagx"], 4),
                        round(params["same_smagy"], 4),
                        round(params["same_srotx"], 4),
                        round(params["same_sroty"], 4),
                        round(params["same_shiftx"], 2),
                        round(params["same_shifty"], 2),
                        round(raw_x, 2), round(raw_y, 2),
                        sts_x, sts_y,
                        st_time,
                    ])
    return rows


# ---------------------------------------------------------------
# Nikonビュー生成
# ---------------------------------------------------------------
NIKON_HEADER = [
    "TEC_KIND", "LOT_ID", "WAFER_ID", "WAFER_NO", "CREATE_TIME",
    "MEASUREMENT_TIME", "PROCESS", "OPERATION", "PRODUCT", "EQPID",
    "DEVICE_TYPE", "CTRL_JOB",
    "WAFER_OFSETX", "WAFER_OFSETY", "WAFER_SCALX", "WAFER_SCALY",
    "WAFER_ROTX", "WAFER_ROTY",
    "SHOT_OFSETX", "SHOT_OFSETY", "SHOT_SCALX", "SHOT_SCALY",
    "SHOT_ROTX", "SHOT_ROTY",
    "CORRDATA_ID", "CORRDATA_POSX", "CORRDATA_POSY",
    "CORRDATA_OFSETX", "CORRDATA_OFSETY", "CORRDATA_SCALX", "CORRDATA_SCALY",
    "CORRDATA_ROTX", "CORRDATA_ROTY",
    "SHOTFAC02X", "SHOTFAC03X", "SHOTFAC04X", "SHOTFAC05X", "SHOTFAC06X",
    "SHOTFAC11Y", "SHOTFAC02Y", "SHOTFAC12Y", "SHOTFAC03Y", "SHOTFAC13Y",
    "SHOTFAC04Y", "SHOTFAC14Y", "SHOTFAC05Y", "SHOTFAC15Y", "SHOTFAC06Y",
    "SHOTFAC20X", "SHOTFAC20Y", "SHOTFAC30X", "SHOTFAC11X", "SHOTFAC12X",
    "SHOTFAC21Y",
    "ST_TIMESTAMP",
]

NIKON_SHOTFAC_COUNT = 21  # SHOTFAC列の数


def nikon_wafer_params():
    """Wafer1枚分の線形成分・高次係数（Wafer内で一定の値）を作る。"""
    return {
        "wafer_ofsetx": random.gauss(0, SHIFT_SIGMA_NM),
        "wafer_ofsety": random.gauss(0, SHIFT_SIGMA_NM),
        "wafer_scalx": random.gauss(0, MAG_SIGMA_PPM),
        "wafer_scaly": random.gauss(0, MAG_SIGMA_PPM),
        "wafer_rotx": random.gauss(0, ROT_SIGMA_URAD),
        "wafer_roty": random.gauss(0, ROT_SIGMA_URAD),
        "shot_ofsetx": random.gauss(0, SHOT_SHIFT_SIGMA_NM),
        "shot_ofsety": random.gauss(0, SHOT_SHIFT_SIGMA_NM),
        "shot_scalx": random.gauss(0, SHOT_COMP_SIGMA),
        "shot_scaly": random.gauss(0, SHOT_COMP_SIGMA),
        "shot_rotx": random.gauss(0, SHOT_COMP_SIGMA),
        "shot_roty": random.gauss(0, SHOT_COMP_SIGMA),
        "shotfac": [
            round(random.gauss(0, SHOTFAC_SIGMA), 6)
            for _ in range(NIKON_SHOTFAC_COUNT)
        ],
    }


def generate_nikon_rows(layouts_by_operation, lot_plans):
    rows = []
    for plan in lot_plans:
        shots, _ = layouts_by_operation[plan["operation"]]
        for wafer_index in range(plan["wafer_count"]):
            wafer_no = wafer_index + 1
            wafer_id = wafer_id_of(plan["lot_id"], wafer_no)
            meas_time = plan["start_time"] + timedelta(
                minutes=WAFER_INTERVAL_MINUTES * wafer_index
            )
            create_time = format_time(meas_time, CREATE_DELAY_MINUTES)
            st_time = format_time(meas_time, STORE_DELAY_MINUTES)
            params = nikon_wafer_params()

            # 補正点はShot中心と同じ位置に置く（1点 = 1 Shot相当）
            for corr_id, (shot_no, pos_x_mm, pos_y_mm) in enumerate(
                shots, start=1
            ):
                corr_ofsetx = (
                    params["wafer_ofsetx"]
                    + params["wafer_scalx"] * pos_x_mm
                    - params["wafer_rotx"] * pos_y_mm
                    + random.gauss(0, CORR_NOISE_SIGMA_NM)
                )
                corr_ofsety = (
                    params["wafer_ofsety"]
                    + params["wafer_scaly"] * pos_y_mm
                    + params["wafer_roty"] * pos_x_mm
                    + random.gauss(0, CORR_NOISE_SIGMA_NM)
                )
                rows.append([
                    TEC_KIND, plan["lot_id"], wafer_id, wafer_no,
                    create_time, meas_time.strftime(DATETIME_FORMAT),
                    plan["process"], plan["operation"], PRODUCT,
                    plan["eqpid"], DEVICE_TYPE,
                    f"CJ_{plan['eqpid']}_{plan['lot_id']}",
                    round(params["wafer_ofsetx"], 2),
                    round(params["wafer_ofsety"], 2),
                    round(params["wafer_scalx"], 4),
                    round(params["wafer_scaly"], 4),
                    round(params["wafer_rotx"], 4),
                    round(params["wafer_roty"], 4),
                    round(params["shot_ofsetx"], 2),
                    round(params["shot_ofsety"], 2),
                    round(params["shot_scalx"], 4),
                    round(params["shot_scaly"], 4),
                    round(params["shot_rotx"], 4),
                    round(params["shot_roty"], 4),
                    corr_id, pos_x_mm, pos_y_mm,
                    round(corr_ofsetx, 2), round(corr_ofsety, 2),
                    round(random.gauss(0, SHOT_COMP_SIGMA), 4),
                    round(random.gauss(0, SHOT_COMP_SIGMA), 4),
                    round(random.gauss(0, SHOT_COMP_SIGMA), 4),
                    round(random.gauss(0, SHOT_COMP_SIGMA), 4),
                    *params["shotfac"],
                    st_time,
                ])
    return rows


# ---------------------------------------------------------------
# メイン処理
# ---------------------------------------------------------------
def write_csv(file_name, header, rows):
    output_path = OUTPUT_DIR / file_name
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)
    print(f"{file_name}: {len(rows)}行を出力しました")


def main():
    layouts_by_operation = build_layouts_by_operation()
    for operation, (shots, mark_offsets) in layouts_by_operation.items():
        print(f"{operation}: Shot数 {len(shots)} / Mark数 {len(mark_offsets)}点")
    used_lot_ids = set()  # Canon / NikonでLOT_IDが重複しないよう共有する
    canon_plans = build_lot_plans(used_lot_ids)
    nikon_plans = build_lot_plans(used_lot_ids)
    write_csv(CANON_CSV_NAME, CANON_HEADER,
              generate_canon_rows(layouts_by_operation, canon_plans))
    write_csv(NIKON_CSV_NAME, NIKON_HEADER,
              generate_nikon_rows(layouts_by_operation, nikon_plans))


if __name__ == "__main__":
    main()
