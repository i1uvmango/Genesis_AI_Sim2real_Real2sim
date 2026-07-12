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




### 7. RL 학습 과정


1. 초기화:
  512 env 생성

2. 각 env reset:
랜덤 scene(p120) + 랜덤 spawn(위치) 선택

3. rollout:
512 env가 동시에 closed-loop 주행
각 step마다 state → BC → RL residual → physics → reward

4. episode 종료 시:
끝난 env만 즉시 새 scene/spawn으로 reset

5. iteration 종료 시:
512 env × H step 데이터로 PPO update

6. 다음 iteration:
업데이트된 policy로 다시 rollout

* spawn 지점 속도 등 state 주입
* settled 안정화 상태로 스폰 
* `Raycast Distance Cache` 재사용 하여 연산 비용 최적화


## RL 학습 구조 이해 정리 — 중간 스폰(spawn)과 PPO 업데이트 주기

> 목적: residual RL 학습에서 "경로 중간 스폰"의 의미를 잘못 이해했던 지점 기록


### 1. 처음의 오해 — "모자이크" 걱정

**오해했던 내용**: 경로 중간 지점에서 에피소드를 시작하면, 서로 다른 위치의 프레임들을 독립적으로 계산해 이어붙이는 것(모자이크)이 되어, open loop 주행과 같은 오차가 생성 되는 것이 아닌가?

* golden data mining 관점에서 비슷한 상황 : 최적화 시 경로를 분할하여 partial 구간 마다 최적화 후 경합 했더니 open loop 오차가 발생하여 사용하지 못하는 데이터가 됨.

## 2. 교정된 이해 — spawn 은 초기조건, 에피소드는 연속 물리

**Random spawn 의 정확한 의미**: reference path 위의 특정 지점에 대해 **미리 settle 시킨 상태**(state cache에 저장), 복원하여 주행 이어나감


**파이프라인 원칙과의 정합**: 이는 우리가 전 단계(Blender 데이터, RL 설계)에서
못 박은 원칙 그대로다 — *에피소드 시작 시 spawn/reset 은 허용, 주행 중 pose
강제 이식은 절대 금지.* 

* 초반 pose, state만 set, 이후 주행은 BC + RL policy 로 closed loop 주행


## 3. 왜 처음부터만 시작하지 않는가 — 학습 효율

- 어려운 구간(예: 700프레임 근처 고속 코너)이 경로 뒤쪽에 있으면, 시작점
  고정 시 매 에피소드 0→700 을 달려야 그 경험을 얻는다.
- 중간 스폰(spawn 690)이면 즉시 고속 코너 진입부 경험을 수집한다.
- 부수 효과: 시작점 고정 시 초반 구간 데이터만 과잉 축적되는 불균형도 해소.
- 초기 속도도 커리큘럼 분포에서 샘플되므로, "그 지점을 그 속도로 지나는"
  다양한 초기조건이 만들어진다.

## 4. 효과

> **배우는 것**: 에피소드 내부의 누적 오차와 그 보정, 복구(recovery) 능력

* 경로 중 랜덤한 위치에서 시작된 에피소드 당연히 오차가 생김
* 해당 오차를 RL policy가 보정하며, 오차에 대한 복구 능력이 생김


## 5. PPO 업데이트 주기 — episode 종료 후 env 는 새로운 episode 비동기 진행

> 업데이트 주기: "에피소드가 끝나면 그때 actor 를 업데이트하나?"

**정확한 구조** (for iteration k):

* iteration : 업데이트 주기

1. actor θ_k 고정
2. 512 env 를 H(=128) step 병렬 rollout 실행
3. rollout 중 done 된 env 는 그 env 만 즉시 reset (새 scene/spawn)
4. H step 이 찰 때까지 계속 수집
5. H size 가 채워지면 `done` 경계 표시 → advantage(score) 계산 시 경계 너머로
   주행평가(advantage)를 계산하지 않음 → policy update 에 오염 방지
6. 512env × H transition 으로 actor policy 1회 update
7. move to #2

> 한 iteration 안에서 한 env 가 여러 에피소드를 끝내도 무방, `done` 마스크가 policy update시 오염이 되지 않도록 방지

예시
```
H = 128

env 7:
step 0   episode A 시작
...
step 39  episode A 종료, done=True
step 40  즉시 reset → episode B 시작
step 41
...
step 127 episode B 계속 진행 중

→ 여기까지 128 step 채움
→ PPO update
```

## 6. DAgger 와 유사 역할

**핵심 통찰 (맞는 부분)**: BC 의 근본 약점은 covariate shift — expert 분포에서만
배우므로, 자기 실수로 분포 밖 상태에 들어가면 복구를 모른다. DAgger 는 "정책이
실제로 방문하는 상태"에서 학습 데이터를 얻어 이를 고친다. **랜덤 중간 스폰 +
폐루프 RL 도 정확히 같은 문제를 공격한다**: 다양한 초기조건(오차가 있는 상태
포함)에서 시작해, 정책 자신의 분포에서 복구 행동을 학습한다. "중간에서 시작한
에피소드가 그 뒤의 경로를 보정하며 복구 능력을 만든다"는 이해가 정확하다.

**차이점**

- DAgger: 정책 방문 상태에서 **expert(MPPI)를 다시 질의**해 라벨을 받아
  지도학습 — 교정 신호 = expert 라벨.
- 본 RL: expert 질의 없이 **reward(MPPI cost 반전)** 로부터 교정 신호를 얻음.
- 실용적 함의: DAgger 는 상태마다 MPPI 마이닝 비용이 들지만, RL 은 마이닝 없이
  같은 목적함수로 폐루프 최적화를 이어간다. golden 이 없는 영역(고속·브레이크)
  까지 확장 가능한 이유가 여기에 있다 — "MPPI 가 못다 한 최적화의 연장".


## 7. Robust Mapper(BC Freeze + RL_PPO)
MLP 처럼 **통합 데이터 주행 policy**

### time vs position

RL 상태 구성 시 레퍼런스 프레임을 고르는 두 방식:
- **time 모드**: i = 스케줄 시계(+1/step, BC 학습과 동일). schedule 앵커 존재.
- **position 모드**: i = 차량 위치에 가장 가까운 레퍼런스 프레임. schedule 앵커 없음 → 위상 자유표류 가능. lag 보상항(W_LAG)으로 지연 억제.

### 3지표 비교 (26씬 통합, best: time 799 / position 600)

| 지표 | time | position | 판정 |
|---|---|---|---|
| frame-matched dist(ref csv, m) | 0.712 | 0.723 | time 우위 (1.5%) |
| **횡오차 lateral (경로선 붙음, 실차 핵심, m)** | 0.075 | **0.068** | **position** (코너 특히: p134 횡 0.19→**0.05**) |
| lag (종방향 오차, m) | 0.705 | 0.705 | **동률** |


![](../res_wjdaksry/0712/grid_TIME_iter799.png) 
* time 기반

![](../res_wjdaksry/0712/grid_POS_iter600.png)
* position 기반


- **핵심**: position 은 **lag 를 동등하게 유지하면서 횡오차를 더 낮춤** = 스케줄 추종은 동등한데 경로선엔 더 정확 
- **단, clean win 은 아님** — 성능(횡추종) pos ≥ time / lag 동률 / **안정성 time > pos** (position 은 학습 중 it200=8.63 대발산 후 회복 → 체크포인트 선발 까다로움, 사인표류·쉬운구간 개입 관찰).
- `Brake`가 있기 때문에, CTE 를 줄이는게 더 중요하다고 판단
- **결론**: 실차 추종(횡·코너)은 position 우위, 학습 안정성은 time 우위 


### 주행 영상 (BC vs RL_time vs RL_pos)

![](../res_wjdaksry/0712/rl_p112_mode_compare.mp4)

https://github.com/user-attachments/assets/68677325-6406-4eb5-82df-97e7b226a5d4

* 코너 오차 감소량을 보며 방향 설정

### 주행 영상 (time vs pos)

![](../res_wjdaksry/0712/p134_time_vs_pos.mp4)

https://github.com/user-attachments/assets/21e860c2-2e7b-42a1-b858-872a4030335d

![](../res_wjdaksry/0712/p135_time_vs_pos.mp4)

https://github.com/user-attachments/assets/f7e24de3-72f6-4080-8023-ac7cfa1ab123

![](../res_wjdaksry/0712/p148_time_vs_pos.mp4)

https://github.com/user-attachments/assets/dc63ce11-df26-42df-89b8-d5820f443c30

![](../res_wjdaksry/0712/p121_time_vs_pos.mp4)

https://github.com/user-attachments/assets/fbe4b419-17a0-4c41-835e-95cc3bff680a
