===================
 What is Decimate?
===================

Developped by the KAUST Supercomputing Laboratory (KSL),
decimate is a SLURM extension written in python designed to handle
dependent jobs more easely and efficiently.

Decimate transparently adds parameters to SLURM sbatch command
to check the correctness of jobs and automatically
reschedules jobs found faulty.

Using Decimate, one can submit, run, monitor or
terminate a workflow composed of dependent jobs. If asked,
thanks to standardized or customized messages, the user will be
informed by mail of the progress of its workflow on the system.

In case of failure of one part of the workflow, decimate
automatically detects the failure, signals it to the user and
launches the misbehaving part after having fixed the job
dependency. By default if the same failure happens three
consecutive times, decimate cancels the whole workfow removing
all the depending jobs from the scheduling. In a next version,
decimate will allow the automatic restarting of the workflow
once the problem causing its failure has been cured.

.. image:: images/healing_workflow.png
	   
Decimate also allows the user to define his own mail alerts
that can be sent at any point of the workflow.

Some customized checking functions can also be designed by the
user. Their purpose is to validate if a step of the workflow
was succesful or not. It could involved checking for the
presence of some result files, grepping some error or success
messages in them, computing ratio or checksum... These
intermediate results can be easely transmitted to decimate
validating or not the correctness of any step. They can also be
forwarded by mail to the user where as the workflow is
executing.
