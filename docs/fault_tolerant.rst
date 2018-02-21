========================
Fault-tolerant Workflows
========================

Adding a user-defined checking function
---------------------------------------

*Decimate* allows the user to define its own function to qualify a job as *ABORT*, *SUCCESS* or *FAILED*.
This can be a simple bash script file or a program written in Python. For example here is a typical script
*check_job.sh* written in shell checking if the message 'job DONE' appears in the job output file::

  job_step=$1
  attempt=$2
  task_id=$3
  running_dir=$4
  output_file=$5
  error_file=$5
  is_job_completed=$6


  echo job_step=$job_step  attempt=$attempt task_id=$task_id
  echo running_dir=$running_dir
  echo output_file=$output_file
  echo error_file=$error_file
  echo is_job_completed=$is_job_completed


  SUCCESS=0
  FAILURE=-1
  ABORT=-9999

  grep 'job DONE' $output_file


All the parameters are passed to the script as arguments added on the command line.

Succesful job submission
------------------------

When submitting the job, one only adds *--check* followed by the path of the checking job script

::

      dbatch --check=check_job.sh --job-name=job_1 my_job.sh

*my_job.sh* is the following job which will be checked as succesfull because echoing the string *job DONE*::

  #!/bin/bash
  #SBATCH -p debug
  #SBATCH -n 1
  #SBATCH -t 0:01:00
 
  
  echo job running on...
  hostname
  sleep 10
  
  echo job DONE

      
One can follows the current status of the workflow thanks to **dlog**
that displays the log file attached to the current workflow.

::

   dlog
   ()
   ================================================================================
   Currently Tailing ... 
    /home/kortass/DECIMATE-GITHUB/.decimate/LOGS/decimate.log
   		Hit CTRL-C to exit...		Hit CTRL-C to exit...
   ================================================================================
   ...
   [INFO ]  launch-0!0:submitting job 1 (for 1) --> Job # 1-0-1 <-depends-on None
   [INFO ]  launch-0!0:submitting job chk_1 (for 1) --> Job # chk_1-0-1 <-depends-on 1-0-1
   [INFO ]  chk_1-1!0: 	ok everything went fine for the step 1 (1) --> Step chk_1 (1) is starting... @ (2018-02-21 11:31:06)
   [INFO ]  chk_1-1!0:=============== workflow is finishing ============== @ (2018-02-21 11:31:09)


Failed job submission and automated restarting
----------------------------------------------

In the case of failure, here is what is observed when submitting a job that fails::

  dbatch --check=check_job.sh --job-name=job_1 my_job_failed.sh

*my_job_failed.sh* is the following job which will be checked as failed because echoing not the string *job DONE*::

  #!/bin/bash
    #SBATCH -p debug
  #SBATCH -n 1
  #SBATCH -t 0:01:00
 
  echo job running on...
  hostname

  echo job FAILED


which leads to the following results observed with the command  **dlog**
that displays the log file attached to the current workflow.

::

   dlog
   ()
   ================================================================================
   Currently Tailing ... 
    /home/kortass/DECIMATE-GITHUB/.decimate/LOGS/decimate.log
   		Hit CTRL-C to exit...		Hit CTRL-C to exit...
   ================================================================================
   ...
   [INFO ]  launch-0!0:submitting job 1f (for 1) --> Job # 1f-0-1 <-depends-on None
   [INFO ]  launch-0!0:submitting job chk_1f (for 1) --> Job # chk_1f-0-1 <-depends-on 1f-0-1
   [INFO ]  1f-1!0:User error detected!!! for step 1f  attempt 0 : (1)
   [INFO ]  chk_1f-1!0:User error detected!!! for step 1f  attempt 0 : (1)
   [INFO ]  chk_1f-1!0:!!!!!!!! oooops pb : job missing or uncomplete at last step 1f : (1)
   [INFO ]  chk_1f-1!0:RESTARTING THE WRONG PART PREVIOUS JOB : 1f (1). current_attempt=0 initial_attempt=0 Extra attempt #1 ( 1 out of 3) @ (2018-02-21 12:39:04)
   [INFO ]  chk_1f-1!0:submitting job 1f (for 1) --> Job # 1f-1-1 <-depends-on None
   [INFO ]  chk_1f-1!0:submitting job chk_1f (for 1) --> Job # chk_1f-0-1 <-depends-on 219553
   [INFO ]  chk_1f-1!0:Job has been fixed and is restarting @ (2018-02-21 12:39:05)
   [INFO ]  1f-1!1:User error detected!!! for step 1f  attempt 1 : (1)
   [INFO ]  chk_1f-1!0:User error detected!!! for step 1f  attempt 1 : (1)
   [INFO ]  chk_1f-1!0:!!!!!!!! oooops pb : job missing or uncomplete at last step 1f : (1)
   [INFO ]  chk_1f-1!0:RESTARTING THE WRONG PART PREVIOUS JOB : 1f (1). current_attempt=1 initial_attempt=0 Extra attempt #2 ( 2 out of 3) @ (2018-02-21 12:39:18)
   [INFO ]  chk_1f-1!0:submitting job 1f (for 1) --> Job # 1f-2-1 <-depends-on None
   [INFO ]  chk_1f-1!0:submitting job chk_1f (for 1) --> Job # chk_1f-0-1 <-depends-on 219555
   [INFO ]  chk_1f-1!0:Job has been fixed and is restarting @ (2018-02-21 12:39:19)
   [INFO ]  1f-1!2:User error detected!!! for step 1f  attempt 2 : (1)
   [INFO ]  chk_1f-1!0:User error detected!!! for step 1f  attempt 2 : (1)
   [INFO ]  chk_1f-1!0:!!!!!!!! oooops pb : job missing or uncomplete at last step 1f : (1)
   [INFO ]  chk_1f-1!0:RESTARTING THE WRONG PART PREVIOUS JOB : 1f (1). current_attempt=2 initial_attempt=0 Extra attempt #3 ( 3 out of 3) @ (2018-02-21 12:39:33)
   [INFO ]  chk_1f-1!0:submitting job 1f (for 1) --> Job # 1f-3-1 <-depends-on None
   [INFO ]  chk_1f-1!0:submitting job chk_1f (for 1) --> Job # chk_1f-0-1 <-depends-on 219557
   [INFO ]  chk_1f-1!0:Job has been fixed and is restarting @ (2018-02-21 12:39:34)
   [INFO ]  1f-1!3:User error detected!!! for step 1f  attempt 3 : (1)
   [INFO ]  chk_1f-1!0:User error detected!!! for step 1f  attempt 3 : (1)
   [INFO ]  chk_1f-1!0:!!!!!!!! oooops pb : job missing or uncomplete at last step 1f : (1)
   [INFO ]  chk_1f-1!0:RESTARTING THE WRONG PART PREVIOUS JOB : 1f (1). current_attempt=3 initial_attempt=0 Extra attempt #4 ( 4 out of 3) @ (2018-02-21 12:39:46)
   [INFO ]  chk_1f-1!0:Too much failed attempt for step 1f my_joid is 219558 @ (2018-02-21 12:39:46)
   [INFO ]  chk_1f-1!0:killing all the dependent jobs...
   [INFO ]  chk_1f-1!0:killing all the dependent jobs...
   [INFO ]  chk_1f-1!0:3 jobs to kill...
   [INFO ]  chk_1f-1!0:killing the job 219552 (step chk_1f-0)...
   [INFO ]  chk_1f-1!0:killing the job 219554 (step chk_1f-0)...
   [INFO ]  chk_1f-1!0:killing the job 219556 (step chk_1f-0)...
   [INFO ]  chk_1f-1!0:=============== workflow is aborting ==============
   [INFO ] launch-0!0:=============== workflow is finishing ==============


Setting the number of restart
-----------------------------

   
The faulty job is restarted automatically three times before *Decimate* declares the workflow as aborted. Restarting
faulty job three times before aborting is the value set per default. It can be changed by adding *--max-retry=<your_value>*
when submitting the job::

    dbatch --max-retry=1 --check=check_job.sh --job-name=job_1 my_job_failed.sh

In this case *Decimate* only restarts the faulty job once, after two successive failed attempts::

   dlog
   ()
   ================================================================================
   Currently Tailing ... 
    /home/kortass/DECIMATE-GITHUB/.decimate/LOGS/decimate.log
   		Hit CTRL-C to exit...		Hit CTRL-C to exit...
   ================================================================================
   ...
   [INFO ]  launch-0!0:submitting job 1f (for 1) --> Job # 1f-0-1 <-depends-on None
   [INFO ]  launch-0!0:submitting job chk_1f (for 1) --> Job # chk_1f-0-1 <-depends-on 1f-0-1
   [INFO ]  1f-1!0:User error detected!!! for step 1f  attempt 0 : (1)
   [INFO ]  chk_1f-1!0:User error detected!!! for step 1f  attempt 0 : (1)
   [INFO ]  chk_1f-1!0:!!!!!!!! oooops pb : job missing or uncomplete at last step 1f : (1)
   [INFO ]  chk_1f-1!0:RESTARTING THE WRONG PART PREVIOUS JOB : 1f (1). current_attempt=0 initial_attempt=0 Extra attempt #1 ( 1 out of 1) @ (2018-02-21 12:44:53)
   [INFO ]  chk_1f-1!0:submitting job 1f (for 1) --> Job # 1f-1-1 <-depends-on None
   [INFO ]  chk_1f-1!0:submitting job chk_1f (for 1) --> Job # chk_1f-0-1 <-depends-on 219561
   [INFO ]  chk_1f-1!0:Job has been fixed and is restarting @ (2018-02-21 12:44:54)
   [INFO ]  1f-1!1:User error detected!!! for step 1f  attempt 1 : (1)
   [INFO ]  chk_1f-1!0:User error detected!!! for step 1f  attempt 1 : (1)
   [INFO ]  chk_1f-1!0:!!!!!!!! oooops pb : job missing or uncomplete at last step 1f : (1)
   [INFO ]  chk_1f-1!0:RESTARTING THE WRONG PART PREVIOUS JOB : 1f (1). current_attempt=1 initial_attempt=0 Extra attempt #2 ( 2 out of 1) @ (2018-02-21 12:45:09)
   [INFO ]  chk_1f-1!0:Too much failed attempt for step 1f my_joid is 219562 @ (2018-02-21 12:45:09)
   [INFO ]  chk_1f-1!0:killing all the dependent jobs...
   [INFO ]  chk_1f-1!0:killing all the dependent jobs...
   [INFO ]  chk_1f-1!0:1 jobs to kill...
   [INFO ]  chk_1f-1!0:killing the job 219560 (step chk_1f-0)...
   [INFO ]  chk_1f-1!0:=============== workflow is aborting ==============
   [INFO ] launch-0!0:=============== workflow is finishing ==============

