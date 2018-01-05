====================
Using *Decimate*
====================

Via *Decimate*, four commands are added to the user environment:
**dbatch** to submit workflows, **dstat** to monitor their current
status, **dlog** to tail the log information produced and **dkill** to
cancel the execution of the workflow.
 

Submitting workflow
-------------------

*Decimate* **dbatch** command accepts the same `options`_ as the SLURM
**sbatch** command and extends it in two ways:

.. _options: https://slurm.schedmd.com/sbatch.html

 - it transparently submits the user job within a fauit-tolerant framework
 - it adds new options to manage the workflow execution if a problem occurs

   
   - ``--check=SCRIPT_FILE`` points to a user script (either in python or shell) to
     validate the correctness of the job at the end of its execution
   - ``--max-retry=MAX_RETRY`` setting number of time a step can fail
     and be restarted automatically before failing the whole workflow
     (3 per default)



How to submit
-------------

>>> print "This is a doctest block." 
This is a doctest block.
