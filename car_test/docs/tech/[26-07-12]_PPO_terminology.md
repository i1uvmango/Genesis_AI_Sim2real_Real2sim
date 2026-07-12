# PPO Terminology

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