====================
Using *Decimate*
====================

Via *Decimate*, four commands are added to the user environment:
**dbatch** to submit workflows, **dstat** to monitor their current
status, **dlog** to tail the log information produced and **dkill** to
cancel the execution of the workflow.
 
Supported Workflows
-------------------

For *Decimate*, a *workflow* is a set of jobs submitted from a same
directory. These jobs can depend on one another and be job array
of any size.

How job are named: *job_name-attempt-array*

Submitting a job 
-----------------

options
```````
*Decimate* **dbatch** command accepts the same options_ as the SLURM
**sbatch** command and extends it in two ways:

.. _options: https://slurm.schedmd.com/sbatch.html
 
 - it transparently submits the user job within a fauit-tolerant framework
 - it adds new options to manage the workflow execution if a problem occurs

   
   - ``--check=SCRIPT_FILE`` points to a user script (either in python or shell) to
     validate the correctness of the job at the end of its execution
   - ``--max-retry=MAX_RETRY`` setting number of time a step can fail
     and be restarted automatically before failing the whole workflow
     (3 per default)

single job
``````````

Here is how to submit a simple job:
::
    
   dbatch --job-name=job_1 my_job.sh

::

   [MSG  ] submitting job job_1 (for 1) --> Job # job_1-0-1 <-depends-on None 
   [INFO ] launch-0!0:submitting job job_1 [1] --> Job # job_1-0-1 <-depends-on None
   Submitted batch job job_1-0-1
   [1] --> Job # job_1-0-1 <-depends-on None

Notice how the command syntax is similar to **sbatch** command. 
   
  - In lines starting with ``[MSG]``, ``[INFO]``, or ``[DEBUG]``, *Decimate* gives us
    additional information about what is going on.

  - All the traces ``[INFO]``, or ``[DEBUG]`` also appears in the
    corresponding job output file as well as in *Decimate* central log
    file dumped in *<current_directory>/.decimate/LOGS/decimate.log*
    ``[MSG]`` traces only appears at the console or in the output
    file of the job.
    
  - for *Decimate*, every job is considered as a job array. In this
    simple case, it considers an array of job made of a single element
    ``1-1``. In the traces, the array indice shows in \"(for
    **1**)\", \"submitting job job_1 [**1**]\", or \"job
    job_1-0-**1**\".  (if needed check `SLURM job array
    documentation`_ for more information).

  - Every job submitted via *Decimate* is part of a fault-tolerant
    environment.  At the end of its execution, its correctness is
    systematically checked thanks to a user defined function or by
    default thanks the return code of the job given by SLURM.  If the
    job is not considered as correct, (and if the return code of the
    user-defined function is not *ABORT*), the job is automatically
    resubmitted for a first and a second attempt if needed.
    In the traces, the attempt number shows as the second figure in
    the job denomination:  \"job job_1-**0**-1\".
   

.. _SLURM job array documentation: https://slurm.schedmd.com/job_array.html

dependent job
`````````````

Here is how to submit a job dependending on a previous job:

::
   
   dbatch --dependency=job_1  --job-name=job_2 my_job.sh
   [INFO ] launch-0!0:Workflow has already run in this directory, trying to continue it
   [MSG  ] submitting job job_2 (for 1) --> Job # job_2-0-1 <-depends-on 218459 
   [INFO ] launch-0!0:submitting job job_2 [1] --> Job # job_2-0-1 <-depends-on 218459
   Submitted batch job job_2-0-1
   [1] --> Job # job_2-0-1 <-depends-on 218459

It again matches **sbatch** original syntax with the subtility that via *Decimate* dependency can be
expressed with respect to a previous job name and not only to a previous job id as **SLURM** only
allows it.

  - It makes it more convenient to write automated script.
  - At this submission time, *Decimate* checks if a previous submitted job has actually
    been submitted with this particular name. If not, an error will be issued and
    the submission is canceled.
  - Of course, dependency on a previous job id is also supported.


other kind of jobs
``````````````````
A comprehensive list of job examples can be found in `Examples of Workflows`_.

.. _Examples of Workflows: http:workflows.html

  
checking the status
-------------------

The current workflow status can be checked with **dstat**:


::
   
   dstat

When no job has been submitted from the current directory. **dstat** shows:

::

   [MSG  ] No workflow has been submitted yet

When jobs submitted submitted the current directory are currently running . **dstat** shows:
   
::
   
   [MSG  ] step job_1-0:1-1                  SUCCESS   SUCCESS:  100% 	FAILURE:   0% -> [] 
   [MSG  ] step job_2-0:1-1                  RUNNING   SUCCESS:    0% 	FAILURE:   0% -> [] 

And when a workflow is completed:
   
::

   dstat
   [MSG  ] CHECKING step : job_2-0 task 1  
   [MSG  ] step job_1-0:1-1                  SUCCESS   SUCCESS:  100% 	FAILURE:   0% -> [] 
   [MSG  ] step job_2-0:1-1                  SUCCESS   SUCCESS:  100% 	FAILURE:   0% -> []

   


  
Displaying the log file
-----------------------

The current *Decimate* log file can be checked with **dlog**:

::
   
   dlog


Cancelling the whole workflow
-----------------------------

The current workflow can be completly killed with the command **dkill**:

::
   
   dkill

If no job of the workflow is either running, queueing or waiting to be queued,
**dkill** prints:
   
::

   [INFO ] No jobs are currently running or waiting... Nothing to kill then!

If any job is still waiting or running, *dkill* asks a confirmation to the user and
cancels all jobs from the current workflow.

   
    
