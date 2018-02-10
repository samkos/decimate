NAME

       decimate - a fault-tolerant SLURM scheduler extension

SYNOPSIS

       dbatch [ Slurm options ] [ --check <user_script> ]
                                [ --max-retry=<number of restart> ]
                                script [args...]

DESCRIPTION

       Developped by the KAUST Supercomputing Laboratory (KSL),
       decimate is a SLURM extension written in python designed to handle
       dependent jobs more easely and efficiently.

       Decimate transparently adds parameters to SLURM sbatch command
       to check the correctness of jobs and automatically
       reschedules jobs found faulty.

       Using Decimate on Shaheen II, one can submit, run, monitor or
       terminate a workflow composed of dependent jobs. If asked,
       thanks to standardized or customized messages, the user will be
       informed by mail of the progress of its workflow on the system.

       In case of failure of one part of tne workflow, decimate
       automatically detects the failure, signals it to the user and
       launches the misbehaving part after having fixed the job
       dependency. By default if the same failure happens three
       consecutive times, decimate cancels the whole workfow removing
       all the depending jobs from the scheduling. In a next version,
       decimate will allow the automatic restarting of the workflow
       once the problem causing its failure has been cured.

       decimate also allows the user to define his own mail alerts
       that can be sent at any point of the workflow through a call to
       a python method. This feature will also be available from bash
       in a next version.

       Some customized checking functions can also be designed by the
       user. Their purpose is to validate if a step of the workflow
       was succesful or not. It could involved checking for the
       presence of some result files, grepping some error or success
       messages in them, computing ratio or checksum... These
       intermediate results can be easely transmitted to decimate
       validating or not the correctness of any step. They can also be
       forwarded by mail to the user where as the workflow is
       executing.

USE

       At this moment, jobs only need to be submitted through the
           dbatch
       command that accepts exactely the same parameters as the
       original SLURM sbatch command plus the new parameters
       
                --check=SCRIPT_FILE
		               where SCRIPT_FILE  is a python
		               or shell script
			       to check if results are ok.

                 --max-retry=MAX_RETRY
		               number of time a step can fail and be
                               restarted automatically before failing the 
                               whole workflow  (3 per default)

       sslog tails out the decimate logging file attached to the
       current directory, tracking all the jobs that were launched
       with dbatch from this directory.

       sstatus gives the current status of the workflow excecuting
       in the current directory.
       
       Decimate is still in a beta phase and under test with some of
       our KSL users. More documentations will be provided once the
       stabilized and fully tested version is made available by the
       end of June 2018.

       If interested in testing decimate or contributing, please send
       a mail to help@hpc.kaust.edu.sa

AUTHOR

       Written by Samuel Kortas (samuel.kortas (at) kaust.edu.sa)

REPORTING BUGS

       Report decimate bugs to help@hpc.kaust.edu.sa


COPYRIGHT
       Copyright (c) 2017, KAUST Supercomputing Laboratory
       All rights reserved.

       Redistribution and use in source and binary forms, with or without
       modification, are permitted provided that the following conditions are met:

       * Redistributions of source code must retain the above copyright notice, this
         list of conditions and the following disclaimer.

       * Redistributions in binary form must reproduce the above copyright notice,
         this list of conditions and the following disclaimer in the documentation
         and/or other materials provided with the distribution.

       THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
       AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
       IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
       DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
       FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
       DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
       SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
       CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
       OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
       OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

SEE ALSO

       decimate official documentation pages:
                <http://http://decimate.readthedocs.io>
		
       KAUST Supercomputing Laboratory: <http://hpc.kaust.edu.sa/>
