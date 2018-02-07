#!/bin/bash
#SBATCH --partition=workq
#SBATCH --job-name="materstudio"
#SBATCH --nodes=1
#SBATCH --time=08:00:00
#SBATCH --exclusive
#SBATCH --error=std.err
#SBATCH --output=std.out


#----------------------------------------------------------#
echo "The job "${SLURM_JOB_ID}"_"${SLURM_ARRAY_TASK_ID}" is running on "${SLURM_JOB_NODELIST}
#----------------------------------------------------------#


ROOT=$PWD
TEMPLATE_DIR=$ROOT/TEMPLATES
TARGET=$ROOT/RUNS/$SLURM_ARRAY_TASK_ID

mkdir -p $TARGET

cd $TARGET

rsync -av $TEMPLATE_DIR/ $TARGET > rsync.out 2>&1

#DECIM SHOW_PARAMETERS > params.out  2> params.err
#DECIM PROCESS_TEMPLATE_FILES > template.out  2> template.err

echo castep should run for task=$SLURM_ARRAY_TASK_ID



# #----------------------------------------------------------#
# module load materstudio/8.0
# export OMP_NUM_THREADS=1

# export SeedName=MOF+GAS
# ${MATERSTUDIO_HOME}/etc/CASTEP/bin/RunCASTEP.sh -np 64 ${SeedName}

# #Resubmit the job if there is no ".cif" file created
# i=`ls -l | grep -c "castep_[0-9]"`
# if [ `grep -c "BFGS: WARNING - Geometry optimization failed to converge" ${SeedName}.castep` -ne 0 ]
# then
#  cp ${SeedName}.castep ${SeedName}.castep_${i}
#  i=$(( i + 1 ))
#  echo "resubmitting the job for the $i time."
#  if [ `grep -c "continuation =" ${SeedName}.param` -eq 0 ]
#  then
#   sed -i '1icontinuation = default' ${SeedName}.param
#  fi
#  sbatch z_jobs_shaheen_restarting
# fi















