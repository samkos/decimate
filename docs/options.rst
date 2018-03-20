===========
 Shell API
===========



dbatch
------

Usage: dbatch [OPTIONS...] job_script [args...]

Help:

-h, --help                show all possible options for **dbatch**
-H, --decimate-help       show hidden option to manage *Decimate* engine


Workflow management:
       --kill                 kill all jobs in the workflow either RUNNING, PENDING or WAITING
       --resume               resume  the already launched step and workflow in this directory
       --restart              restart the already launched step or workflow in this directory

       -ch, --check                  check the step at its end (job DONE printed)
       -chf, --check-file=SCRIPT_FILE python or shell to check if results are ok
       -xj, --max-jobs=MAX_JOBS      maximum number of jobs to keep active in the
                               queue  (450 per default)
       -xr, --max-retry=MAX_RETRY   number of time a step can fail and be
                               restarted automatically before failing the 
                               whole workflow  (3 per default)

        -xj, --max-jobs=MAX_JOBS      maximum number of jobs to keep active in the
                                 queue  (450 per default)
        -xr, --max-retry=MAX_RETRY    number of time a step can fail and be
                                 restarted automatically before failing the 
                                 whole workflow  (3 per default)

			       
.. Execution in a pool:

   -xy, --yalla               Use Yalla Pool
   -xyp, --yalla-parallel-runs=YALLA_PARALLEL_RUNS  number  of parallel runs in a pool

Burst Buffer:

-bbz, --use-burst-buffer-size  use a non persistent burst buffer space
-xz, --burst-buffer-size=BURST_BUFFER_SIZE  set Burst Buffer space size
-bbs, --use-burst-buffer-space      use a persistent burst buffer space
-xs, --burst-buffer-space=BURST_BUFFER_SPACE_name  sets Burst Buffer name


dstat
-----

Usage: dstat [OPTIONS...] 

Help:

-h, --help                show all possible options for **dstat**


dlog
----

Usage: dlog [OPTIONS...] 

Help:

-h, --help                show all possible options for **dlog**



dkill
-----

Usage: dkill [OPTIONS...] 

Help:

-h, --help                show all possible options for **dkill**


environment variables
---------------------

environment variable forwarded to *Decimate* and setting option per default that will be added to
any *Decimate* command initiated from the shell::
  
  DPARAM       

code to return when a job is considered as *Succesfull*::
  
  0                   

code to return when a job is considered as *Failed*::
  
  -1           

code to return when a workflow has to be immediately stopped::
  
  -9999                


Job script directives
---------------------

in script directives (to be added as-is anywhere in a SLURM job script).

To show the parameters set in the job environment from a parametic file processed via *Decimate*::
  
  #DECIM SHOW_PARAMETERS

To process all the files ending by *.template* and replacing any
  parameter (typically *__Name_of_parameter__*) with a value coming
  from the parametric file processed by *Decimate*.::

  #DECIM PROCESS_TEMPLATE_FILES 
