#ml decimate/sk
#gC
d -y -b 1 -e 5 --nopending
ds -d
ds
d --kill -y -d
d -s -d

dss


d -y -b 1 -e 3 --nopending --fake

d -y -b 1 -e 3 --nopending --fake


export SLURM_ARRAY_TASK_ID=1
export SLURM_ARRAY_JOB_ID=99

export PATH=/home/kortass/DECIMATE/:/opt/slurm/share/bin:/opt/slurm/share/sbin/:/opt/slurm/bin:/opt/slurm/sbin/:/home/kortass/SWAN/bin:/home/kortass/liclipse:/home/kortass/ABDOU/opt/bin:/home/kortass/opt/bin:/opt/slurm/bin/:/opt/slurm/sbin/:/home/kortass/public_html/drupal-modules/drush:/home/kortass/OpenFOAM/BUILD_wk/ThirdParty-2.3.1/build/linux64Gcc/ParaView-4.1.0/bin:/home/kortass/OpenFOAM/BUILD_wk/ThirdParty-2.3.1/platforms/linux64Gcc/gperftools-svn/bin:/home/kortass/OpenFOAM/BUILD_wk/ThirdParty-2.3.1/platforms/linux64Gcc/ParaView-4.1.0/bin:/home/kortass/OpenFOAM/BUILD_wk/ThirdParty-2.3.1/platforms/linux64Gcc/cmake-2.8.12.1/bin:/home/kortass/OpenFOAM/kortass-2.3.1/platforms/linux64GccDPOpt/bin:/home/kortass/OpenFOAM/BUILD_wk/site/2.3.1/platforms/linux64GccDPOpt/bin:/home/kortass/OpenFOAM/BUILD_wk/OpenFOAM-2.3.1/platforms/linux64GccDPOpt/bin:/home/kortass/OpenFOAM/BUILD_wk/OpenFOAM-2.3.1/bin:/home/kortass/OpenFOAM/BUILD_wk/OpenFOAM-2.3.1/wmake:/home/kortass/opt/bin:/home/kortass/bin:/home/kortass/SWTOOLS/swtools-1.0/bin:/home/kortass/liclipse:/home/kortass/ABDOU/opt/bin:/opt/slurm/bin/:/opt/slurm/sbin/:/home/kortass/public_html/drupal-modules/drush:/usr/lib/lightdm/lightdm:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games 
export LD_LIBRARY_PATH=/home/kortass/DECIMATE/:/home/kortass/DECIMATE//lib:/opt/slurm/share/lib/:/home/kortass/SWAN/lib:/home/kortass/ABDOU/opt/lib:/home/kortass/OpenFOAM/BUILD_wk/ThirdParty-2.3.1/platforms/linux64Gcc/CGAL-4.3/lib:/home/kortass/OpenFOAM/BUILD_wk/ThirdParty-2.3.1/platforms/linux64Gcc/gperftools-svn/lib:/home/kortass/OpenFOAM/BUILD_wk/ThirdParty-2.3.1/platforms/linux64Gcc/ParaView-4.1.0/lib/paraview-4.1:/home/kortass/OpenFOAM/BUILD_wk/OpenFOAM-2.3.1/platforms/linux64GccDPOpt/lib/openmpi-system:/home/kortass/OpenFOAM/BUILD_wk/ThirdParty-2.3.1/platforms/linux64GccDPOpt/lib/openmpi-system:/usr/lib/openmpi/lib:/home/kortass/OpenFOAM/kortass-2.3.1/platforms/linux64GccDPOpt/lib:/home/kortass/OpenFOAM/BUILD_wk/site/2.3.1/platforms/linux64GccDPOpt/lib:/home/kortass/OpenFOAM/BUILD_wk/OpenFOAM-2.3.1/platforms/linux64GccDPOpt/lib:/home/kortass/OpenFOAM/BUILD_wk/ThirdParty-2.3.1/platforms/linux64GccDPOpt/lib:/home/kortass/OpenFOAM/BUILD_wk/OpenFOAM-2.3.1/platforms/linux64GccDPOpt/lib/dummy:/home/kortass/opt/bin:/home/kortass/ABDOU/opt/lib 
export DECIMATE_PATH=/home/kortass/DECIMATE/ 
export PYTHONPATH=/tmp:/home/kortass/DECIMATE/.dart_mitgcm/SAVE:/home/kortass/DECIMATE/ 
cp /home/kortass/DECIMATE/.dart_mitgcm/SAVE/*py* /tmp 
sleep 1
 python /tmp/run_test.py --step 2 --attempt 0 --log-dir /home/kortass/DECIMATE/.dart_mitgcm/LOGS    --spawned --taskid ${SLURM_ARRAY_TASK_ID},1 --jobid ${SLURM_ARRAY_JOB_ID} --max-retry=3 --workflowid='dart_mitgcm at 1478585138 3692 '  --check-previous-step=1,1  --fake
