====================
Using *Decimate*
====================

Via *Decimate*, four commands are added to the user environment:
**dbatch** to submit workflows, **dstat** to monitor their current
status, **dlog** to tail the log information produced and **dkill** to
cancel the execution of the workflow.
 

Submitting workflow
-------------------

*Decimate* **dbatch** command accepts the same options_ as the SLURM
**sbatch** command and extends it in two ways:

.. _options: 

 - it transparently submits the user job within a fauit-tolerant framework
 - it adds new options to manage the workflow execution if a problem occurs

   
   - ``--check=SCRIPT_FILE`` points to a user script (either in python or shell) to
     validate the correctness of the job at the end of its execution
   - ``--max-retry=MAX_RETRY`` setting number of time a step can fail
     and be restarted automatically before failing the whole workflow
     (3 per default)



How to submit
-------------

Let *my_job.sh* be the following example job:

::

  #!/bin/bash
  #SBATCH -n 1
  #SBATCH -t 0:05:00
   

  echo job running on...
  hostname
  sleep 10

  echo job DONE

If not done yet, we first load the *Decimate* module:  

::

   module load decimate

Then submission of jobs follows the same syntax than with the **sbatch** command:   
   
::
    
   dbatch --job-name=job_1 my_job.sh

::

   [MSG  ] submitting job job_1 (for 1) --> Job # job_1-0-1 <-depends-on None 
   [INFO ] launch-0!0:submitting job job_1 [1] --> Job # job_1-0-1 <-depends-on None
   Submitted batch job job_1-0-1
   [1] --> Job # job_1-0-1 <-depends-on None

::
   
   dbatch --dependency=job_1  --job-name=job_2 my_job.sh
   [INFO ] launch-0!0:Workflow has already run in this directory, trying to continue it
   [MSG  ] submitting job job_2 (for 1) --> Job # job_2-0-1 <-depends-on 218459 
   [INFO ] launch-0!0:submitting job job_2 [1] --> Job # job_2-0-1 <-depends-on 218459
   Submitted batch job job_2-0-1
   [1] --> Job # job_2-0-1 <-depends-on 218459

::
   
   dstat

::
   
   [MSG  ] step job_1-0:1-1                  SUCCESS   SUCCESS:  100% 	FAILURE:   0% -> [] 
   [MSG  ] step job_2-0:1-1                  RUNNING   SUCCESS:    0% 	FAILURE:   0% -> [] 

::

   dstat
   [MSG  ] CHECKING step : job_2-0 task 1  
   [INFO ] launch-0!0:no active job in the queue, changing all WAITING in ABORTED???
   [MSG  ] step job_1-0:1-1                  SUCCESS   SUCCESS:  100% 	FAILURE:   0% -> [] 
   [MSG  ] step job_2-0:1-1                  SUCCESS   SUCCESS:  100% 	FAILURE:   0% -> [] 


