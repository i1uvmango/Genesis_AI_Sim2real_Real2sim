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

```
초기화:
512 env 생성

각 env reset:
랜덤 scene(p120) + 랜덤 spawn(위치) 선택

rollout:
512 env가 동시에 closed-loop 주행
각 step마다 state → BC → RL residual → physics → reward

episode 종료 시:
끝난 env만 즉시 새 scene/spawn으로 reset

iteration 종료 시:
512 env × H step 데이터로 PPO update

다음 iteration:
업데이트된 policy로 다시 rollout
```

* spawn 지점 속도 등 state 주입
* settled 안정화 상태로 스폰 
* `Raycast Distance Cache` 재사용 하여 연산 비용 최적화


---------------------------
# RL 학습 구조 이해 정리 — 중간 스폰(spawn)과 PPO 업데이트 주기

> 목적: residual RL 학습에서 "경로 중간 스폰"의 의미를 잘못 이해했던 지점과,
> 교정된 이해, 그리고 여기서 얻은 인사이트(DAgger 유비 포함)를 기록한다.

---

## 1. 처음의 오해 — "모자이크" 걱정

**오해했던 내용**: spawn 21, spawn 84 처럼 경로 중간 지점에서 에피소드를 시작하면,
서로 다른 위치의 프레임들을 독립적으로 계산해 이어붙이는 것(모자이크)이 되어,
연속 주행에서 생기는 누적 오차를 학습하지 못하는 것 아닌가?

**오해가 그럴듯했던 이유**: BC 데이터 관점에서는 실제로 비슷한 함정이 존재했다.
과거 DAgger CSV에서 여러 씬의 sparse 행이 섞인 채 인접 행을 lookahead/prev 로
사용해 22차원이 오염됐던 버그(2026-07-06 FIX)가 그 예 — "프레임을 이어붙이면
망가진다"는 경계심 자체는 파이프라인 경험에서 나온 정당한 것이었다.

## 2. 교정된 이해 — spawn 은 초기조건, 에피소드는 연속 물리

**spawn 의 정확한 의미**: `spawn_cache_p{s}.npz` 의 유효 스폰 풀 인덱스.
reference path 위의 특정 지점에 대해 **미리 settle 시킨 상태**(qpos, dofs,
omega, prev_compression, heading)를 저장해둔 것이고, reset 은 이 상태의 복원이다.
"원본 CSV의 n번째 프레임을 떼어 붙이는 것"이 아니다.

**에피소드 내부는 완전한 연속 물리다**:
```
초기조건: spawn 지점에 settle 상태 복원 (에피소드 시작 시 1회 — 허용)
t=0 → action_0 → physics.step → state_1
state_1 → action_1 → physics.step → state_2
...  (매 스텝 실제 pos/vel/quat 를 읽고 → observation → BC+RL action → 물리)
```
모자이크라면 "frame 21 독립 계산 + frame 22 독립 계산 + ..." 이어야 하는데,
실제 구조는 "ref 21 에서 출발 → 물리로 22, 23 주변을 지나가는 폐루프 주행"이다.

**파이프라인 원칙과의 정합**: 이는 우리가 전 단계(Blender 데이터, RL 설계)에서
못 박은 원칙 그대로다 — *에피소드 시작 시 spawn/reset 은 허용, 주행 중 pose
강제 이식은 절대 금지.* 중간 스폰은 이 원칙을 위반하지 않는다. 초기조건을
다양화할 뿐, 주행 중 개입이 없기 때문이다.

## 3. 왜 처음부터만 시작하지 않는가 — 학습 효율

- 어려운 구간(예: 700프레임 근처 고속 코너)이 경로 뒤쪽에 있으면, 시작점
  고정 시 매 에피소드 0→700 을 달려야 그 경험을 얻는다.
- 중간 스폰(spawn 690)이면 즉시 고속 코너 진입부 경험을 수집한다.
- 부수 효과: 시작점 고정 시 초반 구간 데이터만 과잉 축적되는 불균형도 해소.
- 초기 속도도 커리큘럼 분포에서 샘플되므로, "그 지점을 그 속도로 지나는"
  다양한 초기조건이 만들어진다.

## 4. 무엇을 배우고, 무엇은 덜 배우나 (정직한 한계 포함)

**배우는 것**: 에피소드 내부의 누적 오차와 그 보정. 중간 스폰 에피소드도
시작 직후부터 policy action → 물리 반응 → cte/heading 오차 누적 → 보정의
폐루프를 그대로 겪는다. 복구(recovery) 능력이 여기서 나온다.

**덜 배우는 것**: 경로 처음부터 수백 프레임 달려와야만 생기는 특수한 장기
이력 상태. 단, 두 가지가 이 한계를 완화한다:
1. 스폰 캐시가 순간이동이 아니라 **settle 된 상태**(서스펜션/접지 복원)라서
   지형 접촉 관점의 부자연스러움은 없다.
2. 현재 차량 모델과 31D 피처(미분 rate 포함 ~0.1s 창)에는 타이어 열 같은
   초장기 이력 변수가 애초에 없다 — 모델이 표현하는 상태 공간 안에서는
   중간 스폰이 정보 손실 없는 초기조건이다.

## 5. PPO 업데이트 주기 — episode 종료는 reset 트리거, update 트리거가 아니다

**오해 여지가 있던 부분**: "에피소드가 끝나면 그때 actor 를 업데이트하나?"

**정확한 구조** (iteration k):
```
1. actor θ_k 고정
2. 512 env 를 H(=128) step 병렬 rollout
3. rollout 중 done 된 env 는 그 env 만 즉시 reset (새 scene/spawn)
4. H step 이 찰 때까지 계속 수집
5. done=True 가 에피소드 경계 표시 → advantage 계산 시 경계 너머로
   return 을 이어붙이지 않음 (서로 다른 에피소드를 한 궤적으로 착각 X)
6. 512×H transition 으로 θ_k → θ_{k+1} 1회 갱신
```
한 iteration 안에서 한 env 가 여러 에피소드를 끝내도 무방하다 —
done 마스크가 경계를 지키므로 batch 에 섞여도 오염이 없다.

## 6. 인사이트 — "이것이 DAgger 의 역할과 같다"

**핵심 통찰 (맞는 부분)**: BC 의 근본 약점은 covariate shift — expert 분포에서만
배우므로, 자기 실수로 분포 밖 상태에 들어가면 복구를 모른다. DAgger 는 "정책이
실제로 방문하는 상태"에서 학습 데이터를 얻어 이를 고친다. **랜덤 중간 스폰 +
폐루프 RL 도 정확히 같은 문제를 공격한다**: 다양한 초기조건(오차가 있는 상태
포함)에서 시작해, 정책 자신의 분포에서 복구 행동을 학습한다. "중간에서 시작한
에피소드가 그 뒤의 경로를 보정하며 복구 능력을 만든다"는 이해가 정확하다.

**유비의 경계 (구분할 부분)**: 메커니즘은 다르다.
- DAgger: 정책 방문 상태에서 **expert(MPPI)를 다시 질의**해 라벨을 받아
  지도학습 — 교정 신호 = expert 라벨.
- 본 RL: expert 질의 없이 **reward(MPPI cost 반전)** 로부터 교정 신호를 얻음.
- 실용적 함의: DAgger 는 상태마다 MPPI 마이닝 비용이 들지만, RL 은 마이닝 없이
  같은 목적함수로 폐루프 최적화를 이어간다. golden 이 없는 영역(고속·브레이크)
  까지 확장 가능한 이유가 여기에 있다 — "MPPI 가 못다 한 최적화의 연장".

정리: **목적(분포 시프트 해소·복구 학습)은 DAgger 와 동일, 수단(expert 재라벨
vs reward 최적화)은 다르다.** 보고 시 이 한 문장으로 유비를 정확히 쓸 수 있다.



**한국어**:
각 env 는 랜덤하게 선택된 scene 과 spawn point 에서 에피소드를 시작한다.
spawn 은 에피소드의 초기조건일 뿐이며, 이후 주행은 매 step 차량의 실제 물리
상태를 읽고 action 을 적용하는 closed-loop 로 연속 전개된다. 에피소드가 끝나면
해당 env 만 새 scene/spawn 으로 reset 된다. actor 는 에피소드 종료마다가 아니라,
모든 병렬 env 에서 fixed rollout horizon 만큼 transition 을 모은 뒤 PPO
iteration 단위로 1회 업데이트된다. 랜덤 중간 스폰은 정책이 실제로 방문하는
상태에서 학습한다는 점에서 DAgger 와 같은 목적을 수행하되, 교정 신호를 expert
재라벨 대신 reward 에서 얻는다.

## 8. 한 줄 요약

**spawn 은 "중간 프레임 이어붙이기"가 아니라 "중간 위치에서 새 폐루프 에피소드
시작하기"이고, episode 종료는 update 가 아니라 reset 의 트리거이며, 이 구조가
BC 가 못 배우던 복구 능력을 — DAgger 와 같은 목적, 다른 수단으로 — 만들어준다.**



--------------------------------------------------


### 8. Robust Mapper(BC Freeze + RL_PPO)
MLP 처럼 **통합 데이터 주행 policy**
* p00 terrain mesh 1회 빌드, env 마다 서로 다른 랜덤 레퍼런스를 추종.

* `cache_spawn`가 매 프레임 `reset` + `spawn` 가능하게 함

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