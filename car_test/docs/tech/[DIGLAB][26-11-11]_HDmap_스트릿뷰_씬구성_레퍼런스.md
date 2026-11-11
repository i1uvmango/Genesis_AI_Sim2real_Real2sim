# References for HD Map and Street View Scene Composition with ADI

> 정밀도로지도(HD map)와 스트릿뷰로 주행 씬을 구성하는 연구 조사. ADI(직접 촬영한 카메라와 LiDAR 주행 데이터)에 적용할 관점에서 정리함. 2026-11-11 기준

## 용어

| 용어 | 설명 |
|---|---|
| 정밀도로지도 (HD map) | 차도와 보도 경계, 차선, 노면표시, 높이를 담은 지도. 국내는 국토지리정보원 |
| V-World 건물 | 건물 외곽선과 높이 속성. 높이만큼 세워 박스 모양 건물로 씀 |
| 스트릿뷰 | 지도 회사가 촬영한 거리 파노라마 (네이버 거리뷰, Google Street View) |
| ADI | 직접 촬영한 주행 데이터. 360 카메라와 VLP-16 LiDAR |
| 2DGS (mesh-bound) | 2D Gaussian Splatting. Gaussian을 mesh 면 위에 고정하고 사진 색만 학습함 |
| 궤적 밖 시점 | 학습 카메라가 지나가지 않은 시점. Genesis 추적 카메라가 여기에 해당 |
| 증류 | 생성모델이 만든 이미지를 다시 3D 학습 데이터로 넣어 3D 표현에 남기는 것 |

## 요약

**결과**

* 연구는 여섯 갈래임. 지도 prior와 주행 로그로 재구성, 지도를 조건으로 씬 생성, 스트릿뷰 이미지 기반, 지도와 위성영상에서 거리 시점 생성, 지도와 주행 데이터 정합, 새 시점 생성 후 3D로 증류
* 공공 지도(정밀도로지도, V-World)를 형상 prior로 쓰고 실제 주행 사진을 mesh에 고정한 Gaussian으로 입혀 물리 주행까지 연결한 연구는 찾지 못함
* 스트릿뷰를 쓴 연구(Streetscapes, Urban Radiance Fields)는 모두 Google 내부 데이터를 씀. 공개 API 이미지로 학습한 사례는 찾지 못함

**미해결**

* 네이버와 Google 약관이 스트릿뷰 영상의 저장과 가공을 금지함. ADI가 스트릿뷰 역할을 대신하는 구조가 현실적임
* 인용한 논문의 학회·연도·arXiv 번호는 모두 검색으로 확인함 (마지막 표)

## 1. 지도 prior와 주행 로그로 재구성

ADI 구성과 가장 가까운 갈래. 실제 주행 사진과 LiDAR로 재구성하고, 지도나 형상 제약을 prior로 씀

| 논문 | 학회 | 핵심 | ADI 적용 |
|---|---|---|---|
| Urban Radiance Fields (Rematas et al.) | CVPR 2022, arXiv 2111.14643 | 스트릿뷰 촬영 차량의 파노라마와 LiDAR로 거리 재구성. LiDAR 형상 감독, 노출 보정, segmentation으로 하늘 처리 | 360 카메라와 LiDAR라는 점에서 ADI와 같은 구성 |
| RoGs: Large Scale Road Surface Reconstruction with Meshgrid Gaussian (Feng et al.) | arXiv 2405.14342 | 도로를 격자 위 2D Gaussian으로 표현하고 높이를 차량 pose로 초기화 | 정밀도로지도 높이 격자 위 2D Gaussian 바닥과 같은 발상 |
| AutoSplat (Khan et al.) | ICRA 2025, arXiv 2407.02598 | 도로와 하늘 Gaussian에 형상 제약을 걸어 차로 변경 시점에서도 유지 | 표면 종류별 학습 규칙, 하늘 dome 처리 |
| Street Gaussians (Yan et al.) | ECCV 2024, arXiv 2401.01339 | 배경과 차량을 분리한 Gaussian 표현 | 차량을 지우고 차량 SDK로 바꾸는 구성 |
| UniSim (Yang et al.) | CVPR 2023, arXiv 2308.01898 | 주행 로그를 재구성해 폐루프 시뮬레이션에 씀 | Genesis 주행과 목적이 같음 |
| Neural Map Prior (Xiong et al.) | CVPR 2023, arXiv 2304.08481 | 여러 번 주행해 지도를 누적 prior로 씀 | 같은 구간을 여러 번 달린 데이터가 생기면 적용 |

## 2. 지도를 조건으로 씬 생성

월드모델 방향. HD map이나 도시 배치를 조건으로 형상과 외관을 생성함

| 논문 | 학회 | 핵심 | ADI 적용 |
|---|---|---|---|
| InfiniCube (Lu et al.) | ICCV 2025, arXiv 2412.03934 | HD map과 3D box로 voxel 세계를 만들고, 영상 생성모델로 외관을 입힌 뒤 3D Gaussian으로 올림. 약 300 m x 400 m | 정밀도로지도로 형상을 먼저 만드는 순서가 같음. 외관은 생성, ADI는 실제 사진 |
| Cosmos-Drive-Dreams (NVIDIA) | 2025, GitHub nv-tlabs/Cosmos-Drive-Dreams | HD map을 영상으로 투영한 조건과 LiDAR depth로 주행 영상 생성 | 정밀도로지도 투영 조건으로 ADI에 없는 시점과 날씨 생성 |
| MagicDrive3D (Gao et al.) | arXiv 2405.14475 | BEV 지도, 3D box, 문장으로 다시점 영상을 생성한 뒤 Gaussian으로 재구성 | 생성 후 재구성 순서. ADI는 재구성이 주, 생성은 보조 |
| MagicDrive (Gao et al.) | ICLR 2024, arXiv 2310.02601 | BEV 지도와 box로 다시점 주행 영상 생성 | MagicDrive3D의 기반 |
| CityDreamer (Xie et al.) | CVPR 2024, arXiv 2309.00610 | OSM 배치와 높이 지도로 건물과 배경을 따로 생성 | V-World 건물과 정밀도로지도 배치를 조건으로 쓸 수 있는 구조 |
| UrbanWorld | arXiv 2407.11965 | OSM으로 형상을 만들고 diffusion으로 질감을 입힘 | V-World 박스 질감 생성 |
| DriveDreamer (Wang et al.) | ECCV 2024, arXiv 2309.09777 | 실제 주행 데이터로 만든 월드모델. 구조화된 교통 정보(지도, box), 문장, 주행 행동을 조건으로 주행 영상 생성. 후속 DriveDreamer-2는 궤적에서 HD map을 생성함 | 정밀도로지도를 교통 정보 조건으로 넣어 ADI 구간의 주행 영상 생성 |
| Panacea (Wen et al.) | CVPR 2024 | BEV 배치를 ControlNet 조건으로 넣어 다시점 주행 영상 생성. 후속 Panacea+ (arXiv 2408.07605) | 정밀도로지도 BEV 배치로 ADI 4방향 카메라 영상 생성 |
| BEVControl (Yang et al.) | arXiv 2308.01661 | 편집 가능한 BEV 스케치로 다시점 거리 영상 생성. 거리 시점과 BEV의 형상 일관성, 시점 간 외관 일관성을 따로 맞춤 | 지도 배치를 바꿔 다른 차로와 차량 배치 생성 |

> Cosmos-Drive-Dreams는 arXiv 번호가 2503.14492와 2506.09042 두 개로 나와 있어 인용 전 확인이 필요함

## 3. 스트릿뷰 이미지 기반

| 논문 | 학회 | 핵심 | ADI 적용 |
|---|---|---|---|
| Streetscapes (Deng et al.) | SIGGRAPH 2024, arXiv 2407.13759 | Google Street View 사진과 지도(도로 배치와 높이 지도)로 학습한 생성모델. 지도 배치를 따라 긴 주행 영상 생성 | Google 내부 데이터 사용. 공개 API로는 재현 불가 |
| Urban Radiance Fields (Rematas et al.) | CVPR 2022, arXiv 2111.14643 | 스트릿뷰 촬영 차량의 원본 데이터 사용 | 같은 이유로 공개 API로는 재현 불가 |

**스트릿뷰 사용 제약**

| 항목 | 내용 |
|---|---|
| 네이버 거리뷰 | 파노라마는 지도 JavaScript 뷰어 안에서만 표시됨. 이미지를 받는 API가 없고, 유료 요금은 뷰어 표시 비용임 |
| 네이버 약관 | 지도 약관 제7조(2025-03-20 시행)가 거리뷰 영상의 저장과 가공을 금지함. 사전 동의 시에만 예외 여지 |
| Google Street View | 이미지 API는 있으나 약관 3.2.3이 저장과 모델 학습용 가공을 금지함 |
| 학습 데이터로서의 한계 | 촬영 시기가 ADI(2019-11-27)와 달라 주차 차량, 잎, 그림자가 다름. 카메라 위치와 방향 정보가 없음 |

## 4. 지도와 위성영상에서 거리 시점 생성

위에서 본 자료(위성영상, 지도)로 거리 시점의 형상과 외관을 만드는 갈래. ADI가 지나가지 않은 곳이나 가려진 곳을 채우는 데 해당함

| 논문 | 학회 | 핵심 | ADI 적용 |
|---|---|---|---|
| Sat2Scene (Li et al.) | CVPR 2024, arXiv 2401.10786 | 위성영상에서 얻은 형상의 점에 3D diffusion으로 색을 입히고 neural rendering으로 거리 시점 렌더. 하늘은 별도 2D diffusion 파노라마 | V-World 정사영상과 건물 형상으로 ADI 밖 영역 외관 생성 |
| Sat2Density (Qian et al.) | ICCV 2023, arXiv 2303.14672 | 위성영상과 지상 사진 쌍으로 깊이 감독 없이 3D 밀도장을 학습해 지상 시점 합성. 후속 Sat2Density++ (arXiv 2505.17001)는 도시 장면 대상 | 위성영상과 ADI 사진 쌍으로 같은 방식 적용 가능 |
| Coming Down to Earth (Toker et al.) | CVPR 2021 | 위성영상에서 거리 시점을 합성하고 그 결과로 위치 추정 성능을 올림 | 합성과 정합을 한 모델로 묶는 예 |

## 5. 스트릿뷰나 지도와 주행 데이터 정합

주행 데이터의 카메라나 LiDAR를 지도 좌표에 맞추는 갈래. ADI LiDAR 궤적을 정밀도로지도와 V-World에 맞추는 단계에 해당함

| 논문 | 학회 | 핵심 | ADI 적용 |
|---|---|---|---|
| OrienterNet (Sarlin et al.) | CVPR 2023, arXiv 2304.02009 | 카메라 사진의 BEV 특징을 OpenStreetMap과 맞춰 위치와 방향을 1 m 미만 정확도로 추정. 3D 점군 없이 공개 지도만 씀 | ADI 카메라 pose를 지도 기준으로 점검하거나 보정 |
| MapLocNet (Wu et al.) | IROS 2024, arXiv 2407.08561 | 주변 카메라 BEV 특징과 내비게이션 지도를 거친 단계와 세밀한 단계로 정합. HD map 없이 위치 재추정 | 정밀도로지도가 없는 골목(forward40)에서 지도 정합 |
| VIGOR (Zhu et al.) | CVPR 2021, arXiv 2011.12172 | 거리 사진과 위성영상을 맞춰 위치를 m 단위로 추정하는 기준 데이터와 방법 | 거리 사진과 위성영상 정합의 기준 |
| OSM-aided LiDAR SLAM (Frontiers in Robotics and AI 2023) | Frontiers in Robotics and AI, 2023, doi 10.3389/frobt.2023.1064934 | LiDAR scan을 OpenStreetMap 건물 외곽과 맞춰 궤적을 보정하고, 지도 건물 위치가 틀린 곳도 찾음 | ADI LiDAR와 V-World 건물 외곽 정합. 지금 정합 확인(건물 벽 중앙값 0.46 m)의 자동화 |
| OPAL | arXiv 2504.19258 | LiDAR 점군을 OpenStreetMap 타일과 맞춰 장소를 인식. 가시성 mask로 시점 차이 처리 | LiDAR 기반 지도 위치 찾기 |

## 6. 새 시점 생성 후 3D로 증류

궤적 밖 시점 품질을 올리는 갈래. Genesis 추적 카메라에서 나무가 얼룩지는 문제에 해당함

| 논문 | 학회 | 핵심 |
|---|---|---|
| Difix3D+ (Wu et al.) | CVPR 2025, arXiv 2503.01774 | 새 시점 렌더를 한 단계 diffusion으로 보정하고 3D로 증류 |
| StreetCrafter (Yan et al.) | CVPR 2025, arXiv 2412.13188 | LiDAR 점을 새 시점에 투영한 이미지를 조건으로 영상 생성, Gaussian으로 증류 |
| DriveDreamer4D (Zhao et al.) | CVPR 2025, arXiv 2410.13571 | 주행 월드모델로 차로 변경 궤적 영상을 만들어 재구성 학습에 추가 |
| ReconDreamer | CVPR 2025, arXiv 2411.19548 | 렌더 잔상을 점진적으로 고치며 재학습. 최대 6 m 차로 이동 시점 |

## 7. 파이프라인 레퍼런스 (seq60)

| 항목 | 참고 논문 |
|---|---|
| 바닥 | RoGs (arXiv 2405.14342) |
| 건물 | CityDreamer (CVPR 2024, arXiv 2309.00610) |
| 인도 위 물체 | Urban Radiance Fields (CVPR 2022, arXiv 2111.14643) |
| 지도와 LiDAR 정합 | ICP (Besl and McKay, IEEE TPAMI 14(2), 1992) |
| 이미지 label | Mask2Former (CVPR 2022, arXiv 2112.01527), SAM 3 (arXiv 2511.16719) |
| 학습 | 2D Gaussian Splatting (SIGGRAPH 2024, arXiv 2403.17888), 3D Gaussian Splatting (SIGGRAPH 2023, arXiv 2308.04079), SuGaR (CVPR 2024, arXiv 2311.12775), Street Gaussians (ECCV 2024, arXiv 2401.01339), AutoSplat (ICRA 2025, arXiv 2407.02598) |
| 생성모델 | SDXL (ICLR 2024, arXiv 2307.01952), Latent Diffusion Models (CVPR 2022, arXiv 2112.10752), Difix3D+ (CVPR 2025, arXiv 2503.01774) |
| 시뮬레이션 | Genesis (GitHub Genesis-Embodied-AI/Genesis), Pure Pursuit (Coulter, CMU-RI-TR-92-01, 1992) |

## 8. ADI 구성에 가져올 것

| 우리 단계 | 참고 논문 | 가져올 점 |
|---|---|---|
| 바닥 | RoGs, AutoSplat | 도로 surfel 격자, 도로와 하늘 형상 제약 |
| 건물 | CityDreamer, UrbanWorld | V-World 박스에 생성 질감 입히기 (가려진 면, 높은 층) |
| 인도 위 물체 | Urban Radiance Fields | LiDAR 형상 감독, 노출 보정 |
| 궤적 밖 시점 | Difix3D+, StreetCrafter, ReconDreamer | 새 시점 생성, 보정, 재학습 |
| 월드모델 확장 | InfiniCube, Cosmos-Drive-Dreams | 정밀도로지도 투영 조건으로 날씨, 시간, 다른 차로 생성 |

## 서지 확인 상태

| 상태 | 논문 |
|---|---|
| 2026-11-11 검색으로 확인 | Urban Radiance Fields, RoGs, AutoSplat, InfiniCube, Cosmos-Drive-Dreams(번호 두 개), MagicDrive3D, CityDreamer, UrbanWorld, Streetscapes, StreetCrafter, DriveDreamer4D, ReconDreamer, Difix3D+, SAM 3, Street Gaussians, UniSim, Neural Map Prior, MagicDrive, 2D Gaussian Splatting, 3D Gaussian Splatting, SuGaR, Mask2Former, SDXL, Latent Diffusion Models, ICP, Pure Pursuit, DriveDreamer, Panacea(CVPR 수록 확인, arXiv 번호 미확인), BEVControl, Sat2Scene, Sat2Density, Coming Down to Earth, OrienterNet, MapLocNet, VIGOR, OSM-aided LiDAR SLAM, OPAL |
