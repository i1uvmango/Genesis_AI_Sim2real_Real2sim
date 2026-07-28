# Path-Following Evaluation and Disturbance-Robust RL Training


## 평가 지표 변경 (Path-Following 표준)

### metric 변경의 필요성



![](../res_wjdaksry/0712/p134_bc_vs_time_vs_pos.mp4)

https://github.com/user-attachments/assets/71cc1e65-3f56-4483-8360-11ecb3ae9b70

* 코너 구간에서 `time mode`의 선제적 조향 발생
* 그럼에도 기존 정량 측정 지표로는 `time mode` > `pos`보다 우세하게 나옴 &rarr; 측정에 문제가 있음을 발견


#### 기존 metric  

| 지표 | BC (2.3) | RL time | RL pos | BC 대비 개선 | 
|---|---|---|---|---| 
| **frame 거리오차 fm (m)** | 0.855 | **0.448** | 0.721 | **−48%** | 
| **횡오차 CTE (경로선 붙음, 실차 핵심, m)** | 0.232 | **0.051** | 0.059 | **−78%** | 
| **heading 오차 HE (°)** | 1.74 | 0.69 | **0.67** | **−62%** | 
| **lag (종방향 오차, m)** | 0.752 | **0.434** | 0.697 | **−42%** |

> $$\text{fm}^2 \approx \text{cte}^2 + \text{lag}^2$$

**문제점**: 너무 time 추종에 유리한 metric이며, CTE/HE 등이 차량이 목표점(ref car pos)를 time serial 하게 잘 추종한다면 오류가 없지만, 조금이라도 뒤쳐지는 순간 feedback이 오염이 발생.

* 정량 평가는 `time`이 우세했지만, 실제 viewer를 통해 확인 시 경로 추종 능력은 `RL Pos`가 더 우수
* 잘못된 정량 지표 측정
  * 문제: 커브길에서 선제 조향 나타나지 않음 : time mode은 발생



#### RL의 목표 정리

* 속도 오차가 있더라도, 해당 경로를 **어떤 상황에서도** 잘 따라가도록 하는 것, 
* **외란** 같이 특수한 상황이 발생했을때 이를 반영하여 **경로 추종 능력**을 유지하여 **오차를 복구**하는 것이 RL의 목표이다.



### Fair한 정량 측정 지표

**Optimization-based autonomous racing of 1:43 scale RC cars,2015** 선행 연구 참고

> 이 관점은 본 보고서의 metric 변경 방향과 연결된다. 즉, 고속 path-following 평가는 “같은 frame에서 reference와 얼마나 가까운가”가 아니라, **경로 상의 동일한 위치를 얼마나 잘 따라갔는가**, 그리고 **그 위치에 도달하는 pace가 reference 주행과 얼마나 다른가**를 분리해서 봐야 한다. 


1. pace : 경로 추종이 중요하더라도, time을 아예 무시할 순 없음 , path만 잘 따라도 너무 느리게 기어가면 좋은 주행이라고 보기 어려움. 

>동일 궤적의 주행이더라도, 스포츠카의 주행과 자전거의 주행은 다르다

* time: 같은 프레임에 어디에 있었는가 (x)
* **fair** : 동일 point x에 도달하는데 걸린 시간 (o)


2. arc-length average CTE/HE : 경로를 **구간별로 분할**하여, 해당 구간 길이 별 CTE/HE의 평균을 측정한다

![](../res_wjdaksry/0726/arclength.png)


> 기존 metric 평균은 “시간별 평균”이고, arc length average CTE/HE는 “경로 길이 기준 평균”

![](../res_wjdaksry/0721/tangential_err.png)


3. CTE/HE 계산은 차량과 heading 방향과 나란한 nearest point(ref point) 기준으로 계산

* 속도 지연에 따른 측정 오류를 막기 위함


## new metric 

RL closed loop 성능 비교를 위한 최종 평가 기준이다.


#### 단계

| 구분 | 역할 | 승패 반영 |
|---|---|---|
| **Gate0** | 주행이 평가 가능한 정상 run인지 확인 | pass/fail 조건 |
| **Primary Path Metrics(main)** | 경로를 얼마나 잘 따라갔는지 평가 | main 평가 |
| **Primary Feasibility Metrics(main)** | 곡률 대비 말 되는 속도로 달렸는지 평가 | main 평가 |
| **Secondary Pace Metrics** | reference다운 속도/pace였는지 평가 | 보조 평가 |



- **Primary**: 메인 평가 기준, 경로를 얼마나 잘 따라갔는가
- **Feasibility**: 그 속도가 곡률 대비 물리적으로 말이 되는가
- **Secondary**: 그 경로를 얼마나 reference다운 pace로 달렸는가

**공간 기반 path-following 지표**로 판단하고, 시간 성능은 별도 표에서 해석한다.  
기존 `frame distance`, `lag`처럼 시간 인덱스에 묶인 지표는 primary에서 제외한다.

---

## 1. Gate0 — Gate fail이면 평가하지 않음(평균 오염 방지)
 
| 항목 | 기준 | 비고 |
|---|---|---|
| Completion | 완주율 | **시간 무관** — 공간 도달로만 판정 |
| Coverage | `coverage_ratio ≥ 0.90` | 외란 평가시 미사용 |
| Spinout | yaw rate + sideslip β 복합 판정 | 외란 평가시 미사용 |
| 전복 | \|roll\| > 0.8 rad | |

**coverage_ratio 정의**

횡방향 오차 비율을 넘지 않으며 `|CTE| < c_coverage` 방문한 s-grid cell 의 길이 비율.


**Spinout 정의 (복합)**

기준 heading 보다 커지면 차가 스핀 했다고 판단: `|yaw_rate| > N rad/s` 


## 2. Primary Metrics(메인 평가 지표)
 
| 지표 | 정의 |
|---|---|
| spatial \|CTE\| mean / p95 / max | s-grid 셀 평균 / 95분위 / 최대 |
| spatial \|HE\| mean / p95 / max | 위와 동일, 단위 deg |
| curve-only \|CTE\|/\|HE\| mean / p95 / max | \|κ\| 상위 30% 구간 / threshold 기반 |
| **pre-corner cutting** mean / max / integral | s-grid 구간 에서 `inside_cut = max(0, dir_inside · CTE_signed)` — 아래 부호 규약 |

**부호 규약**
> CTE>0 (경로 좌측): 좌커브 +1 / 우커브 −1 

ISO 8855 sign convention end-to-end: +X forward, +Y left, +Z up, +steer = right turn, +throttle = forward

구현 기준: `CTE_signed = -dx·sin θ + dy·cos θ` (θ = 경로 접선각, (dx,dy) = 차량 − 경로점).
법선 `(-sin θ, cos θ)` 는 heading 을 +90° 회전한 **좌측 법선**이므로 → **CTE_signed > 0 = 경로 좌측**.



 
## 3. Primary — Feasibility (참조속도 오차의 대체)
 
"곡률에 맞는 말이 되는 속도"의 직접 채점 — v_ref 대비 감속은 벌점이 아니다.
> reference가 17m/s로 지나가는데, 어떤 policy가 곡률/접지 상태를 보고 14m/s로 감속해서 path를 안정적으로 따라갔다면 이건 나쁜 게 아님.

| 지표 | 정의 |
|---|---|
| feasible overspeed mean / p95 / max | `max(0, v − v_feasible(s_hat))`, `v_feasible = √(a_safe / max(\|κ\|, 1e-3))` |
| a_lat violation ratio | `v²\|κ(s_hat)\| > a_safe` 인 방문 셀 길이 / 방문 총길이 |
 
* v_feasible: `가능한 속도` 라는 것인데, SDK에서 lateral 방향 그립력을 계산해서 `a_safe`를 측정하여 곡률에 맞는 속도를 계산


## 4. Secondary — Pace / Time (승패 미결정, 별도 표)
 
"스포츠카를 자전거 속도로 몰면 안 된다"의 채점 자리 — 단 정의는 공간 인덱스 기준.

| 지표 | 정의 |
|---|---|
| point-to-point time | checkpoint s ∈ {0.25S, 0.5S, 0.75S, S} 도달시각의 ref 대비 오차 RMS |
| finish time ratio | 완주시간 / ref 완주시간. **> 1.5 는 ⚠ 경고 표기 (탈락 아님)** |




## 5. Disturbance Recovery — 외란 주행 전용 평가

Disturbance Recovery는 RL의 핵심 목표인 “외란 발생 후 경로 추종 오차를 복구하는 능력”을 평가하기 위한 지표
>이 항목은 외란을 인위적으로 주입한 run에서만 산출하며, 무외란 run의 기본 평가표에는 포함하지 않는다.

외란은 고정된 path progress 위치 `s/S ∈ {0.30, 0.60}`에서 world 횡방향 선속도 임펄스로 주입한다.  
크기는 `Δv_lat ∈ {1.5, 3.0, 5.0} m/s`이며, 좌/우 양방향을 모두 평가한다.  
* 외란 주입 직전 `|CTE| < 0.3 m` 조건을 만족해야 한다. 이미 흐트러진 상태에 외란을 추가하면 복구 능력이 아니라 누적 실패를 측정하게 되기 때문이다.

복구 성능은 시간 기준이 아니라 arc-length 기준으로 측정한다. 


| 지표 | 정의 | 의미 |
|---|---|---|
| `peak` |CTE| after disturbance` | 외란 이후 recovery window 안의 최대 `|CTE|` | 외란 직후 최대 이탈량 |
| `recovery distance` | `s0`부터 |CTE|<`c_rec`로 복귀하고 일정 거리 유지될 때까지의 arc-length | **정상 상태로 돌아오는 데 필요한 거리** |
| `recovery success rate` | recovery window 안에 복귀한 run 비율 | 외란 복구 성공률 |
| `excursion area` | `∫` |CTE(s)| ds, `s0`부터 복귀점까지 | 이탈 크기와 지속 거리를 함께 반영한 누적 복구 비용 |

`c_rec`은 복구 판정용 임계값이며, coverage 계산에 사용하는 `c_coverage`와 별도로 정의한다.  
일시적인 threshold 통과를 복구로 오판하지 않기 위해, 복귀 후 `L_hold` m 이상 `|CTE| < c_rec` 상태를 유지해야 한다.

Recovery window 안에 복귀하지 못한 run은 실패로 처리하며, `d_rec = NaN`으로 기록하고 `recovery success rate`에만 반영한다. 실패 run을 평균 `d_rec`에 섞으면 실패가 은폐될 수 있기 때문이다.




## 결과: 26씬 정량 측정

측정 대상: **pos(iter350) vs time(iter500)**


### 요약 — 26씬 평균

| 표 | 지표 | pos | time |
|---|---|---|---|
| A | Primary \|CTE\| mean (m) | **0.036** | 0.044 |
| B | 곡률존 \|CTE\| (m) | **0.041** | 0.066 |
| C | Primary \|HE\| (°) | **5.60** | 5.83 |
| D | Feasibility a_lat 위반율 (%) | 0.7 | 0.8 |
| E | Secondary 조향 (mrad/m) | **194** | 257 |

**pos 가 전 지표 우세** 

* 곡률존 오차 38% 우위
* 조향 −25% 우위
* |CTE| 18% 우위
* time 은 p134·p135 고곡률에서 붕괴.

#### 표 비교

| 구분 | time 기반 | **position 기반** |
|:---:|:---:|:---:|
| 이전 metric <br>(before) | ![](../res_wjdaksry/0712/grid_TIME_lagfix_iter500.png) | ![](../res_wjdaksry/0712/grid_POS_iter600.png) |
| **새 metric** <br>(after) | ![](../res_wjdaksry/0721/postime_grid_time.png) | ![](../res_wjdaksry/0721/postime_grid_pos.png) |


<details>
<summary>씬별 상세 표 A~E 펼치기</summary>

### 표 A — Primary |CTE| mean (m)
| 모드 | p120 | p121 | p122 | p123 | p124 | p125 | p126 | p129 | p130 | p131 | p132 | p133 | p134 | p135 | p138 | p140 | p141 | p142 | p143 | p145 | p146 | p148 | p149 | p151 | p152 | p153 | **평균** |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pos | 0.062 | 0.019 | 0.025 | 0.069 | 0.035 | 0.009 | 0.014 | 0.035 | 0.024 | 0.026 | 0.046 | 0.116 | 0.042 | 0.043 | 0.054 | 0.027 | 0.019 | 0.039 | 0.034 | 0.029 | 0.026 | 0.014 | 0.031 | 0.050 | 0.018 | 0.037 | **0.036** |
| time | 0.050 | 0.018 | 0.061 | 0.021 | 0.051 | 0.049 | 0.074 | 0.069 | 0.044 | 0.018 | 0.037 | 0.046 | 0.104 | 0.173 | 0.022 | 0.043 | 0.031 | 0.014 | 0.017 | 0.031 | 0.061 | 0.017 | 0.010 | 0.037 | 0.048 | 0.005 | **0.044** |

### 표 B — 곡률존 |CTE| mean (m) — |κ| 상위 30% 구간
| 모드 | p120 | p121 | p122 | p123 | p124 | p125 | p126 | p129 | p130 | p131 | p132 | p133 | p134 | p135 | p138 | p140 | p141 | p142 | p143 | p145 | p146 | p148 | p149 | p151 | p152 | p153 | **평균** |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pos | 0.062 | 0.013 | 0.018 | 0.121 | 0.043 | 0.009 | 0.014 | 0.014 | 0.010 | 0.024 | 0.048 | 0.130 | 0.076 | 0.069 | 0.025 | 0.033 | 0.019 | 0.053 | 0.022 | 0.033 | 0.036 | 0.012 | 0.049 | 0.068 | 0.016 | 0.046 | **0.041** |
| time | 0.044 | 0.011 | 0.067 | 0.040 | 0.069 | 0.047 | 0.071 | 0.094 | 0.060 | 0.034 | 0.051 | 0.033 | 0.244 | 0.388 | 0.026 | 0.072 | 0.026 | 0.017 | 0.025 | 0.050 | 0.098 | 0.012 | 0.022 | 0.055 | 0.049 | 0.009 | **0.066** |

### 표 C — Primary |HE| mean (deg)
| 모드 | p120 | p121 | p122 | p123 | p124 | p125 | p126 | p129 | p130 | p131 | p132 | p133 | p134 | p135 | p138 | p140 | p141 | p142 | p143 | p145 | p146 | p148 | p149 | p151 | p152 | p153 | **평균** |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pos | 1.35 | 7.50 | 7.71 | 4.19 | 8.22 | 4.56 | 9.19 | 8.56 | 7.83 | 3.68 | 10.97 | 11.01 | 1.26 | 1.84 | 7.55 | 4.99 | 5.26 | 4.01 | 4.26 | 10.61 | 3.81 | 2.51 | 1.54 | 6.53 | 6.43 | 0.34 | **5.60** |
| time | 1.35 | 7.55 | 8.18 | 4.55 | 8.36 | 4.66 | 9.36 | 8.69 | 8.14 | 3.68 | 10.97 | 11.05 | 2.03 | 2.67 | 7.77 | 5.25 | 5.30 | 4.07 | 4.54 | 10.75 | 5.07 | 2.59 | 1.49 | 6.76 | 6.46 | 0.28 | **5.83** |

### 표 D — Feasibility a_lat 위반율 (%) — v²|κ| > 4.0 m/s²
| 모드 | p120 | p121 | p122 | p123 | p124 | p125 | p126 | p129 | p130 | p131 | p132 | p133 | p134 | p135 | p138 | p140 | p141 | p142 | p143 | p145 | p146 | p148 | p149 | p151 | p152 | p153 | **평균** |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pos | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 9.0 | 9.4 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | **0.7** |
| time | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 10.2 | 9.8 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | **0.8** |

### 표 E — Secondary 조향 effort (mrad/m) — 거리기준
| 모드 | p120 | p121 | p122 | p123 | p124 | p125 | p126 | p129 | p130 | p131 | p132 | p133 | p134 | p135 | p138 | p140 | p141 | p142 | p143 | p145 | p146 | p148 | p149 | p151 | p152 | p153 | **평균** |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pos | 81 | 237 | 216 | 203 | 254 | 184 | 290 | 268 | 247 | 163 | 218 | 198 | 107 | 111 | 255 | 223 | 200 | 138 | 155 | 227 | 181 | 141 | 140 | 231 | 200 | 177 | **194** |
| time | 113 | 281 | 254 | 293 | 323 | 215 | 311 | 399 | 343 | 251 | 292 | 182 | 138 | 133 | 310 | 288 | 299 | 176 | 257 | 306 | 238 | 215 | 254 | 277 | 212 | 311 | **257** |

</details>


#### 고속 주행 및 다양한 경로 데이터 추가



![](../res_wjdaksry/0721/replay_p161.mp4)

https://github.com/user-attachments/assets/c8fbfca5-eb12-4e2c-8bd0-d3595012f5c5

> 기존 checkpoint: RL_pos(iter350) 으로 미학습 고속 데이터 추론 결과
* 고속 + 커브 + 속도 변화

위와 같은 다양한 고속 데이터 주행 추가 중



---


## 학습 방법: PPO vs MPPI optimization Based

![](../res_wjdaksry/0726/ppo_vs_mppi.png)

* **PPO** : 일반화 된 주행 모델을 만들기 위해서 env 별로 (scene,spawnpoint(frame))을 샘플링 하여 랜덤 소환 후, batch 단위로 업데이트
* **MPPI like Optimization** : 동일 scene에 여러 env를 병렬로 배치하고, 서로 다른 `residual/action` 후보 또는 `perturbation`을 주입한 뒤, `closed-loop path-following score`가 가장 좋은 후보를 선택·갱신한다. 이후 다른 scene에 대해서도 같은 최적화 과정을 반복한다.

#### MPPI Optimization Based 장점
* 특정 커브, 특정 고속 구간, 특정 지형에서 실패하는 이유를 집중 학습 가능
* state perturbation에 대한 복구 능력 향상
* hard case를 빠르게 개선 가능

#### 단점
* scene-specific overfitting
* 다음 scene으로 넘어갈 때 catastrophic forgetting
* curriculum 순서에 민감
* batch 다양성 감소

#### 의문점 : 복구 능력이 목표라면 GA(유전 알고리즘)이 더 낫지 않나?
> 아이디어 : scene 에 multi env로 병렬적으로 노이즈를 주어 복구 능력을 강화시킨다

* 특정 어려운 case들은 잘 고칠 수 있음
* scene에 과적합될 수 있음
* 다음 scene으로 넘어가며 같은 residual network를 계속 업데이트하면 이전 scene에서 배운 복구 전략이 덮어써질 수 있음



### PPO vs MPPI like Optimization based

| 항목        | PPO Residual Policy                                       | Scene-wise GA / MPPI-like Optimization                     |
| --------- | --------------------------------------------------------- | ---------------------------------------------------------- |
| 기본 아이디어   | 여러 scene/spawn 경험을 모아 공유 residual policy를 gradient update | 동일 scene/hard segment에서 여러 후보 보정을 병렬 rollout하고 best 후보를 선택 |
| 학습/최적화 단위 | shared policy                                             | scene 또는 hard segment                                      |
| 장점        | 일반화된 residual stabilizer 학습                               | 특정 failure case 집중 개선                                      |
| 위험        | reward/critic 설계 민감                                       | scene-specific overfitting, 순차 업데이트 시 forgetting           |
| 적합한 용도    | sim2real generalist policy                                | hard-case recovery tuning / failure-case optimizer         |

#### 관련 연구

Reinforcement Learning-Based Robust Vehicle Control for Autonomous Vehicle Trajectory Tracking, 2024

* RL 기반 model + Robust Optimization(correction) - 우리와 구조는 반대(MLP + RL PPO)
> 이 논문은 pure RL과 robust/model-based supervisor를 결합한 구조임. RL agent는 reward 기반으로 lap time이나 tracking을 최적화하지만, supervisor는 model-based prediction과 optimization constraints로 path tracking error를 제한함. 논문에서는 pure RL이 더 빠르지만 corner cutting과 tracking error violation이 발생할 수 있고, supervisor-based 구조는 lap time은 느려져도 tracking error 제한을 더 잘 만족한다고 설명함.

---

A Tube Linear Model Predictive Control Approach for Autonomous Vehicles Subjected to Disturbances, 2024

* MPC/optimization 기반 disturbance recovery : optimization 기반 외란 복구
> 논문은 disturbance가 autonomous vehicle path tracking과 obstacle avoidance 성능을 떨어뜨린다고 보고, tube linear MPC를 사용해 common disturbance 조건에서 constraint를 만족시키는 구조를 제안함. disturbance 조건에서 tube MPC는 모든 trajectory가 obstacle avoidance에 성공했지만, traditional MPC는 약 80%만 성공했다고 보고함
---

Reaching the Limit in Autonomous Racing: Optimal Control versus Reinforcement Learning, Science Robotics 2023

autonomous racing에서 optimization-based control과 RL을 직접 비교함. 분야는 차량이 아니라 drone racing
> 논문 설명에 따르면 optimal control은 trajectory 같은 중간 표현을 두고 planning/control을 분리하는데, 이 구조가 unmodeled effect나 한계 주행에서 표현 가능한 행동을 제한할 수 있다고 해석함. 반면 RL은 task-level objective를 직접 최적화하고 domain randomization으로 model uncertainty에 더 강한 반응을 찾을 수 있다고 설명


## privilige 정보 수정

### 이전 privilige 설계 (33D)
| 특권 정보 | 차원 | 내용 | 유지 여부 |
|---|---|---|---|
| `last_distances` | 4 | 바퀴별 레이캐스트 지면 거리 &rarr; real-world에서 practical하다고 보기 어려움 | 
| `omega` | 4 | 바퀴별 회전 각속도 (휠스핀/슬립 감지 &rarr; privilige 정보 아님) | 
| `last_compression` | 4 | 바퀴별 서스펜션 압축량 (접지 상태) &rarr;  privilige 정보 아님 | 
| `k_ex` | 10 | 먼 미래 곡률 (t+11~t+20 — actor의 lookahead보다 멀리) &rarr; 경로 preview 이지, 특권정보는 아님 |
| `a_ex` | 10 | 먼 미래 가속도 (t+11~t+20) &rarr; 경로 preview 이지만, 이는 reference속도에 time을 따라가라 라는 강한 제약 가능성 |
| `lag` | 1 | 스케줄 지연(m) |


#### 제거항목
| 항목                      | 이유                                           | 최종 판단            |
| ----------------------- | -------------------------------------------- | ---------------- |
| `last_distances`        | 바퀴별 raycast 지면 거리. real-world practical하지 않음 | **삭제**           |
| `lag`                   | time-schedule 기반 정보. path-first 목적과 충돌 가능    | **삭제**           |
| `exact future state`    | 미래 실제 상태는 oracle leakage                     | **사용 금지**        |
| `future reward/success` | 성공 여부 oracle                                 | **사용 금지**        |



### 수정 설계 (Privilege → Critic Observation, 21D)

Privilege → Critic Observation

> 선정 원칙 3가지:
> 1. `Real2Sim/Sim2Real` 관점에서 실차에서 practical하게 얻을 수 있는 데이터
> 2. **비중복 기준**: 다른 입력으로부터 한 스텝(선형/준선형)에 유도 가능한 항목은 제외  
> 3. critic에는 노이즈 주입 X, 단위 정규화(omega ~수십 rad/s vs compression ~수 cm)

| 항목 | 차원 | 분류 | 채택 이유 (한 줄) |
| --- | -: | --- | --- |
| `suspension_compression` | 4 | 센서 (서스 트래블) | 차량 하중과 접지 상태 신호 |
| `wheel_omega` | 4 | 센서 (휠 엔코더) | 슬립 간접 신호 |
| `body_accel` | 3 | 센서 (IMU) | a_y=횡가속 핵심, a_z=접지·요철 |
| `yaw_rate` | 1 | 센서 (IMU gyro) | yaw_rate≈v·κ 이탈 = 오버/언더스티어 감지 |
| `v_lat` | 1 | 추정 (VIO/GPS+IMU) | 슬립각 현재값 — 원신호에서 한 스텝 유도 불가 |
| `k_ex` (t+12~+20, 5pt) | 5 | planner preview | 매끄러워 10→5 압축 손실 미미 |
| `time_to_next_hard_curve` | 1 | preview 유도 | 곧 급커브 |
| `next_curve_severity` | 1 | preview 유도 | 전방 최대 곡률 요약 |
| `progress (s/S)` | 1 | episode context | 랜덤 spawn 의 return 분산 흡수 |
| `spawn_init_speed` | 1 | episode context | 커리큘럼 문맥 |

**합계 21D**

> 주의점 : 미팅 피드백 후 반영 예정


## 외란 설계
> 예시 : kick
![](../res_wjdaksry/0721/rl_p134_position_rl_iter350_kick_base.mp4)

https://github.com/user-attachments/assets/aac06905-8f9d-4323-bf87-891eaa3697ea


RL-외란 의 목표는 nominal 궤적을 그대로 재현하는 게 아니라 **교란이 있어도 경로 추종을 유지·복구**하는 것이다. 이를 위해 주행 중 무작위 외란을 주입하고 그로부터 복구하는 법을 학습시킨다.

**공통 원칙**

- 모든 주행 중 외란은 **정상 추종 상태(경로 이탈이 작을 때)에서만** 발동한다. 이미 흐트러진 상태에 외란을 더하면 "복구"가 아니라 "누적 실패"를 학습하기 때문.
- 강도는 학습 초반 0에서 시작해 서서히 키운다(커리큘럼). 처음부터 최대 외란을 주면 아직 미숙한 정책이 붕괴한다.
- 일부 env 만 교란하고 나머지는 무외란으로 둔다 — 외란 대응에만 과보수화되어 정상 주행이 나빠지는 것을 막는 baseline.

### Disturbance Types

| disturbance | 모사하는 실제 상황 | 무엇을 교란하나 | 강도 | 발동 시점 | 상태 |
|---|---|---|---|---|---|
| **spawn**(초기조건) | 출발 지점의 위치·자세·속도 오차 | 에피소드 시작 상태 | 횡 ±0.8m, 방향 ±8°, 속도 ±20% | 리셋 시 | 채택 |
| **kick**(횡충격) | 옆바람·노면 단차에 차가 옆으로 밀림 | 주행 중 횡방향 속도 | 0.5~2.0 m/s, 좌우 랜덤 | 정상 주행 중 | 채택 |
| **steer**(조향교란) | 빙판·단차·조향 글리치로 핸들이 튐 | 주행 중 조향 입력(정책 명령 덮어씀) | ≈6~14°, 좌우 랜덤, 4프레임 지속 | 정상 주행 중(\|cte\|<0.8) | 채택 |
| **brake**(강제제동) | 급제동·브레이크 끌림·장애물 회피 | 브레이크 강제 인가 + 구동 차단 | 0.3~0.8(제동량), 5~15프레임 지속 | 정상 주행 중(\|cte\|<0.8) | 채택 |



### 단계적(staged) 학습 

curriculum learning : 쉬운 외란부터 단계적으로 학습

| stage | warm-start | 주입 외란 / 변경 | 목적 | 
|---|---|---|---|
| A | 깨끗한 추종 policy | spawn(초기조건) + kick(횡충격) | 외란 강건 policy 확보 (검증된 안전 구성) | 
| B | A 결과 policy | + steer(조향교란) | 핸들 튐 복구까지 학습 | 
| C | B 결과 policy | + brake(강제제동) | 급제동·브레이크 끌림 복구까지 학습 | 
| D | C 결과 policy | (외란 동일) + pacefix 보상 (과속 벌점 강화 VEL_OVER_W 2.4) | 복구 중 과속(ref 공보다 앞섬) 억제 | 
| E | D 결과 policy | + friction(노면 구간 마찰 μ 1.0/0.75/0.5) | 저마찰 노면 대응 | 
| **F** | pos(오염방지) | 4종(spawn·kick·steer·brake) 통합 + **reward_v3**(OOD 종료조건 완화) | 통합 단일모델 — 대이탈 복구까지 한 체크포인트로 시도 | 



### 발동 조건 
> |cte| < 0.3 m
* 횡충격의 발동 게이트가 너무 엄격하면 직선·완만한 구간에만 외란이 몰림  
* 게이트를 넓혀(이탈 허용폭 확대) 커브·회복 중 상태까지 외란 허용

### 학습 결과 checkpoint F(4096env × 300iter ≈ 4.2h)

**kick / brake / spawn 은 복구 성공** (정직 완주판정 |cte|<3m 기준)

![](../res_wjdaksry/0726/30_F_kick5.0_p124_복구.mp4)

https://github.com/user-attachments/assets/fbe2fa02-12aa-4347-b268-d752f4af5b0f

* kick 5.0 m/s → 완주 0.84배 (cte 0.23 복귀)

![](../res_wjdaksry/0726/31_F_brake_p134_복구.mp4)

https://github.com/user-attachments/assets/d10c5cd6-2bf0-4d72-aeb2-be3ac83d5942

* brake 1.0 강제제동(75f) → **완전 정차 후 재출발** → 완주 1.17배 (정차 중에도 cte 0.09 이내 경로 유지)

![](../res_wjdaksry/0726/32_F_spawn0.8_p120_복구.mp4)

https://github.com/user-attachments/assets/1cedddeb-564f-42f9-9d11-1c050ae90666

* spawn 횡 0.8m 오프셋 복구, **과속 경향** (cte 0.07)

**단, spin(대이탈)은 전부 복구 실패**

![](../res_wjdaksry/0726/00_F_spin_fail.mp4)

https://github.com/user-attachments/assets/3aecdeab-5c90-472a-a51a-5b8b75d447d7

* spin 2.5·4.0 모두 5~11m 배회하며 복구 fail 

**F 외란별 복구 정량평가** (정직 완주판정 |cte|<3m)

| 외란 | 조건 | 완주비 | 복구 후 \|cte\| | 판정 |
|---|---|---|---|---|
| **kick** | 5.0 m/s (p124) | 0.84배 | 0.23 m | **복구** |
| **brake** | 0.7×12f (p134) | 1.00배 | 0.02 m | **복구** |
| **spawn** | 횡 0.8m (p120) | 0.94배 | 0.07 m | **복구**|
| **spin** | 2.5 (p120) | 3.49배 | 5~11m 배회 | **실패** |
| **spin** | 4.0 (p120·p161) | DNF(did not finish) | 발산 | **실패** |

> **핵심**: 통합 단일모델 F 는 소규모 외란(kick·brake·spawn)은 정상 복구하나, **spin에서 무너짐**

> F는 소규모 외란(kick·brake·spawn)은 복구하지만 대이탈(spin)에서 무너진다. 문제는 학습량도 보상도 아닌 관측 — 기존 31D는 경로 근처만 전제해 대이탈에서 무의미(OOD)해지기 때문이다. 그렇다면 대이탈에서도 유효한 관측을 갖춘 별도 정책을 두면 어떨까?

---
next step : policy switch(RL_pos &lrarr; RL_recovery)