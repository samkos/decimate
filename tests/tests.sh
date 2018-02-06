mmld
ml maestro/1.6
#cp $DECIMATE_PATH/maestro_jobs/* .
#ftn -o prog.exe a_mpi.f
ml dart_mitgcm/.maestro
python testexe.py -h
python testexe.py --cores=24 --restart --account=k01 --tasks-per-job=12 --debug --debuglogger --debugjobs
python testexe.py --cores=128 --restart --account=k01 --tasks-per-job=8 --nocleaning
--debug

cd /lustre/scratch/kortass/HABIB/maestro; 
bash STUDY/LOGS/job.cmd 17 nid01040 9032     323   = LOGGER_ADDRESS


ml dart_mitgcm/decimate_only
gC
db -o 1.%j.out -e 1.%j.err -J 1 tests/my_job.sh 
db -o 2.%j.out -e 2.%j.err -J 2 tests/my_job.sh 
db -o 3.%j.out -e 3.%j.err -J 3 --dependency 2 tests/my_job.sh 
db -o 4.%j.out -e 4.%j.err -J 4 --dependency 3 tests/my_job.sh 
db -o 5.%j.out -e 5.%j.err -J 5 --dependency 4 tests/my_job.sh 
b

b


#error when --error
db -f API,PS -P tests/error_pb_params.sh tests/error_pb_job.sh

# running a test case with dependency and failure
ml dart_mitgcm/decimate_only
gC
export DPARAM="-f API --test tests/pbx2.txt --fake"
gC
export DPARAM="-f UNCONSISTENT --test tests/pbx2.txt --fake"

gC
export DPARAM="-f STATUS_DETAIL --test tests/pbx2.txt --fake"

gC
export DPARAM=" --test tests/pbx2.txt --fake"
db -a 1-3 -J 1 tests/my_job.sh ;db -a 1-3 -J 2 --dependency 1 tests/my_job.sh ; db -a 1-3 -J 3 --dependency 2 tests/my_job.sh ; db -a 1-3 -J 4 --dependency 3 tests/my_job.sh ; db -a 1-3 -J 5 --dependency 4 tests/my_job.sh 
sl
sl
sa    
# error


gC
db -a 1-3 -J 1 tests/my_job.sh  --decimate --test tests/pbx2.txt --fake -f API,USER_CHECK
db -a 1-3 -J 2 --dependency 1 tests/my_job.sh --decimate --test tests/pbx2.txt --fake -f API,USER_CHECK
db -a 1-3 -J 3 --dependency 2 tests/my_job.sh --decimate --test tests/pbx2.txt --fake -f API,USER_CHECK
db -a 1-3 -J 4 --dependency 3 tests/my_job.sh --decimate --test tests/pbx2.txt --fake -f API,USER_CHECK
db -a 1-3 -J 5 --dependency 4 tests/my_job.sh --decimate --test tests/pbx2.txt --fake -f API,USER_CHECK
sl

sca; gC; d -y -b 1 -e 4 --scratch -a 1-3 


DPARAM='-f PARSE' db -o 1.%j.out -e 1.%j.err -J 1 tests/my_job.sh  

# test erreur de soumission --time missing: not working killing all workflow @decimate:2268
# What should be the right behavior? it will be reached only when the job get activated...
ml dart_mitgcm/decimate_only
gC
db -o 1.%j.out -e 1.%j.err -J 1 tests/my_job.sh 
db -o 2.%j.out -e 2.%j.err -J 2 tests/my_job.sh 
db -o 3.%j.out -e 3.%j.err -J 3 --dependency 2 tests/my_job.sh 
db -o 4.%j.out -e 4.%j.err -J 4 --dependency 3 tests/my_job.sh 
db tests/es_no_time.sh
db -o 5.%j.out -e 5.%j.err -J 5 --dependency 4 tests/my_job.sh 
b

# debugging final checking job
gC; db -f SUBMIT -o 1.%j.out -e 1.%j.err -J 1 tests/my_job.sh
gC; db -f SUBMIT_JOB,JOBS,WRAP,ACTIVATE,SUBMIT,SUBMITTED -o 1.%j.out -e 1.%j.err -J 1 tests/my_job.sh
gC; db -f PARSE,SUBMIT_JOB,JOBS,WRAP,ACTIVATE,SUBMIT,SUBMITTED -o 1.%j.out -e 1.%j.err -J 1 tests/my_job.sh
gC; db -f PARSE,CHECK_FINAL -o 1.%j.out -e 1.%j.err -J 1 tests/my_job.sh

gC; db -o 1.%j.out -e 1.%j.err -J 1 tests/my_job_fail.sh ; dl
gC; db -f CRITICAL,HEAL,PARSE -o 1.%j.out -e 1.%j.err -J 1 --max-retry=2 tests/my_job_fail.sh; dl
gC; db -f CRITICAL -o 1.%j.out -e 1.%j.err -J 1 --max-retry=2 tests/my_job_fail.sh; dl



# working on moving job parsing
ml dart_mitgcm/decimate_only
gC
db -o 4.%j.out -e 4.%j.err -J 4 --dependency 3 tests/my_job.sh --decimate -f PARSE

# testing array
ml dart_mitgcm/decimate_only
gC
db -a 1-90 -o 1.%j.out -e 1.%j.err -J 1_a tests/my_job.sh --decimate -xj 10 -xr 0 
db -a 1-90 -o 1.%j.out -e 1.%j.err -J 1_a tests/my_job.sh --decimate -xj 10 -xr 0 -f FEED_DETAIL,

# testing yalla
ml dart_mitgcm/decimate_only
gC
db -N 1 -f YALLA -a 1-30 --yalla tests/my_job.sh my_job_no_wait.sh


db -a 1-10 -N 1 -c 32 -o 1.%j.out -e 1.%j.err -J 1 --yalla tests/my_job.sh --decimate  -f SUBMIT_JOB
db -f YALLA -a 1-10 -o 1.%j.out -e 1.%j.err -J 1 --yalla tests/my_job.sh 

# testing BB
ml dart_mitgcm/decimate_only
gC
db -o 1.%j.out -e 1.%j.err -J 1 -bbz tests/my_job.sh --decimate 

# testing user script to check
gC
db -J 1 --check=tests/check_job.sh tests/my_job_no_wait.sh
ds
dl
db -f USER_CHECK --check=tests/check_job.sh -J 3 tests/my_job_no_wait.sh

db -f USER_CHECK --check=tests/check_job.sh -a 1-90 -J 4 tests/my_job_no_wait.sh 


# testing parameter file
gC;
db -a 1-2 -P tests/my_params.txt tests/my_job_params.sh
db -f PARAMETRIC -a 1-2 -P tests/my_params.txt tests/my_job_params.sh
db -f PARAMETRIC_DETAIL -a 1-2 -P tests/my_params.txt tests/my_job_params.sh
db -f PARAMETRIC_DETAIL -a 1-2 -P tests/anamika_params.txt tests/my_job_params.sh
db -f PARAMETRIC_SUMMARY -a 1-2 -P tests/anamika_params.txt tests/my_job_params.sh
db  -a 1-2 -P tests/anamika_params.txt tests/my_job_params.sh
db  -a 1-2 -P tests/anamika_params_errors.txt tests/my_job_params.sh
db  -f PARAMETRIC_DETAIL -a 1-2 -P tests/loop_params.txt tests/my_job_params.sh
db  -f PARAMETRIC_SUMMARY -a 1-2 -P tests/loop_params.txt tests/my_job_params.sh
db  -a 1-2 -P tests/loop_params.txt tests/my_job_params.sh
db  -a 1-2 -P tests/loop_params_error.txt tests/my_job_params.sh

db  -f PARAMETRIC_PROG,PARAMETRIC_SUMMARY -a 1-2 -P tests/prog_params.txt tests/my_job_params.sh
db  -f PARAMETRIC_PROG_DETAIL,PARAMETRIC_SUMMARY -a 1-2 -P tests/prog_params.txt tests/my_job_params.sh
db  -f PARAMETRIC_SUMMARY -a 1-2 -P tests/prog_params.txt tests/my_job_params.sh
db  -a 1-2 -P tests/prog_params.txt tests/my_job_params.sh

db  -f PARAMETRIC_SUMMARY -a 1-2 -P tests/prog_params_error.txt tests/my_job_params.sh
db  -f PARAMETRIC_SUMMARY -a 1-2 -P tests/prog_params_error2.txt tests/my_job_params.sh

db  -f PARAMETRIC_DETAIL,PARAMETRIC_SUMMARY -a 1-2 -P tests/combine_params.txt tests/my_job_params.sh
db  -f PARAMETRIC_SUMMARY -a 1-2 -P tests/combine_params.txt tests/my_job_params.sh

python
import subprocess
cmd='/home/kortass/DECIMATE-GITHUB/tests/check_job.sh 1 0 1 /home/kortass/DECIMATE-GITHUB 1.218470.out.task_0001-attempt_0 1.218470.err.task_0001-attempt_0 True/'
proc = subprocess.Popen(cmd, shell=True, bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
proc.wait()
print "\n".join(proc.stdout.readlines())
print proc.returncode

# status
python slurm_frontend.py --decimate 

# test no job output or error
db tests/my_job.sh --decimate --filter JOB_OUTERR

# test restart

ml dart_mitgcm/decimate_only
gC; d -y -xy -e 7 -a 1-5
d -r2 3 -a 1-5 -e 7


\rm 6* 5* 7*
(cd .decimatest; tar xvf ARCHIVE/4-0-ok.20170625-07:49:50.tgz)
d -e 7 -y
 


# kill test with yalla

gC; d -xy --no

mpirun -n 4 .decimatests/SAVE/yalla.exe './my_job.sh %d' 10 1
cat yalla.%j.out

ml dart_mitgcm/decimate_only 
gC; d -y -xy -e 7 -np; sleep 1; d -k -y -f KILL
gC; d -y -xy -e 7 -a 1-5



# testing submission cmd line
ml dart_mitgcm/decimate_only 
db -o 1.%j.out -J 1 edbad.sh -y -i --banner
db -o 2.%j.out -J 2 --dependency 1 -t 0:00:10 my_job.sh -y -i --banner
tail -f .decimate/LOGS/decimate.log


db -o 1.%j.out -J 1 edbad.sh -y 
db -o 2.%j.out -J 2 --dependency 1 -t 0:00:10 my_job.sh -y 
tail -f .decimate/LOGS/decimate.log



#ml decimate/sk
#gC
d -y -b 1 -e 5 --no-pending
ds -d
ds
d --kill -y -d
d -s -d

dss


python run_test.py -y -b 1 -e 3 --nopending --fake

python run_test.py -y -b 1 -e 3 --nopending --fake


gC
python run_test.py -y -b 1 -e 5  --test=tests/pbx2.txt --fake

python run_test.py --feed





python run_test.py -y -b 1 -e 5 --no-pending --scratch -a 1-50





-ii 





sca; gC; d -y -b 1 -e 4 --scratch -a 1-15 --test tests/pbx2.txt --fake
0




rm .decimatest/SAVE/Complete* .decimatest/SAVE/Done*; python /tmp/run_test.py --step 2 --attempt 0 --log-dir /home/kortass/DECIMATE/.decimatest/LOGS    --spawned --taskid 3,3 --jobid 109420 --max-retry=3 --workflowid='decimatest at 1484128774 3584 ' --test tests/pbx2.txt  --check-previous-step=1,3  --fake

qq



STEPS={'1-0': {'completion': 100.0,
         'items': 1.0,
         'jobs': [111680],
         'status': 'DONE',
         'success': 100.0,
         'tasks': '1-1'},
 '2-0': {'completion': 100.0,
         'items': 1.0,
         'jobs': [111681],
         'status': 'DONE',
         'success': 100.0,
         'tasks': '1-1'},
 '2-1': {'completion': 100.0,
         'items': 1.0,
         'jobs': [11168],
         'status': 'DONE',
         'success': 100.0,
         'tasks': '1-1'},
 '3-0': {'completion': 100.0,
         'items': 1.0,
         'jobs': [111682],
         'status': 'DONE',
         'success': 0,
         'tasks': '1-1'},
 'xxx123-0': {'completion': 100.0,
              'items': 1.0,
              'jobs': [111679],
              'status': 'DONE',
              'success': 0,
              'tasks': '1-1'}}

map(lambda k: k[0].split('-')[:-1],STEPS.items())

