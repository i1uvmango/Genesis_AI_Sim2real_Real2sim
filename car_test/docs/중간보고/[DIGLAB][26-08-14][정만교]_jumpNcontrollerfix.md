# Terrain Jump Slowdown & Controller Check

> 전 보고(sweep table 커버리지 수정) 이후 진행분 — 이륙 방지 감속, disturbance 복구 실패(policy switch 진동)의 원인 규명.


## 요약

**결과**

- 이륙 방지 감속으로 **무외란 41/42**, 신규 10씬 52.9→**23.3 cm**
- policy switch 진동의 understeer 가설은 기각 — steer 포화 없음·조향 cap 여유 실측
- OOD 가설(관측 클리핑 ±3σ + 재가속 금지)로 **disturbance PASS 33→34/42**, p166 진동 9→4회 — 이득은 있으나 근본 원인 아님으로 판명

**미해결**

- closed loop 제어기(base Stanley) 피드백 구조 결함 검증 중 
- disturbance 잔여 FAIL 7씬 — 4씬은 100~120 cm 근소 미달, p169 는 recovery 데드락

---

## 2. 이륙 방지 감속 로직

**진단**: p179, **경로에 실재하는 점프대** 방지

**규칙**: 지형 볼록 curvature 로 접지 유지 상한 v_cap=√(g·0.7/κ) → 초과 구간 속도 클램프(7씬 정도 적용됨)

| 씬 | 감속 전 (base 단독) | 감속 후 | 완주 프레임 비 |
|---|---|---|---|
| p179 | 341 cm / 최대 20.1 m | **32 cm / 1.7 m** | **0.92×** |
| p178 | 262 cm / 10.3 m | **19 cm / 1.5 m** | **0.85×** |
| p170 | 84 cm / 7.6 m | 13 cm / 1.6 m | 1.07× |
| p172 | 59 cm / 3.8 m | 15 cm / 0.4 m | 1.04× |



#### 무외란 42씬 before / after (풀스택: v2 tuned + residual it300)

| 감속 전 | 감속 후 |
|:---:|:---:|
| <img src="../../res_wjdaksry/0812/A0_무외란42씬_승계it300.png" width="480"> | <img src="../../res_wjdaksry/0812/C1_무외란42씬_풀스택_JUMPSLOW.png" width="480"> |
| 신규 10씬 평균 CTE 52.9 cm | 신규 10씬 평균 CTE **23.3 cm** |

* 점프로 인한 오차 누적이 사라짐

## 3. Disturbance 복구 실패의 원인 분석




### 가설 : recovery &rarr; rl_stn 진입 시 understeer가 일어나서 cte가 벌어지고, 다시 recovery mode로 들어간다(반복)

![](../../res_wjdaksry/0812/C3_p166_리밋사이클.gif)
> RL_recovery -> RL_stn 스위치 과정에서 진동하는 현상, 무외란 주행 성능은 우수함
관찰 1: stanley 제어기가 경로 진입 시 초반 진동하는 것을 확인 
관찰 2: policy switch 과정에서 경로를 제대로 추종못하는 모습, understeer라고 생각함


* 하지만 확인결과 steer 포화되지 않았고, 조향 cap도 여유 있었음
* 제어기가 있는 closed loop이면 오차 피드백으로 경로로 돌아가야한다고 생각했음
* closed loop 제어기 설계에 문제가 있는걸 확인 후 검증 중에 있음


### 가설 2 : RL_recovery &rarr; RL_stn 시의 state가 OOD 이다

조치 :
* 관측 클리핑 ±3σ 
*RL_recovery -> RL_stn 스위칭 후 천천히 속도를 올리도록 급격한 가속 제한 재한
결과 : 

| before — residual 상시, **PASS 33/42** | after — 관측 클리핑 3σ, **PASS 34/42** |
|:---:|:---:|
| <img src="../../res_wjdaksry/0812/C2_외란42씬_풀스택_JUMPSLOW.png" width="480"> | <img src="../../res_wjdaksry/0812/C9_외란42씬_관측클립.png" width="480"> |

> scene 166 대폭 품질 향상

| 항목 | before (residual 상시) | after (클리핑 3σ) |
|---|---|---|
| PASS | 33/42 | **34/42** |
| recovery 진입 합 | 78회 | **73회** |
| p166 recovery 진입 | 9회 | **4회** |
| p166 후반 중앙 CTE | 152 cm | **106 cm** |

* 진동 반복이 절반으로 줄지만 완전히는 못 잡음 — 여러 관측이 동시에 3σ 경계에 붙은 조합 자체가 학습 분포에 없던 상태
* 이득을 보긴했지만, 근본 원인은 아니라고 판명 


현재까지의 결과
![](../../res_wjdaksry/0812/C11_외란42씬_풀조합.png)


#### next step / 방향

* stanley 제어기 피드백 구조 확인중