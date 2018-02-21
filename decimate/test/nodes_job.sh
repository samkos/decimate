#!/bin/bash
#SBATCH --job-name=nodes
#SBATCH --time=00:1:00 

ROOT=$PWD
TARGET=$ROOT/RUNS/${x}_${y}_${x}_nodes_${nodes}_ntasks_${ntasks}

mkdir -p $TARGET
cd $TARGET

#DECIM SHOW_PARAMETERS

echo should run  srun -n ${ntasks} hostname
srun -n ${ntasks} hostname

echo job DONE

