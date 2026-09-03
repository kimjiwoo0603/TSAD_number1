# TSAD Decision Studio

기업의 시계열 이상탐지 모델 선정을 돕는 Streamlit 의사결정 대시보드입니다. 제공된 Dev18 brief를 근거로 `관측됨`, `후보 milestone`, `추가 측정 필요`를 분리해 보여줍니다.

## Run

```powershell
python -m pip install -r requirements.txt
streamlit run app.py
```

브라우저에서 표시되는 URL(일반적으로 `http://localhost:8501`)을 엽니다.

## Included

- 정상 데이터 확보율, VRAM, 실시간성, 비용·성능 중요도 기반의 설명 가능한 후보 추천
- Dev18 checkpoint 기반 Data Availability → VUS-PR 그래프
- model switching timeline 및 후보 제외 이유
- Tier/모델 카드와 관측된 GPU peak memory
- Computational Cost와 Data Investment Cost의 분리된 설계
- 본 실험에서 추가할 측정 항목 및 권장 experiment log schema

## Evidence rules

- Tier는 비용 등급이 아니라 실험 구조입니다.
- TSPulse의 반복된 점수는 데이터 증가에 따른 성능 향상으로 표시하지 않습니다.
- PaAno 40%의 0.331은 전달된 brief의 전환 예시를 후보 시각화에 사용했으며, 전체 결과 파일로 대체해야 합니다.
- 비용, FP/FN 손실, 통계적 유의성 및 현장 일반화는 아직 최종 주장으로 표시하지 않습니다.

## Repository integration

이 폴더를 원본 저장소의 최상위에 복사한 뒤, `.streamlit/config.toml` 또는 배포 설정을 저장소 표준에 맞춰 추가하면 됩니다. 이 작업 환경에서는 GitHub TLS 자격 증명 오류 때문에 원격 저장소를 자동 clone/push하지 못했습니다.
