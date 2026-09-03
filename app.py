"""TSAD Decision Studio — a decision-support prototype based on Dev18 evidence."""

from __future__ import annotations

import math

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


st.set_page_config(
    page_title="TSAD Decision Studio",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)


# The figures marked observed come from the supplied Dev18 brief.  Values marked
# candidate are selection milestones, not claims of statistically significant wins.
CHECKPOINTS = [5, 10, 20, 40, 60, 80, 100]
OBSERVED_VUS = {
    "MWVAR": {q: 0.274663 for q in CHECKPOINTS},
    "GDN": {10: 0.276017, 20: 0.306231},
    "TSPulse": {q: 0.281481 for q in CHECKPOINTS},
    "PaAno": {40: 0.331},
}

MODEL_DATA = {
    "MWVAR": {
        "tier": "Tier 1", "kind": "경량·비학습 기준선", "min_q": 5,
        "gpu_gib": 0.0, "cost": 1, "latency": "낮음", "training": "불필요",
        "desc": "Cold start에서도 비교 가능한 경량 기준선입니다.",
        "status": "Observed (Dev18)",
    },
    "GDN": {
        "tier": "Tier 2", "kind": "target 정상 데이터 학습", "min_q": 10,
        "gpu_gib": 18.35, "cost": 4, "latency": "중간", "training": "필요",
        "desc": "10%부터 공통 실행 가능; 20%에서 Dev18 성능 우세 후보입니다.",
        "status": "Observed (Dev18)",
    },
    "PaAno": {
        "tier": "Tier 2", "kind": "target 정상 데이터 학습", "min_q": 40,
        "gpu_gib": 0.53, "cost": 3, "latency": "중간", "training": "필요",
        "desc": "40%부터 전환 재평가 대상인 학습형 후보입니다.",
        "status": "Candidate milestone",
    },
    "TSPulse": {
        "tier": "Tier 3", "kind": "target 학습 불필요 zero-shot", "min_q": 5,
        "gpu_gib": 8.23, "cost": 4, "latency": "높음", "training": "불필요",
        "desc": "Cold start의 zero-shot 선택지이며, 비용 우위는 아직 검증되지 않았습니다.",
        "status": "Observed (Dev18)",
    },
    "SQDIFF_LAST3": {
        "tier": "Baseline", "kind": "경량 기준선", "min_q": 5,
        "gpu_gib": 0.0, "cost": 1, "latency": "낮음", "training": "불필요",
        "desc": "최근 값 차분 기반의 설명 가능한 기준선입니다.", "status": "Portfolio",
    },
    "PCA": {
        "tier": "Baseline", "kind": "전통적 비지도", "min_q": 5,
        "gpu_gib": 0.0, "cost": 2, "latency": "낮음", "training": "필요",
        "desc": "낮은 운영 부담의 전통적 비교 모델입니다.", "status": "Portfolio",
    },
    "TimeRCD": {
        "tier": "Portfolio", "kind": "구조 기반 모델", "min_q": 10,
        "gpu_gib": 3.17, "cost": 3, "latency": "중간", "training": "필요",
        "desc": "현재 recipe에서 peak GPU memory가 3.17 GiB로 기록되었습니다.",
        "status": "Resource observed",
    },
    "ALoRa": {
        "tier": "Excluded", "kind": "recipe 제약", "min_q": math.inf,
        "gpu_gib": None, "cost": None, "latency": "—", "training": "—",
        "desc": "현재 채널 구조에서는 공통 후보로 비교할 수 없습니다.", "status": "Constraint",
    },
}

PALETTE = {"MWVAR": "#8da2b6", "GDN": "#45d5b0", "PaAno": "#7b8cff", "TSPulse": "#eeae57"}


def inject_css() -> None:
    st.markdown("""
    <style>
      @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Manrope:wght@400;500;600;700;800&display=swap');
      :root { --ink:#0b1726; --paper:#f5f8fc; --navy:#101f35; --muted:#6a788b; --line:#dce5ef; --mint:#45d5b0; --violet:#7b8cff; --amber:#eeae57; }
      .stApp { background: var(--paper); color:var(--ink); font-family:'Manrope', sans-serif; }
      #MainMenu, footer, header {visibility:hidden;}
      [data-testid="stSidebar"] { background: #101f35; }
      [data-testid="stSidebar"] * { color:#eaf1f7 !important; }
      [data-testid="stSidebar"] .stRadio label { border-radius: 9px; padding: 5px 8px; }
      .block-container { padding: 1.8rem 3rem 3.2rem; max-width:1500px; }
      .hero { background: radial-gradient(circle at 88% 18%, #24496d 0, #101f35 43%, #0a1425 100%); border-radius:18px; padding:34px 38px 31px; color:white; margin-bottom:22px; position:relative; overflow:hidden; }
      .hero:after { content:''; position:absolute; right:5%; top:-95px; width:280px; height:280px; border:1px solid rgba(129,174,211,.28); border-radius:50%; box-shadow:0 0 0 33px rgba(129,174,211,.08), 0 0 0 67px rgba(129,174,211,.04); }
      .eyebrow { color:#65dfc0; font:500 12px 'DM Mono', monospace; letter-spacing:.12em; text-transform:uppercase; margin-bottom:11px; }
      .hero h1 { font-size:34px; letter-spacing:-.045em; margin:0 0 11px; line-height:1.12; position:relative; z-index:1; }
      .hero p { max-width:710px; color:#c3d2df; font-size:14px; margin:0; line-height:1.7; position:relative; z-index:1; }
      .section-title { font-weight:800; font-size:19px; letter-spacing:-.035em; margin:24px 0 5px; }
      .section-sub { color:var(--muted); font-size:13px; margin:0 0 14px; }
      .metric-box { border:1px solid var(--line); border-radius:13px; padding:15px 17px; background:#fff; min-height:100px; }
      .metric-kicker { color:#718096; font:500 10px 'DM Mono',monospace; text-transform:uppercase; letter-spacing:.08em; }
      .metric-value { font-size:25px; font-weight:800; letter-spacing:-.05em; margin-top:6px; color:#12253b; }
      .metric-note { color:#758397; font-size:11px; margin-top:4px; }
      .recommendation { background:linear-gradient(115deg,#e8fbf5,#f6fffc); border:1px solid #bdebdc; padding:22px 24px; border-radius:14px; }
      .recommendation h2 { margin:4px 0 5px; color:#143f39; font-size:25px; letter-spacing:-.045em; }
      .recommendation p { margin:0; color:#3b635d; font-size:13px; }
      .badge { display:inline-block; border-radius:100px; padding:4px 8px; font:500 10px 'DM Mono',monospace; background:#e9eef4; color:#445365; }
      .warn { background:#fff8e9; border:1px solid #f1d696; border-radius:11px; color:#68521d; padding:12px 14px; font-size:12px; line-height:1.55; }
      .evidence { background:#fff; border:1px solid var(--line); border-radius:12px; padding:15px 17px; margin:8px 0; }
      .evidence strong { font-size:14px; }
      .evidence span { color:#708092; font-size:12px; }
      .stButton button { background:#172c47; color:white; border:0; border-radius:8px; font-weight:700; }
      div[data-testid="stMetric"] { background:#fff; border:1px solid var(--line); border-radius:12px; padding:10px 14px; }
      div[data-testid="stMetricLabel"] { font-size:11px; color:#758397; }
      div[data-testid="stMetricValue"] { font-size:23px; color:#12253b; }
      .sidebar-logo { font-weight:800; font-size:18px; letter-spacing:-.04em; }
      .sidebar-caption { font:11px 'DM Mono',monospace; opacity:.65; letter-spacing:.07em; margin-bottom:25px; }
    </style>
    """, unsafe_allow_html=True)


def checkpoint_for(percent: int) -> int:
    return max(q for q in CHECKPOINTS if q <= percent)


def next_checkpoint(q: int) -> int | None:
    return next((v for v in CHECKPOINTS if v > q), None)


def availability(percent: int, vram: float) -> tuple[list[str], list[str]]:
    viable, blocked = [], []
    for name in ("MWVAR", "GDN", "PaAno", "TSPulse"):
        item = MODEL_DATA[name]
        if percent < item["min_q"]:
            blocked.append(f"{name}: 검증된 데이터 단계({item['min_q']}%) 미도달")
        elif item["gpu_gib"] > vram:
            blocked.append(f"{name}: 현재 recipe의 peak GPU memory {item['gpu_gib']:.2f} GiB 필요")
        else:
            viable.append(name)
    return viable, blocked


def choose_model(viable: list[str], perf_weight: int, realtime: bool) -> str:
    if not viable:
        return "MWVAR"
    # Normalize only across the candidates currently under consideration.  This
    # prevents the 1–5 operational cost index from numerically overpowering VUS-PR.
    raw_performance = {
        name: OBSERVED_VUS.get(name, {}).get(max(OBSERVED_VUS.get(name, {0: 0})), 0.20)
        for name in viable
    }
    low, high = min(raw_performance.values()), max(raw_performance.values())
    score = {}
    for name in viable:
        item = MODEL_DATA[name]
        performance = 1.0 if high == low else (raw_performance[name] - low) / (high - low)
        cost_score = 1 - ((item["cost"] - 1) / 4)
        latency_score = 0.25 if realtime and item["latency"] == "높음" else 1
        score[name] = (performance * perf_weight / 100 + cost_score * (100 - perf_weight) / 100) * latency_score
    return max(score, key=score.get)


def stage_label(q: int) -> str:
    if q <= 5:
        return "Cold Start"
    if q < 40:
        return "Early Learning"
    return "Scale & Re-evaluate"


def hero(title: str, copy: str, eyebrow: str = "ENTERPRISE ANOMALY DECISIONING") -> None:
    st.markdown(f"<div class='hero'><div class='eyebrow'>{eyebrow}</div><h1>{title}</h1><p>{copy}</p></div>", unsafe_allow_html=True)


def dashboard(percent: int, target_rows: int, vram: float, perf_weight: int, realtime: bool, daily_rows: int, acquisition_per_10k: float, gpu_hourly: float) -> None:
    q = checkpoint_for(percent)
    upcoming = next_checkpoint(q)
    viable, blocked = availability(q, vram)
    recommendation = choose_model(viable, perf_weight, realtime)
    current_rows = round(target_rows * percent / 100)
    to_next_rows = 0 if upcoming is None else max(0, round(target_rows * (upcoming - percent) / 100))
    acq_cost = to_next_rows / 10000 * acquisition_per_10k
    rec_item = MODEL_DATA[recommendation]
    performance = OBSERVED_VUS.get(recommendation, {}).get(q)

    hero("운영 조건을 선택하고, 다음 의사결정 지점을 찾으세요.", "Dev18 결과를 기업 환경 입력과 함께 해석합니다. 추천은 자동 교체 지시가 아니라, 다음 검증·전환 논의를 위한 설명 가능한 후보입니다.")
    st.markdown("<div class='section-title'>현재 운영 상태</div><p class='section-sub'>입력된 정상 데이터와 인프라 조건을 실험의 공통 비교 지점에 매핑했습니다.</p>", unsafe_allow_html=True)
    a, b, c, d = st.columns(4)
    for col, kicker, value, note in [
        (a, "normal data", f"{current_rows:,} rows", f"목표 {target_rows:,} rows · {percent}%"),
        (b, "decision stage", f"{q}% · {stage_label(q)}", "가장 가까운 검증 완료 checkpoint"),
        (c, "next review", f"{upcoming if upcoming else '—'}%", "자동 교체가 아닌 재평가 시점"),
        (d, "environment", f"{vram:g} GiB VRAM", "현재 recipe 기준 실행 가능성"),
    ]:
        col.markdown(f"<div class='metric-box'><div class='metric-kicker'>{kicker}</div><div class='metric-value'>{value}</div><div class='metric-note'>{note}</div></div>", unsafe_allow_html=True)

    left, right = st.columns([1.25, .75], gap="large")
    with left:
        score_text = f"Dev18 VUS-PR {performance:.3f}" if performance is not None else "해당 checkpoint의 수치 입력 예정"
        st.markdown(f"<div class='recommendation'><span class='badge'>{rec_item['tier']} · {rec_item['status']}</span><h2>Recommended: {recommendation}</h2><p>{score_text} · {rec_item['desc']}</p></div>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>Why this candidate</div>", unsafe_allow_html=True)
        for text in [
            f"데이터 조건: {recommendation}은 현재 실험 구조에서 {rec_item['min_q']}%부터 공통 비교 가능합니다.",
            f"자원 조건: peak GPU memory {rec_item['gpu_gib']:.2f} GiB (현재 {vram:g} GiB).",
            "운영 조건: " + ("실시간 탐지로 설정되어 높은 latency 후보에는 감점을 적용했습니다." if realtime else "배치 탐지로 설정되어 latency 제약을 완화했습니다."),
        ]:
            st.markdown(f"<div class='evidence'><strong>{text}</strong></div>", unsafe_allow_html=True)
    with right:
        st.markdown("<div class='section-title'>Investment preview</div><p class='section-sub'>기업 입력값에 따른 시나리오 추정치입니다.</p>", unsafe_allow_html=True)
        if upcoming:
            st.metric(f"{upcoming}%까지 추가 정상 데이터", f"{to_next_rows:,} rows")
            st.metric("데이터 확보비용 (입력 기반)", f"₩{acq_cost:,.0f}")
        else:
            st.metric("다음 checkpoint", "최종 구간")
        gpu_note = "실측 GPU-hour 입력 후 산출" if rec_item["gpu_gib"] else "GPU 사용 없음"
        st.metric("컴퓨팅 비용", gpu_note)
        st.caption(f"참고 GPU 시간당 요금: ₩{gpu_hourly:,.0f} (사용자 가정)")

    st.markdown("<div class='section-title'>Model switching timeline</div><p class='section-sub'>각 점은 모델을 자동으로 바꾸라는 의미가 아니라, 새 후보를 검증할 가장 이른 시점입니다.</p>", unsafe_allow_html=True)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=CHECKPOINTS, y=[1] * len(CHECKPOINTS), mode="lines+markers", line=dict(color="#bfd0df", width=2), marker=dict(color="#ffffff", size=13, line=dict(color="#607892", width=2),), hoverinfo="skip"))
    annotations = [(5, "TSPulse / MWVAR", "Cold start"), (10, "GDN 도입 검토", "Tier 2 available"), (40, "PaAno 전환 검토", "Re-evaluate")]
    for x, label, sub in annotations:
        fig.add_annotation(x=x, y=1, text=f"<b>{label}</b><br><span style='font-size:10px'>{sub}</span>", showarrow=False, yshift=43 if x != 10 else -44, font=dict(color="#17324d", size=12), align="center")
    fig.add_vline(x=q, line_color="#45d5b0", line_width=3)
    fig.add_annotation(x=q, y=1, text="현재", showarrow=False, yshift=-78, font=dict(color="#177f68", size=11))
    fig.update_layout(height=205, margin=dict(l=10, r=10, t=35, b=20), plot_bgcolor="#ffffff", paper_bgcolor="#f5f8fc", xaxis=dict(tickvals=CHECKPOINTS, ticksuffix="%", showgrid=False, zeroline=False), yaxis=dict(visible=False, range=[.5,1.5]), showlegend=False)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    st.markdown("<div class='section-title'>Unavailable / review required</div>", unsafe_allow_html=True)
    if blocked:
        st.markdown("<div class='warn'>" + "<br>".join(f"• {item}" for item in blocked) + "</div>", unsafe_allow_html=True)
    else:
        st.success("현재 4개 핵심 후보가 데이터·GPU 조건을 충족합니다. 실측 비용과 외부 검증 결과로 최종 선택을 확인하세요.")

    st.markdown("<div class='section-title'>Data availability → performance</div><p class='section-sub'>Zero-shot TSPulse는 데이터 확보율에 따른 성능 향상으로 해석하지 않도록 동일 수치를 반복 표시합니다.</p>", unsafe_allow_html=True)
    chart = go.Figure()
    for name, values in OBSERVED_VUS.items():
        xs, ys = zip(*sorted(values.items()))
        chart.add_trace(go.Scatter(x=xs, y=ys, mode="lines+markers", name=name, line=dict(color=PALETTE.get(name, "#52677b"), width=3), marker=dict(size=8)))
    chart.add_vline(x=q, line_dash="dot", line_color="#45d5b0")
    chart.update_layout(height=350, margin=dict(l=5, r=5, t=25, b=5), paper_bgcolor="#ffffff", plot_bgcolor="#ffffff", legend=dict(orientation="h", y=1.12), xaxis=dict(title="정상 데이터 확보율", ticksuffix="%", tickvals=CHECKPOINTS, gridcolor="#edf1f5"), yaxis=dict(title="VUS-PR", range=[.24,.35], gridcolor="#edf1f5"))
    st.plotly_chart(chart, use_container_width=True, config={"displayModeBar": False})
    st.caption("PaAno 40% 값은 제공된 Dev18 brief의 전환 예시(0.331)를 사용한 후보 시각화입니다. 전체 checkpoint, seed variation, Family-LOFO는 결과 파일 연결 후 갱신해야 합니다.")


def portfolio() -> None:
    hero("모델 카드는 성능 주장과 운영 제약을 분리합니다.", "Tier는 비용 등급이 아니라 실험 구조입니다. Tier 1은 경량·비학습 기준선, Tier 2는 target 정상 데이터 학습, Tier 3는 target 학습 불필요 zero-shot입니다.", "MODEL PORTFOLIO")
    st.markdown("<div class='section-title'>Portfolio at a glance</div><p class='section-sub'>현재 측정된 자원 수치와 실험 recipe 제약을 함께 봅니다.</p>", unsafe_allow_html=True)
    rows = []
    for name, item in MODEL_DATA.items():
        rows.append({"Model": name, "Tier / role": item["tier"], "Common from": "—" if math.isinf(item["min_q"]) else f"{item['min_q']}%", "Peak GPU memory": "—" if item["gpu_gib"] is None else f"{item['gpu_gib']:.2f} GiB", "Training": item["training"], "Latency": item["latency"], "Evidence": item["status"]})
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True, column_config={"Model": st.column_config.TextColumn(width="medium"), "Tier / role": st.column_config.TextColumn(width="medium")})
    st.markdown("<div class='section-title'>Model cards</div>", unsafe_allow_html=True)
    cards = ["MWVAR", "GDN", "PaAno", "TSPulse", "TimeRCD", "ALoRa"]
    for first, second in zip(cards[::2], cards[1::2]):
        c1, c2 = st.columns(2)
        for col, name in [(c1, first), (c2, second)]:
            item = MODEL_DATA[name]
            gpu = "공통 후보 불가" if item["gpu_gib"] is None else ("GPU 불필요" if item["gpu_gib"] == 0 else f"peak {item['gpu_gib']:.2f} GiB")
            col.markdown(f"<div class='evidence'><span class='badge'>{item['tier']} · {item['status']}</span><br><br><strong>{name}</strong><br><span>{item['kind']} · {item['desc']}<br><br>학습: {item['training']} &nbsp; | &nbsp; GPU: {gpu} &nbsp; | &nbsp; Latency: {item['latency']}</span></div>", unsafe_allow_html=True)
    st.markdown("<div class='warn'><b>해석 가드레일</b><br>‘Tier 3 = 저비용’, ‘40% = PaAno의 실제 최소 데이터량’, ‘Dev18 우세 = 현장 일반화’는 현재 근거로 주장하지 않습니다. 각 항목은 본 실험의 비용·외부 검증으로 확인해야 합니다.</div>", unsafe_allow_html=True)


def evidence() -> None:
    hero("근거의 경계를 보여주는 것이 기업용 신뢰의 시작입니다.", "대시보드는 관측값, 사용자 입력, 그리고 추가 측정이 필요한 항목을 의도적으로 분리합니다.", "EVIDENCE & ROADMAP")
    cols = st.columns(3)
    sections = [
        ("01 · 지금 사용 가능", "#e8fbf5", ["데이터 확보율별 선택 가능 모델", "Dev18 VUS-PR (제공된 수치)", "GPU peak memory", "모델 recipe · 채널 제약", "Cold start · switching timeline"]),
        ("02 · 본 실험 측정", "#eef0ff", ["1K / 10K / 100K inference time", "checkpoint별 재학습 시간", "GPU-hour · CPU-hour · peak RAM", "checkpoint / artifact storage", "GHL25 · HAI external validation"]),
        ("03 · 방법론 확정", "#fff7e5", ["GPU 시간당 비용 benchmark", "Data acquisition cost 입력 방식", "Cost index 정규화", "FP / FN threshold cost function", "전환 가치 및 latency 기준"]),
    ]
    for col, (title, color, items) in zip(cols, sections):
        body = "".join(f"<div style='padding:8px 0;border-bottom:1px solid #dbe5ec;font-size:12px'>{x}</div>" for x in items)
        col.markdown(f"<div style='background:{color};border-radius:13px;padding:18px;border:1px solid #dce5ef;min-height:280px'><strong>{title}</strong><div style='margin-top:12px'>{body}</div></div>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Cost architecture</div><p class='section-sub'>서로 성격이 다른 비용을 하나의 근거 없는 숫자로 합치지 않습니다.</p>", unsafe_allow_html=True)
    a, arrow, b = st.columns([1,.15,1])
    with a:
        st.markdown("<div class='evidence'><strong>Computational cost</strong><br><span>연구에서 직접 측정: GPU / CPU 시간, 메모리, 추론 시간, storage.<br>→ cloud GPU benchmark로 비용 추정</span></div>", unsafe_allow_html=True)
    with arrow:
        st.markdown("<div style='font-size:30px;text-align:center;padding-top:22px;color:#7b8cff'>+</div>", unsafe_allow_html=True)
    with b:
        st.markdown("<div class='evidence'><strong>Data investment cost</strong><br><span>기업별 입력: 정상 운전 비용, 센서 운영, 저장, 기회비용.<br>→ 현재 데이터에서 다음 checkpoint까지의 투자 추정</span></div>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Recommended experimental log</div>", unsafe_allow_html=True)
    st.code("checkpoint, model, seed, normal_rows, train_seconds, inference_rows, inference_seconds, gpu_hours, cpu_hours, peak_vram_gib, peak_ram_gib, artifact_mb, vus_pr, family, run_id", language="text")
    st.caption("위 스키마의 CSV/JSONL을 연결하면, 현재 prototype의 정적 evidence 영역을 재현 가능한 실험 데이터로 교체할 수 있습니다.")


inject_css()
st.sidebar.markdown("<div class='sidebar-logo'>◈ TSAD<br>Decision Studio</div><div class='sidebar-caption'>EVIDENCE-BOUND ADVISORY</div>", unsafe_allow_html=True)
page = st.sidebar.radio("Navigation", ["Decision studio", "Model portfolio", "Evidence & roadmap"], label_visibility="collapsed")
st.sidebar.markdown("---")
st.sidebar.markdown("**기업 환경 입력**")
target_rows = st.sidebar.number_input("목표 정상 데이터 rows", min_value=10_000, max_value=10_000_000, value=100_000, step=10_000)
percent = st.sidebar.slider("현재 정상 데이터 확보율", min_value=5, max_value=100, value=27, step=1, format="%d%%")
vram = st.sidebar.number_input("사용 가능 GPU VRAM (GiB)", min_value=0.0, max_value=256.0, value=16.0, step=1.0)
realtime = st.sidebar.toggle("Real-time 탐지", value=True)
daily_rows = st.sidebar.number_input("하루 처리 데이터 (rows)", min_value=1_000, max_value=100_000_000, value=100_000, step=1_000)
st.sidebar.markdown("---")
st.sidebar.markdown("**의사결정 가정**")
perf_weight = st.sidebar.slider("성능 중요도", min_value=0, max_value=100, value=70, help="높을수록 Dev18 성능에 더 큰 가중치를 둡니다. 실제 cost index가 확정되면 교체하세요.")
acquisition_per_10k = st.sidebar.number_input("정상 데이터 1만 rows 확보비용 (₩)", min_value=0, max_value=100_000_000, value=300_000, step=10_000)
gpu_hourly = st.sidebar.number_input("GPU 시간당 비용 가정 (₩)", min_value=0, max_value=100_000, value=4_000, step=500)
st.sidebar.markdown("<div class='sidebar-caption' style='margin-top:22px'>DEV18 · PROTOTYPE<br>NOT A PRODUCTION CLAIM</div>", unsafe_allow_html=True)

if page == "Decision studio":
    dashboard(percent, int(target_rows), vram, perf_weight, realtime, int(daily_rows), acquisition_per_10k, gpu_hourly)
elif page == "Model portfolio":
    portfolio()
else:
    evidence()
