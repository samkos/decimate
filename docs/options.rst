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

--check=SCRIPT_FILE    python or shell to check if results are ok
--max-retry=MAX_RETRY  number of time a step can fail and be
                       restarted automatically before failing the 
                       whole workflow  (3 per default)

.. Execution in a container:

   -xy, --yalla               Use Yalla Container
   -xyp, --yalla-parallel-runs=YALLA_PARALLEL_RUNS  number  of parallel runs in a container

Burst Buffer:

-bbz, --use-burst-buffer-size  use a non persistent burst buffer space
-xz, --burst-buffer-size=BURST_BUFFER_SIZE  set Burst Buffer space size
-bbs, --use-burst-buffer-space      use a persistent burst buffer space
-xs, --burst-buffer-space=BURST_BUFFER_SPACE_name  sets Burst Buffer name


environment variables:

DPARAM                      options forwarded to Decimate

