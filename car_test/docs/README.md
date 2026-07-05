# 문서 인덱스

프로젝트 전 과정의 연구 기록. 루트 문서는 단계별 보고서, `tech/`(🔧)는 심화 분석·레퍼런스 노트다.

> **처음 읽는다면 이 순서를 추천**
> [최상위 목적](_motivation.md) → [Sim2Sim Calibration](%5B26-03-15%5D_Sim2Sim_Calibration.md) → [MPPI 개요](%5B26-02-22%5D_MPPI.md) → [3D 지형 마이닝](%5B26-06-01%5D_MPPI_onTerrain.md) → [데이터 스케일링](%5B26-06-24%5D_data.md) → [BC Inverse Mapper](%5B26-03-05%5D_BC_inverse_mappper.md)

---

## 0. 프로젝트 개요

| 날짜 | 문서 | 내용 |
|---|---|---|
| — | [최상위 목적 (End Goal)](_motivation.md) | 프로젝트의 동기와 최종 목표 |

## 1. 시뮬레이션 환경 구축 (Blender ↔ Genesis)

| 날짜 | 문서 | 내용 |
|---|---|---|
| 25-10-14 | [Genesis Car URDF](%5B25-10-14%5D_genesis_car_urdf.md) | Genesis에서 URDF 차량 첫 구동 |
| 25-10-15 | [Vehicle Blending](%5B25-10-15%5D_vehicle_blending.md) | 차량 모델링 및 Genesis 통합 |
| 25-10-16 | [Blender 1](%5B25-10-16%5D_blender1.md) | Blender→Genesis(URDF) 분리·정렬 이슈 |
| 25-10-21 | [Blender 2](%5B25-10-21%5D_blender2.md) | Blender 차량 리깅 |
| 25-10-23 | [Blender 3](%5B25-10-23%5D_blender3.md) | 차량 물리 제약(constraint) 추가 |
| 25-11-03 | [Blender to Genesis](%5B25-11-03%5D_blendertoGenesis.md) | Genesis 엔진을 Blender 기준으로 정합 |
| 25-11-26 | [Blender Troubleshooting](%5B25-11-26%5D_blender_trouble_shooting.md) | Guide Path 주행 구현 트러블슈팅 |
| — | 🔧 [Setting](tech/setting.md) | 차량(RBC rigged car)·환경 설정 레퍼런스 |
| 26-04-04 | 🔧 [RBC Auto Drive Troubleshooting](tech/%5B26-04-04%5D_blender_troubleshooting.md) | Blender reference 주행 자동화 트러블슈팅 |

## 2. 제어·학습 접근 탐색 (Pure Pursuit · PID · RL · 초기 MLP)

| 날짜 | 문서 | 내용 |
|---|---|---|
| 25-11-25 | [MLP Construction](%5B25-11-25%5D_mlp_construction.md) | Genesis에 MLP 제어기 도입 |
| 25-12-17 | [Steer·Throttle Unify](%5B25-12-17%5D_steer_throttle_unify.md) | 제어 인터페이스 통일 |
| 25-12-28 | [MLP Change](%5B25-12-28%5D_mlp_change.md) | 데이터 전처리·MLP 구조 개편 |
| 25-12-30 | [Waypoint & Dual MLP](%5B25-12-30%5D_waypoint_and_dual_mlp.md) | Waypoint 방식과 local overfitting 대응 |
| 26-01-06 | [Pure Pursuit](%5B26-01-06%5D_purePursuit.md) | Pure Pursuit 경로 추종 |
| 26-01-12 | [PPO Residual RL](%5B26-01-12%5D_ppo_residualRL.md) | PPO 기반 Residual RL 설계 |
| 26-01-19 | [Supervised Learning](%5B26-01-19%5D_supervised_learning.md) | UKMAC 지도학습 |
| 26-01-19 | [Supervised Learning 2](%5B26-01-19%5D_supervised_learning2.md) | 지도학습 보강 (closed-loop 재정의) |
| 26-01-26 | [Troubleshooting](%5B26-01-26%5D_troubleshooting.md) | 레일 주행 데이터의 CTE·HE≈0 문제 |
| 26-02-08 | [PID](%5B26-02-08%5D_pid.md) | PID 제어 기반 Ground Truth 생성 |
| 25-12-31 | 🔧 [Dual MLP](tech/%5B25-12-31%5D_dual_mlp.md) | Dual MLP 아키텍처 상세 |
| 26-01-07 | 🔧 [Pure Pursuit Plan](tech/%5B26-01-07%5D_purePersuitPlan.md) | 경로 오차 기반 MLP 제어기 설계 |
| 26-01-07 | 🔧 [Try PyTorch](tech/%5B26-01-07%5D_tryPytorch.md) | PyTorch 변환 시도 |
| 26-01-07 | 🔧 [Try RigidDiff](tech/%5B26-01-07%5D_tryRigidDiff.md) | Genesis 미분가능 물리 시도 |
| 26-01-11 | 🔧 [Pipeline](tech/%5B26-01-11%5D_pipeline.md) | Behavioral Cloning 설계 명세서 |
| 26-01-15 | 🔧 [Reward](tech/%5B26-01-15%5D_reward.md) | PPO 보상 함수 설계 |

## 3. Sim2Sim 정합

| 날짜 | 문서 | 내용 |
|---|---|---|
| 26-03-15 | ⭐ [Sim2Sim Calibration](%5B26-03-15%5D_Sim2Sim_Calibration.md) | **대표 문서** — Inverse Dynamics Mapping 기반 Blender↔Genesis 정합 |
| 26-03-10 | 🔧 [Blender 제어 최적화 보고서](tech/%5B26-03-10%5D_troubleshooting_blender.md) | 차량 제어 최적화·MLP 학습 보고서 |
| 26-03-15 | 🔧 [Blender2Genesis 상세](tech/%5B26-03-15%5D_blender2genesis.md) | 정합 파이프라인 기술 상세 |
| 26-04-29 | 🔧 [Slope·Kappa RMSE](tech/%5B26-04-29%5D_slope_kappa_rmse.md) | 정량 평가 구간 분류 기준 (국토교통부 도로 기준 근거) |

## 4. 3D 차량 물리 고도화 (Ray-wheel · Pacejka)

| 날짜 | 문서 | 내용 |
|---|---|---|
| 26-04-03 | [Z-axis](%5B26-04-03%5D_z_axis.md) | 데이터에 Z축(3D) 추가 |
| 26-04-26 | [Z-axis 2](%5B26-04-26%5D_z_axis2.md) | Z축 물리 안정성 분석 |
| 26-05-02 | [Ray Wheel](%5B26-05-02%5D_ray_wheel.md) | Ray+BVH 충돌 모델 전환 |
| 26-05-07 | [Numerical Stability](%5B26-05-07%5D_numerical_stability.md) | 서스펜션·dt 수치 안정성 |
| 26-05-07 | [Pacejka Model](%5B26-05-07%5D_pacejka_model.md) | Pacejka 이방성 타이어 모델 |
| 26-05-19 | [Ray 3](%5B26-05-19%5D_ray3.md) | 등판 시 속도 추종 문제 분석 |
| 26-05-26 | [SDK Migration](%5B26-05-26%5D_sdk.md) | genesis_vehicle SDK 마이그레이션 |
| 26-04-14 | 🔧 [Mesh Troubleshoot](tech/%5B26-04-14%5D_Mesh_Troubleshoot.md) | 지형 OBJ Dense Export 문제 분석 |
| 26-05-02 | 🔧 [Lidar Bug Report](tech/%5B26-05-02%5D_lidar_bugReport.md) | Lidar/Ray-wheel 구현 버그 리포트 |
| 26-05-23 | 🔧 [Pacejka Slip Test](tech/%5B26-05-23%5D_pacejka_slip_test.md) | 슬립·브레이크 물리 검증 스윕 |

## 5. MPPI 골든 라벨 채굴

| 날짜 | 문서 | 내용 |
|---|---|---|
| 26-02-16 | [MPC to MPPI](%5B26-02-16%5D_mpc2mppi.md) | MPC→MPPI 전환 배경과 근거 |
| 26-02-22 | [MPPI](%5B26-02-22%5D_MPPI.md) | MPPI 원리와 최적화 파이프라인 개요 |
| 26-06-01 | [MPPI on Terrain](%5B26-06-01%5D_MPPI_onTerrain.md) | 3D 지형 골든 데이터 마이닝 |
| 26-06-24 | [Data Scaling](%5B26-06-24%5D_data.md) | 단일 지형 다중 경로 골든 데이터 스케일링 |
| 26-03-15 | 🔧 [MPPI Troubleshooting](tech/%5B26-03-15%5D_MPPI_troubleshooting.md) | MPPI 트러블슈팅과 인사이트 |
| 26-06-01 | 🔧 [MPPI Warm-start](tech/%5B26-06-01%5D_MPPI_warmstart.md) | MPPI 파라미터 레퍼런스 (grid search 우승값) |

## 6. Path→(T,S) Mapper 학습 (BC + DAgger)

| 날짜 | 문서 | 내용 |
|---|---|---|
| 26-03-05 | ⭐ [BC Inverse Mapper](%5B26-03-05%5D_BC_inverse_mappper.md) | **대표 문서** — MPPI 골든 라벨 지도학습 파이프라인 |
| 26-03-05 | 🔧 [DAgger](tech/%5B26-03-05%5D_DAgger.md) | DAgger 기반 반복 학습 (분포 불일치 해결) |
| — | 🔧 [State Sheet](tech/state_sheet.md) | 상태 벡터 정의 레퍼런스 |
