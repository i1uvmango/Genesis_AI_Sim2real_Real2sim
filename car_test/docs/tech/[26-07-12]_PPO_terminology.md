# PPO Terminology & RL 학습 구조 정리

## Terminology
### GAE : Generalized Advantage Estimation
> GAE(Generalized Advantage Estimation)는 PPO에서 Actor를 업데이트할 때 사용하는 Advantage를 더 안정적으로 계산하는 방법

1. advantage : Actor의 행동이 좋은 행동이었는가? 를 평가하는 기준(entropy 의 information gain 의 개념)

A(s,a)=Q(s,a)−V(s) 

  * V(s) : 현재 상태의 평균적인 가치
  * Q(s,a) : 그 행동을 했을 때의 가치

2. 그런데 현재 가치 Q(s,a)는 에피소드 끝까지 가봐야 알기 때문에 매 스텝 보상을 주어야하는 RL 입장에서는 사용 불가함

3. 그래서 `TD Error`보다는 긴 시퀀스를 보고, `monte-carlo`보다는 짧은 시퀀스를 보는 `GAE`를 사용

* TD Error : $δ_{t}$ = $reward_{t}$ + $γ$ $V(s_{t+1})$ − $V(s_{t})$

  > 의미 : "이번 행동이 예상보다 얼마나 좋았는가?"
  * 현재 스텝 : $V(s_{t})$
  * 다음 스텝 : $V(s_{t+1})$ 
> 하지만 `TD Error`는 1 step 만 보기 때문에 연속적인 주행 시퀀스에서 부정확

* Monte Carlo : Episode(480 frame)까지 보기때문에 정확하지만 분산이 매우 큼

4. GAE 사용 : TD와 Monte Carlo를 적절히 섞어서 이를 `Loss Function` 에 사용

$$A_t = \delta_t + (\gamma\lambda)\,\delta_{t+1} + (\gamma\lambda)^2\,\delta_{t+2} + \cdots$$

* λ=0 &rarr; TD Error만 사용

  * 분산 ↓
  * bias ↑
* λ=1 &rarr; 거의 Monte Carlo

  * 분산 ↑
  * bias ↓

5. Residual_RL_PPO Loss Function

$$L = -\log \pi(a \mid s)\,A_t$$


---

### clip (0.2)
> PPO의 핵심 아이디어. 정책이 한 번에 너무 많이 변하지 않도록 제한

정책 확률비율(policy ratio):

$$r_t(\theta) = \frac{\pi_\theta(a_t \mid s_t)}{\pi_{\theta_{old}}(a_t \mid s_t)}$$

π : policy

* "이번 업데이트가 정책을 너무 많이 바꾸지는 않았는가?" 를 확인하기 위해 이 비율을 사용


### Adam 

학습이 진행될때 하이퍼파라미터가 Learning Rate 가 다음과 같이 감소하며 자동 최적화
```
0.00025

↓

0.00018

↓

0.0001

↓

0
``` 

### Curriculum Learning

쉬운 문제부터 점차 어려운 문제로 확장하면서 필요한 부분만 fine-tuning

> CNN 학습과 동일하게 처음부터 어려운 사진 학습 시 수렴이 어려움
```
Stage1
깨끗한 정면 사진

        ↓

Stage2
조금 회전된 사진

        ↓

Stage3
가려진 사진

        ↓

Stage4
노이즈가 있는 사진
```

위 처럼 속도 보정에 대해서 curriculum learning 적용
* 조금씩 보정
* 더 적극적으로 보정
* 고속에서도 안정적인 보정



---




# RL 학습 구조 이해 정리 — 중간 스폰(spawn)과 PPO 업데이트 주기

> 목적: residual RL 학습에서 "경로 중간 스폰"의 의미를 잘못 이해했던 지점과,
> 교정된 이해, 그리고 여기서 얻은 인사이트(DAgger 유비 포함)를 기록한다.

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



### 내용 정리
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

