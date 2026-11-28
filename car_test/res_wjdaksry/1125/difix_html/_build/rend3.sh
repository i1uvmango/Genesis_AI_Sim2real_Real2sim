#!/bin/bash
R=/home/diglab/workspace/workspace/instant_nurec; D=$R/results/alpamayo/058bf960/alpamayo_full_clip; MK=$D/track_mask_v3/mask_v3.npz; M=$R/shm_backup_20261123/alpamayo_v3/model
PY=$R/adi_quality_20261018/wall_overnight_20261023/pgsr_env/bin/python; TP=$R/adi_quality_20261018/depth_normal_campaign_20261025/training/2dgs_deps
C=$(pwd)
G="BLOCK=40 NLAB=40 ALLFR=1 GTAG=L000_199V3 SAMPLES_DIR=$M MESHBASE=$D/collider_v3/collider.ply GEOM=mesh_dome_world.ply CARMASK=1 SHADOW=0 OUTDIR=$C/out CMF=$MK DYNX=$MK DYNALL=1 PYTHONPATH=$TP"
echo "$(date +%T) under1k"; env $G LOADCOL=$M/colors_2dgs_v3_startfix.npz RENDER_POSES=$C/viewer_poses.json TAG=_viewerD3 $PY s3x.py 2dgs 1 > log_vd.txt 2>&1 || { echo FAIL_U; exit 1; }
echo "$(date +%T) DONE"
