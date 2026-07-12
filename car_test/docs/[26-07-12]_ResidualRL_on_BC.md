# Adding Residual RL(PPO) on BC Mapper

```
              ┌────────────────────┐
s_bc ────────>│ frozen BC Mapper    │
              │ no gradient update  │
              └─────────┬──────────┘
                        │
                        │ base action
                        │ [T_BC, S_BC]
                        ▼
              ┌────────────────────┐
s_rl ────────>│ RL residual policy  │
              │ PPO로 학습          │
              └─────────┬──────────┘
                        │
                        │ residual
                        │ [Δu, ΔS]
                        ▼

u = T_BC + Δu
S = S_BC + ΔS

# 가속 & 제동 분리 로직
if u >= 0:
    throttle = u
    brake = 0
else:
    throttle = 0
    brake = -u

# u: BC + RL 보정을 거친 최종 longitudinal command
```


----------


## Residual RL — Frozen BC + Residual PPO

> BC Mapper의 경로 추종 능력은 준수하나 곡률 추종, 속도 변경·고속 추종 능력을 국소  교정 * 강화하기 위해, 학습이 끝난 **BC Mapper 를 Freeze** 하고 그 위에
**잔차(residual) 정책**만 PPO 로 학습한다. 최종 행동 = BC 기본행동 + 잔차.
→ BC 의 전역 안정성을 보존하면서, RL 은 "얼마나 더/덜 밟고 꺾을지"의 **작은 보정**만 담당한다.

###  Policy : Actor - Critic

| - | 구조 | 비고 |
|---|---|---|
| **Actor (행동 결정자)** | 31 → 128 → 128 → 2 (ELU) | 행동 생성 (Residual Δu,ΔS) |
| **Critic (평가자)** | (31 + 특권 33) → 256 → 256 → 1 (ELU) | 현재 상태 평가 V(s) |
| PPO | - | Actor 업데이트를 안정화 |



### 브레이크 설계

```
u = T_BC + Δu      S = S_BC + ΔS
비대칭 잔차 cap:  Δu ∈ [−0.7, +0.3]   ΔS ∈ [−0.25, +0.25]   (감속 방향 여유를 크게)
게이팅:  u ≥ 0 → throttle=u, brake=0
         u < 0 → throttle=0, brake=−u
```

> PPO 보상 설계에서 Action의 변경은 최소한으로 하지만, 실제 주행 중 감속은 빠르게 변화가 나타나야 하므로, 비대칭 보상치를 부여

* 가속(+Δu)은 좁게(0.3)
* 감속/브레이크(−Δu)는 넓게(0.7) 
    * 안전측(감속) 보정을 더 허용


### 4. State Sheet (31D — BC와 동일 구조)
`state7`(Δv, Δheading, CTE, v_long, κ, pitch, roll) + `k_look×10` + `a_look×10` + `a_target` + `deriv3`(v̇, ṗ, ṙ, backward-slope K=5)


| 그룹 | Dim | 피처 | 설계 의도 |
|---|---|---|---|
| **FeedBack** | 3 | `delta_v`, `delta_heading`, `cte` | 누적 오차 명시 → PID 의 오차 항을 신경망으로 |
| **Current Dynamic State** | 4 | `v_long`, `kappa`, `pitch`, `roll` | Genesis 차량의 현재 물리 상태 |
| **Current FF** | 1 | `a_target` | 현재 스텝 FF (직접 참조) |
| **FeedForward k** | 10 | `k_target[t+1..t+10]` | 10-step 미래 곡률 — 사전 조향 준비 |
| **FeedForward a** | 10 | `a_target[t+1..t+10]` | 10-step 미래 가속 — 사전 스로틀 준비 |
| **경향성 미분** | 3 | `dv_rate`, `pitch_rate`, `roll_rate` | 상태 변화 방향 (관측 스파이크 흡수) |


### 5. Reward 설계

> 1 Episode : Scene 전체의 frame(ex: 480f)을 기준으로 보상 설계 


| 항 | weight | 정의 / 목적 |
|---|---|---|
| Progress (+) | **+1.0** | 차량이 목표 경로를 따라 계속 전진하도록 유도합니다. 한 번에 너무 멀리 점프해서 점수를 얻는 것을 막기 위해 프레임당 최대 전진량을 제한 |
| CTE (−) | **2.0** | 경로에서 벗어나면 큰 감점 |
| Heading (−) | **0.8** | 차량의 방향이 경로 방향과 다르면 감점 |
| Velocity (−) | **0.5** | 코너에서는 천천히 가는 것이 자연스러우므로 느린 것은 비교적 관대하게 보고, 과속은 크게 감점합니다. |
| Lag (−) | **0.3** | 시간표나 목표 위치를 따라가지 못하는 것을 방지합니다. (position 기반 모드에서만 사용 : 이후 설명 예정) |
| Backward (−) | 0.5 | 실제 후진(Δs<−0.05 & v<0.1)외에 차량이 뒤로 움직이는 이상한 행동을 하지 않도록 합니다. |
| Smooth / Res / Brake (−) | 0.05 / 0.1 / 0.02 | 핸들을 갑자기 꺾거나, RL이 너무 큰 보정을 하거나, 브레이크를 과도하게 사용하는 것을 억제 |
| 종료 벌점 | **−10** | \|cte\|>3.0m or \|roll\|>45° or \|pitch\|>45° 크게 실패하면 큰 감점 후 종료 |


### 6. PPO 학습 설정

> PPO 핵심 용어(GAE · clip)는 [PPO terminology 정리](tech/%5B26-07-12%5D_PPO_terminology.md) 참고

* 병렬 env **512**
* GAE advantage
* **clip 0.2**(정책+가치 동시 클리핑)
* value clipping
* Adam **lr 3e-4 (0.0003, linear decay)**
* minibatch 4096
* grad-norm clip 0.5
* entropy 0.0(이미 BC 단계에서 exploration 진행)
* **Curricum Learning**: 허용 최대 속도 점진 상승(학습 안정성)
    * CNN의 점진 학습 처럼 쉬운 데이터 부터 학습
      * 최대속도 5m/s 
      * 최대속도 8m/s
      * 최대속도 12m/s 등 허용 속도 점진 증가




### 7. 스폰 (cache_spawn)
- **프로파일 스폰**: 스폰지점의 v_target 를 초기 선속도로 주입, 휠 스핀 ω=v/r(구름 조건)
- settled 상태 + 레이캐스트 거리 캐시 재사용(stale-raycast override), `spawn_ok` 필터(roll/pitch/잔여프레임 여유)

### 8. Robust Mapper(BC Freeze + RL_PPO)
MLP 처럼 **통합 데이터 주행 policy**
* p00 terrain mesh 1회 빌드, env 마다 서로 다른 랜덤 레퍼런스를 추종.

* `cache_spawn`이 이를 가능하게 함

### 9. 검증 게이트
- **Gate1**: 잔차=0 강제 → 출력이 BC 2.3 과 동일한지 확인 (하네스 정합 검증)
- **Gate2**: 억제(minor_scale=0.1) 하에 학습 수렴 확인
- **결과**: 멀티씬 통합 RL **0.710** vs BC **0.822** (−14%, frame-matched 평균)

## 레퍼런스 인덱싱: time vs position

RL 상태 구성 시 레퍼런스 프레임을 고르는 두 방식:
- **time 모드**: i = 스케줄 시계(+1/step, BC 학습과 동일). schedule 앵커 존재.
- **position 모드**: i = 차량 위치에 가장 가까운 레퍼런스 프레임. schedule 앵커 없음 → 위상 자유표류 가능. lag 보상항(W_LAG)으로 지연 억제.

### 3지표 비교 (26씬 통합, it: time 799 / position 600)

| 지표 | time | position | 판정 |
|---|---|---|---|
| frame-matched (golden 시간정합, m) | 0.712 | 0.723 | time 근소 (1.5%) |
| **횡오차 lateral (경로선 붙음, 실차 핵심, m)** | 0.075 | **0.068** | **position** (코너 특히: p134 횡 0.19→**0.05**) |
| lag (스케줄 지연, m) | 0.705 | 0.705 | **동률** |

- **핵심**: position 은 **lag 를 동등하게 유지하면서 횡오차를 더 낮춤** = 스케줄 추종은 동등한데 경로선엔 더 정확 (공짜 개선). frame-matched 만 time 이 앞선 건 *golden 시간정합* 기준이지 실차 추종성이 아니다.
- **단, clean win 은 아님** — 성능(횡추종) pos ≥ time / lag 동률 / **안정성 time > pos** (position 은 it200=8.63 대발산 후 회복 → 체크포인트 선발 까다로움, 사인표류·쉬운구간 개입 관찰).
- **결론**: 실차 추종(횡·코너)은 position 우위, 학습 안정성은 time 우위 → 최종 방향 = **하이브리드**(position 상태정렬 + 학습 안정화).

### 산출물
- `z_vid/multi/p{N}_time_vs_pos.mp4` (26씬 나란히 주행, HUD 체크포인트 표기)
- `z_vid/multi/grid_TIME_iter799.png` (0.710) / `grid_POS_iter600.png` (0.725)
- 초기 단일씬 실험: `z_vid/rl_p112_mode_compare_ 쉬운구간건드림.mp4`