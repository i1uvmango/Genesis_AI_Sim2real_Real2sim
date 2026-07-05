


# Physics-Grounded Driving Policy via MPPI Label Mining

> **대규모 병렬 물리 시뮬레이션의 최적 제어를, 실시간 주행 정책으로 증류한다.**
> Genesis 물리 엔진 위에서 MPPI가 채굴한 골든 제어 라벨로 Path→(Steer, Throttle, Brake)
> Mapper를 학습하고, Real2Sim–Sim2Real 정책 전이로 확장하는 프로젝트.

![](./car_test/res_wjdaksry/0625/mppi_fan_chicane_LRL_teaser.gif)

*매 스텝 2048개의 후보 미래를 병렬 물리로 시뮬레이션하고, 최적 궤적 하나를 선택해 지형을 주행하는 MPPI — 반투명 고스트는 컨트롤러가 "상상한" 미래들이다.*

---

## 무엇을 하는가

자율주행 경로 추종 제어기를 **물리적으로 실현 가능한(physically feasible) 데이터**로 학습한다.

1. **Reference 생성** — 한국 도로공사 표준 기반 지형 위에서 차량이 순수 물리 주행으로 만든
   궤적을 추출한다. 위치를 강제로 이식한 kinematic 궤적은 배제한다 — 지형 경사, 하중 이동,
   타이어 접지, 서스펜션 응답이 빠진 데이터로는 실물에서 일반화되지 않기 때문이다.
2. **골든 라벨 채굴 (sim2sim)** — Genesis의 ray-wheel 차량 물리 위에서 **MPPI**(Model
   Predictive Path Integral)가 reference 궤적을 재추종한다. 매 스텝 **2048개 병렬 환경**에서
   후보 제어 시퀀스를 실제 물리로 전개·평가해 최적 입력을 선택하고, 그 결과로
   *(주행 상태 → Throttle, Steer, Brake)* 전문가 라벨이 쌓인다.
3. **Path→(ST,B) Mapper 학습** — 채굴된 라벨을 지도학습(BC + DAgger)해, 경로와 현재 상태만
   보고 제어를 출력하는 경량 정책을 만든다. 학습 후에는 **2048-env 최적화 없이** 단일
   신경망 추론만으로 실시간 경로 추종이 가능하다.

## 왜 중요한가

- **최적 제어의 증류** — MPPI는 강력하지만 실시간 실차 제어에는 무겁다. 이를 오프라인
  라벨 생성기로만 사용하고 실시간 주행은 경량 mapper가 담당하는 구조는, 대규모 시뮬레이션
  최적화의 성능을 실차 수준의 연산 예산으로 가져오는 실용적 경로다.
- **Dynamic-first 데이터** — 학습 라벨이 이상적 궤적이 아니라 물리 응답(경사 등판, 미끄러짐,
  하중 이동)을 담고 있어, 험지·비정형 지형에서의 일반화를 겨냥한다.
- **전이 파이프라인의 리허설** — 현재의 Blender→Genesis sim2sim 정합(좌표계·시간 스텝·
  지형·차량 파라미터)은 그대로 real2sim 정합의 방법론이 된다.

## 로드맵

| 단계 | 내용 | 문서 |
|---|---|---|
| ✅ Sim2Sim 정합 | Blender 물리 주행 ↔ Genesis ray-wheel 물리 정합 | [Sim2Sim Calibration](car_test/docs/%5B26-03-15%5D_Sim2Sim_Calibration.md) · [Ray-wheel 충돌 모델](car_test/docs/%5B26-05-02%5D_ray_wheel.md) · [Pacejka 타이어 모델](car_test/docs/%5B26-05-07%5D_pacejka_model.md) · [정합 평가 지표](car_test/docs/tech/%5B26-04-29%5D_slope_kappa_rmse.md) |
| ✅ 골든 라벨 채굴 | 34개 기동 시나리오 × 표준 지형, MPPI 마이닝 (최저 CTE 0.11 m) | [MPPI 개요](car_test/docs/%5B26-02-22%5D_MPPI.md) · [3D 지형 마이닝](car_test/docs/%5B26-06-01%5D_MPPI_onTerrain.md) · [데이터 스케일링](car_test/docs/%5B26-06-24%5D_data.md) · [MPPI 파라미터](car_test/docs/tech/%5B26-06-01%5D_MPPI_warmstart.md) |
| 🔄 Path→(ST,B) Mapper | BC 학습 + DAgger 폐루프 개선 | [BC Inverse Mapper](car_test/docs/%5B26-03-05%5D_BC_inverse_mappper.md) · [DAgger](car_test/docs/tech/%5B26-03-05%5D_DAgger.md) |
| ⏳ Real2Sim | 실측 궤적·지형의 시뮬 정합, 실환경 분포 라벨 재채굴 | — |
| 🎯 Sim2Real | 학습 정책의 실차 전이 | — |

전체 연구 기록(50여 편)은 **[문서 인덱스](car_test/docs/README.md)** 에서 단계별로 볼 수 있다.