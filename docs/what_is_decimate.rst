=====================
 What is *Decimate*?
=====================

Developped by the KAUST Supercomputing Laboratory (KSL), *Decimate* is
a SLURM extension written in Python allowing the user to handle jobs
per hundreds in an efficient and transparent way. In this context, the
constraint limiting the number of jobs per users is completely
masked. The time consuming burden of managing thousands of jobs by
hand is also alleviated by making available to the user the concept of
workflow gathering a set of jobs that he can manipulate as a whole.

*Decimate* is released as an Open Source Software under BSD Licence.
It is available at 

Features
--------

*Decimate* allows a user to:

- Submit any number of jobs regardless of any limitation set in the
  scheduling policy on the maximum number of jobs authorized per user.
- Manage all the submitted jobs as a single workflow easing their
  submission, monitoring, deletion or reconfiguration.
- Ease the definition, submission and management of jobs
  run on a large set of combinations of parameters.
- Benefit from a centralized log file,  a unique point of
  capture of relevant information about the behavior of the workflow.
  From Python or shell, at any time and from any jobs,
  the logging levels info, debug, console and mail are available.
- Send fully-configurable mail messages detailing the
  current completion of the workflow at any step of its execution.  
- Easily define a procedure (in shell or Python) to check for
  correctness of the results obtained at the end of given step. Having
  access to the complete current status of the workflow, this
  procedure can make the decision on-the-fly either
  to stop the whole workflow, to resubmit partially the failing
  components as is, or to modify it dynamically.

Automated restart in case of failure
------------------------------------
  
In case of failure of one part of the workflow, *Decimate*
automatically detects the failure, signals it to the user and
launches the misbehaving part after having fixed the job
dependency. By default if the same failure happens three
consecutive times, *Decimate* cancels the whole workfow removing
all the depending jobs from the scheduling. In a next version,
*Decimate* will allow the automatic restarting of the workflow
once the problem causing its failure has been cured.

.. image:: images/healing_workflow.png

Fully user configurable environment
-----------------------------------
	   
*Decimate* also allows the user to define his own mail alerts
that can be sent at any point of the workflow.

Some customized checking functions can also be designed by the
user. Their purpose is to validate if a step of the workflow
was succesful or not. It could involved checking for the
presence of some result files, grepping some error or success
messages in them, computing ratio or checksum... These
intermediate results can be easely transmitted to *Decimate*
validating or not the correctness of any step. They can also be
forwarded by mail to the user where as the workflow is
executing.
