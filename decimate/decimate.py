#!/sw/xc40/python/2.7.11/sles11.3_gnu5.1.0/bin/python

import argparse
from contextlib import contextmanager
import copy
from engine import *
from env import TMPDIR
import fnmatch
import itertools
import math
import os
import pandas as pd
import pprint
import shlex
from stat import *
import sys
import termios


DECIMATE_VERSION = '0.9.2'
RSYNC_CMD = "timeout 60 bash -c 'until time srun -N ${SLURM_NNODES} --ntasks=${SLURM_NNODES} " + \
            "--ntasks-per-node=1 rsync %s /tmp; do > /dev/null :; done  > /dev/null 2>&1' \n"

SUCCESS = True
FAILURE = False
ABORT = -9999

HELP_MESSAGE = """
Usage: dbatch [OPTIONS...] executable [args...]

Parallel run options:
  -a, --array=indexes         job array index values
  -A, --account=name          charge job to specified account
      --bb=<spec>             burst buffer specifications
      --begin=time            defer job until HH:MM MM/DD/YY
  -M, --clusters=names        Comma separated list of clusters to issue
                              commands to.  Default is current cluster.
                              Name of 'all' will submit to run on all clusters.
      --comment=name          arbitrary comment
      --cpu-freq=min[-max[:gov]] requested cpu frequency (and governor)
  -c, --cpus-per-task=ncpus   number of cpus required per task
  -d, --dependency=type:jobid defer job until condition on jobid is satisfied
  -D, --workdir=directory     set working directory for batch script
  -e, --error=err             file for batch script's standard error
      --export[=names]        specify environment variables to export
      --export-file=file|fd   specify environment variables file or file
                              descriptor to export
      --get-user-env          load environment from local cluster
      --gid=group_id          group ID to run job as (user root only)
      --gres=list             required generic resources
  -H, --hold                  submit job in held state
      --ignore-pbs            Ignore #PBS options in the batch script
  -i, --input=in              file for batch script's standard input
  -I, --immediate             exit if resources are not immediately available
      --jobid=id              run under already allocated job
  -J, --job-name=jobname      name of job
  -k, --no-kill               do not kill job on node failure
  -L, --licenses=names        required license, comma separated
  -m, --distribution=type     distribution method for processes to nodes
                              (type = block|cyclic|arbitrary)
      --mail-type=type        notify on state change: BEGIN, END, FAIL or ALL
      --mail-user=user        who to send email notification for job state
                              changes
  -n, --ntasks=ntasks         number of tasks to run
      --nice[=value]          decrease scheduling priority by value
      --no-requeue            if set, do not permit the job to be requeued
      --ntasks-per-node=n     number of tasks to invoke on each node
  -N, --nodes=N               number of nodes on which to run (N = min[-max])
  -o, --output=out            file for batch script's standard output
  -O, --overcommit            overcommit resources
  -p, --partition=partition   partition requested
      --parsable              outputs only the jobid and cluster name (if present),
                              separated by semicolon, only on successful submission.
      --power=flags           power management options
      --priority=value        set the priority of the job to value
      --profile=value         enable acct_gather_profile for detailed data
                              value is all or none or any combination of
                              energy, lustre, network or task
      --propagate[=rlimits]   propagate all [or specific list of] rlimits
      --qos=qos               quality of service
  -Q, --quiet                 quiet mode (suppress informational messages)
      --reboot                reboot compute nodes before starting job
      --sicp                  If specified, signifies job is to receive
      --signal=[B:]num[@time] send signal when time limit within time seconds
      --switches=max-switches{@max-time-to-wait} Optimum switches and max time
                              to wait for optimum
      --requeue               if set, permit the job to be requeued
  -t, --time=minutes          time limit
      --time-min=minutes      minimum time limit (if distinct)
  -s, --share                 share nodes with other jobs
  -S, --core-spec=cores       count of reserved cores
      --uid=user_id           user ID to run job as (user root only)
  -v, --verbose               verbose mode (multiple -v's increase verbosity)
      --wckey=wckey           wckey to run job under
      --wrap                  wrap commmand string in a sh script and submit

Constraint options:
      --contiguous            demand a contiguous range of nodes
  -C, --constraint=list       specify a list of constraints
  -F, --nodefile=filename     request a specific list of hosts
      --mem=MB                minimum amount of real memory
      --mincpus=n             minimum number of logical processors (threads)
                              per node
      --reservation=name      allocate resources from named reservation
      --tmp=MB                minimum amount of temporary disk
  -w, --nodelist=hosts...     request a specific list of hosts
  -x, --exclude=hosts...      exclude a specific list of hosts

Consumable resources related options:
      --exclusive             allocate nodes in exclusive mode when
                              cpu consumable resource is enabled
      --mem-per-cpu=MB        maximum amount of real memory per allocated
                              cpu required by the job.
                              --mem >= --mem-per-cpu if --mem is specified.

Affinity/Multi-core options: (when the task/affinity plugin is enabled)
  -B,  --extra-node-info=S[:C[:T]]            Expands to:
       --sockets-per-node=S   number of sockets per node to allocate
       --cores-per-socket=C   number of cores per socket to allocate
       --threads-per-core=T   number of threads per core to allocate
                              each field can be 'min' or wildcard '*'
                              total cpus requested = (N x S x C x T)

      --ntasks-per-core=n     number of tasks to invoke on each core
      --ntasks-per-socket=n   number of tasks to invoke on each socket


Help options:
  -h,   --help                show this help message
  -H,   --decimate-help       show Decimate help message
  -f,   --filter=FILTERS      activate traces
                              API, PARSE, USER_CHECK

Parametric Jobs:
  -P,  --parameter-file=PARAM_FILE file listing all parameter
                                          combinations to cover
  -Pl, --parameter-list lists all parameters combination to scan and exit

  -Pf, --parameter-filter=FILTER filter while reading parameter file
  -Pa, --parameter-range=range numeric filter while reading parameter file

Containers:
  -xy,  --yalla               Use Yalla Container
  -xyp, --yalla-parallel-runs=YALLA_PARALLEL_RUNS  number 
                              of parallel runs in a container


Burst Buffer:
  -bbz, --use-burst-buffer-size        use a non persistent burst buffer space
  -xz,  --burst-buffer-size=BURST_BUFFER_SIZE
  -bbs, --use-burst-buffer-space      use a persistent burst buffer space
  -xs,  --burst-buffer-space=BURST_BUFFER_SPACE_name

Checking option:
        --check=SCRIPT_FILE      python or shell to check if results are ok
        --max-retry=MAX_RETRY    number of time a step can fail and be
                                 restarted automatically before failing the 
                                 whole workflow  (3 per default)

Other options:
  -V, --version               output version information and exit

environment variables:
  DPARAM                      options forwarded to Decimate
xxxxxxxxxxxx
      """


@contextmanager
def working_directory(directory):
    owd = os.getcwd()
    try:
        os.chdir(directory)
        yield directory
    finally:
        os.chdir(owd)


class decimate(engine):

  def __init__(self, app_name='decimate', app_version='???',
               decimate_version_required=DECIMATE_VERSION, extra_args=False):

    self.DECIMATE_VERSION = DECIMATE_VERSION
    self.APPLICATION_NAME = app_name
    self.APPLICATION_VERSION = app_version

    self.JOBS_DEPENDS_ON = {}

    #self.DECIMATE_DIR = os.getenv('DECIMATE_PATH')
    self.DECIMATE_DIR = os.path.dirname(os.path.abspath(__file__))
    self.TEMPLATE_SOURCE_DIR = "%s/templates" % self.DECIMATE_DIR
    self.YALLA_DIR = "%s/yalla" % self.DECIMATE_DIR

    if not(hasattr(self, 'FILES_TO_COPY')):
        self.FILES_TO_COPY = []
    for f in ['decimate.py', 'engine.py', 'env.py', 'slurm_frontend.py',
              'decimate.pyc', 'engine.pyc', 'env.pyc', 'slurm_frontend.pyc']:
        self.FILES_TO_COPY = self.FILES_TO_COPY + ['%s/%s' % (self.DECIMATE_DIR, f)]

        

    # checking
    self.check_python_version()
    self.check_decimate_version(decimate_version_required)
    self.STEPS_RESTART_STATUS = {}
    self.STEPS_RESTART_ATTEMPT = {}

    self.steps_to_restart_anyway = []

    # slurm parser variable
    self.slurm_parser = None
    self.slurm_options = {}

    # debugging variable
    self.in_kill_worflow = False
    self.jobs_queued = 'not yet computed'
    self.jobs_waiting = 'not yet computed'
    self.heal_workflow_started = False

    engine.__init__(self, engine_version_required='0.23', app_name=app_name,
                    app_version=app_version, extra_args=extra_args)

    self.FEED_LOCK_FILE = "%s/feed_lock" % self.LOG_DIR
    self.MAIL_DIR = "%s/kortass/decimate_buffer/" % TMPDIR
    if not(os.path.exists(self.MAIL_DIR)):
      self.log_info("creating mail directory %s" % self.MAIL_DIR)
      os.system("mkdir -p %s; chmod 777 %s; chmod o+t %s; chmod o+t %s/.." % 
                (self.MAIL_DIR, self.MAIL_DIR, self.MAIL_DIR, self.MAIL_DIR))
    self.MAIL_LOCK_FILE = "%s/lock" % self.MAIL_DIR

    # files to save into local /tmp/ directory

    self.files_to_copy_to_tmp = []

  #########################################################################
  # welcome message
  #########################################################################
  def welcome_message(self, print_header=True, print_cmd=True):
    """welcome message"""

    if print_header and self.args.banner:
      print()
      print("          ########################################")
      print("          #                                      #")
      print("          # Welcome to %11s v %6s!#" % 
            (self.APPLICATION_NAME, self.APPLICATION_VERSION))
      print("          #   (using DECIMATE Framework %3s)     #" % self.DECIMATE_VERSION)
      print("          #                                      #")
      print("          ########################################")
      print("       ")

    engine.welcome_message(self, print_header=False, print_cmd=print_cmd)

  #########################################################################
  # checking methods
  #########################################################################
  def check_decimate_version(self, version):
    current = int(("%s" % self.DECIMATE_VERSION).split('.')[1])
    asked = int(("%s" % version).split('.')[1])
    if (asked > current):
        self.error("Current Decimate version is %s while requiring %s, please fix it!"
                   % (current, asked))
  #########################################################################
  # starting the dance
  #########################################################################

  def start(self):

    self.log_debug('[Decimate:start] entering', 4, trace='CALL')
    engine.start(self)
    self.run()

  #########################################################################
  # check for tne option on the command line
  #########################################################################
  def initialize_parser(self):
    engine.initialize_parser(self)

    # self.log_debug('[Decimate:initialize_parser] entering',4,trace='CALL')

    self.parser.add_argument("-l", "--log", action="store_true",
                             help='display and tail current log')
    self.parser.add_argument("-s", "--status", action="store_true",
                             help='list status of jobs and of the workflow')
    self.parser.add_argument("-sa", "--status-all", action="store_true",
                             help='list status of all the jobs of the workflow')
    self.parser.add_argument("-sl", "--status-long", action="store_true",
                             help='list detailed status of jobs of the workflow')
    self.parser.add_argument("-k", "--kill", action="store_true",
                             help='kills job of this workflow')
    self.parser.add_argument("-c", "--cont", action="store_true",
                             help='continue the already launched workflow in this directory',
                             default=True)
    self.parser.add_argument("-sc", "--scratch", action="store_true",
                             help='relaunch a new workflow, erasing all from the previous one',
                             default=False)

    self.parser.add_argument("-x", "--explore", action="store_true",
                             help='start a console to explore the results', default=False)

    # fake option to separate option targetted at decimate from the slurm frontend

    self.parser.add_argument("--decimate", action="store_true",
                             help=argparse.SUPPRESS)
    self.parser.add_argument("--check", type=str,
                             help=argparse.SUPPRESS)
    self.parser.add_argument("-pe", "--print-environment", action="store_true", default=False,
                             help="print environment variables in job output file")

    # send key to console
    self.parser.add_argument("--input", type=str, default="", help=argparse.SUPPRESS)

    self.parser.add_argument("--finalize", action="store_true", help=argparse.SUPPRESS)

    # option to run test case
    self.parser.add_argument("--test", type=str, help=argparse.SUPPRESS)
    self.parser.add_argument("--fake-pause", type=int, help=argparse.SUPPRESS)

    self.parser.add_argument("-j", "--job_status", action="store_true",
                             help=argparse.SUPPRESS)

    # internal decimate flags
    self.parser.add_argument("--spawned", action="store_true",
                             help=argparse.SUPPRESS)
    self.parser.add_argument("--check-previous-step", action="store_true",
                             help=argparse.SUPPRESS, default=False)
    self.parser.add_argument("--step", default='launch', type=str,
                             help=argparse.SUPPRESS)
    self.parser.add_argument("--taskid", type=str,
                             help=argparse.SUPPRESS)
    self.parser.add_argument("--jobid", type=int,
                             help=argparse.SUPPRESS)
    self.parser.add_argument("--attempt", type=int, default=0,
                             help=argparse.SUPPRESS)
    self.parser.add_argument("--attempt-initial", type=int, default=0,
                             help=argparse.SUPPRESS)
    self.parser.add_argument("--array-first", type=int,
                             help=argparse.SUPPRESS)
    self.parser.add_argument("--workflowid", type=str, default="0",
                             help=argparse.SUPPRESS)

    # temporary fixes to deal with heavy/huge workflows to overcome the saving
    # of global context
    self.parser.add_argument("-ql", "--quick-launch", action="store_true",
                             help='launches jobs quicky only saving state at the end',
                             default=False)
    self.parser.add_argument("--quick-launch-no-load", action="store_true",
                             help='launches jobs quicky only saving state at the end',
                             default=False)

    # Force checking of jobs
    self.parser.add_argument("--force-check", action="store_true",
                             help=argparse.SUPPRESS, default=False)
    self.parser.add_argument("-ncls", "--no-clear-screen", action="store_true",
                             help='do not clear the screen in the console', default=False)

    self.parser.add_argument("-y", "--yes", action="store_true",
                             help=argparse.SUPPRESS, default=False)
    self.parser.add_argument("--no", action="store_true",
                             help=argparse.SUPPRESS, default=False)

    self.parser.add_argument("--feed", action="store_true",
                             help=argparse.SUPPRESS, default=False)
    self.parser.add_argument("--fix", action="store_true",
                             help=argparse.SUPPRESS, default=False)
    self.parser.add_argument("--ufix", action="store_true",
                             help=argparse.SUPPRESS, default=False)
    self.parser.add_argument("--forward-mail", action="store_true",
                             help=argparse.SUPPRESS, default=False)

    # ease of use of decimate
    self.parser.add_argument("--template", action="store_true",
                             help='create template files')
    self.parser.add_argument("--process-templates", type=str, 
                             help=argparse.SUPPRESS)
    if not(self.user_initialize_parser() == 'default'):
            # hidding some engine options
        self.parser.add_argument("--create-template", action="store_true",
                                 help='Download all the template files in the current directory')

    self.parser.add_argument("--all", action="store_true", default=False,
                             help=argparse.SUPPRESS)

    if not(self.user_initialize_parser() == 'default'):
            # hidding some engine options
        self.parser.add_argument("-r", "--reservation", type=str,
                                 help='run in the given reservation name')
        self.parser.add_argument("-p", "--partition", type=str,
                                 help='set the default partition')

    self.parser.add_argument("-r2", "--rollback", type=str,
                             help='rollback to step xxx')
    self.parser.add_argument("-rl", "--rollback-list", action="store_true", default=False,
                             help='list available step to rollback to')

    self.parser.add_argument("-xr", "--max-retry", type=int, default=3,
                             help='Number of time a step can fail successively (3 per default)')
    self.parser.add_argument("-xj", "--max-jobs", type=int, default=450,
                             help='Maximimum jobs queued at a time (450 per default)')

    self.parser.add_argument("-sc", "--stripe-count", type=int, default=0,
                             help='stripe count set for new directory created (0 per default)')

    self.parser.add_argument("-xa", "--all-released", action="store_true",
                             help='do release all the job of a step.', default=False)

    self.parser.add_argument("-xy", "--yalla", action="store_true",
                             help='Use yalla container', default=False)
    self.parser.add_argument("-xyp", "--yalla-parallel-runs", type=int,
                             help='# of job to run in parallel in a container', default=4)
    self.parser.add_argument("-xyf", "--parameter-file", type=str,
                             help='file listing all parameter combinations to cover')

    self.parser.add_argument("-bbz", "--use-burst-buffer-size", action="store_true",
                             help='Use a non persistent burst buffer space', default=False)
    self.parser.add_argument("-bbs", "--use-burst-buffer-space", action="store_true",
                             help='Use a non persistent burst buffer space', default=False)
    self.parser.add_argument("-xz", "--burst-buffer_size", type=str,
                             help='use a non persistent burst buffer space of size',
                             default='80TiB')
    self.parser.add_argument("-xs", "--burst-buffer-space", type=str,
                             help='name of the persistent burst buffer space used',
                             default='Tst01')

  #########################################################################
  # check for tne option on the command line defined by the user
  # (stub)
  #########################################################################
  def user_initialize_parser(self):
      return 'default'

  #########################################################################
  # create template (matrix and job)
  #########################################################################
  def create_template_files(self, template_source_dir=False):

    if not(template_source_dir):
        template_source_dir = self.TEMPLATE_SOURCE_DIR

    for cur, _dirs, files in os.walk(template_source_dir):
      cur = cur.replace(template_source_dir, '')
      filename = './%s' % cur
      dirname = os.path.dirname(filename)
      if not(os.path.exists(dirname)):
        self.log_info("creating dir %s" % dirname)
        os.makedirs(dirname)
      for f in files:
        filename = '%s/%s' % (dirname, f)
        if os.path.exists(filename):
          print("\tfile %s already exists... skipping it!" % filename)
        else:
          source = '%s/%s' % (template_source_dir, f)
#           print(source)
          content = "".join(open(source, "r").readlines())
          f = open(filename, "w")
          f.write(content)
          f.close()
          self.log_info("file %s created " % filename)

    sys.exit(0)

    for filename_content in l.split("__SEP1__"):
      filename, content = filename_content.split("__SEP2__")
      if os.path.exists(filename):
        print("\t file %s already exists... skipping it!" % filename)
      else:
        if filename[-1] == "*":
          filename = filename[:-1]

  #########################################################################
  # Main loop:
  #   large switch leading to all possible action
  #########################################################################

  def run(self):

    self.log_debug('[Decimate:run] entering', 4, trace='CALL')
    # self.args.max_retry = 0
    # if not(self.args.spawned):
    #   self.log_console('ZZZZZZZZZ!!!!!!! max_retry is set to 0 ')

    if hasattr(self, 'init_jobs'):
        self.error('recable: --> function init_jobs which is now obsolete', exit=True)

    self.set_mail_subject_prefix('Re: %s' % (self.args.workflowid))

    self.currently_healing_workflow = False

    if self.args.max_jobs < 8:
        self.error("maximumm jobs in the queue should be at least of 8", exit=True)

    self.chunk_size = min(self.args.max_jobs / 2, 100)

    if self.args.template:
      self.create_template_files()
      sys.exit(0)

    if self.args.use_burst_buffer_size and not(self.args.burst_buffer_size):
        self.error('Wanting to use Burst Buffer? please precise which space ' + 
                   'with --burst-buffer-size argument',
                   exit=True)

    if self.args.use_burst_buffer_space and not(self.args.burst_buffer_space):
        self.error('Wanting to use Burst Buffer? please precise which space ' + 
                   'with --burst-buffer-space argument',
                   exit=True)

    # initialization of some parameters appearing in traces

    if self.args.yalla:
        makefile_name = "%s/Makefile.%s" % (self.YALLA_DIR, self.machine)
        yalla_exe = "%s/YALLA/yalla.exe" % (self.SAVE_DIR)
        if not(os.path.exists(yalla_exe)):
          if not os.path.isfile(makefile_name):
              self.error("yalla not available on %s ... \
                     no makefile %s available for this type of machine"
                         % (self.machine, makefile_name), exit=True)

          # compilation of yalla
          self.log_console('Compiling Yalla...', trace='YALLA')
          cmd = ("mkdir -p %s/YALLA; cd %s/YALLA; cp %s/yalla.c .; " + 
                 "make -f %s > %s/yalla_compile.out 2>&1") % \
                (self.SAVE_DIR, self.SAVE_DIR, self.YALLA_DIR, makefile_name, self.LOG_DIR)
          self.log_debug('Compile cmd = \n%s' % cmd, 3, trace='YALLA')
          output = os.system(cmd)
          self.log_debug('%s' % output, 3, trace='YALLA')

        if not(os.path.exists(yalla_exe)):
          self.error('could not compile yalla successfully\n output=\n%s' % output,
                     exit=True, exception=True)

    # reading of the parameter file
    if self.args.parameter_file:
          self.read_parameter_file()
            
    if self.args.taskid:
      try:
        args = self.args.taskid.split(',')
        self.TASK_ID = int(args[0])
        self.TASK_IDS = args[1]
      except Exception:
        self.error('pb in reading taskid', exception=True, exit=True)
        self.TASK_ID = 1
        self.TASK_IDS = '1-1'
    else:
        self.TASK_ID = 0
        self.TASK_IDS = '1-1'

    # process template file
    if self.args.process_templates:
          self.process_templates(self.args.process_templates)
          sys.exit(0)
            
    if self.args.array_first:
      self.MY_ARRAY_CURRENT_FIRST = int(self.args.array_first)

    self.set_log_prefix("%s-%s!%s" % (self.args.step, self.TASK_ID, self.args.attempt))

    # initialization of mail feature

    if self.args.mail:
      self.init_mail()

    # in case of testing mode, reads the scenario file that will simulate a use case
    # to run

    if self.args.test:
      self.read_scenario_file()
      if not(self.args.fake):
          self.error('To use a test file, the --fake option has to be set', exit=True)
    else:
      if not(self.args.spawned):
          self.log_debug('no test scenario!!!')
      self.SCENARIO = ""

    #
    # Main loop of possible actions
    #

    if self.args.rollback_list:
      self.rollback_list(from_console=True)
      sys.exit(0)

    if self.args.rollback:
      self.rollback_workflow(self.args.rollback)
      # sys.exit(0)

    if self.args.kill:
      self.kill_workflow()
      sys.exit(0)

    if self.args.feed:
      self.feed_workflow()
      sys.exit(0)

    if self.args.explore:
      self.args.no_fix_unconsistent = True
      self.explore_workflow()
      sys.exit(0)

    if self.args.fix:
      self.fix()
      sys.exit(0)

    if self.args.ufix:
      self.user_fix()
      sys.exit(0)

    if self.args.forward_mail:
      self.forward_mail()
      sys.exit(0)

    if self.args.status or self.args.status_long or self.args.status_all:
      self.print_workflow()
      if not(self.args.log):
          sys.exit(0)

    if self.args.log:
      self.tail_log_file(keep_probing=True, no_timestamp=True, nb_lines_tailed=5,
                         stop_tailing=['workflow is finishing',
                                       'workflow is aborting'])
      self.log_info('=============== workflow is finishing ==============')
      sys.exit(0)

    if self.args.finalize:
      self.finalize()
      sys.exit(0)

    if self.args.check_previous_step and self.args.parameter_file and self.args.spawned:
      param_file = '/tmp/parameters.%s' % self.TASK_ID
      task_parameter_file = open(param_file, "w")
      params = self.parameters.iloc[self.TASK_ID]
      task_parameter_file.write('# set parameter from file %s for task %s' % \
                                (self.args.parameter_file, self.TASK_ID))
      s = ""
      for p in self.parameters.columns:
        task_parameter_file.write('\nexport %s=%s' % (p, params[p]))
        s = s + "%s=>%s< " % (p, params[p])
        
      #task_parameter_file.write('\necho Current Parameters[%s]: "%s"' % (self.TASK_ID, s))
      
      task_parameter_file.write('\n')
      task_parameter_file.close()
      self.log_debug('file %s created' % param_file, 4, trace='PARAMETRIC,PARAMETRIC_DETAIL')
      
    if self.args.check_previous_step:
      lock_file = self.take_lock(self.FEED_LOCK_FILE)
      self.load()
      if not(self.args.jobid in self.JOBS.keys()):
        self.error(('strange, while checking if dependency exists, ' + 
                    'my own job-id %s is not known in self.JOBS... ' + 
                    'self.args.check_previous_step=%s') % 
                   (self.args.jobid, self.args.check_previous_step),
                   exit=False, exception=True)
      else:
        my_job = self.JOBS[self.args.jobid]
        dep_jobid = my_job['dependency']
        step = self.STEPS[my_job['step']]
        self.log_info('status of the current step %s: %s ' % 
                      (step['job_name'], self.print_job(step, step.keys())),
                      2, trace='COMPUTE_CHECK,CURRENT')

        if dep_jobid and my_job['check_previous']:
          dep = self.JOBS[dep_jobid]
          self.CHECK_STEP = step_to_check = dep['step']
          self.CHECK_TASK_IDS = array_to_check = dep['array']
          dep_dep_jobid = dep['dependency']
          # moving back to the dependency till a check_previous is set again
          if dep_dep_jobid and not(dep['check_previous']):
            dep_dep = self.JOBS[dep_dep_jobid]
            array_to_check = RangeSet('%s,%s' % (dep_dep['array'], array_to_check))
          self.CHECK_TASK_IDS = array_to_check
          self.compute_critical_path()
          self.log_debug('while checking step=%s attempt=%s' % \
                         (step_to_check, array_to_check), 4, \
                         trace='HEAL,RESTART,CHECK,COMPUTE_CHECK')
          self.log_debug('self.steps_submitted_attempts=%s' % \
                         pprint.pformat(self.steps_submitted_attempts), 4, \
                         trace='RESTART,HEAL,CHECK,COMPUTE_CHECK')
          step = "-".join(step_to_check.split("-")[:-1])
          if step in self.steps_submitted_attempts.keys():
            attempts_done = self.steps_submitted_attempts[step]
            step_to_check = "%s-%s" % (step, attempts_done)
            array_to_check = self.STEPS[step_to_check]['initial_array']
            self.CHECK_ATTEMPT = attempts_done
            self.log_debug(('should check step %s (%s) attempt %s, ' + \
                           'STEPS.keys=%s self.steps_submitted_attempts=%s') % \
                           (step_to_check, array_to_check, attempts_done, \
                            ",".join(self.STEPS.keys()), \
                            pprint.pformat(self.steps_submitted_attempts)), \
                           4, trace='CHECK_SHORT')
            self.log_console("\n" + self.system('ls -l %s.*-attempt_* ' % step))
            self.log_debug('should check step %s (%s) attempt %s: %s' % \
                           (step_to_check, array_to_check, attempts_done, \
                            pprint.pformat(self.STEPS[step_to_check])), \
                           4, trace='COMPUTE_CHECK,CHECK,WHAT_CHECK')
            self.check_current_state(step, attempts_done, tasks=RangeSet(array_to_check))
            self.save()
      self.release_lock(lock_file)

      self.feed_workflow()
      sys.exit(0)


    if self.args.job_status:
      self.get_current_jobs_status()
      sys.exit(0)

    s = 'starting Task %s-%s (out of %ss Job_id=%s) ' % \
        (self.args.step, self.args.taskid, self.TASK_IDS, self.args.jobid)
    self.log_info(s, 2)

    self.send_mail('%s' % s, 2)

    self.load()

    if self.args.fake and self.args.step and self.args.spawned:
        self.fake_actual_job()

    if not(self.args.spawned):
      if len(self.jobs_list) > 0 and self.args.cont:
          # self.ask("Adding jobs to the current workflow? ", default='y' )
          self.log_debug('Workflow has already run in this directory, trying to continue it', \
                         4, trace='WORKFLOW')
      elif len(self.jobs_list) > 0 and self.args.scratch:
          self.ask("Forgetting the previous workflow and starting from scratch? ", default='n')
          self.clean()
          if os.path.exists(self.WORKSPACE_FILE):
              os.unlink(self.WORKSPACE_FILE)

      elif len(self.jobs_list) > 0:
          print("""
                ----------> <      WARNING     > <--------------
                Some workflow has already been launched from this
                    directory and may be still running

                   following options :
                   --kill     to kill the ongoing workflow
                              and keep previous results
                   --status   to obtain a detailed status on
                              ongoing workflow
                   --cont     to add jobs to the current
                              worklfow.
                   --scratch  to kill an eventual ongoing
                              workflow and start a new one
                              from scratch, deleting any
                              tracking information about the
                              previous workflow
                Please modify your command
                ---------->  END OF COMMAND   <-------------
                """)
          sys.exit(0)
      print(self.launch_jobs())

    try:
      if self.TASK_ID == RangeSet(self.TASK_IDS)[-1] and not(self.currently_healing_workflow):
        if not(self.JOBS[self.args.jobid]['make_depend']):
            self.log_info('Normal end of this batch')
            self.log_info('=============== workflow is finishing ==============')
            if self.args.mail:
                self.send_mail('Workflow has just completed successfully')
    except Exception:
        self.error("ZZZZZZZZ problem in decimate main loop ", exit=False, exception=True)
        self.log_info("problem in decimate main loop -> JOBS=\n%s " % 
                      pprint.pformat(self.JOBS).replace('\\n', '\n'))

        pass

  #########################################################################
  # print workflow
  #########################################################################

  def print_workflow(self, all_steps=False):

    self.get_current_jobs_status()
    self.compute_critical_path()

    if len(self.STEPS) == 0:
        self.log_console('No workflow has been submitted yet from this directory')

    if self.args.status_long or self.args.status_all or all_steps:
      steps = self.steps_in_order
    else:
      steps = self.steps_critical_path_with_attempt

    self.log_info('in print_wokflow steps[%s] ' % ",".join(steps), 1, trace='PRINT')
    # self.log_info('in print_wokflow self.STEPS[2]=\n%s ' % pprint.pformat(self.STEPS[steps[1]]))
    for s in steps:
        status = self.STEPS[s]['status']
        if self.args.status_long or self.args.status_all or all_steps:
          array_item = self.STEPS[s]['array']
        else:
          array_item = self.STEPS[s]['initial_array']
        comment = ""

#         if status in ['DONE', 'RUNNING', 'ABORTED']:
#
        try:
          g = []
          for global_stuff in ['global_completion', 'global_success', 'global_failure']:
            i = self.STEPS[s][global_stuff]
            self.log_debug('for step %s global_stuff %s i:%s' % \
                           (s, global_stuff, pprint.pformat(i)), 3, trace='PRINT')
            if len(i):
              r = '%s' % RangeSet(i)
            else:
              r = ''
            g = g + [r]
          self.log_debug('g=%s' % pprint.pformat(g), 3, trace='PRINT')

          # global_completion_percent = self.STEPS[s]['global_completion_percent']
          global_success_percent = self.STEPS[s]['global_success_percent']
          global_failure_percent = self.STEPS[s]['global_failure_percent']

          total_nb = len(RangeSet(self.STEPS[s]['initial_array']))

          # global_completion_percent = 100.*len(self.STEPS[s]['global_completion'])/total_nb
          global_success_percent = 100. * len(self.STEPS[s]['global_success']) / total_nb
          global_failure_percent = 100. * len(self.STEPS[s]['global_failure']) / total_nb

          if self.args.status_long:
            comment = "SUCCESS: %4d%% -> [%20s] \tFAILURE: %3d%% -> [%s]" % \
                      (global_success_percent, g[1], global_failure_percent, g[2])
          else:
            comment = "SUCCESS: %4d%% \tFAILURE: %3d%% -> [%s]" % \
                      (global_success_percent, global_failure_percent, g[2])

        except Exception:
          comment = "pb  array_item=%s global_completion=%s global_success=%s global_failure=%s" % \
                    (self.STEPS[s]['global_completion'], self.STEPS[s]['global_success'], \
                     self.STEPS[s]['global_failure'])
          self.dump_exception()

        self.log_console('step %s:%-20s %-8s  %s' % (s, array_item, status, comment))

  #########################################################################
  # kill job
  #########################################################################

  def kill_workflow(self, force=False, exceptMe=False):

    #
    lock_file = self.take_lock(self.FEED_LOCK_FILE)

    self.get_current_jobs_status()

    self.in_kill_worflow = True

    self.load()

    jobs_to_kill = []
    for jid in self.JOBS.keys():
        self.log_debug("%s:self.JOBS[%s]['completion_percent']=%s and self.JOBS[%s]['status']: %s"\
                       % (self.JOBS[jid]['job_name'], jid, \
                          self.JOBS[jid]['completion_percent'], jid, self.JOBS[jid]['status']), 3, \
                       trace='KILL')
        if self.JOBS[jid]['completion_percent'] < 100. and \
           not(self.JOBS[jid]['status'] == 'ABORTED'):
            if not(exceptMe) or not(jid == self.args.jobid):
                jobs_to_kill = jobs_to_kill + [jid]

    if len(jobs_to_kill) == 0:
        self.log_info('No jobs are currently running or waiting... Nothing to kill then!')
        self.release_lock(lock_file)
        if not(force):
            sys.exit(0)

    if not(force):
        self.ask("Do you want to kill all jobs related to this current workflow now? ", \
                 default='n')

    s = 'killing all the dependent jobs...'
    self.log_info(s)
    self.send_mail(s)

    self.log_info('%s jobs to kill...' % (len(jobs_to_kill)))
    self.log_debug('job to kill : (%s)' % ",".join(map(lambda x: str(x), jobs_to_kill)))
    for job_id in jobs_to_kill:
      step = self.JOBS[job_id]['step']
      if not(self.JOBS[job_id]['status'] == 'WAITING'):
          cmd = ' scancel %s ' % job_id
          self.log_debug('killing step %s with %s' % (step, cmd), 4, trace='KILL')
          self.system(cmd)
      self.JOBS[job_id]['status'] = 'ABORTED'
      self.STEPS[step]['status'] = 'ABORTED'

      self.log_info('killing the job %s (step %s)...' % (job_id, step))

    # self.log_info('Abnormal end of this batch... waiting 15 s for remaining job to be killed')
    # time.sleep(15)
    s = '=============== workflow is aborting =============='
    self.save(take_lock=False)

#   self.log_debug("get_status:end -> JOBS=\n%s " % pprint.pformat(self.JOBS),2)
#   self.log_debug("get_status:end -> STEPS=\n%s " % pprint.pformat(self.STEPS), 1)
#   self.log_info("get_status:end -> TASKS=\n%s " % pprint.pformat(self.TASKS),2)

    self.log_info(s)
    self.send_mail(s)

    self.job_lists = []

    self.release_lock(lock_file)

    if not(force):
      self.keep_probing = False
      sys.exit(0)

  #########################################################################
  # finalize the job, putting a stamp somewhere
  #########################################################################

  def finalize(self):
    if not(self.SCENARIO.find(",%s," % self.args.step) >= 0 or \
           self.SCENARIO.find(",%s-%s," % (self.args.step, self.TASK_ID)) >= 0 or \
           self.SCENARIO.find(",%s-%s-%s," % (self.args.step, self.TASK_ID,
                                              self.args.attempt)) >= 0):
      self.log_info("finalizing job : %s-%s " % (self.args.step, self.TASK_ID), 2)
      filename = '%s/Done-%s-%s' % (self.SAVE_DIR, self.args.step, self.TASK_ID)
      open(filename, 'w')

      self.send_mail('%s-%s Done' % (self.args.step, self.TASK_ID), 2)

      self.log_info('Done! -> creating stub file %s' % filename, 3)

      # checking current worflow
      self.check_current_state(self.args.step, self.args.attempt,
                               tasks=[self.TASK_ID],
                               from_finalize=True)


      # need to feed the workflow when finalizing, removing current job
      # from running or waiting job...
      self.feed_workflow(from_finalize=True)

      if self.TASK_ID == RangeSet(self.TASK_IDS)[-1] and not(self.currently_healing_workflow):
        self.load()
        if not(self.JOBS[int(self.args.jobid)]['make_depend']):
            self.log_info('Normal end of this batch', 2)
            self.log_info('=============== workflow is finishing ==============', timestamp=True)
            if self.args.mail:
                self.send_mail('Workflow has just completed successfully')

  #########################################################################
  # check the state  of the current jobs and heal them
  #########################################################################

  def check_current_state(self, what, attempt, tasks=None,
                          checking_from_console=False, from_heal_workflow=False,
                          from_finalize=False):

    if not(checking_from_console):
      self.load()

    # if len(RangeSet(tasks))>5:
    #   print 'FAAAAAAAAAAAAAAAAKE set tasks to 1-5'
    #   tasks='1-5'

    state_has_changed = False
    step = '%s-%s' % (what, attempt)

    if checking_from_console:
      self.args.info_offset = self.args.info_offset + 1

    if not(tasks):
      tasks = self.CHECK_TASK_IDS

    self.log_info("check_current_state(what=>%s<, attempt=>%s<, tasks=>%s<" % \
                  (what, attempt, tasks), 4, trace='CHECK_SHORT,COMPUTE_CHECK,CHECK,WHAT_CHECK')

    filename_all_ok = '%s/Done-%s!%s-all' % (self.SAVE_DIR, what, attempt)
    filename_all_nok = '%s/Done-%s!%s-nok' % (self.SAVE_DIR, what, attempt)
    check_it = False
    if checking_from_console or from_finalize:
        check_it = True
    else:
        if self.TASK_ID == RangeSet(self.TASK_IDS)[0]:
            check_it = True
    if check_it:
      self.log_info("checking status of previous job : %s!%s [%s] " % \
                    (what, attempt, tasks), 2)

      all_complete = True
      tasks_not_complete = []
      # tasks_complete = []
      user_check = True

      nb_current_task = 0
      nb_tasks_to_check = len(RangeSet(tasks))
      last_percent_printed = -1
      self.errors = {}
      for i in RangeSet(tasks):
        nb_current_task = nb_current_task + 1
        percent_task_checked = int(100. * nb_current_task / nb_tasks_to_check)
        if (nb_tasks_to_check > 100) and (percent_task_checked % 5 == 0)\
           and not(last_percent_printed == percent_task_checked):
          self.log_console("step %s-%s: checking  task #%s out of %s for   --> %0d%%..." % \
                           (what, attempt, i, nb_tasks_to_check, percent_task_checked), noCR=True)
          last_percent_printed = percent_task_checked
        try:
          if self.TASKS[step][i]['status'] == 'SUCCESS' and not(self.args.force_check):
            # if i in self.STEPS[step]['global_success'] and not(self.args.force_check):
            self.log_info("task %s-%s (step %s) found successfull " % (what, i, step), \
                          2, trace='CHECK')
            continue
        except Exception:
          self.error('missing key for step=%s i=%s from tasks=(%s) self.TASKS=\n%s' % \
                     (step, i, tasks, pprint.pformat(self.TASKS)), killall=True, exception=True)

        # filename_failure = '%s/FAILURE-%s-%s' % (self.SAVE_DIR, what, i)
        # is_failure = os.path.exists(filename_failure)
        # if is_failure and not(self.args.force_check):
        #     self.log_info("Failure file found for task %s-%s (step=%s) " % (what,i,step),
        #                   2,trace='CHECK')
        #     self.TASKS[step][i]['status'] = 'FAILURE'
        #     continue
          
        filename_complete = '%s/Complete-%s-%s' % (self.SAVE_DIR, what, i)
        is_complete = os.path.exists(filename_complete)
        if is_complete and not(self.args.force_check):
            self.log_info("Complete file found for task %s-%s (step=%s) " % (what, i, step),
                          2, trace='CHECK')
            self.TASKS[step][i]['status'] = 'SUCCESS'
            continue

        filename_done = '%s/Done-%s-%s' % (self.SAVE_DIR, what, i)
        is_done = os.path.exists(filename_done)
        self.log_info('checking presence of file %s : %s ' % (filename_done, is_done), 3)

        user_check = self.prepare_user_defined_check_job(what, i, attempt, is_done,
                                                         checking_from_console)
        self.log_info("user_check=%s for task %s-%s (step=%s) " % (user_check, what, i, step),
                      2, trace='CHECK')

        if user_check == SUCCESS:
            if not(is_done) and user_check:
                s = ('ZZZZZZZ step %s-%s was not complete but was validated successfully ' + \
                     '+by a check made by a user defined function') % (what, i)
                self.log_info(s)
                self.append_mail(s)

            if self.CanLock:
                open(filename_complete, 'w')
            task_status = self.TASKS[step][i]['status'] = 'SUCCESS'
            self.log_info("set status=SUCCESS for task %s-%s (step=%s) " % (what, i, step),
                          2, trace='CHECK')
            state_has_changed = True
            continue

        if not(is_done) or not(user_check == SUCCESS):
          self.log_debug('adding task %s to tasks_not_complete' % i, \
                         4, trace='CHECK')
          tasks_not_complete = tasks_not_complete + [i]
          all_complete = False
          if is_done:
              os.unlink(filename_done)
          if not(user_check == SUCCESS):
            if user_check == FAILURE:
              task_status = self.TASKS[step][i]['status'] = 'FAILURE'
            elif user_check == ABORT:
              task_status = self.TASKS[step][i]['status'] = 'ABORT'
            state_has_changed = True
            self.log_info("set status=%s for task %s-%s (step=%s) " % (task_status, what, i, step),
                          2, trace='CHECK')

        if not(user_check == SUCCESS):
          self.log_info('task %s_%s rejected by user check' % (what, i), 2, trace='CHECK')

        # self.log.info('all_complete=%s' % all_complete,1)
        # self.log.info('not_complete=%s' %  pprint.pformat(tasks_not_complete),1)

        if (user_check == ABORT):
          self.log_info('User error detected... and asking for abortion of the whole workflow!!!' + \
                        '\n\t for step %s  attempt %s' % (what, attempt))
          self.kill_workflow(force=True, exceptMe=True)

        filename_result = '%s/%s-%s-%s' % (self.SAVE_DIR, task_status, what, i)
        open(filename_result, "w")
      
    
      self.errors_print()

      if (from_finalize):
        return
        
      if not(all_complete):
        s = '!!!!!!!! oooops pb : job missing or uncomplete at last step %s : (%s)' % \
            (what, ",".join(map(lambda x: str(x), tasks_not_complete)))
        self.log_info(s)
        self.append_mail('Will restart the uncomplete step and fix the workflow')
        if self.CanLock:
            open(filename_all_nok, "w")
        if (checking_from_console):
          self.args.info_offset = self.args.info_offset - 1
          return (False, RangeSet(tasks_not_complete))
        if state_has_changed:
          self.save()
        self.archive(what, attempt, 'restart')
        self.heal_workflow(what, tasks_not_complete)
        sys.exit(1)
      else:
        if self.CanLock:
            open(filename_all_ok, "w")
        self.STEPS[step]['status'] = 'DONE'
        if (checking_from_console):
          self.args.info_offset = self.args.info_offset - 1
          return (True, RangeSet(tasks_not_complete))
        self.save()
        self.log_debug('what=%s,step=%s' % (what, self.args.step))
        s = ' \tok everything went fine for the step %s (%s) --> Step %s (%s) is starting...' % \
            (what, tasks, self.args.step, self.TASK_IDS)
        self.log_info(s, timestamp=True)
        step_with_attempt = "%s-%s" % (what, attempt)
        step_content = self.STEPS[step_with_attempt]
        self.log_debug('at this point for step %s: %s' % \
                       (step_with_attempt, \
                        self.print_job(step_content, print_only=step_content.keys())), \
                       3, trace='GLOBAL')
        self.append_mail(s.replace('--> ', '\n'))
        self.send_mail(s)
        self.archive(what, attempt, 'ok')

        self.feed_workflow()
        self.log_debug('\t\t --> releasing dependent jobs', 1, trace='HEAL,RELEASED')
        job = self.JOBS[self.args.jobid]
        next_job_id = job['make_depend']
        if next_job_id:
          next_job = self.JOBS[next_job_id]
          while not(next_job['check_previous']):
            self.log_info('\t\t --> releasing jobs %s (%s)' % \
                          (next_job['step'], next_job['array']),
                          2, trace='RELEASED')
            cmd = 'scontrol update jobid=%s dependency=after:%s' % (next_job_id, self.args.jobid)
            out = self.system(cmd, force=True)
            self.log_info('update cmd >%s< -> %s ' % (cmd, out), 1, trace='HEAL,RELEASED')
            next_job_id = next_job['make_depend']
            if next_job_id and self.args.all_released:
              next_job = self.JOBS[next_job_id]
            else:
              break

        return True

    else:
      self.log_info("waiting for the checking of previous job : %s %s " % \
                    (what, tasks), 2, trace='CHECK_WAIT')
      for i in range(10):
        if os.path.exists(filename_all_ok) or os.path.exists(filename_all_nok):
          break
        self.log_info('waiting...', 2, trace='CHECK_WAIT')
        time.sleep(5)

      if os.path.exists(filename_all_ok):
          self.log_info('ok done! returning', 1, trace='CHECK_WAIT')
          if (checking_from_console):
            return (True, [])
          else:
            return 0

      if (checking_from_console):
        self.args.info_offset = self.args.info_offset - 1
        return (False, RangeSet(tasks_not_complete))

      s = 'something went wrong when checking last step...giving it up!'
      self.log_info(s)
      self.send_mail(s, 4)
      self.archive(what, attempt, 'failed')
      sys.exit(1)

  #########################################################################
  # prepare to call user defined function to check if the job actually passed
  #########################################################################

  def prepare_user_defined_check_job(self, what, task_id, attempt,
                                     is_done, checking_from_console=False):

    step = "%s-%s" % (what, attempt)
    job_id = self.TASKS[step][task_id]['job']
    if job_id == 'UNKNOWN':
      # poor workaround
      return False
      self.error('UNKNOWN key found in self.TASKS[%s][%s][job] \n self.TASKS[%s]=\n%s' % \
                 (step, task_id, step, pprint.pformat(self.TASKS[step])), \
                 exit=False, exception=False)  # ,exit=True,exception=True)
      return False

    # poor workaround
    if not(job_id in self.JOBS.keys()):
      return False
    if not('output' in self.JOBS[job_id].keys()):
      return False

    job_tasks = RangeSet(self.JOBS[job_id]['array'])
    step_tasks = RangeSet(self.STEPS[self.JOBS[job_id]['step']]['array'])

    original_output_pattern = "%s.TASK_ID-attempt" % (self.JOBS[job_id]['output'])
    pattern = "%s.task_%04d-attempt" % (self.JOBS[job_id]['output'], int(task_id))
    if checking_from_console:
          pattern = pattern + "_*"
          original_output_pattern = original_output_pattern + "_*"
    else:
          pattern = pattern + "_%s" % (attempt)
          original_output_pattern = original_output_pattern + "_%s" % (attempt)
    output_file_pattern = pattern.replace('%a', str(task_id)).replace('%j', '*').replace('%J', '*')

    original_error_pattern = "%s.TASK_ID-attempt" % (self.JOBS[job_id]['error'])
    pattern = "%s.task_%04d-attempt" % (self.JOBS[job_id]['error'], int(task_id))
    if checking_from_console:
          pattern = pattern + "_*"
          original_error_pattern = original_error_pattern + "_*"
    else:
          pattern = pattern + "_%s" % (attempt)
          original_error_pattern = original_error_pattern + "_%s" % (attempt)
    error_file_pattern = pattern.replace('%a', str(task_id)).replace('%j', '*').replace('%J', '*')

    running_dir = self.JOBS[job_id]['submit_dir']

    s = "CHECKING step: %s   Task: %s " % (step, task_id) + " " + \
        "Output file pattern : %s" % (output_file_pattern) + " " + \
        "Error file pattern : %s" % (error_file_pattern) + " " + \
        "Running dir : %s" % (running_dir) + " "
    self.log_info(s, 4, trace='USER_CHECK')

    with working_directory(running_dir):
      output_file_candidates = glob.glob(output_file_pattern)
      if len(output_file_candidates):
          output_file_candidates.sort()
          output_file = output_file_candidates[-1]
          self.log_debug('output_file to be scanned : >%s< chosen from [%s]' % \
                         (output_file, ",".join(output_file_candidates)), 2)
      else:
          self.log_debug('ZZZZZZ weird... no output file produced of actual pattern %s' % \
                         output_file_pattern, 3, trace='CHECK_PATTERN')
          self.error_add('ZZZZZZ weird... no output file produced of pattern %s' % \
                         original_output_pattern, task_id)
          output_file = 'No_output_file_found'
          return False

      error_file_candidates = glob.glob(error_file_pattern)
      if len(error_file_candidates):
          error_file_candidates.sort()
          error_file = error_file_candidates[-1]
          self.log_info('error_file to be scanned : >%s< chosen from [%s]' % \
                        (error_file, ",".join(error_file_candidates)), 2)
      else:
          self.log_debug('ZZZZZZ weird... no error file produced of pattern %s' % \
                         error_file_pattern, 3, trace='CHECK_PATTERN')
          self.error_add('ZZZZZZ weird... no error file produced of pattern %s' % \
                         original_error_pattern, task_id)
          error_file = 'No_error_file_found'

    s = "CHECKING step : %s task %s " % (step, task_id)

    self.log_info(s, 2)
    
    if checking_from_console and not(self.args.decimate):
      self.log_console(s, noCR=True)
        
    if self.args.check:
      # if a user check procedure was given as a script file
      # executing it
      cmd = "%s %s %s %s %s %s %s %s" % \
            (self.args.check, what, attempt, task_id, running_dir, output_file, error_file, is_done)
      self.log_debug('checking via user_script with cmd/%s/' % cmd, \
                     4, trace='USER_CHECK')
      (return_code, result) = self.system(cmd, return_code=True)
      user_check = FAILURE
      self.log_debug('return_code=/%s/' % return_code, 4, trace='USER_CHECK')
      try:
        return_code = int(return_code)
      except:
        self.log_info('Aborting workflow because\nreturn_code=/%s/ not integer code while checking via user_script with cmd/%s/' % \
                      (return_code, cmd))
        user_check = ABORT
      if return_code == 0:
        user_check = SUCCESS
      elif return_code == -9999 or return_code == 'ABORT':
        user_check = ABORT
      self.log_debug('user_check=/%s/\nresult=/%s/' % (user_check, result), \
                     4, trace='USER_CHECK')

    else:
      # else calling either default python method, either user overload python method    
      
      try:
        user_check = self.check_job(what, attempt, task_id, running_dir, output_file, error_file,
                                    is_done, fix=not(checking_from_console),
                                    job_tasks=job_tasks, step_tasks=step_tasks)
      except Exception:
        # something went wrong during user_check
        s = "User defined function check_job had a problem while CHECKING step: %s Task: %s " % \
            (step, task_id)
        self.error(s, exit=False, exception=True)
        user_check = FAILURE

    s = "%s found while CHECKING step: %s   Task: %s " % (user_check, step, task_id) + " " + \
        "running_dir : %s" % (running_dir) + " " + \
        "output_file : %s" % (output_file) + " " + \
        "error_file : %s" % (error_file) + " " + \
        "Running dir : %s" % (running_dir) + " "
    self.log_info(s, 4, trace='USER_CHECK')

    if not(user_check == SUCCESS):
        self.error_add('User error detected!!! for step %s  attempt %s' % (what, attempt), task_id)

    return user_check

  def error_add(self, msg, params):
    if not(msg in self.errors):
      self.errors[msg] = []
    self.errors[msg] = self.errors[msg] + [params]

  def errors_print(self):
    if len(self.errors):
      self.log_debug('self.errors=\n%s' % pprint.pformat(self.errors), 4, trace='ERRORS')
      msg_all = []
      for k in self.errors.keys():
        msg = '%s : (%s)' % (k, RangeSet(self.errors[k]))
        self.log_info(msg)
        msg_all = msg_all + [msg]
      self.append_mail("\n".join(msg_all))

  ################################################################################
  # check current workflow returns steps to be checked and next steps to resubmit
  ################################################################################

  def what_to_restart_from_workflow(self):

    # computing last step done
    self.get_current_jobs_status()

    self.STEPS_RESTART_STATUS = {}
    self.STEPS_RESTART_ATTEMPT = {}

    if len(self.STEPS) == 0:
        self.log_console('No workflow has been submitted yet from this directory')
        return 'FROM_SCRATCH'

    self.compute_critical_path()
#     steps = self.steps_submitted
    steps = self.steps_critical_path_with_attempt
    first_step_not_done = False
    last_step_completed = False
    self.log_debug('in print_wokflow steps=[%s] ' % ",".join(steps), 2, trace='ROLLBACK')
    # self.log_info('in print_wokflow self.STEPS[2]=\n%s ' % pprint.pformat(self.STEPS[steps[1]]))
    for s in steps:
        status = self.STEPS[s]['status']
        step_only = "-".join(s.split("-")[:-1])
        self.log_info('for step %s -> %s  %s%% success %s%% failure' % \
                      (s, status, self.STEPS[s]['success_percent'], self.STEPS[s]['failure_percent']))
        # poor
        # if status in ['SUCCESS','RUNNING','PENDING']:
        if abs(self.STEPS[s]['global_success_percent'] - 100.) < 1.e-6:
          last_step_completed = s
          self.STEPS[s]['status'] = 'SUCCESS'
          last_step_completed_status = status
          self.STEPS_RESTART_STATUS[step_only] = 'DONE'
        else:
          first_step_not_done = s
          first_step_not_done_status = status
          self.STEPS_RESTART_STATUS[step_only] = 'TO_RESTART'
          break

    if last_step_completed:
      s = last_step_completed
      comment = " COMPLETED: %3d%%  SUCCESS: %3d%%  FAILURE: %3d%%" % \
                (self.STEPS[s]['completion_percent'], self.STEPS[s]['success_percent'],
                 self.STEPS[s]['failure_percent'])
      self.log_info('from job_log last step completed %s: %-8s  %s' % \
                    (s, last_step_completed_status, comment))

    if first_step_not_done:
      step_to_check = first_step_not_done
      comment = " COMPLETED: %3d%%  SUCCESS: %3d%%  FAILURE: %3d%%" % \
                (self.STEPS[step_to_check]['completion_percent'], \
                 self.STEPS[step_to_check]['success_percent'], self.STEPS[s]['failure_percent'])
      self.log_info('from job_log next step to run %s: %-8s  %s' % \
                    (s, first_step_not_done_status, comment))
    else:
      step_to_check = last_step_completed
      self.log_info('last step %s found completed, rechecking it to be sure' % s)
      # last_step_completed_array = self.STEPS[s]['initial_array']

    current_checked_step = "-".join(step_to_check.split('-')[:-1])
    next_steps_candidates = self.steps_critical_path[self.steps_position[current_checked_step]:]
    next_steps = []

    already_found = False
    # print('will forget following steps [%s]',','.join(next_steps_candidates))
    # self.forget_steps(next_steps_candidates)
    # self.save()
    while len(next_steps_candidates):
        s = next_steps_candidates[0]
        next_steps_candidates = next_steps_candidates[1:]
        if already_found:
          if args.ends > 0:
            if not(int(s.split('-')[0]) == int(self.args.ends)):
                break
        next_steps = next_steps + [s]
        if args.ends > 0:
          if int(s.split('-')[0]) == int(self.args.ends):
            already_found = True

    for s in next_steps:
        self.STEPS_RESTART_STATUS[s] = 'TO_RERUN'
        self.STEPS_RESTART_ATTEMPT[s] = int(self.steps_submitted_attempts[s]) + 1
    return (step_to_check, next_steps)

  #########################################################################
  # checking initial state of the workflow and restart it
  #########################################################################

  def check_workflow_and_start(self, no_restart=False, from_heal_workflow=False):

    # check if a workflow is still running

    to_be_restarted = self.what_to_restart_from_workflow()

    if to_be_restarted == 'FROM_SCRATCH':
      self.log_info('Brand new directory, Starting simulation from scratch...')
      return

    (step_to_check, next_steps) = to_be_restarted

    self.log_info("Job is believed to be restarted at step %s  " % step_to_check)
    self.log_debug("next_steps=[%s]" % ",".join(next_steps), 2, trace="RESTART")

    step = self.STEPS[step_to_check]
    self.log_info('step to launch %s' % pprint.pformat(step), 1)

    tasks_todo = []
    self.log_info("ZZZZZZZZ should adapt it to multiple breakit jobs??????")

    step_to_check_not_done_array = RangeSet(self.STEPS[step_to_check]['array'])

    self.log_console('Checking steps %s ' % step_to_check_not_done_array)

    for task_id in step_to_check_not_done_array:
      job_id = self.TASKS[step_to_check][int(task_id)]['job']
#       job = self.JOBS[job_id]
      items = step_to_check.split('-')
      what = "-".join(items[:-1])
      attempt = items[-1]
      (res, tasks_uncomplete) = self.check_current_state(what, attempt, '%s' % task_id, \
                                                        checking_from_console=True, \
                                                        from_heal_workflow=from_heal_workflow)
      if not(res):
        tasks_todo = tasks_todo + [task_id]

    last_step_uncompleted = what
    last_step_completed = what
    if len(tasks_todo) == 0:
      last_step_uncompleted = False

      self.log_info('step  %s is OK, checking next step' % (step_to_check))
      self.STEPS_RESTART_STATUS[step_to_check] = 'DONE'
      while len(next_steps):
        step = next_steps.pop(0)
        attempt = self.steps_submitted_attempts[step]
        tasks = self.STEPS["%s-%s" % (step, attempt)]['initial_array']
        self.log_info(" Checking actual status of step %s-%s [%s] ..." % \
                      (step, attempt, tasks))
        ret = self.check_current_state(step, attempt, tasks, checking_from_console=True, \
                                       from_heal_workflow=from_heal_workflow)
        (res, tasks_todo) = ret
        if res:
          self.log_info('for step %s job is OK, checking next step' % (step))
          last_step_completed = step
          self.STEPS_RESTART_STATUS[step] = 'DONE'
        else:
          self.log_info('for step %s job was found uncompleted' % (step))
          last_step_uncompleted = step
          self.STEPS_RESTART_STATUS[step] = 'RESTART'
          break

    if last_step_completed:
      self.tags['previous_step'] = last_step_completed

    if last_step_uncompleted:
      self.log_info("should restart from step %s and do tasks [%s] next_steps=[%s]" % \
                    (last_step_uncompleted, RangeSet(tasks_todo), ",".join(next_steps)))
      self.log_debug("self.steps_submitted=[%s]" % \
                     (",".join(self.steps_submitted)), trace='RESTART')
      self.steps_to_restart_anyway = next_steps

      self.STEPS_RESTART_STATUS[last_step_uncompleted] = 'TO_RERUN'

      self.log_info("step to restart anyway [%s] " % \
                    (self.steps_to_restart_anyway))

    else:
      self.log_info("all previous steps seems to have performed fine...")
      return

#     self.ask("Do you want to resubmit step %s [%s] followed by [%s] now ? " % \
#              (last_step_uncompleted,RangeSet(tasks_todo),",".join(next_steps)),default='y')

    # steps_submitted = ",%s," % (",".join(self.steps_submitted))
    # for s in next_steps:
    #   step_to_remove = "%s-%s" % (s,self.steps_submitted_attempts[s])
    #   steps_submitted = steps_submitted.replace(",%s," % step_to_remove,",")

    # self.steps_submitted = steps_submitted[1:-1].split(",")

    # self.log_info("new self.steps_submitted=[%s]" % \
    #                 (",".join(self.steps_submitted)))

    self.ask("Do you want to resubmit workflow starting with step %s [%s] ? " % \
             (last_step_uncompleted, RangeSet(tasks_todo)), default='y')
    self.tag_value['restart_from_step'] = int(last_step_uncompleted.split('-')[0])

    self.log_debug('STEPS a restart (%s)' % ",".join(self.STEPS.keys()), \
                   4, trace='RESTART')

    # resubmit failed job
    for step_name in [last_step_uncompleted]:  # + next_steps:
      attempt = self.steps_submitted_attempts[step_name]
      last_step_uncompleted_with_attempt = "%s-%s" % (step_name, attempt)
      # WRONG IDEA TO FORCE self.STEPS[last_step_uncompleted_with_attempt]['jobs'] = tasks_todo
      self.STEPS[last_step_uncompleted_with_attempt]['status'] = 'FAILURE'
      step2print = self.STEPS[last_step_uncompleted_with_attempt]
      self.log_debug('STEPS to restart (%s) = %s ' % \
                     (last_step_uncompleted_with_attempt, \
                      self.print_job(step2print, print_only=step2print.keys())), \
                     4, trace='RESTART')
      previous_jobs = self.STEPS[last_step_uncompleted_with_attempt]['jobs']
      if len(previous_jobs) == 0:
          self.log_info("I don't know how to resubmit step %s" % \
                        last_step_uncompleted_with_attempt)
          return
      previous_job_id = previous_jobs[0]
      previous_job = self.JOBS[previous_job_id]
      previous_job['attempt'] = previous_job['attempt'] + 1
      self.STEPS_RESTART_ATTEMPT[step_name] = previous_job['attempt']

      if step_name == last_step_uncompleted:
        previous_job['array'] = RangeSet(tasks_todo)
        previous_job['dependency'] = None
        previous_job['check_previous'] = None
        self.args.attempt_inital = previous_job['attempt']
        (job_id, cmd_previous_new) = self.submit_job(previous_job, resubmit=True)
      else:
        previous_job['array'] = previous_job['initial_array']
        previous_job['dependency'] = job_id
        previous_job['check_previous'] = job_id

    self.log_debug('STEPS after restart (%s)' % ",".join(self.STEPS.keys()), \
                   4, trace='RESTART')

    self.log_debug('self.STEPS_RESTART_STATUS=\n%s' % pprint.pformat(self.STEPS_RESTART_STATUS), \
                   4, trace='RESTART_FAKED')
    self.log_debug('self.STEPS_RESTART_ATTEMPT=\n%s' % pprint.pformat(self.STEPS_RESTART_ATTEMPT), \
                   4, trace='RESTART_FAKED')
    # last_step_uncompleted = last_step_uncompleted_new

  #########################################################################
  # fixing workflow after a failure
  #########################################################################

  def heal_workflow(self, what, not_present, from_resubmit=False):

    self.log_debug('heal_workflow: Taking the lock', 4, trace='SAVE,LOCK')
    lock_file = self.take_lock(self.LOCK_FILE)

    self.get_current_jobs_status(from_heal_workflow=True, from_resubmit=from_resubmit)
    self.compute_critical_path()

    current_attempt = self.steps_submitted_attempts[what]
    previous_step = "%s-%s" % (what, current_attempt)
    previous_initial_attempt = self.STEPS[previous_step]['initial_attempt']

    s = ("RESTARTING THE WRONG PART PREVIOUS JOB : %s (%s). current_attempt=%s" + \
         " initial_attempt=%s Extra attempt #%s ( %s out of %s)") % \
        (what, \
         RangeSet(",".join(map(lambda x: str(x), not_present))), \
         int(current_attempt), int(previous_initial_attempt), \
         int(current_attempt) - int(previous_initial_attempt) + 1, \
         int(current_attempt) - int(previous_initial_attempt) + 1, self.args.max_retry)
    self.log_info(s, timestamp=True)
    self.append_mail(s)
    # print(self.JOBS.keys())
    # self.log_debug("heal workflow begin -> JOBS=\n%s " % self.print_jobs(),2,trace='JOBS')

    # ===============================================================================
    # checking the status of the previous step
    # ===============================================================================

    if self.args.jobid in self.JOBS.keys():
      job = self.JOBS[self.args.jobid]

      if (int(current_attempt) - int(previous_initial_attempt)) >= (self.args.max_retry):
        # ===============================================================================
        # killing everything, too much failed attempts occurred
        # ===============================================================================
        s = 'Too much failed attempt for step %s my_joid is %s' % (what, self.args.jobid)
        self.log_info(s, timestamp=True)
        self.append_mail(s)
        self.log_info('killing all the dependent jobs...')
        self.send_mail('killing all the dependent jobs...')
        self.kill_workflow(force=True, exceptMe=True)
        # self.log_info(self.print_workflow(job['job_id']))
        while job['make_depend']:
          next_job_id = job['make_depend']
          cmd = ' scancel %s ' % next_job_id
          os.system(cmd)
          self.log_info('killing the job %s...', next_job_id, 2)
          job = self.JOBS[next_job_id]
        self.log_info('Abnormal end of this batch... waiting 15 s for remaining job to be killed')
        time.sleep(15)
        s = '=============== workflow is aborting =============='
        self.log_info(s, timestamp=True)
        self.send_mail(s)
        time.sleep(5)
        self.release_lock(lock_file)
        sys.exit(1)

      # ===============================================================================
      # launching next attempt
      # ===============================================================================

      self.log_info('job that found the failure: %s ' % self.print_job(job), 2, trace='HEAL')
      step = self.STEPS[job['step']]
      self.log_info('status of the step %s that found the failure: %s ' % \
                    (step['job_name'], self.print_job(step)), 2, trace='HEAL')

      next_job_id = job['make_depend']
      previous_job_id = job['dependency']
      previous_job = self.JOBS[previous_job_id]
      previous_job['attempt'] = previous_job['attempt'] + 1
      previous_job['array'] = RangeSet(",".join(map(str, not_present)))
      previous_job['make_depend'] = None
      previous_job['dependency'] = None

      self.args.attempt = int(self.args.attempt) + 1
      self.log_info('resubmitting previous_job %s ' % self.print_job(previous_job), 2, trace='HEAL')
      (job_previous_id_new, cmd_previous_new) = self.submit_and_activate_job(previous_job)

      job['dependency'] = job_previous_id_new
      job['attempt'] = job['attempt']
      # ########## for myself, I did not even do an attempt yet... was just checking previous
      job['array'] = '1-1'  # resubmit the whole job as other part will be suicided
      # job['array'] = job['initial_array'] # resubmit the whole job as other part will be suicided
      self.log_info('resubmitting same myself job %s for same attempt' % \
                    self.print_job(job), 2, trace='HEAL')
      (job_id_new, cmd_new) = self.submit_and_activate_job(job)
      job = self.JOBS[job_id_new]
      previous_job = self.JOBS[job_previous_id_new]
      self.log_info('resubmitted previous_job %s final:  %s' % \
                    (previous_job_id, self.print_job(previous_job)), 2, trace='HEAL')
      resubmitted_step = self.STEPS[job['step']]
      job_ids = resubmitted_step['jobs']
      self.log_info('resubmitted current job  %s: jobs: %s' % \
                    (job_id_new, pprint.pformat(job_ids)), 2, trace='HEAL,HEAL_CURRENT')
      for jid in job_ids:
        self.log_info('resubmitted current job  %s final:  %s' % \
                      (jid, self.print_job(self.JOBS[jid])), 2, trace='HEAL,HEAL_CURRENT')

      job['job_id'] = job_id_new
      job['submit_cmd'] = cmd_new
      self.JOBS[job_id_new] = job

      # fixing dependencies...
      previous_job['make_depend'] = job_id_new
      self.log_info('resubmitted previous_job %s fixed make_depend????:  %s' % \
                    (previous_job_id, self.print_job(previous_job)), 2, trace='HEAL,,HEAL_DEPEND')
      if next_job_id:
        job['make_depend'] = next_job_id
        job['dependency'] = job_previous_id_new
        # self.log_debug('fixing new dependency for step %s  job_id %s' % \
        #                (self.JOBS[next_job_id]['job_name'],next_job_id),4,trace='HEAL')
        cmd = 'scontrol update jobid=%s dependency=afterany:%s' % (next_job_id, job_id_new)
        out = self.system(cmd, force=True)
        self.log_info('update cmd >%s< -> %s ' % (cmd, out), 1, trace='HEAL')
        cmd = 'scontrol show job %s ' % (next_job_id)
        out = self.system(cmd, force=True)
        self.log_info('update cmd >%s< -> %s ' % (cmd, out), 1, trace='HEAL')
        self.currently_healing_workflow = True

      self.JOBS[job_previous_id_new] = previous_job
      self.JOBS[job_id_new] = job

      self.log_info('ZZZZZZZZZz before save: job_id_new=%s : %s' % \
                    (job_id_new, self.print_job(job)), 2, trace='HEAL,HEAL_CURRENT')
    else:
      self.log_info('strange... for job %s no dependency recorded??? \n ' % \
                    (self.args.jobid), 0)
      self.log_debug(('strange... for job %s no dependency recorded???' + \
                      '\n heal workflow ends -> self.JOBS=%s') % \
                     (self.args.jobid, self.print_jobs()), 4, trace='STRANGE')

    self.log_info('end of heal_workflow', 1, trace='HEAL')
    self.log_info('committing suicide in 5 seconds....', 1, trace='HEAL')

    if from_resubmit:
      self.release_lock(lock_file)
      return

    self.log_info('Job has been fixed and is restarting', timestamp=True)
    self.flush_mail('Job has been fixed and is restarting')

    self.feed_workflow()

    self.save()
    self.release_lock(lock_file)
    # self.close_save()

    self.log_info('status of the step %s that found the failure: %s ' % \
                  (step['job_name'], self.print_job(step)), 2, trace='HEAL')

    time.sleep(5)
    sys.exit(1)

  #########################################################################
  # gathering what to restart from a previous workflow
  #########################################################################

  # ===============================================================================
  # compute critical path showing only last attempts
  # ===============================================================================
  def compute_critical_path(self):

      self.steps_submitted_attempts = {}
      self.steps_position = {}
      self.steps_critical_path = []
      # computation of the critical path
      # self.log_info("self.steps_submitted=[%s]" % ",".join(self.steps_submitted))
      self.log_debug('computing critical path: self.steps_submitted=[%s]' % \
                     pprint.pformat(self.steps_submitted), 4, trace="CRITICAL,RESTART")
      self.steps_addressed = []

      if len(self.steps_submitted):
        for current_step in self.steps_submitted:
          step_alone = "-".join(current_step.split('-')[:-1])
          if not(step_alone in self.steps_addressed):
            self.steps_addressed = self.steps_addressed + [step_alone]
        self.log_debug(' steps_addressed=%s' % (",".join(self.steps_addressed)), trace='CRITICAL')

      self.steps_in_order = []
      for s in self.steps_addressed:
        for ss in self.steps_submitted:
          if ("-".join(ss.split('-')[:-1]) == s):
            if not(ss in self.steps_in_order):
              self.steps_in_order = self.steps_in_order + [ss]

      self.log_debug(' steps_in_order=%s' % (",".join(self.steps_in_order)), trace='CRITICAL')
      for s in self.steps_in_order:
        if s.find('finish') > -1:
            continue
        items = s.split('-')
        step = "-".join(items[:-1])
        attempt = items[-1]
        if step in self.steps_position.keys():
          self.steps_submitted_attempts[step] = self.steps_submitted_attempts[step] + 1
          # self.steps_submitted_attempts[step] = int(attempt)
        else:
          self.steps_critical_path = self.steps_critical_path + [step, ]

          self.steps_position[step] = len(self.steps_critical_path)
          self.steps_submitted_attempts[step] = 0

      self.steps_critical_path_with_attempt = []
      for step in self.steps_critical_path:
        attempt = self.steps_submitted_attempts[step]
        self.steps_critical_path_with_attempt = self.steps_critical_path_with_attempt + \
                                              ["%s-%s" % (step, attempt)]

      self.log_debug(' steps_critical_path=(%s)' % (",".join(self.steps_critical_path)), \
                     trace='CRITICAL')
      self.log_debug(' steps_critical_path_with_attempt=(%s)' % \
                     (",".join(self.steps_critical_path_with_attempt)), trace='CRITICAL')

  #########################################################################
  # resubmit step
  #########################################################################

  def resubmit_step(self, step_name, step_array=False, dep=False,
                    clear_dependency=False, return_all_job_ids=False):

    self.log_info('resubmitting step %s depending on %s ' % (step_name, dep))

    step = self.STEPS["%s-%s" % (step_name, self.steps_submitted_attempts[step_name])]
    self.log_info('step to launch %s' % pprint.pformat(step), 1)

    job = self.JOBS[step['jobs'][0]]
    self.log_info('first_job : %s' % pprint.pformat(job), 1)

    new_job = copy.deepcopy(job)
    if step_array:
      new_job['array'] = job['initial_array']
    if (clear_dependency):
      new_job['dependency'] = None
    if (dep):
      new_job['dependency'] = dep
    new_job['check_previous'] = dep

    self.log_info('new_job : %s' % pprint.pformat(new_job), 1)

    return self.submit_job(new_job, resubmit=True)

  #########################################################################
  # fake computation in order to test
  #########################################################################

  def fake_actual_job(self):
    self.log_debug('searching step=>%s[-%s[-%s]]< in SCENARIO=>%s<' % \
                   (self.args.step, self.TASK_ID, self.args.attempt, self.SCENARIO))
    if self.SCENARIO.find(",%s," % self.args.step) >= 0 or \
       self.SCENARIO.find(",%s-%s," % (self.args.step, self.TASK_ID)) >= 0 or \
       self.SCENARIO.find(",%s-%s-%s," % (self.args.step, self.TASK_ID, self.args.attempt)) >= 0:
      s = "According to test file FAILING the step : %s-%s " % (self.args.step, self.TASK_ID)
      self.log_info(s, 2)
      s = "******* I AM OUT OF HERE ********* CRASHING step : %s-%s-%s !!!!" % \
          (self.args.step, self.TASK_ID, self.args.attempt)
      self.log_info(s)
      sys.exit(1)
    else:
      self.log_info("faking the step : %s-%s " % (self.args.step, self.TASK_ID), 4)
      self.fake_job(self.args.step, self.TASK_ID, self.args.attempt)


  #########################################################################
  # faking a job to run some test case
  #########################################################################

  def fake_job(self, step, task, attempt):

    s = 'faking step %s task %s attempt %s' % (step, task, attempt)
    self.log_info(s, 1, trace='FAKE')
    if self.args.fake_pause:
      print('pausing for %s seconds' % self.args.fake_pause)
      self.log_info('pausing for %s seconds...' % self.args.fake_pause, 1, trace='FAKE')
      time.sleep(self.args.fake_pause)
    print('job DONE')
    self.log_info('job DONE', 1, trace='FAKE')

  #########################################################################
  # read the scenario file in order to fake a behavior
  #########################################################################

  def read_scenario_file(self):
    self.log_debug('reading scenario files %s' % self.args.test, 2)

    if self.args.test and not(os.path.exists(self.args.test)):
      self.error('Scenario Test file %s does not exist!!!' % self.args.test)

    if os.path.exists(self.args.test):
      l = open(self.args.test, "r").readlines()
      self.SCENARIO = ",%s," % ",".join(l).replace('\n', '')
      if not(self.args.spawned):
          self.log_info("Have just read the scenario file : %s " % (self.args.test))
          self.log_debug("Content of the Scenario: %d Commands (%s)" % \
                         (len(l), self.SCENARIO))

  #########################################################################
  # parse an additional tags from the yalla parameter file
  #########################################################################
  def additional_tag(self, line):
    # direct sweeping of parameter
    matchObj = re.match(r'^#DECIM\s*COMBINE\s*(\S+|_)\s*=\s*(.*)\s*$', line)
    if (matchObj):
      (t, v) = (matchObj.group(1), matchObj.group(2))
      self.log_debug("combine tag definitition: /%s/ " % line, 4, trace='YALLA,PARAMETRIC_DETAIL')
      self.combined_tag[t] = v
      self.direct_tag[t] = v
      self.direct_tag_ordered = self.direct_tag_ordered + [t]
      return True
    # direct setting of parameter
    matchObj = re.match(r'^#DECIM\s*(\S+|_)\s*=\s*(.*)\s*$', line)
    if (matchObj):
      (t, v) = (matchObj.group(1), matchObj.group(2))
      self.log_debug("direct tag definitition: /%s/ " % line, 4, trace='YALLA,PARAMETRIC_DETAIL')
      self.direct_tag[t] = v
      self.direct_tag_ordered = self.direct_tag_ordered + [t]
      return True
    return False

 #########################################################################
  # compute a cartesian product of two dataframe
  #########################################################################
  def cartesian(self, df1, df2):
    rows = itertools.product(df1.iterrows(), df2.iterrows())

    df = pd.DataFrame(left.append(right) for (_, left), (_, right) in rows)
    return df.reset_index(drop=True)

  #########################################################################
  # evaluate a tag from a formula
  #########################################################################
  def eval_tag(self, tag, formula, already_set_variables):
    expr = already_set_variables + "\n%s = %s" % (tag, formula)
    try:
      exec(expr)
    except Exception:
      self.error('error in evalution of the parameters: expression to be evaluted : %s=%s ' % (tag, formula), \
                 exception=True, exit=True, where="eval_tag")
    value = locals()[tag]
    self.log_debug('expression to be evaluted : %s  -> value of %s = %s' % (expr, tag, value), \
                   4, trace='PARAMETRIC_DETAIL')
    return value

  #########################################################################
  # evaluate tags from a formula
  #########################################################################
  def eval_tags(self, formula, already_set_variables):
    eval_expr = already_set_variables + "\n%s" % (formula)
    self.log_debug('expression to be evaluated : %s  ' % (eval_expr), \
                   4, trace='PARAMETRIC_PROG_DETAIL')
    try:
      exec(eval_expr)
    except Exception:
      self.error('error in evaluation of the parameters (eval_tags): expression to be evaluted : %s ' % \
                 (eval_expr), where="eval_tags", exception=True, exit=True)
    values = {}
    variables = locals()
    del variables['formula']
    del variables['already_set_variables']
    del variables['eval_expr']
    del variables['values']

    for tag, value in variables.items():
      if tag.find('__') == -1 and ("%s" % value).find('<') == -1:
        values[tag] = value
        self.log_debug('value of %s = %s' % (tag, value), \
                       4, trace='PARAMETRIC_DETAIL,PARAMETRIC_PROG')
    return values

  #########################################################################
  # apply parameters to template files
  #########################################################################
  def process_templates(self, from_dir='.'):

    pattern = "*.template"
    matches = []
    params = self.parameters.iloc[self.TASK_ID]
    for root, dirnames, filenames in os.walk(from_dir):
	for filename in fnmatch.filter(filenames, pattern):
            f = os.path.join(root, filename)
	    matches.append(f)
            self.log_debug('processing template file %s' % f,4,trace='TEMPLATE')
            content = "".join(open(f).readlines())
            for k in self.parameters.columns:
                v = params[k]
                content = content.replace('__%s__' % k, "%s" % v)
            processed_file = open(f.replace('.template', ""), 'w')
            processed_file.write(content)
            processed_file.close()

    return matches
          
 

  #########################################################################
  # read the yalla parameter file in order to submit a pool of jobs
  #########################################################################

  def read_parameter_file(self):
    self.log_debug('reading yalla parameter files %s' % self.args.parameter_file, \
                   2, trace='YALLA,PARAMETRIC_DETAIL')

    if not(os.path.exists(self.args.parameter_file)):
      self.error('Parameter file %s does not exist!!!' % self.args.parameter_file)
    else:
      tags_ok = False
      lines = open(self.args.parameter_file).readlines()+["\n"]

    # warning message is sent to the user if filter is applied on the combination to consider

    if not(self.args.parameter_filter == None) or \
       not(self.args.parameter_range == None):
      if self.args.parameter_filter:
        self.log_info("the filter %s will be applied... Only following lines will be taken into account : " % \
                      (self.args.parameter_filter))
      if self.args.parameter_range:
        self.log_info("only lines %s will be taken " % self.args.parameter_range)

      self.direct_tag = {}
      self.combined_tag = {}
      self.direct_tag_ordered = []
      nb_case = 1

      for line in lines:
        line = clean_line(line)
        if self.additional_tag(line):
          continue
        if len(line) > 0 and not (line[0] == '#'):
          if not(tags_ok):
            tags_ok = True
            continue
          for k in self.direct_tag.keys():
            line = line + " " + self.direct_tag[k]
          self.log_debug('direct_tag: /%s/' % line, 4, trace='PARAMETRIC_DETAIL')
          matchObj = re.match("^.*" + self.args.parameter_filter + ".*$", line)
          # prints all the tests that will be selected
          if (matchObj) and not(self.args.yes):
            if nb_case == 1:
              for k in self.direct_tag.keys():
                print "%6s" % k,
              print

            if not(self.args.parameter_range) or self.args.parameter_range == nb_case:
              print "%3d: " % (nb_case),
              for k in line.split(" "):
                print "%6s " % k[:20],
              print
            nb_case = nb_case + 1

      # askine to the user if he is ok or not
      if not(self.args.spawned):
        self.ask("Is this correct?", default='n')

      tags_ok = False
          
    # direct_tag contains the tags set through #DECIM tag = value
    # it needs to be evaluated on the fly to apply right tag value at a given job
    self.direct_tag = {}
    self.combined_tag = {}
    self.direct_tag_ordered = []
    self.python_tag = {}
    self.python_tag_ordered = []
    
    nb_case = 0
    self.parameters = {}


    full_text = "\n".join(lines)
    in_prog = False
    prog = ""
    nb_prog = 0
    line_nb = 0
    nb_lines = len(lines)
    # parsing of the input file starts...
    for line in lines:
      line_nb = line_nb + 1
      line = clean_line(line)
      # while scanning a python section storing it...
      if ((line.find("#DECIM") > -1) or (line_nb == nb_lines)) and in_prog:
        t = "YALLA_prog_%d" % nb_prog
        self.direct_tag[t] = prog 
        self.direct_tag_ordered = self.direct_tag_ordered + [t]
        nb_prog = nb_prog + 1
        self.log_debug("prog python found in parametric file:\n%s" % prog, \
                       4, trace='PARAMETRIC_PROG,PARAMETRIC_PROG_DETAIL')
        in_prog = False
      # is it a program  enforced by #DECIM PYTHON directive?
      matchObj = re.match(r'^#DECIM\s*PYTHON\s*$', line)
      if (matchObj):
        in_prog = True
        prog = ""
        continue
      elif in_prog:
        prog = prog + line + "\n"
        continue
      # is it a tag enforced by #DECIM directive?
      if self.additional_tag(line):
        continue
      
      # if line void or starting with '#', go to the next line
      if len(line) == 0 or (line[0] == '#'):
        continue

      # parsing other line than #DECIM directive
      if not(tags_ok):
        # first line ever -> Containaing tag names
        tags_names = line.split(" ")
        tags_ok = True
        continue 

      line2scan = line
      for k in self.direct_tag.keys():
        line2scan = line2scan + " " + self.direct_tag[k]
        
      nb_case = nb_case + 1

      # if job case are filtered, apply it, jumping to next line if filter not match
      if self.args.parameter_filter:
        matchObj = re.match("^.*" + self.args.parameter_filter + ".*$", line2scan)
        if not(matchObj):
          continue

      if self.args.parameter_range and not(self.args.parameter_range == nb_case - 1):
        continue

      self.log_debug("testing : %s\ntags_names:%s" % (line, tags_names), \
                     4, trace='PARAMETRIC_DETAIL')
    
      tags = shlex.split(line)

      if not(len(tags) == len(tags_names)):
        self.error("\tError : pb encountered in reading the test matrix file : %s " % self.args.parameter_file + \
                   "at  line \n\t\t!%s" % line + \
                   "\n\t\tless parameters to read than expected... Those expected are\n" + \
                   "\n\t\t\t %s " % ",".join(tags_names) + \
                   "\n\t\tand so far, we read" + \
                   "\n\t\t\t %s" % tag, exception=True, exit=True)
      
      ts = copy.deepcopy(tags_names)
      tag = {}
      self.log_debug("ts:%s\ntags:%s" % (pprint.pformat(ts), pprint.pformat(tags))\
                     , 4, trace='PARAMETRIC_DETAIL')
      
      while(len(ts)):
        t = ts.pop(0)
        tag["%s" % t] = tags.pop(0)
        self.log_debug("tag %s : !%s! " % (t, tag["%s" % t]), 4, trace='PARAMETRIC_DETAIL')
      self.log_debug('tag:%s' % pprint.pformat(tag), 4, trace='PARAMETRIC_DETAIL')

      self.parameters[nb_case] = tag

    self.log_debug('self.parameters: %s ' % \
                     (pprint.pformat(self.parameters)), \
                     4, trace='PARAMETRIC_DETAIL,PARAMETRIC')

    pd.options.display.max_rows = 999
    pd.options.display.max_columns = 999
    # pd.options.display.width = 3000
    pd.options.display.expand_frame_repr = True
    pd.options.display.max_columns = None

    
    l = pd.DataFrame(self.parameters).transpose()
    if len(l):
      tag = l.iloc[[0]]
    else:
      tag = {}
    self.log_debug('%d parameters before functional_tags : \n %s' % (len(l), l), \
                   4, trace='PARAMETRIC_DETAIL')
    self.log_debug('tag before functional_tags : \n %s' % l.columns, \
                   4, trace='PARAMETRIC_DETAIL')
    self.log_debug('prog before functional_tags : \n %s' % prog, \
                   4, trace='PARAMETRIC_DETAIL')

    
    
    # evaluating parameter computed...
    
    if len(self.direct_tag):

      # first evaluation these parameter with the first combination of
      # parameter to check if they are unique or an array of values
      #
      # if unique, then evaluation remains to be done for all the
      #            possible combination
      # if arrays of values, its dimension  should be conformant to the set of
      #            combinations already known and that these values will complete

      
      self.log_debug('self.direct_tag %s tag:%s' % \
                   (pprint.pformat(self.direct_tag), pprint.pformat(tag)), \
                   4, trace='PARAMETRIC_DETAIL')
      self.log_debug('self.direct_tag_ordered %s ' % \
                   (pprint.pformat(self.direct_tag_ordered)), \
                   4, trace='PARAMETRIC_DETAIL')
      # adding the tags enforced by a #DECIM directive
      # evaluating them first

      # first path of evaluation for every computed tag
      
      for t in self.direct_tag_ordered:
        already_set_variables = ""
        if len(l) > 1:
          values = l.iloc[[1]]
          self.log_debug('values on first line : \n %s' % values, \
                         4, trace='PARAMETRIC_DETAIL')
          for c in l.columns:
            already_set_variables = already_set_variables + "\n" + "%s = %s " % (c, l.iloc[0][c])
        self.log_debug('already_set_variables : \n %s' % already_set_variables, \
                       4, trace='PARAMETRIC_DETAIL')

        formula = self.direct_tag[t]
        if t.find("YALLA_prog") == -1:
          results = { t:  self.eval_tag(t, formula, already_set_variables)}
          tag, result = t, results[t]
          self.log_debug('evaluated! %s = %s = %s' % (tag, formula, result), \
                         4, trace='PARAMETRIC_DETAIL')
          # output produced is a row of values
          if isinstance(result, list):
            if  len(l) > 0 and (t in self.combined_tag):
              new_column = pd.DataFrame(pd.Series(result), columns=[t])
              self.log_debug('before cartesian product \n l: %d combinations : \n %s' % (len(l), l), \
                             4, trace='PARAMETRIC_DETAIL')
              self.log_debug('before cartesian product \n new_column: %d combinations : \n %s' % (len(new_column), new_column), \
                             4, trace='PARAMETRIC_DETAIL')
              l = self.cartesian(l, new_column)
              self.log_debug('after cartesian product %d combinations : \n %s' % (len(l), l), \
                             4, trace='PARAMETRIC_DETAIL')
            else:
              if len(result) == len(l) or len(l) == 0:
                if len(l) > 0:
                  ser = pd.Series(result, index=l.index)
                else:
                  ser = pd.Series(result)
                l[t] = ser
              else:
                self.error(('parameters number mistmatch for expression' + \
                            '\n\t %s = %s \n\t --> ' + \
                            'expected %d and got %d parameters...') % \
                           (tag, formula, len(l), len(result)))
          else:
            # output produced is only one value -> computing it for all combination
            results = [result]
            for row in range(1, len(l)):
              values = l.iloc[[row]]
              self.log_debug('values on row %s: \n %s' % (row, values), \
                             4, trace='PARAMETRIC_DETAIL')
              already_set_variables = ""
              for c in l.columns:
                already_set_variables = already_set_variables + "\n" + "%s = %s " % (c, l.iloc[row][c])
              self.log_debug('about to be revaluated! t=%s results=%s' % (t, results), \
                             4, trace='PARAMETRIC_DETAIL')
              result = self.eval_tag(t, formula, already_set_variables)
              results = results + [result]
            self.log_debug('evaluated! %s = %s = %s' % (t, formula, results), \
                          4, trace='PARAMETRIC_DETAIL')

            ser = pd.Series(results, index=l.index)
            l[t] = ser
        else:
          results = self.eval_tags(formula, already_set_variables)
          del self.direct_tag[t]

          # first updating all parameter that produces a vector
          result_as_column = {}
          for tag, result in results.items():  
            self.log_debug('evaluated! %s = %s = %s' % (tag, formula, result), \
                           4, trace='PARAMETRIC_DETAIL')
            # output produced is a row of values
            if isinstance(result, list):
              if len(result) == len(l) or len(l) == 0 or (t in self.combined_tag):
                result_as_column[tag] = result
                ser = pd.Series(result, index=l.index)
                l[tag] = ser
              else:
                self.error(('parameters number mistmatch for parameter %s computed from a python section' + \
                            '\n\t expected %d and got %d parameters...') % \
                           (tag, len(l), len(result)))

          # second applying formula for all other variables and check that
          # row as column remains constant
          results_per_var = {}
          for v in results.keys():
            results_per_var[v] = [results[v]]
            
          for row in range(1, len(l)):
            
            values = l.iloc[[row]]
            self.log_debug('values on row %s: \n %s' % (row, values), \
                           4, trace='PARAMETRIC_PROG_DETAIL')
            already_set_variables = ""
            for c in l.columns:
              already_set_variables = already_set_variables + "\n" + "%s = %s " % (c, l.iloc[row][c])
            results_for_this_row = self.eval_tags(formula, already_set_variables)
            for v in results.keys():
              results_per_var[v] = results_per_var[v] + [results_for_this_row[v]]
              if (v in result_as_column.keys()):
                if not(cmp(result_as_column[v], results_for_this_row[v]) == 0):
                  self.error('mismatch in parameter list  computed from file %s \n\tfor parameter %s: ' % \
                             (self.args.parameter_file, v) + \
                             '\n\t    returned %s for first combination ' % result_as_column[v] + \
                             '\n\tbut returned %s for %dth combination ' % (results_for_this_row[v], row),
                             exit=True, where='read_parameter_file', exception=False)

            self.log_debug('evaluated! for row %s = %s' % (row, pprint.pformat(results_for_this_row)), \
                           4, trace='PARAMETRIC_PROG_DETAIL')

          for v in results.keys():
            if not(v in result_as_column.keys()):
              ser = pd.Series(results_per_var[v], index=l.index)
              l[v] = ser

    parameter_list = '%d combination of %d parameters  : l \n %s' % (len(l), len(l.columns), l)
    
    self.log_debug(parameter_list,\
                   4, trace='PS,PARAMETRIC_DETAIL,PARAMETRIC_SUMMARY')

    if self.args.parameter_list:
        self.log_console(parameter_list)
        sys.exit(0)

    if 'nodes' in l.columns:
      job_per_node_number = l.groupby(['nodes']).size()
      # print job_per_node_number
      # for j in job_per_node_number.keys():
      #   print j,':',job_per_node_number[j]
      # print l.groupby(['nodes']).size()
      cols_orig = l.columns
      cols = ['nodes', 'ntasks']
      for c in cols_orig:
        if not(c in ['nodes', 'ntasks']):
          cols = cols + [c]
      self.log_debug('parameter combinations:\n%s' % l.groupby(cols).size(), \
                     4, trace='PARAMETRIC_DETAIL')
    # sys.exit(1)

    self.parameters = l
    return self.parameters
      

  #########################################################################
  # print job
  #########################################################################

  def print_jobs(self, J=None, short_format=True, print_only=False):
                     # print_only=['job_id','job_name','status','array','attempt'],filter=['python']):
                     # print_only=['job_name','status','content','job_id','step','dependency','make_depend','attempt'],filter=['python']):

    if J is None:
      J = self.JOBS
    out = ''
    for j in J.keys():
      if print_only:
          out = out + "%s:%s\n" % (j, self.print_job(J[j], short_format, print_only))
      else:
          out = out + "%s:%s\n" % (j, self.print_job(J[j], short_format))
    return out

  #########################################################################
  # print job
  #########################################################################

  def print_job(self, job, short_format=True,
                print_only=['check_previous', 'script_file', 'array', 'inital_array',
                            'job_name', 'status', 'content', 'job_id', 'step',
                            'dependency', 'make_depend', 'attempt', 'global_completion'],
                filter=['python /tmp/dart_mitgcm.py'], filtered=['content'], allkey=True, \
                print_all=False, except_none=False):

    fields_to_compress = ['jobs', 'success', 'completion', 'failure',
                          'global_success', 'global_completion', 'global_failure']
    if print_all:
      print_only = job.keys()
    new_job = copy.deepcopy(job)
    if allkey:
      new_job['000keys000'] = ','.join(job.keys())
    if short_format:
      for k in job.keys():
        if except_none:
          if not(new_job[k]):
            del new_job[k]
            continue
        if not(k in print_only):
          del new_job[k]
          continue
        if k in fields_to_compress:
          if len(new_job[k]) > 1:
            values = ','.join(map(lambda x:str(x), new_job[k]))
            try:
              new_job[k] = '[%s] <- *compressed' % RangeSet(values)
            except Exception:
              new_job[k] = '[%s]' % values

        if len("%s" % job[k]) > 100:
          if not(filter is None) and (k in filtered):
            content = ('%s' % new_job[k]).split('\n')
            filtered_content = '--filtered--'
            for c in content:
              for f in filter:
                if c.find(f) > -1:
                  filtered_content = filtered_content + '\n' + c
            new_job[k] = filtered_content
            pass
#           else:
#             new_job[k] = 'filtered'
    return pprint.pformat(new_job).replace('\\n', '\n')

  #########################################################################
  # submitting and activate one job
  #########################################################################

  def submit_and_activate_job(self, job):

      self.log_info('in submit_and_activate job to submit  %s ' % \
                    self.print_job(job), 2, trace='SUBMIT_AND_ACTIVATE')
      (submitted_job_ids, cmd) = self.submit_job(job, registration=False, \
                                                 resubmit=True, return_all_job_ids=True)
      for submitted_job_id in submitted_job_ids:
        submitted_job = self.JOBS[submitted_job_id]
        self.log_info('in submit_and_activate job %s ' % self.print_job(submitted_job), 3)
        (job_id, cmd) = self.activate_job(submitted_job, registration=False)
      return (job_id, cmd)

  #########################################################################
  # submitting one job separating it in chunks if needed
  #########################################################################

  def submit_job(self, job, registration=True, resubmit=False, \
                 take_lock=False, return_all_job_ids=False):

    # taking care of restart
    if job['job_name'] in self.STEPS_RESTART_STATUS:
      step_only = job['job_name']
      if (self.STEPS_RESTART_STATUS[step_only] in ['DONE']):
        # and not(step_only in self.steps_to_restart_anyway):
        self.log_info('step %s not actually submitted as it was marked as DONE use --resubmit to resubmit it again ' % (job['job_name']), \
                       0, trace='RESTART_FAKED,SUBMITTED')
        return (None, 'nothing')

    lock_file = self.take_lock(self.LOCK_FILE)

    self.log_debug('submit_job submitting job: %s ' % self.print_job(job, print_all=True), 2, trace='SUBMIT_JOB')

    self.log_debug('in submit JOBS start: %s' % (','.join(map(str, self.JOBS.keys()))), 2, trace='JOBS')

    job_default_value = {'array': '1-1', \
                         'attempt': 0, \
                         'check': None,
                         'initial_attempt': 0, \
                         'make_depend': None, \
                         'yalla': 0,
                         'burst_buffer_size': 0,
                         'burst_buffer_space': 0,
                         'submit_dir': os.getcwd(),
                         'ntasks': 1,
                         }

    # scanning original script for merging slurm option
    self.log_debug('Scanning file %s for additional slurm parameters' % job['script'], \
                   4, trace='PARSE')
    original_script_content_lines = open(job['script'], 'r').readlines()
    (job, job_file_args_overloaded) = self.complete_slurm_args(original_script_content_lines, job)

    self.log_debug('after reading job script file job %s=%s' % \
                   (job['script'], self.print_job(job, print_only=job.keys())), \
                   4, trace='WRAP,PARSE')

    # if no time is given, rejecting the job...
    if not(job['time']):
      self.error('sbatch: error: Invalid time limit specification', exit=1)

    # if no name is given, rejecting the job...
    if not(job['job_name']):
      self.error('sbatch: error: Invalid name specification', exit=1)

    for field in job_default_value:
         if not(field in job.keys()):
            job[field] = job_default_value[field]
         else:
            if not(job[field]):
                job[field] = job_default_value[field]

    # forcing job output or error filename to be valued
    for n in ['error', 'output']:
      if job[n] == None:
        job[n] = '%s.%%j.%s' % (job['job_name'], n[:3])
        self.log_info('empty job %s filename forced to %s' % (n, job[n]), \
                      4, trace='API,WORKFLOW,ACTIVATE_DETAIL,JOB_OUTERR')
      
    (job_script_content, job) = self.wrap_job_script(job, original_script_content_lines,
                                                    job_file_args_overloaded)

    if not('nodes' in job.keys()):
      job['nodes'] = int(math.ceil(job['ntasks'] / 64.))

    # forcing job output or error filename to be valued
    for n in ['error', 'output']:
      if job[n] == None:
        job[n] = '%s.%%j.%s' % (job['job_name'], n[:3])
        self.log_info('empty job %s filename forced to %s' % (n, job[n]), \
                      4, trace='API,WORKFLOW,ACTIVATE_DETAIL,JOB_OUTERR')

    self.log_debug('after wrap job=%s' % self.print_job(job), 4, trace='WRAP')

    if False:
      # calculating the unique identifier
      timestamp = "%s" % time.time()
      unique_identifier = get_checksum_id(job_script_content + timestamp)
      unique_job_script = "%s/%s_%s" % (self.SAVE_DIR, job['job_name'], unique_identifier)
    else:
      unique_job_script = "%s/%s" % (self.SAVE_DIR, job['job_name'])
    job_script = job['script'] = unique_job_script

    self.compute_critical_path()

    f = open("%s" % job_script, 'w')
    f.write("".join(original_script_content_lines))
    f.close()

    f = open("%s+" % job_script, 'w')
    f.write(job_script_content)
    f.close()

    job['script_file'] = job_script + '+'

    if (not('initial_array' in job.keys())):
      job['initial_array'] = job['array']

    index_to_submit = RangeSet(job['array'])

    if self.args.parameter_file and not(self.args.spawned):
      array_params_coherent = False
      parameter_nb = len(self.parameters)
      array_length = len(index_to_submit)
      if array_length > parameter_nb:
        msg = "array has %s occurence while there are %d combinations" % \
              (array_length, parameter_nb)
        self.error(msg, exit=True)
    

    if job['job_name'] in self.STEPS_RESTART_STATUS.keys():
      if self.STEPS_RESTART_STATUS[job['job_name']] in ['TO_RERUN', 'TO_RESTART']:
        if not(job['job_name'] in self.STEPS_RESTART_ATTEMPT.keys()):
            self.STEPS_RESTART_ATTEMPT[job['job_name']] = 0
        job['attempt'] = self.STEPS_RESTART_ATTEMPT[job['job_name']]
        job['initial_attempt'] = self.STEPS_RESTART_ATTEMPT[job['job_name']]
        job['array'] = job['initial_array']

    step = '%s-%s' % (job['job_name'], job['attempt'])

    # checking if step already exists and which state it has
    step_only = job['job_name']
    resubmitted_job = False

    previously_registred_step = None
    self.log_debug('self.steps_submitted_attempts=%s' % \
                   pprint.pformat(self.steps_submitted_attempts), 4, trace='GLOBAL')
    if step_only in self.steps_submitted_attempts.keys():
      # returning last job id of the step
      previously_registred_step = "%s-%s" % (job['job_name'],
                                             self.steps_submitted_attempts[step_only])
      status = self.STEPS[previously_registred_step]['status']
      completion = self.STEPS[previously_registred_step]['completion']
      self.log_info(('step already launched before as %s found ' + \
                     'with status %s and completion %s%%') % \
                    (previously_registred_step, status, completion), 1, trace='RESTART')

    if not(resubmit) and not(step_only in self.steps_to_restart_anyway) \
       and step_only in self.steps_submitted_attempts.keys():
      if status in ['SUBMITTED', 'WAITING', 'PENDING', 'RUNNING', 'SUCCESS']:
          job_id = self.STEPS[previously_registred_step]['jobs'][-1]
          cmd = self.JOBS[job_id]['cmd']
          if not((previously_registred_step in self.steps_submitted)):
              self.steps_submitted = self.steps_submitted + [previously_registred_step, ]
              self.log_debug("submitted_jobs= [%s]" % ','.join(self.steps_submitted), \
                             4, trace='JOBS')
              self.save(take_lock=False)
          self.log_debug('returning an already submitted job %s' % job_id, \
                         4, trace='RESTART,HEAL,RESTART_FAKED')
          self.release_lock(lock_file)
          return (job_id, cmd)
      resubmitted_job = True

    if resubmit or not(step in self.STEPS.keys()) or (step_only in self.steps_to_restart_anyway):
      if (resubmit) or (step_only in self.steps_to_restart_anyway):
        self.log_info('in resubmitting step %s previously_registred_step=%s' % \
                      (step, previously_registred_step), \
                      4, trace='RESTART,HEAL')
        self.steps_submitted = self.steps_submitted + [previously_registred_step, ]
        self.add_step_to_history(step, previously_registred_step)
      if not(previously_registred_step == step):
        self.STEPS[step] = my_dict(name='STEPS_%s' % step)  # {}
      if previously_registred_step is None:
        # creating global accounting variables from scratch if it's first attempt
        self.STEPS[step]['array'] = job['array']
        self.STEPS[step]['global_status'] = 'WAITING'
        self.STEPS[step]['global_completion'] = []
        self.STEPS[step]['global_success'] = []
        self.STEPS[step]['global_completion_percent'] = 0
        self.STEPS[step]['global_success_percent'] = 0
        self.STEPS[step]['global_failure'] = []
        self.STEPS[step]['global_failure_percent'] = 0
        self.STEPS[step]['global_items'] = float(len(RangeSet(job['initial_array'])))
        self.STEPS[step]['jobs'] = []
        self.STEPS[step]['items'] = float(len(index_to_submit))
      else:
        previous_step = self.STEPS[previously_registred_step]
        self.log_debug('previous step of this kind was step %s:%s' % \
                       (previously_registred_step, \
                        self.print_job(previous_step, short_format=False)), \
                       4, trace='GLOBAL,GLOBAL_JOBS')
        self.log_debug('current_job to be submitted:%s' % \
                       (self.print_job(job)), 4, trace='GLOBAL,GLOBAL_JOBS')

        # transmitting global accouting from an attempt to another
        self.STEPS[step]['global_status'] = 'WAITING'
        self.STEPS[step]['array'] = previous_step['array']
        self.STEPS[step]['items'] = previous_step['items']
        self.STEPS[step]['global_completion'] = previous_step['global_completion']
        self.STEPS[step]['global_success'] = previous_step['global_success']
        self.STEPS[step]['global_completion_percent'] = previous_step['global_completion_percent']
        self.STEPS[step]['global_success_percent'] = previous_step['global_success_percent']
        self.STEPS[step]['global_failure'] = []
        self.STEPS[step]['global_failure_percent'] = 0.
        self.STEPS[step]['global_items'] = previous_step['global_items']
        self.STEPS[step]['jobs'] = previous_step['jobs']

        # removing previous job from the set of jobs in the current step
        if (previously_registred_step == step):
          previous_jobs = ",%s," % (",".join(map(lambda x:str(x), previous_step['jobs'])))
          jobs_to_remove = []
          self.log_debug('filtering resubmitted previous jobs %s : tasks (%s) to be removed' % \
                         (previous_jobs, job['array']), \
                         4, trace='GLOBAL,GLOBAL_REDUCTION,GLOBAL_JOBS')
          for task_to_remove in RangeSet(job['array']):
            jid = self.TASKS[step][task_to_remove]['job']
            if not (jid in jobs_to_remove):
              jobs_to_remove = jobs_to_remove + [str(jid)]
              # self.STEPS[step]['jobs']                      =
            self.log_debug('filtering resubmitted previous jobs %s : jobs (%s) to be removed' % \
                           (previous_jobs, ",".join(jobs_to_remove)), \
                           4, trace='GLOBAL,GLOBAL_REDUCTION,GLOBAL_JOBS,GLOBAL_TASKS')

            for jid in jobs_to_remove:
              if previous_jobs.find(",%s," % jid) > -1:
                previous_jobs = previous_jobs.replace(",%s," % jid, ",")
            if previous_jobs in ["", ",", ",,"]:
              self.STEPS[step]['jobs'] = []
            else:
              self.log_debug('previous_jobs final %s ' % \
                             (previous_jobs), \
                             4, trace='GLOBAL,GLOBAL_REDUCTION,GLOBAL_JOBS,GLOBAL_TASKS')
              new_jobs = []
              for jid in previous_jobs[1:-1].split(","):
                try:
                  jid = int(jid)
                except Exception:
                  pass
                new_jobs = new_jobs + [jid]
              self.STEPS[step]['jobs'] = new_jobs
        else:
          self.STEPS[step]['jobs'] = []
          self.STEPS[step]['array'] = job['array']

        # removing failed job resubmitted from job completed
        global_completion = ",%s," % (",".join(map(lambda x:str(x), \
                                                   self.STEPS[step]['global_completion'])))
        self.log_debug('global_completion initial %s : (%s) to be removed' % \
                       (global_completion, job['array']), \
                       4, trace='GLOBAL,GLOBAL_REDUCTION')
        for task in RangeSet(job['array']):
          if global_completion.find(",%s," % task) > -1:
            global_completion = global_completion.replace(",%s," % task, ",")
            self.STEPS[step]['global_completion_percent'] \
              -= 100. / self.STEPS[step]['global_items']
        if global_completion in ["", ",", ",,"]:
          self.STEPS[step]['global_completion'] = []
        else:
          self.log_debug('global_completion final %s ' % \
                         (global_completion), 4, trace='GLOBAL,GLOBAL_REDUCTION')
          self.STEPS[step]['global_completion'] = map(lambda x:int(x), \
                                                      global_completion[1:-1].split(","))

    self.log_debug('self.STEPS[step][global_completion] %s ' % \
                   (self.STEPS[step]['global_completion']), 4, trace='GLOBAL,GLOBAL_REDUCTION')

    self.STEPS[step]['job_name'] = step
    self.STEPS[step]['initial_array'] = job['initial_array']
    self.STEPS[step]['initial_attempt'] = job['initial_attempt']
    self.STEPS[step]['status'] = 'WAITING'
    self.STEPS[step]['completion'] = []
    self.STEPS[step]['success'] = []
    self.STEPS[step]['completion_percent'] = 0
    self.STEPS[step]['success_percent'] = 0
    self.STEPS[step]['failure'] = []
    self.STEPS[step]['failure_percent'] = 0
    if not(step in self.TASKS.keys()):
      if previously_registred_step:
        self.TASKS[step] = copy.deepcopy(self.TASKS[previously_registred_step])
      else:
        self.TASKS[step] = my_dict(name='TASKS_%s' % step)  # {}
      for task_id in RangeSet(job['array']):
        self.TASKS[step][task_id] = my_dict(name='TASKS_%s_%s' % (step, task_id))  # {}
        if task_id in self.STEPS[step]['global_completion']:
          for item in ['job', 'status', 'counted']:
            self.TASKS[step][task_id][item] = self.TASKS[previously_registred_step][task_id][item]
        else:
          self.TASKS[step][task_id]['job'] = 'UNKNOWN'
          self.TASKS[step][task_id]['status'] = 'WAITING'
          self.TASKS[step][task_id]['counted'] = False

    self.log_debug('just before submitting step %s:%s' % \
                   (step, self.print_job(self.STEPS[step], short_format=False)), \
                   4, trace='GLOBAL')
    self.log_debug('just before submitting job to be submitted:%s' % \
                   (self.print_job(job)), 4, trace='GLOBAL')

    self.log_debug('just before submitting step %s : TASKS: \n%s' % \
                   (step, pprint.pformat(self.TASKS[step])), \
                   4, trace='GLOBAL,GLOBAL_JOBS,GLOBAL_TASKS')

    dep = job['dependency']
    step_dep = None
    if dep:
      step_dep = self.JOBS[dep]['step']

    # updating list of submitted steps and their history
    self.add_step_to_history(step, step_dep)

    job_ids = []

    chunk_splitted = self.chunk_size

    if job['yalla']:
        chunk_splitted = 10000

    starting_indices = range(0, len(index_to_submit), chunk_splitted)
    self.log_debug(('starting_indices=[%s], index_to_submit=%s, ' + \
                    'len(index_to_submit)=%s chunk_size=%s, job=%s') % \
                   (",".join(map(lambda x: str(x), starting_indices)), index_to_submit, \
                    len(index_to_submit), chunk_splitted, self.print_job(job)), \
                   4, trace='SUBMIT,CHUNK')

    first_one_in_step = True
    dep_init = dep
    for i in starting_indices:
      chunk_size = RangeSet(index_to_submit[i:(i + chunk_splitted)])
      if dep and len(chunk_size) > 1 and first_one_in_step and not(resubmit) and not(job['yalla']):
        array_items = [RangeSet('%s-%s' % (index_to_submit[i], index_to_submit[i])),
                       RangeSet(index_to_submit[i + 1:(i + chunk_splitted)])]
      else:
        array_items = [RangeSet(index_to_submit[i:(i + chunk_splitted)])]

      self.log_debug('starting indice %s : array_items %s' % \
                     (i, pprint.pformat(array_items)), \
                     4, trace='GLOBAL,GLOBAL_JOBS,GLOBAL_TASKS')
      for array_item in array_items:
        new_job = copy.deepcopy(job)
        new_job['dependency'] = dep
        if not(dep_init):
            new_job['dependency'] = dep_init
        new_job['array'] = "%s" % array_item
        new_job['items'] = len(array_item)
        new_job['step'] = step
        new_job['check_previous'] = (first_one_in_step and dep)
        (job_id, cmd) = self.submit_chunk_job(new_job, registration)
        dep = job_id
        job_ids = job_ids + [job_id]
        self.log_debug('submitting job depending on %s with array (%s) --> job_id=%s' % \
                       (dep, array_item, job_id), 1, trace='SUBMIT,CHUNK')

        for task in array_item:
          self.TASKS[step][task] = my_dict(name='TASKS_%s_%s' % (step, task))  # {}
          self.TASKS[step][task]['job'] = job_id
          self.TASKS[step][task]['status'] = 'WAITING'
          self.TASKS[step][task]['counted'] = False

        current_job = self.JOBS[job_id]
        self.log_debug('index_to_submit = >%s< job = %s' % \
                       (pprint.pformat(index_to_submit), self.print_job(current_job)), 2)
        first_one_in_step = False

    self.STEPS[step]['jobs'] = self.STEPS[step]['jobs'] + job_ids

    self.log_debug('submit_job self.TASKS[%s]: %s ' % (step, pprint.pformat(self.TASKS[step])), \
                   2, trace='GLOBAL_TASKS')

    if not(self.args.quick_launch):
        self.save(take_lock=take_lock)

    self.log_debug('submitting job %s (for %s) --> Job # %s <-depends-on %s' % \
                   (job['job_name'], job['array'], job_id, job['dependency']))

    if resubmitted_job:
        status = self.JOBS[job_id]['status']
        self.log_debug('resubmitting job %s [%s]-->Job # %s <-depends-on %s, current_status=%s' % \
                       (job['job_name'], RangeSet(job['array']), job_id, job['dependency'], status), \
                       0, trace='RESTART,RESTART_FAKED')
    else:
      self.log_debug('submitting job %s [%s] --> Job # %s <-depends-on %s' % \
                     (job['job_name'], RangeSet(job['array']), job_id, \
                      job['dependency']), 0, trace='RESTART,RESTART_FAKED')
      if not(self.args.spawned) and not(self.args.decimate):
        self.log_info('submitting job %s [%s] --> Job # %s <-depends-on %s' % \
                      (job['job_name'], RangeSet(job['array']), job_id, \
                       job['dependency']), 0, trace='RESTART,RESTART_FAKED')

    self.release_lock(lock_file)

    if return_all_job_ids:
      return (job_ids, cmd)
    else:
      return (job_id, cmd)

  #########################################################################
  # submitting one job
  #########################################################################

  def submit_chunk_job(self, job, registration=True):

    self.log_debug('in submit_chunk JOBS start: %s' % ','.join(map(str, self.JOBS.keys())), \
                   4, trace='CHUNK')

    # self.log_debug('submit_chunk_job/begining submitting job: %s ' % \
    #               self.print_job(job),2,trace='SUBMIT_CHUNK_JOB')

    if ('account' in job.keys()):
        if self.args.account:
            job['account'] = self.args.account

    # job_script = job['script']
    if ('attempt' in job.keys()):
        attempt = job['attempt']
        self.args.attempt = attempt
    else:
        attempt = self.args.attempt

    cmd = ["cd %s ; " % job['submit_dir'], self.SCHED_SUB]
    prolog = []

    if (job['dependency']):
      prolog = prolog + [self.SCHED_DEP + ":%s #" % job['dependency']]

    if self.args.exclude_nodes:
      prolog = prolog + ["--exclude=%s" % self.args.exclude_nodes]

    if self.args.partition:
      prolog = prolog + ["--partition=%s" % self.args.partition]

    if self.args.reservation:
      prolog = prolog + ["--reservation=%s" % self.args.reservation]

    if job['array']:
      if not(job['yalla']):
        prolog = prolog + ["--array=%s" % job['array']]
      array_range = job['array']
    else:
      if not(job['yalla']):
        prolog = prolog + ["--array=%s" % ' 1-1']
      array_range = '1-1'

    if job['account'] and not(self.MY_MACHINE == "sam"):
      prolog = prolog + ['--account=%s' % job['account']]

    prolog = prolog + ['--job-name=%s' % (job['job_name'])]

    if job['yalla']:
      if not(job['nodes']):
        self.error('when asking for a Yalla container, number of nodes has to be valued',
                   exit=True)

      nb_jobs = len(RangeSet(job['array']))
      job['yalla_parallel_runs'] = min(job['yalla_parallel_runs'], nb_jobs)
      # compute new time for yalla container
      (d, h, m, s) = ([0, 0, 0, 0, 0] + map(lambda x:int(x), job['time'].split(':')))[-4:]
      print job['yalla_parallel_runs']
      factor = math.ceil(nb_jobs / (job['yalla_parallel_runs'] + 0.))
      whole_time = (((d * 24 + h) * 60 + m) * 60 + s) * factor  # NOQA
      (h, m, s) = (int(whole_time / 3600), int(whole_time % 3600) / 60, whole_time % 60)
      job['time'] = '%d:%02d:%02d' % (h, m, s)
      self.log_debug('yalla related parameters in job:%s' % \
                     self.print_job(job, print_only=['time', 'ntasks', 'nodes', 'array', \
                                                    'yalla', 'output', 'error']), 4, trace='YALLA')

      prolog = prolog + \
               ['--time=%s' % job['time'],
                '--ntasks=%s' % (int(job['ntasks']) * job['yalla_parallel_runs']),
                '--nodes=%s' % (job['nodes'] * job['yalla_parallel_runs']),
                '--error=%s.task_yyy-attempt_%s' % \
                (job['error'].replace('%a', job['array'][0:20]), attempt),
                '--output=%s.task_yyy-attempt_%s' % \
                (job['output'].replace('%a', job['array'][0:20]), attempt)]
    else:
      prolog = prolog + \
               ['--time=%s' % job['time'],
                '--ntasks=%s' % job['ntasks'],
                '--error=%s.task_%%04a-attempt_%s' % (job['error'], attempt),
                '--output=%s.task_%%04a-attempt_%s' % (job['output'], attempt)]

    cmd = cmd + ['%s_%s' % (job['script_file'], attempt)]
    self.log_debug("submitting cmd prolog : %s " % prolog, 4, trace='SUBMIT')

    job_content_template = "#!/bin/bash\n"
    for p in prolog:
        job_content_template = job_content_template + "%s %s " % (self.SCHED_TAG, p) + "\n"

    if job['burst_buffer_space']:
        job_content_template = job_content_template + "#DW persistentdw name=%s " % \
                               (job['burst_buffer_space']) + "\n"
    if job['burst_buffer_size']:
          job_content_template = job_content_template + \
                                 "#DW jobdw type=scratch access_mode=striped capacity=%s" % \
                                 (job['burst_buffer_size']) + "\n"

    job_content_template = job_content_template + \
                           "".join(open(job['script_file'], "r").readlines())
    job_content_updated = job_content_template.replace('__ATTEMPT__', "%s" % attempt)
    job_content_updated = job_content_updated.replace('__ATTEMPT_INITIAL__', "%s" % \
                                                      job['initial_attempt'])
    job_content_updated = job_content_updated.replace('__ARRAY__', "%s" % job['array'])
    if self.args.yalla:
      array_unfold = ""
      for index in RangeSet(array_range):
        array_unfold = array_unfold + "%s" % index + " "
      job_content_updated = job_content_updated.replace('__ARRAY_UNFOLD__', array_unfold)
    job_script_updated = open('%s_%s' % (job['script_file'], attempt), "w")
    job_script_updated.write(job_content_updated)
    job_script_updated.close()

    self.log_debug("for step %s self.args.attempt_initial=%s" % \
                   (job['step'], job['initial_attempt']), 4, trace='ATTEMPT_INITIAL')

    step = job['step']
    job['cmd'] = cmd
    job['array'] = array_range

    job['status'] = 'WAITING'
    job['completion'] = []
    job['success'] = []
    job['failure'] = []
    job['completion_percent'] = 0
    job['success_percent'] = 0
    job['failure_percent'] = 0

    self.log_debug("submitting cmd: " + " ".join(cmd), 4, trace='SUBMIT')
    # unique jid building
    job_id = '%s-%s-%s' % (step, array_range, time.strftime('%Y-%b-%d-%H:%M:%S'))
    job_id = '%s-%s' % (step, array_range[:20])
    self.log_debug("job submitted : %s depends on %s" % (job_id, job['dependency']), 1)

    job_script_updated = open('%s_%s_%s_waiting' % \
                              (job['script_file'], self.args.attempt, job_id), "w")
    job_script_updated.write(job_content_updated.replace('${SLURM_ARRAY_JOB_ID}', '%s' % job_id))
    job_script_updated.close()

    job['script_file'] = '%s_%s_%s_waiting' % (job['script_file'], self.args.attempt, job_id)
    job['content'] = job_content_updated

    job_before = job['dependency']
    if job_before:
      self.JOBS[job_before]['make_depend'] = job_id

    job['job_id'] = job_id
    self.JOBS[job_id] = job
    # self.JOB_ID[job['job_name']] = job_id

    self.log_info('--------\nin submit_job_chunk \n%s\n-------------\n' % self.print_job(job), 2)

    if (registration):
        self.jobs_list = self.jobs_list + [job_id]
        self.jobs_submitted = self.jobs_submitted + [job_id]
        self.last_job_submitted = job_id

    self.log_debug('in submit_chunk_job ends job=%s' % pprint.pformat(job).replace('\\n', '\n'))

    self.log_debug("Saving Job Ids...", 1, trace='QUICK')
    self.log_debug("quich_launch flag=%s" % self.args.quick_launch, 1, trace='QUICK')

    if not(self.args.quick_launch):
        self.save()

    self.log_debug('submit_chunk_job/end submitting job: %s ' % self.print_job(job), \
                   2, trace='SUBMIT_CHUNK_JOB')

    s = 'submitting job %s (for %s) --> Job # %s <-depends-on %s' % \
        (job['job_name'], job['array'], job_id, job['dependency'])
    self.log_debug(s, 4, trace='SUBMITTED')
    if not(self.args.decimate):
      self.log_console(s, noCR=True)
    else:
      self.log_info(s)
    # self.error('here',exception=True,exit=False)
      
    return (job_id, cmd)

  #########################################################################
  # activate job taking constraints into account
  #########################################################################

  def activate_job(self, job, registration=True, take_lock=True):

    #
    lock_file = self.take_lock(self.LOCK_FILE)

    self.log_debug('in activate_job self.waiting_job_final_id=%s' % \
                   (self.waiting_job_final_id), 4, trace='ACTIVATE_DETAIL')
    # self.log_debug('in activate_job job=%s' % self.print_job(job).replace('\\n', '\n'),\
    #                4,trace='ACTIVATE_DETAIL')
    # self.log_debug('beginning of activate_job job=%s' % self.print_jobs(),\
    #                4,trace='ACTIVATE_DETAIL')

    cmd = job['cmd']
    step = job['step']

    job_content_updated = job['content']
    job_script_final = '%s_%s_final' % (job['script_file'], step)
    job_script_final_file = open(job_script_final, 'w')

    self.log_debug("job_content_updated=\n===============\n%s\n================" % \
                   (job_content_updated), 4, trace='REPLACE')
    self.log_debug("waiting_job_final_id : \n%s " % pprint.pformat(self.waiting_job_final_id), \
                   4, trace='REPLACE,ACTIVATE_DETAIL,CMD,RESTART')
    for jid in self.waiting_job_final_id.keys():
        new_job_id = self.waiting_job_final_id[jid]
        self.log_debug('replace %s by %s' % (jid, new_job_id), 4, trace='REPLACE')
        job_content_updated = job_content_updated.replace(':%s #' % jid, ':%s #' % new_job_id)
    job_script_final_file.write(job_content_updated)
    job_script_final_file.close()
    self.log_debug("job_content_updated after=\n===============\n%s\n================" % \
                   (job_content_updated), 4, trace='REPLACE')

    if not self.args.dry:
      self.log_debug("cmd before: %s" % " ".join(cmd), 4, trace='ACTIVATE_DETAIL')
      self.log_debug("job['script_file']=>%s<, attempt=>%s<" % \
                     (job['script_file'], self.args.attempt), 4, trace='ACTIVATE_DETAIL')

      # creating directory if output and error files directory does not exists yet
      self.log_debug('job=%s' % (pprint.pformat(job)), 4, trace='ACTIVATE_DETAIL,JOB_OUTERR')
      for n in ['error', 'output']:
        n_directory = os.path.dirname(job[n])
        if (len(n_directory) == 0):
            n_directory = '.'
        if not(os.path.exists(n_directory)):
          os.makedirs(n_directory)
          if self.args.stripe_count:
              os.system("lfs setstripe -c %s %s " % (self.args.stripe_count, n_directory))
        if n == 'output':
          f = open('%s/%s.job' % (n_directory, job['job_name']), 'w')
          f.write(job_content_updated)
          f.close()
      cmd = [self.SCHED_SUB, job_script_final]

      # cmd = re.sub('%s.*$' % (job['script_file']),  '%s_%s_final' % (job['script_file'], step),
      #     'xxx__xxxx_xxxx'.join(cmd)).split('xxx__xxxx_xxxx')
      self.log_debug("cmd after: %s" % " ".join(cmd), 4, trace='ACTIVATE_DETAIL')
      self.log_debug("submitting : " + " ".join(cmd), 4, trace='ACTIVATE_DETAIL,CMD,RESTART')
      try:
        if not(self.args.dry):
          output = subprocess.check_output(cmd)
        else:
          output = 'Job_%s' % job['job_name']
        self.log_debug("result of submission:\n%s" % output, 4, trace='ACTIVATE_DETAIL,CMD,RESTART')
      # except subprocess.CalledProcessError as exc:
      #      print(exc.output))
      # else:
      except Exception:
        self.system('cp %s %s_XXXXX' % (job_script_final, job_script_final), force=True)
        still_depends = self.system('grep dependency %s' % job_script_final, force=True)
        if len(still_depends):
          job_still_to_be_activated = still_depends.split('--dependency=afterany:')[1].\
                                    split(" #")[0]
          self.log_debug(('problem in activating job=%s\n script %s   content still contains' + \
                          ' unsolved _waiting dependency: %s \n putting it back on the pile ') \
                         % \
                         (self.print_job(job), \
                          job_script_final, \
                          job_still_to_be_activated))
          self.log_info(('problem in activating job script %s   content still contains ' + \
                        'unsolved _waiting dependency: %s \n putting it back on the pile ') \
                        % \
                        (job_script_final,
                         job_still_to_be_activated))
          self.release_lock(lock_file)
          return (job_still_to_be_activated, "UNKNOWN_DEPENDENCY")
        else:
          job_still_to_be_activated = 'All dependent jobs activated'
          self.error(('problem in activating job=%s\n script %s content still contains unsolved' + \
                      '_waiting dependency: \n  -------------------------  \n %s' + \
                      '\n ----------------------------\nwaiting_job_final_id : ' + \
                      '\n%s \njobs_queued: \n%s\njobs_waiting: \n%s') % \
                     (self.print_job(job),
                      job_script_final,
                      job_still_to_be_activated,
                      pprint.pformat(self.waiting_job_final_id),
                      pprint.pformat(self.jobs_queued),
                      pprint.pformat(self.jobs_waiting)),
                     killall=10, exit=True, exception=True)

      if self.args.pbs:
        # print(output.split("\n"))
        job_id = output.split("\n")[0].split(".")[0]
        waiting_job_id = job['job_id']
        job_id = int(job_id)
        # print(job_id)
      else:
        for l in output.split("\n"):
          self.log_debug(l, 1)
          # print(l.split(" "))
          if "Submitted batch job" in l:
            job_id = int(l.split(" ")[-1])
            waiting_job_id = job['job_id']
            job['job_id'] = job_id

      self.log_debug("job submitted : %s depends on %s" % (job_id, job['dependency']), \
                     1, trace='ACTIVATE_DETAIL,RESTART')
    else:
      self.log_info("should submit job %s (%s)" % (job['job_name'], job['array'][0:20]))
      self.log_info(" with cmd = %s " % " ".join(cmd), 2)
      job_id = "%s" % job['job_name']

    job_script_updated = open('%s_%s_%s_%s' % \
                              (job['script_file'], job['array'][0:20], \
                               self.args.attempt, job_id), "w")
    for jid in self.waiting_job_final_id.keys():
        new_job_id = self.waiting_job_final_id[jid]
        self.log_debug('replace %s by %s' % (jid, new_job_id))
        job_content_updated = job_content_updated.replace('%s' % jid, '%s' % new_job_id)
    job_script_updated.write(job_content_updated.replace('${SLURM_ARRAY_JOB_ID}', '%s' % job_id))
    job_script_updated.close()

    self.waiting_job_final_id[waiting_job_id] = job_id
    job['job_id'] = job_id
    job['submit_cmd'] = cmd

    job_before = job['dependency']
    if job_before:
      self.JOBS[job_before]['make_depend'] = job_id
    job_after = job['make_depend']
    if job_after:
      if job_after in self.JOBS.keys():
          self.log_debug('job_after=%s' % pprint.pformat(job_after), 3)
          self.log_debug('self.JOBS[job_after]=%s' % pprint.pformat(self.JOBS[job_after]), 3)
          self.JOBS[job_after]['dependency'] = job_id
      else:
          self.log_info('strange... job_after %s does not exists in self.JOBS!!! EXITING......' % \
                        (job_after), 0)
          self.log_debug(('strange... job_after %s does not exists in self.JOBS!!! ' + \
                          'EXITING......\n self.JOBS=%s') % \
                         (job_after, self.print_jobs()), 4, trace='STRANGE')
          sys.exit(1)

    self.JOBS[job_id] = job
    del self.JOBS[waiting_job_id]

    # updating the final id of the jobs in the steps and in the tasks
    jobs_in_same_step = self.STEPS[step]['jobs']
    jobs_in_same_step_updated = []
    for j in jobs_in_same_step:
        if j == waiting_job_id:
            j = job_id
        jobs_in_same_step_updated = jobs_in_same_step_updated + [j]
    self.STEPS[step]['jobs'] = jobs_in_same_step_updated

    jobs_list = self.jobs_list
    jobs_list_updated = []
    for j in jobs_list:
        if j == waiting_job_id:
            j = job_id
        jobs_list_updated = jobs_list_updated + [j]
    self.jobs_list = jobs_list_updated

    for task in RangeSet(job['array']):
        self.TASKS[step][task]['job'] = job_id
        self.TASKS[step][task]['status'] = 'SUBMITTED'
        self.TASKS[step][task]['counted'] = False

    if (registration):
        self.jobs_submitted = self.jobs_submitted + [job_id]
        self.last_job_submited = job_id

    self.JOBS[job_id]['status'] = 'SUBMITTED'
    self.JOBS[job_id]['completion_percent'] = 0
    self.JOBS[job_id]['success_percent'] = 0
    self.JOBS[job_id]['failure_percent'] = 0

    if self.STEPS[step]['status'] == 'WAITING':
        self.STEPS[step]['status'] = 'SUBMITTED'

    self.log_debug('ZZZZZZZZZ job activated:\n%s' % self.print_job(self.JOBS[job_id]), 2)

    self.log_debug("Saving Job Ids...", 1)
    if not(self.args.quick_launch):
        self.save()

    self.log_info(('step %s [%s] activating job %s (for %s) --> ' + \
                   'Job # %s (was %s) <-depends-on %s\njobs_waiting=%s') % \
                  (self.args.step, self.args.taskid, job['job_name'], job['array'], \
                   job_id, waiting_job_id, job['dependency'], self.jobs_waiting), \
                  4, trace='ACTIVATE_DETAIL,ACTIVATE,ACTIVATE_NOTE')

    self.release_lock(lock_file)

    self.log_debug('end of activate_job.', 4, trace='ACTIVATE_DETAIL')
    # self.log_debug('end of activate_job job=%s' % self.print_jobs(),4,trace='ACTIVATE_DETAIL')

    return (job_id, cmd)

  #########################################################################
  # add to self.slurm_args new value coming from a job script file
  #########################################################################

  def create_slurm_parser(self, DEBUG=False):

    self.slurm_parser = argparse.ArgumentParser(description='Slurm parser',
                                                conflict_handler='resolve')
    self.slurm_options = {}

    for o in HELP_MESSAGE.split("\n"):
      o = clean_line(o)
      if o.find("--") > -1:
        options = o.split(' ')
        # typical example will be
        # -M, --clusters=names Comma separated list of clusters to issue
        # --comment=name arbitrary comment
        # --exclusive allocate nodes in exclusive mode when
        # --cpu-freq=min[-max[:gov]] requested cpu frequency (and governor)
        # print len(options), options

        if options[1][0:2] == '--':
          short_option = options[0][:-1]
          long_option = options[1]
          help_message = " ".join(options[2:])
          if long_option.find("=") > -1:
            long_option = long_option.split('=')[0]
            long_option = long_option.split('[')[0]
            if help_message.find('number') > -1:
              if DEBUG:
                print("adding int parsing argument %s %s %s" % \
                             (short_option, long_option, help_message))
              self.slurm_parser.add_argument(short_option, long_option,
                                             type=int, help=help_message)
            else:
              self.slurm_parser.add_argument(short_option, long_option,
                                             type=str, help=help_message)
          else:
            self.slurm_parser.add_argument(short_option, long_option,
                                           action="store_true", help=help_message)
          self.slurm_options[short_option] = long_option[2:]
          self.slurm_options[long_option] = long_option[2:]
        else:
          long_option = options[0]
          help_message = " ".join(options[1:])
          if long_option.find("=") > -1:
            long_option = long_option.split('=')[0]
            long_option = long_option.split('[')[0]
            if help_message.find('number') > -1:
              self.slurm_parser.add_argument(long_option, type=int, help=help_message)
            else:
              self.slurm_parser.add_argument(long_option, type=str, help=help_message)
          else:
            self.slurm_parser.add_argument(long_option, action="store_true", help=help_message)
          self.slurm_options[long_option] = long_option[2:]

  #########################################################################
  # add to self.slurm_args new value coming from a job script file
  #########################################################################

  def complete_slurm_args(self, original_script_content_lines, job):

    self.log_debug('[Decimate:complete_slurm_args] entering', 4, trace='CALL')

    if not(self.slurm_parser):
      self.create_slurm_parser()

    # parsing job_script
    job_file_args = []
    for li in original_script_content_lines:
      if li[:7] == "#SBATCH":
        to_be_parsed = clean_line(li[7:][:-1])
        self.log_debug('from job_file: %s' % to_be_parsed, 1, trace='PARSE')
        job_file_args = to_be_parsed.split(' ') + job_file_args

    self.log_debug('slurm_args before completion: %s' % pprint.pformat(self.slurm_args), \
                   4, trace='PARSE')

    job_file_slurm_args, job_file_extra_args = self.slurm_parser.parse_known_args(job_file_args)
    self.log_debug('slurm_args from job file=%s' % pprint.pformat(job_file_slurm_args), \
                   4, trace='PARSE')

    p_slurm_args = vars(self.slurm_args)
    p_job_file_slurm_args = vars(job_file_slurm_args)

    job_file_args_overloaded = []
    for k, v in p_job_file_slurm_args.items():
      if p_job_file_slurm_args[k]:
        # option present in file is not known yet in slurm_args
        if not(p_slurm_args[k]):
          p_slurm_args[k] = v
          self.log_debug('adding from job_file to slurm_args : --%s=%s' % (k, v), \
                         4, trace='PARSE')
        else:
          job_file_args_overloaded = job_file_args_overloaded + [k]

    for k, v in p_slurm_args.items():
      if p_slurm_args[k]:
        job[k] = v

    return (job, job_file_args_overloaded)

  #########################################################################
  # wrapping job to put control over it
  #########################################################################

  def wrap_job_script(self, job, original_script_content_lines, job_file_args_overloaded):
    self.log_debug("adding prefix and suffix to job %s [%s] : " % (job['script'], job['array']), \
                   4, trace='WRAP')

    l0 = ""

    # analyzing existing scheduler flags...
    args = vars(self.slurm_args)
    l = "###DECIM### Original job script was : %s \n" % os.path.abspath(job['script'])

    self.log_debug('slurm_options=/%s/' % pprint.pformat(self.slurm_options), 4, trace='PARSE')
    self.log_debug('job_file_args_overloaded=/%s/' % job_file_args_overloaded, 4, trace='PARSE')
    for li in original_script_content_lines:
      if li[:7] == "#SBATCH":
        to_be_parsed = clean_line(li[7:][:-1])
        job_file_arg = to_be_parsed.split(' ')[0]
        job_file_arg = job_file_arg.split('=')[0]
        slurm_option = self.slurm_options[job_file_arg].replace('-', '_')
        self.log_debug('from job_file: /%s/ job_file_arg:/%s/ slurm_option:/%s/' % \
                       (to_be_parsed, job_file_arg, slurm_option), 1, trace='PARSE')
        if slurm_option in job_file_args_overloaded:
          self.log_debug('option %s overloaded' % to_be_parsed, 4, trace='PARSE')
          l = l + '###DECIM###' + li[:-1] + \
              ' ### <-- now OVERLOADED by -%s=%s ###\n' % (slurm_option, args[slurm_option])
        else:
          l = l + '###DECIM###' + li
      else:
        l = l + li
      

    self.log_info('after merging job and command line l=\n%s' % l, 2)

    environment_variables = ""
    for env_var in ['PATH', 'LD_LIBRARY_PATH', 'DECIMATE_PATH']:
        environment_variables = environment_variables + "export %s=%s \n" % \
                                (env_var, os.getenv(env_var))

    for env_var in ['PYTHONPATH']:
        environment_variables = environment_variables + "export %s=/tmp:%s:%s \n" % \
                                (env_var, self.SAVE_DIR, os.getenv(env_var))

    if 'partition' in job.keys():
        self.args.partition = job['partition']

    if self.args.print_environment:
      environment_variables = environment_variables + "\n# Environment settings \n\n"
      for env_var in ['PATH', 'LD_LIBRARY_PATH', 'PYTHONPATH',
                      'SLURM_ARRAY_TASK_ID', 'SLURM_ARRAY_JOB_ID']:
        environment_variables = environment_variables + \
                                "echo export %s=$%s \n" % (env_var, env_var)

    environment_variables = environment_variables + "\n# Starting from the right directory \n\n"
    environment_variables = environment_variables + "cd %s \n" % (job['submit_dir'])

    l0 = l0 + ("sleep 1\npython %s/%s --decimate --step %s --attempt __ATTEMPT__ " + \
               "--attempt-initial __ATTEMPT_INITIAL__ --log-dir %s  %s %s %s--spawned ") % \
               ("/tmp",
                os.path.basename(sys.argv[0]), \
                job['job_name'], self.LOG_DIR, "-d " * self.args.debug, "-i " * self.args.info,
                "-m " * self.args.mail_verbosity)

    # taking care of dbatch special case
    l0 = l0.replace('python /tmp/dbatch ','dbatch ') 
    
    l0 = l0 + "--taskid ${SLURM_ARRAY_TASK_ID},__ARRAY__ --jobid ${SLURM_ARRAY_JOB_ID}"
    l0 = l0 + " --max-retry=%s" % self.args.max_retry
    l0 = l0 + " --max-jobs=%s" % self.args.max_jobs
    l0 = l0 + " --workflowid='%s'" % self.args.workflowid
    l0 = l0 + " --filter='%s'" % self.args.filter
    if job['check']:
      l0 = l0 + " --check='%s'" % job['check']

    if self.args.partition:
        l0 = l0 + " --partition='%s'" % self.args.partition

    if self.args.account:
        l0 = l0 + " --account='%s'" % self.args.account

    if self.args.mail:
      l0 = l0 + " --mail %s " % self.args.mail

    if self.args.banner:
      l0 = l0 + " --banner "

    if self.args.yalla:
      l0 = l0 + " --yalla "

    if self.args.nocleaning:
      l0 = l0 + " --nocleaning "

    if self.args.all_released:
      l0 = l0 + " --all-released"

    if self.args.test:
      l0 = l0 + " --test %s" % self.args.test

    if self.args.parameter_file:
      l0 = l0 + " --parameter-file %s" % self.args.parameter_file

    if self.args.parameter_filter:
      l0 = l0 + " --parameter-filter %s" % self.args.parameter_filter

    if self.args.parameter_range:
      l0 = l0 + " --parameter-range %s" % self.args.parameter_range

    if self.args.fake:
      l0 = l0 + " --fake"
      l = '#!/bin/bash\n#JOB_FAKE\n'
      l = l + """echo "I am task ${SLURM_ARRAY_TASK_ID} on node `hostname`" \n""" + \
          """echo "Main jobid is: ${SLURM_JOB_ID}" \n"""

      l = l + l0

    # handling more general dependency
    #  on waiting jobs
    #  on job names
    #

    if job['dependency']:
      initial_dependency = job['dependency']

      # the dependency corresponds to a waiting job that has been
      # scheduled since --> replacing it
      if job['dependency'] in self.waiting_job_final_id.keys():
        job['dependency'] = self.waiting_job_final_id[job['dependency']]

      # in last resort checking if the dependency corresponds to
      # a step name... if yes --> replacing it
      if not(job['dependency'] in self.JOBS.keys()):
        step_names = map(lambda k: k[0].split('-')[:-1][0], self.STEPS.items())
        step_names.sort()
        if not(job['dependency'] in step_names):
          # dependency isn't even a job name --> sending an error
          self.error(('jobs depends on unknown job id or name : %s' + \
                      '\n   dependency required was not even found in job names' + \
                      '\n    ---> (%s)     ') % \
                     (initial_dependency, ",".join(step_names)), exit=True)
        # job name exists matching this dependency
        # trying to gather the last attempt of it
        job_found = None
        for k, step in self.STEPS.items():
          if k.split('-')[:-1][0] == job['dependency']:
             job_found = k
        if not(job_found):
          self.error(('jobs depends on unknown job id or name : %s\n   Weird... ' + \
                      'it was found exisiting in job_names though... \n    ---> (%s)') % \
                     (initial_dependency, ",".join(self.STEPS.keys())), exit=True)
        else:
          self.log_info(('Dependency %s was found in job names.' + \
                         '\n\tConcerned step is %s \n\t  with jobs (%s)') % \
                        (initial_dependency, job_found, ",".\
                         join(map(lambda x:str(x), self.STEPS[job_found]['jobs']))), 1)
          job['dependency'] = self.STEPS[job_found]['jobs'][-1]

      if job['dependency'] in self.waiting_job_final_id.keys():
        job['dependency'] = self.waiting_job_final_id[job['dependency']]

      # checking if dependency points to a known job

      if not(job['dependency'] in self.JOBS.keys()):
        self.error('jobs depends on unknown job id or name : %s ' % initial_dependency, exit=True)

    prefix = '#!/bin/bash\n'

    prefix = prefix + "\n# Copying often accessed files into node's /tmp directory\n\n"
    files_to_sync = "%s/*py*" % (self.SAVE_DIR) + \
                    " ".join(self.files_to_copy_to_tmp)

    # no need apriory to copy dbatch in /tmp
    # we are treating python /tmp/dbatch as a special case
    # when wrapping the job
    #
    # for f in ['dbatch','dstat']:
    #   decimate_cmd=self.system('which %s' % f)[:-1]
    #   files_to_sync = files_to_sync + " " + decimate_cmd

    prefix = prefix + RSYNC_CMD % files_to_sync 

                     # '\n# Setting Environment variables and preparing node\n\n%s\n' % 
                     # environment_variables + 

    check_previous = \
                     '# Checking the status of previous Jobs\n' + \
                     '\n%s  --check-previous-step \n' % (l0) + \
                     "if [ $? -ne 0 ] ; then\n" + \
                     '   echo "[ERROR] FAILED in precedent step : ' + \
                     'stopping current job and reconnecting..."\n' + \
                     "    exit 1\n" + \
                     "fi\n\n"

    if job['yalla']:
      tasks = []
      for t in RangeSet(job['array']):
          tasks = tasks + [t]
      prefix = prefix + \
               check_previous.replace('${SLURM_ARRAY_TASK_ID}', '%s' % tasks[0]).\
               replace('${SLURM_ARRAY_JOB_ID}', '${SLURM_JOB_ID}').\
               replace('--check-previous-step', \
                       '--check-previous-step > %s.checking.out 2> %s.checking.err' % \
                       (job['job_name'], job['job_name']))
      prefix = prefix + \
               '\n# Defining main loop of tasks in replacemennt for job_array\n\n' + \
               ('cat >> %s.job.__ARRAY__ << EOF \n#!/bin/bash\n' % job['job_name'])
      prefix = prefix + "cd %s \n" % (job['submit_dir'])

      prefix0 = ""
    else:
      prefix0 = check_previous
      if self.args.parameter_file:
        prefix0 = prefix0 + '\n#Sourcing parameters taken from file: %s ' % \
                  self.args.parameter_file
        # prefix0 = prefix0 + '\necho Sourcing parameters taken from file: %s ' % \
        #           self.args.parameter_file
        # prefix0 = prefix0 + '\necho --- parameters set here --------------'
        # prefix0 = prefix0 + '\ncat  /tmp/parameters.${SLURM_ARRAY_TASK_ID}'
        # prefix0 = prefix0 + '\necho --------------------------------------'
        
        
        prefix0 = prefix0 + '\n.  /tmp/parameters.${SLURM_ARRAY_TASK_ID}'
        # prefix0 = prefix0 + '\nrm /tmp/parameters.${SLURM_ARRAY_TASK_ID}'
      


    l = prefix0 + "\n\n# Starting user job\n" + \
        "\n# ---------------- START OF ORIGINAL USER SCRIPT  -------------------\n" + \
        l.replace('#DECIM PROCESS_TEMPLATE_FILES',
                  '# should replace template here returning in the right directory \n\n' +\
                  "HERE_TO_PROCESS=$PWD \n (cd %s;" % (job['submit_dir'])  +\
                  '%s --process-templates $HERE_TO_PROCESS; cd - )' % l0)\
                  .replace('#DECIM SHOW_PARAMETERS','cat  /tmp/parameters.${SLURM_ARRAY_TASK_ID}')  \
        + "\n# ----------------   END OF ORIGINAL USER SCRIPT  -------------------\n\n"

    l = l + """
          if [ $? -ne 0 ] ; then
              echo "[ERROR] FAILED in current step : exiting immediately..."
              #exit 1
          else """ + '\n\n ################# finalizing job ####################\n'
    if self.args.fake:
        l = l + l0 + ' --finalize --fake\n'
    else:
        l = l + "\n# returning in the right directory \n\n"
        l = l + "cd %s \n" % (job['submit_dir'])
        l = l + '      \n# Touching file to signify the job reached its end\n\n'
        l = l + '           touch %s/Done-%s-${SLURM_ARRAY_TASK_ID}\n           ' % \
            (self.SAVE_DIR, job['job_name'])
        l = l + l0 + ' --finalize \n'

    l = l + "\n          fi       # closing if of successfull job \n"

    self.log_debug('wrap job before yalla filling =%s' % self.print_job(job), \
                   4, trace='WRAP')

    if job['yalla']:
      stream = {}
      for w in ['output', 'error']:
        s = job[w].replace('%J', '\$SLURM_JOB_ID').replace('%j', '\$SLURM_JOB_ID')\
            .replace('%a', '\${task}')
        stream[w] = s + '.task_\${formatted_task}-attempt_%s' % job['attempt']
      
      l = prefix + (l).replace('$', '\$') + 'EOF\n'

      # l = l + \
      #     'export SLURM_ARRAY_JOB_ID=$SLURM_JOB_ID \n' +\
      #     'for task in __ARRAY_UNFOLD__; do\n ' +\
      #     '  export SLURM_ARRAY_TASK_ID=$task \n ' + \
      #     '  formatted_task=$(printf "%04d" $task) \n' + \
      #     '  . ./%s.job.__ARRAY__  > %s 2>  %s \n' % \
      #             (job['job_name'],stream['output'],stream['error']) + \
      #     "done\n"

      input_file = "%s/job.%s" % (self.YALLA_DIR, self.machine)
      output = "".join(open(input_file, "r").readlines())
      output = output.replace('__save_dir__', self.SAVE_DIR)
      output = output.replace('__PARALLEL_RUNS__', str(job['yalla_parallel_runs']))
      output = output.replace('__NB_NODES_PER_PARALLEL_RUNS__', str(job['nodes']))
      output = output.replace('__NB_CORES_PER_PARALLEL_RUNS__', str(job['ntasks']))
      output = output.replace('__job_name__', str(job['job_name']))
      output = output.replace('__job_array__', str(job['array']))
      output = output.replace('__job_output__', stream['output'])
      output = output.replace('__job_error__', stream['error'])
      output = output.replace('__NB_JOBS__', str(len(RangeSet(job['array']))))
      output = output.replace('__job_submit_dir__', job['submit_dir'])
      
      if self.args.debug:
        output = output.replace('__DEBUG__', 'debug')
      else:
        output = output.replace('__DEBUG__', '')

      f = open('%s/YALLA/%s.yalla_job' % (self.SAVE_DIR, job['job_name']), 'w')
      f.write(output)
      f.close()

      l = l + '\n\n# Yalla container execution...\n\n'
      l = l + output
    else:
      l = prefix + l

      # l = l + '\n\n# Cleaning the node before releasing it\n\n\\rm -rf /tmp/*py'

    self.log_info('end fo =\n%s' % l, 2)
    return (l, job)

  #########################################################################
  # submitting all the first jobs
  #########################################################################

  def launch_jobs(self, **optional_parameters):
      lock_file = self.take_lock(self.FEED_LOCK_FILE)

      # self.args.quick_launch = True
      if self.args.quick_launch:
          self.args.quick_launch_no_load = True

      self.log_info('=============== New workflow starting ==============', 1)
      self.log_info('ZZZ cleaning workspace before launching ...', 2)
      self.log_info('=============== New workflow starting ==============', 2)

      os.system(('\\rm -rf *.err *.out *.pickle *.pickle.old .%s/SAVE/*.pcy*' + \
                 ' .%s/SAVE/Done* .%s/SAVE/*job+_*') % \
                (self.APPLICATION_NAME, self.APPLICATION_NAME, self.APPLICATION_NAME))

      for f in glob.glob("*.py"):
        self.log_debug("copying file %s into SAVE directory " % f, 1)
        os.system("cp ./%s  %s" % (f, self.SAVE_DIR))

      epoch_time = int(time.time())
      st = "%s+%s+%s" % (self.APPLICATION_NAME, os.getcwd(), epoch_time)
      current_dir = os.getcwd().split('/')[-1]
      self.args.workflowid = "%s_at_%s_%s_%s " % \
                             (self.APPLICATION_NAME, current_dir,
                              epoch_time, reduce(lambda x, y:x + y, map(ord, st)))
      self.set_mail_subject_prefix('Re: %s' % (self.args.workflowid))
      self.send_mail('=============== New workflow starting ==============')

      self.user_launch_jobs(**optional_parameters)

      if self.args.mail:
        self.send_mail('Workflow has just been submitted')

      self.feed_workflow()

      if not(self.args.quick_launch):
          self.save(take_lock=False)

      self.log_debug("after feed_workflow in launch_jobs, self.STEPS=[%s]" % \
                     ",".join(self.STEPS.keys()), 4, trace='FEED,LAUNCH')
      self.release_lock(lock_file)

      if not(self.args.decimate):
        self.tail_log_file(nb_lines_tailed=1, no_timestamp=True,
                           stop_tailing=['workflow is finishing', 'workflow is aborting'])
      sys.exit(0)

  def user_launch_jobs(self):
        self.error_report("launch_jobs needs to be valued", exit=True)

  #########################################################################
  # submitting on the fly additional jobs
  #########################################################################

  def feed_workflow(self, from_finalize=False):

    lock_file = self.take_lock(self.LOCK_FILE)
    self.log_debug('entering feed_workflow  TASK_ID=%s  TASK_IDS=%s' % \
                   (self.TASK_ID, self.TASK_IDS), 4, trace='FEED_DETAIL,LOAD')
    self.load()
    # add new jobs
    if self.TASK_ID == RangeSet(self.TASK_IDS)[0] or not(self.args.spawned):

        self.log_debug('feed_workflow: trying to activate jobs', 1, trace='FEED_DETAIL')

        # count how many jobs are running
        jobs_queued = self.get_current_jobs_status(in_queue_only=True, take_lock=False)

        nb_jobs_running_or_queued = len(jobs_queued)

        nb_jobs_running_or_queued_computed = 0
        jobs_waiting = []
        nb_jobs_waiting = 0
        jobs_queued_computed = []
        # print(pprint.pformat(self.STEPS))
        # print(pprint.pformat(self.JOBS))
        # print(pprint.pformat(self.TASKS))
        for j in self.jobs_list:
            job = self.JOBS[j]
            status = job['status']
            nb_jobs = len(RangeSet(job['array']))
            self.log_debug('feed_workflow: status of job %s ([%s]):%s  size:%s' % \
                           (j, job['array'], status, nb_jobs), 1, trace='FEED_DETAIL')
            if status == 'WAITING':
                jobs_waiting = jobs_waiting + [j]
                nb_jobs_waiting = nb_jobs_waiting + nb_jobs

            elif not(status in ['DONE', 'ABORTED', 'WAITING']):
                nb_jobs_running_or_queued_computed += 1
                jobs_queued_computed = jobs_queued_computed + [j]

        self.log_debug('feed_workflow: %d jobs_queued' % (len(jobs_queued)), \
                       1, trace='FEED_DETAIL')
        self.log_debug('feed_workflow: %d jobs_queued:%s' % \
                       (len(jobs_queued), pprint.pformat(jobs_queued)), \
                       2, trace='FEED_DETAIL')
        self.log_debug('feed_workflow: %d jobs_waiting:%s' % \
                       (len(jobs_waiting), ','.join(map(lambda x:str(x), jobs_waiting))), \
                       1, trace='FEED_DETAIL,FEED')

        self.jobs_queued = jobs_queued  # saved for debug reason
        self.jobs_waiting = jobs_waiting  # saved for debug reason

        if nb_jobs_waiting > 0:
            self.log_debug("self.args.max_jobs(%d)-nb_jobs_running_or_queued(%d)=%d" % \
                           (self.args.max_jobs, nb_jobs_running_or_queued, \
                            self.args.max_jobs - nb_jobs_running_or_queued), \
                           1, trace='FEED_DETAIL')

            if from_finalize:
              # my own job is dying, removing it from running job
              nb_jobs_running_or_queued = nb_jobs_running_or_queued - 1
            nb_jobs_to_add = min(self.args.max_jobs - nb_jobs_running_or_queued, nb_jobs_waiting)
            self.log_debug('feed_workflow: nb_jobs_to_add=%s' % nb_jobs_to_add, \
                           1, trace='FEED_DETAIL,FEED')
            # activate additional jobs if under max_running_jobs threshold
            if nb_jobs_to_add > 0:
                nb_job_added = 0
                self.log_debug('feed_workflow: job_waiting=[%s] ' % \
                               (",".join(map(lambda x:str(x), self.jobs_waiting))), \
                               1, trace='FEED_DETAIL,ACTIVATE_NOTE')
                while nb_job_added < nb_jobs_to_add and len(self.jobs_waiting):
                    job_to_add = self.jobs_waiting[0]
                    job = self.JOBS[job_to_add]
                    job_range = RangeSet(job['array'])
                    self.log_debug('feed_workflow: activating job %s (%s) ' % \
                                   (job_to_add, job['array']), \
                                   1, trace='FEED_DETAIL,ACTIVATE_NOTE')
                    (job_id, cmd) = self.activate_job(job, take_lock=False)
                    self.log_debug('feed_workflow: activating job %s (%s) (was %s) -> job # %s' % \
                                   (job['step'], job['array'], job_to_add, job_id), \
                                   1, trace='FEED_DETAIL,FEED')
                    if cmd == "UNKNOWN_DEPENDENCY":
                      self.jobs_waiting = [job_id] + self.jobs_waiting
                    else:
                      self.jobs_waiting.pop(0)
                      nb_job_added = nb_job_added + len(job_range)
    else:

        self.log_debug('feed_workflow: Not my job!!!', 1, trace='FEED_DETAIL')

    # add new tasks (> breakit)
    self.release_lock(lock_file)

###################################################################################################
# interactive console
###################################################################################################

  #########################################################################
  # init_console
  #########################################################################

  def init_console(self):

    self.console_current_step_names = None
    self.console_step_filter = None
    self.console_current_step_name = None
    self.console_current_tasks = None
    self.console_current_task = None
    self.console_current_jobs = None
    self.console_current_job = None
    self.show_zeroed_files = False
    self.load_console()

  #########################################################################
  # save_workspace
  #########################################################################

  def save_console(self, take_lock=True):

    if not(self.CanLock):
        return

    self.log_debug('entering save()', 4, trace='SAVE')
    #
    if take_lock or True:
        lock_file = self.take_lock(self.CONSOLE_LOCK_FILE)
        self.log_debug('save_console: Taking the lock', 4, trace='SAVE')

    # could need to load workspace and merge it

    # print("saving variables to file "+workspace_file)
    workspace_file = self.CONSOLE_SAVE_FILE
    self.pickle_file = open(workspace_file + ".new", "wb")
    pickle.dump(self.console_step_filter, self.pickle_file)
    pickle.dump(self.console_current_step_names, self.pickle_file)
    pickle.dump(self.console_current_step_name, self.pickle_file)
    pickle.dump(self.console_current_tasks, self.pickle_file)
    pickle.dump(self.console_current_task, self.pickle_file)
    pickle.dump(self.console_current_jobs, self.pickle_file)
    pickle.dump(self.console_current_job, self.pickle_file)
    pickle.dump(self.show_zeroed_files, self.pickle_file)
    self.pickle_file.close()
    if os.path.exists(workspace_file):
      os.rename(workspace_file, workspace_file + ".old")
    os.rename(workspace_file + ".new", workspace_file)

    if take_lock or True:
        self.log_debug('save_console: releasing the lock', 4, trace='SAVE')
        self.release_lock(lock_file)
    self.log_debug('leaving save_console()', 4, trace='SAVE')

  #########################################################################
  # load_workspace
  #########################################################################

  def load_console(self, take_lock=True):

    #
    self.log_debug('entering load_console()', 4, trace='SAVE')
    if take_lock or True:
        lock_file = self.take_lock(self.CONSOLE_LOCK_FILE)
        self.log_debug('load: Taking the lock', 4, trace='SAVE')

    try:
      if os.path.exists(self.CONSOLE_SAVE_FILE):
          self.pickle_file = open(self.CONSOLE_SAVE_FILE, "rb")
          self.console_step_filter = pickle.load(self.pickle_file)
          self.console_current_step_names = pickle.load(self.pickle_file)
          self.console_current_step_name = pickle.load(self.pickle_file)
          self.console_current_tasks = pickle.load(self.pickle_file)
          self.console_current_task = pickle.load(self.pickle_file)
          self.console_current_jobs = pickle.load(self.pickle_file)
          self.console_current_job = pickle.load(self.pickle_file)
          self.show_zeroed_files = pickle.load(self.pickle_file)
          self.pickle_file.close()
      else:
          self.console_current_step_names = self.steps_critical_path_with_attempt
          self.console_step_filter = 'CRITICAL'
          self.console_current_step_name = self.steps_submitted[-1]
    except Exception:
        self.error(('[load]  problem encountered while loading current console ' + \
                    '\n---->  rerun with -d to have more information'),
                    exit=True, exception=True)  # self.args.debug)

    try:
        step = self.STEPS[self.console_current_step_name]
    except Exception:
        self.console_current_step_name = self.steps_submitted[0]
        step = self.STEPS[self.steps_submitted[0]]
    # self.log_debug('self.STEPS in load_console  : %s' % pprint.pformat(self.STEPS),
    #               4, trace='SAVE_STEPS')

    self.console_current_tasks = step['array']
    self.console_current_task = step['array'][0]
    try:
      self.console_current_jobs = RangeSet(",".join(map(lambda x:str(x), step['jobs'])))
    except Exception:
      self.console_current_jobs = step['jobs']
    self.console_current_job = step['jobs'][0]

    if take_lock or True:
        self.release_lock(lock_file)
        self.log_debug('load_console():releasing lock', 4, trace='SAVE')

    self.log_debug('leaving load_console()', 4, trace='SAVE')

  #########################################################################
  # explore workflow initialization
  #########################################################################

  def initialize_explore_workflow(self):
    try:
      rows, columns = subprocess.check_output(['stty', 'size']).decode().split()
      self.rows = int(rows) - 2
      self.columns = int(columns)
      self.log_debug('terminal size (%s,%s)' % (self.rows, self.columns), 4, trace='TERM')
    except Exception:
      self.rows = 10
      self.columns = 80
      self.log_info('WARNING terminal was not identified, abitrary size (%s,%s) taken' % \
                    (self.rows, self.columns), 0, trace='TERM')

    self.print_workflow()

    if len(self.STEPS) == 0:
        return

    self.init_console()
    self.load_console()

    self.user_name = os.getenv("USER")
    self.last_x = self.current_x = self.previous_x = 's'

    self.args.input = 'r' + self.args.input

  #########################################################################
  # explore workflow
  #########################################################################

  def explore_workflow(self):

    self.initialize_explore_workflow()

    self.menu_keys = 'bBeEgGoOrRdDiIJkKlLmMp:;PhHsStuTXvzZ+-*.,/|\\'

    self.console_help()
    self.general_info()

    x = ''
    while not(x == "X"):
      x = self.getkey()
      self.react_on_key(x)
    self.save_console()
    sys.exit(0)

  def react_on_key(self, x):
      if x in ['b', 'B']:
          squeue_base_user = 'squeue -l -o "%.20i %.6P %.15j %.8T %.10M %.9l %.6D %R" '
          squeue_base_all = 'squeue -l -o "%.20i %.6P %.15j %.8u %.8T %.10M %.9l %.6D %R" '
          if x == 'b':
            cmd = ' %s  -u ' % squeue_base_user + self.user_name + ' | more'
          else:
            cmd = ' %s | more' % squeue_base_all
          os.system(cmd)
      elif x == 'z':
          cmd = 'sinfo'
          os.system(cmd)
      elif x == 'Z':
          self.show_zeroed_files = not(self.show_zeroed_files)
          self.general_info()
      elif x == 'u':
        self.initialize_explore_workflow()
      elif x == 'v':
        if self.file_chosen:
          os.system('EDITOR=vi less %s' % (self.file_chosen))
      elif x in ["l", 'L']:
        if x == 'L':
          self.print_workflow(all_steps=True)
        else:
          self.print_workflow()
      elif x in ['p', ';', ':', 'P', '+', '-', '*', '/', ',', '.']:
          self.log_debug(' >%s< hit and last_x=>%s< previous_x=>%s<' % \
                         (x, self.last_x, self.previous_x), 4, trace='KEY')
          if x in ['+', '-', 'p', ';', ':', 'P']:
            candidates = self.console_current_tasks
            current = self.console_current_task
          elif x in ['/', '*']:
            candidates = self.console_current_step_names
            current = self.console_current_step_name
          else:
            candidates = self.console_current_jobs
            current = self.console_current_job
          possibles = []
          for t in RangeSet(candidates):
            possibles = possibles + [t]
          nb_candidates = len(possibles)
          self.log_debug('searching %s in possible choice:%s' % (current, possibles), \
                         4, trace='KEY')
          previous_possible = possibles[-1]
          possibles = possibles + possibles[0:]
          if len(possibles) > 1:
            item_found = False
            self.log_debug('possibles=%s' % ",".join(map(lambda x:str(x), possibles)))
            while len(possibles) and not(item_found):
              t = possibles.pop(0)
              next_possible = possibles[0]
              self.log_debug('scanning %s, result=%s next=%s previous=%s' % \
                             (t, ('%s' % current == '%s' % t), next_possible, previous_possible), \
                             4, trace='KEY')
              if ('%s' % current == '%s' % t):
                  if x == '-':
                    self.console_current_task = previous_possible
                  elif x == '/':
                    self.console_current_step_name = previous_possible
                  elif x == '+':
                    self.console_current_task = next_possible
                  elif x == 'p':
                    self.console_current_task = possibles[9]
                  elif x == 'P':
                    self.console_current_task = possibles[99]
                  elif x == ';':
                    self.console_current_task = possibles[nb_candidates - 11]
                  elif x == ':':
                    self.console_current_task = possibles[nb_candidates - 101]
                  elif x == '*':
                    self.console_current_step_name = next_possible
                  elif x == '.':
                    self.console_current_job = next_possible
                  elif x == ',':
                    self.console_current_job = previous_possible
                  if x in ['*', '/']:
                    step = self.STEPS[self.console_current_step_name]
                    self.console_current_tasks = step['array']
                    self.console_current_task = step['array'][0]
                    try:
                      self.console_current_jobs = \
                              RangeSet(",".join(map(lambda x:str(x), step['jobs'])))
                    except Exception:
                      self.console_current_jobs = step['jobs']
                    try:
                        self.console_current_job = step['jobs'][0]
                    except Exception:
                        self.error('could not get first job for step: %s ' % \
                                   self.print_job(step, print_only=step.keys()), \
                                   exit=True, exception=True)
                        self.console_current_job = 0
                  self.log_debug(' >%s< hit and last_x=>%s< previous_x=>%s<' % \
                                 (x, self.last_x, self.previous_x), 4, trace='KEY')
                  self.args.input = self.previous_x + self.args.input
                  item_found = True
                  self.save_console()
              previous_possible = t
          # print(self.args.input)
          # sys.exit(0)
      elif x in ["s", "S"]:
          if x == "s":
              steps = self.console_current_step_names = self.steps_critical_path_with_attempt
              self.console_step_filter = 'CRITICAL'
          else:
              steps = self.console_current_step_names = self.steps_in_order
              self.console_step_filter = 'SUBMITTED'
          self.general_info()
          self.console_current_steps = steps
          new_step = self.choose_in_set(steps)
          if new_step:
            self.console_current_step_name = new_step
            step = self.STEPS[self.console_current_step_name]
            self.console_current_tasks = step['array']
            try:
                self.console_current_jobs = RangeSet(",".join(map(lambda x:str(x), step['jobs'])))
            except Exception:
                self.console_current_jobs = step['jobs']
            self.console_current_job = step['jobs'][0]
            self.console_current_task = step['array'][0]
            self.save_console()
      elif x in ["j"]:
          step = self.STEPS[self.console_current_step_name]
          self.console_current_jobs = RangeSet(",".join(map(lambda x:str(x), step['jobs'])))
          self.console_current_job = step['jobs'][0]
          new_job = self.choose_in_set(RangeSet(self.console_current_jobs))
          if new_job:
            self.console_current_jobs = new_job
            self.save_console()
      elif x in ["t"]:
          step = self.STEPS[self.console_current_step_name]
          self.console_current_tasks = step['array']
          new_task = self.choose_in_set(RangeSet(self.console_current_tasks))
          if new_task:
            self.console_current_tasks = new_task
            self.save_console()
      elif x in ["i", "I"]:
        s = self.STEPS[self.console_current_step_name]
        print('step %s:\n%s' % (self.console_current_step_name, \
                                self.print_job(s, short_format=(x == "i"), print_only=s.keys())))
      elif x in ["k", "K"]:
        s = self.STEPS[self.console_current_step_name]
        for task in RangeSet(self.console_current_tasks):
          task_nb = int(task)
          if x == "K" or int(self.console_current_task) == task_nb:
            t = self.TASKS[self.console_current_step_name][task_nb]
            print('task %s.%s:\n%s' % (self.console_current_step_name, task_nb, \
                                       self.print_job(t, print_only=t.keys())))
      elif x in ['m', 'M']:
        # for job_id in RangeSet(self.console_current_jobs):
          # job = self.JOBS[job_id]
          job_id = self.console_current_job
          job = self.JOBS[job_id]
          if x == 'm':
              print('job %s.%s:\n%s' % (self.console_current_step_name, \
                                        job_id, \
                                        self.print_job(job, print_only=job.keys())))
          else:
              print('job %s.%s:\n%s' % (self.console_current_step_name, \
                                        job_id, \
                                        self.print_job(job, filter=None, print_only=job.keys())))
      elif "rReEoOdDgG\|".find(x) > -1:
        file_list = []
        if "REO".find(x) > -1:
          tasks_to_list = RangeSet(self.console_current_tasks)
        else:
          tasks_to_list = [self.console_current_task]
        for task in tasks_to_list:
          task_nb = int(task)
          t = self.TASKS[self.console_current_step_name][task_nb]
          job_id = t['job']
          try:
            job = self.JOBS[job_id]
          except Exception:
            self.error('job_id %s not known in self.JOBS for step %s  task %s' % \
                       (job_id, self.console_current_step_name, task_nb), exception=True, exit=False)
            # self.ask("continue ? ", default='y' )
            continue
          error_mask = job['error'].replace('%j', '*').replace('%J', '*').replace('%a', '*')
          output_mask = job['output'].replace('%j', '*').replace('%J', '*').replace('%a', '*')
          files_error = files_output = ''
          if x in ['o', 'O', 'r', 'R']:
            files_output = '%s*.task_%04d*' % (output_mask, task_nb)
          if x in ['e', 'E', 'r', 'R']:
            files_error = '%s*.task_%04d*' % (error_mask, task_nb)
          if x in ['d', 'D']:
              dir_output = os.path.dirname(job['error'])
              file_list = glob.glob('./%s/*' % dir_output)
              file_list.sort()
          elif x in ['g', 'G']:
              dir_output = 'generate'
              file_list = glob.glob('%s/*' % dir_output)
              file_list.sort()
          elif x in ['\\']:
              dir_output = self.SAVE_DIR
              file_list = glob.glob('%s/*' % dir_output)
              file_list.sort()
          elif x in ['|']:
              dir_output = self.LOG_DIR
              file_list = glob.glob('%s/*' % dir_output)
              file_list.sort()
          else:
              file_list = file_list + glob.glob(files_error) + glob.glob(files_output)
        self.last_x = self.current_x
        if len(file_list):
          choices = []
          file_list.sort()
          for f in file_list:
            try:
              stat = os.stat(f)
              sz = stat.st_size
              # mode = stat[ST_MODE]
              tm = time.ctime(stat.st_mtime)
              format_beg = format_end = ""
              if os.path.isdir(f):
                format_beg = colors.BLUE
                f = f + '/'
              elif os.path.islink(f):
                format_beg = colors.GREEN
                f = f + ' ->'
              elif sz > 0:
                format_beg = colors.BOLD
              format_end = colors.END
              if sz > 0 or self.show_zeroed_files:
                choices = choices + ["%21s %09s   %s%s%s" % (tm, sz, format_beg, f, format_end)]
            except Exception:
              sz = '?'
              tm = '?'
              choices = choices + ["%21s %09s   %s" % (tm, sz, f)]
          self.log_debug('list of files : [%s]' % ','.join(file_list), 4, trace='KEY')
          if len(choices):
            (choice, extra_choices, current_choices, offset) = \
                   self.choose_in_set(choices, get_choices=True)
            if choice:
              self.file_chosen = file_chosen = \
                   choice.split(" ")[-1].replace(colors.BOLD, "").replace(colors.END, "")
              more_file_chosen = True
              while more_file_chosen:
                print()
                print()
                first_dashes_length = (80 - len(file_chosen)) / 2
                second_dashes_length = 80 - first_dashes_length - len(file_chosen) - 2
                more_what = '-' * first_dashes_length + ' %s ' % \
                   file_chosen + '-' * second_dashes_length
                if False:
                    print(more_what)
                    os.system('more %s' % file_chosen)
                    print(more_what)
                try:
                    f_lines = open(file_chosen, 'r').readlines()
                except Exception:
                    f_lines = ["Problem found while opening file %s" % file_chosen]
                    return
                i = 0
                for f in f_lines:
                  f_lines[i] = f[:-1]
                  i = i + 1
                lines = [more_what] + f_lines + [more_what]
                self.log_debug('calling more with %s lines...' % len(lines), 4, trace='KEY')
                self.choose_in_set(lines, line_number=False, extra_choices=extra_choices)
                self.log_debug(('back from more  self.current_key=%s' + \
                                ' self.args.inputs=%s extra_choices=%s') % \
                               (self.current_x, self.args.input, extra_choices), 4, trace='KEY')
                if len(self.args.input):
                  if self.args.input[0] in extra_choices:
                    new_choice = self.args.input[0]
                    self.args.input = self.args.input[1:]
                    position = extra_choices[offset:].index(new_choice) + offset
                    file_chosen = file_list[position]
                    self.log_debug('new_choice=%s, position=%s, file_list=[%s], file_chosen=%s' % \
                                   (new_choice, position, ",".join(file_list), file_chosen), \
                                   4, trace='KEY')
                    self.general_info()
                    print(current_choices)
                  else:
                    more_file_chosen = False
                    self.general_info()
                    return
          else:
            print('\t  ---- nothing at all ----')
        else:
          print('\t  ---- nothing at all ----')
      elif x == "h":
          self.console_help()
      elif x == "X":
          sys.exit(0)
      else:
          return

      x = self.getkey()
      if not(x in self.menu_keys):
        self.args.input = self.last_x + self.args.input
      else:
        self.args.input = x + self.args.input
        if not(x in ['p', ';', ':', 'P', '+', '-', '*', '/', '.', ',']):
          self.last_x = x
        else:
          self.current_x = self.last_x

      self.general_info()

      sys.stdout.flush()

  def general_info(self):
      if not(self.args.no_clear_screen):
          print "\033[H\033[J",
      if False:
          print('Current explored step  : %s from [%s]' % \
                   (self.console_current_step_name, self.console_step_filter))
          print('Current explored jobs : %s ' % self.console_current_jobs)
          print('Current explored task : %s from [%s] ' % \
                   (self.console_current_task, self.console_current_tasks))
      else:
          if self.show_zeroed_files:
            zeroed_files = 'YES'
          else:
            zeroed_files = 'NO'
          print('\rstep %s from [%s]' % \
                (self.console_current_step_name, self.console_step_filter) + \
                '- jobs %s from %s (j for more)' % \
                (self.console_current_job, len(self.console_current_jobs)) + \
                '- task %s from [%s] ' % (self.console_current_task, self.console_current_tasks) + \
                '  [0 files %s] ' % zeroed_files)
      self.log_debug('general info last_x=>%s< previous_x=>%s<' % \
                         (self.last_x, self.previous_x), 4, trace='KEY')

  def console_help(self):

      print("\n\t --------------- Press a key ----------------\n")
      print("\t l) status            \t b) info on my jobs in queue")
      print("\t z) sinfo             \t B) info on all jobs in queue")
      print("\t s) change step       \t S) same in all steps submitted")
      print("\t t) change task       \t a) change attempt number ")
      print("\t i) info current step \t j) info current task")
      print("\t m) info current job  \t ?) ??????")
      print("\t *) next step         \t /) previous step")
      print("\t +) next task         \t -) previous task")
      print("\t p) task + 10         \t P) task + 100")
      print("\t ;) task - 10         \t :) task - 100")
      print("\t d) ls dir            \t D) same with -l ")
      print("\t r) ls out & err      \t R) same with -l ")
      print("\t o) print output.log  \t e) print error.logr")
      print("\t h) print this screen \t X) quit\n")

  def choose_in_set(self, choices, on_key_return=None, line_number=True, \
                    get_choices=False, extra_choices=''):
      if on_key_return is None:
          on_key_return = self.menu_keys
      on_key_return = on_key_return + extra_choices
      possible_indice = '1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ' + \
                        '!@#$%^&*()_+=-[]{};:",./<>`~'
      if len(on_key_return):
         filtered_indice = ''
         while len(possible_indice):
           x = possible_indice[0]
           possible_indice = possible_indice[1:]
           if on_key_return.find(x) == -1:
              filtered_indice = filtered_indice + x
      else:
          filtered_indice = possible_indice
      i = 0
      choice_list = []
      for c in choices:
          choice_list = choice_list + [c]
      choice_list_initial = choice_list
      indexed_choices = {}
      current_choices_keys = ""
      more_message = False
      self.log_debug('choice_list=>%s<' % choice_list, 4, trace='CHOICE')
      choice_made = False
      while not(choice_made):
        j = 0
        i = 0
        offset = 0
        current_choices = ""
        if more_message > 1:
          print "\r" + " " * 80 + "\r",
          more_message = more_message - 1
        if len(choice_list) == 0:
            choice_list = choice_list_initial
            indexed_choices = {}
            offset = offset + len(current_choices_keys)
            current_choices_keys = ""
            i = 0
        nb_lines = min(max(10, self.rows - 3), len(filtered_indice))
        if not(line_number):
            nb_lines = self.rows - 3
        else:
            if nb_lines < 1:
                self.error('pb: nb_lines<1...', exit=True, exception=False)
        self.log_debug('nb_lines=%s' % nb_lines, 4, trace='TERM')
        while len(choice_list) and j < nb_lines:
          c = choice_list.pop(0)
          if len(current_choices) and not(more_message):
              current_choices = current_choices + "\n"
          more_message = 0
          if line_number:
            k = filtered_indice[i]
            indexed_choices[k] = c
            current_choices_keys = current_choices_keys + k
            # current_choices = current_choices+"%s -> %s %s <- %s" % \
            #                        (k,c," "*(int(self.columns)-10-len(c)),k)
            current_choices = current_choices + "%s -> %s" % (k, c)
          else:
            current_choices = current_choices + "%s" % (c)
          i = i + 1
          j = j + 1
        if len(current_choices):
          print(current_choices)
          pick_a_choice = ''
          if line_number:
              pick_a_choice = 'pick a choice,'

          if len(choice_list):
            print '\r ----  %s call a command or press space for more ----' % pick_a_choice,
            space_accepted = " "
          else:
            print '\r ---- %s  call a command ----' % pick_a_choice,
            space_accepted = ""
          more_message = 2
          sys.stdout.flush()
          self.log_debug('remaining line in the more session [%s] ' % ','.join(choice_list), \
                         4, trace='MORE,KEY')
          if line_number:
              acceptable_key = space_accepted + current_choices_keys + on_key_return
          else:
              acceptable_key = space_accepted + on_key_return
          x = '?'
          while (acceptable_key.find(x) == -1):
            x = self.getkey()
          self.log_debug('while a more session key >%s< was hit... ' % x, 4, trace='KEY')
          if x in current_choices_keys or x in on_key_return:
             self.current_x = self.last_x
             self.args.input = x + self.args.input
             self.log_debug('Choice picked up or command called... leaving the more session ', \
                            4, trace='KEY')
             choice_made = True

      self.log_debug('out of more session ', 4, trace='MORE')
      while True:
          x = self.getkey()
          self.log_debug('x = >%s< ' % x, 4, trace='KEY')
          if (x in on_key_return):
              self.log_debug('key %s hit to be taken in account by general menu ' % x, \
                             4, trace='KEY')
              self.current_x = self.last_x
              self.args.input = x + self.args.input
              if get_choices:
                return (None, current_choices_keys, current_choices, offset)
              else:
                return None
          if x in indexed_choices.keys():
              if get_choices:
                self.log_debug('return str(indexed_choices[x])=>%s<,current_choices_keys=>%s<)' % \
                               (str(indexed_choices[x]), current_choices_keys), 4, trace='KEY')
                return (str(indexed_choices[x]), current_choices_keys, current_choices, offset)
              else:
                self.log_debug('return str(indexed_choices[x])=>%s<' % \
                               (str(indexed_choices[x])), 4, trace='KEY')
                return str(indexed_choices[x])
          else:
            print('    Error: choice %s unavalaible' % x)
      if get_choices:
        return (None, current_choices_keys, current_choices, offset)
      else:
        return None

  #########################################################################
  # get a key from the keyboard
  #########################################################################

  def getkey(self):
    self.previous_x = self.current_x
    if len(self.args.input):
      x = self.args.input[0]
      self.args.input = self.args.input[1:]
      self.current_x = x
      self.log_debug('getkey from input x=>%s< args.input=%s last_x=>%s< previous_x=>%s<' % \
                         (x, self.args.input, self.last_x, self.previous_x), 4, trace='KEY')
      return x
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    new = termios.tcgetattr(fd)
    new[3] = new[3] & ~termios.ICANON & ~termios.ECHO
    new[6][termios.VMIN] = 1
    new[6][termios.VTIME] = 0
    termios.tcsetattr(fd, termios.TCSANOW, new)
    c = None
    try:
            c = os.read(fd, 1)
    finally:
            termios.tcsetattr(fd, termios.TCSAFLUSH, old)
    self.current_x = c
    self.log_debug('getkey direct x=>%s< args.input=%s last_x=>%s< previous_x=>%s<' % \
                         (c, self.args.input, self.last_x, self.previous_x), 4, trace='KEY')

    return c

  #########################################################################
  # fixing things
  #########################################################################

  def close_save(self):
    saved_workfile = '%s/%s' % (self.LOG_DIR, os.path.basename(self.WORKSPACE_FILE))
    os.system('chmod 444  %s ' % saved_workfile)
    return

  #########################################################################
  # fixing things
  #########################################################################

  def fix(self):
      self.load()

      self.compute_critical_path()
      print('self.STEPS=\n%s' % pprint.pformat(self.STEPS.keys()))
      print('self.steps_submitted_attempts=\n%s' % pprint.pformat(self.steps_submitted_attempts))
      print('self.STEPS_RESTART_ATTEMPT=\n%s' % pprint.pformat(self.STEPS_RESTART_ATTEMPT))
      sys.exit(0)

      self.compute_critical_path()
      sys.exit(0)

      print('self.waiting_job_final_id=\n%s' % pprint.pformat(self.waiting_job_final_id))
      sys.exit(0)

      jobs = self.JOBS.keys()
      # print(jobs)
      known_jobs = ",%s," % (",".join(map(lambda x:str(x), jobs)))
      # print('known_jobs:',known_jobs)
      for s in self.STEPS.keys():
        for jid in self.STEPS[s]['jobs']:
          known_jobs = known_jobs.replace(',%s,' % jid, ",")
          self.JOBS[jid]['0kept'] = True
      print('untracked_jobs:', known_jobs)
      # for j in known_jobs[1:-1].split(","):
      for j in self.JOBS.keys():
        try:
          job = self.JOBS[int(j)]
        except Exception:
          job = self.JOBS[j]
        if job['job_name'] == '2' or True:
          print('%s' % (self.print_job(job, print_only=['array', 'job_id', 'make_depend', '0kept'], \
                                       allkey=False)))
      sys.exit(0)

      print('self.TASKS%s' % pprint.pformat(self.TASKS))
      sys.exit(0)

      print('self.submitted:' + pprint.pformat(self.steps_submitted))
      print('self.submitted_history:' + pprint.pformat(self.steps_submitted_history))
      sys.exit(0)

      print(self.print_jobs())
      print(self.print_jobs(self.STEPS))
      sys.exit(0)

      for s in self.TASKS.keys():
          for t in self.TASKS[s].keys():
              self.TASKS[s][t]['status'] = 'COMPLETE'
      self.save()
      return

#       print(self.steps_submitted)
      l = list(self.steps_submitted)
      for i in [0, 1, 2, 3, 4, 5, 6, 7, 8]:
        s = '4-mitgcm-%d' % i
        try:
          l.remove(s)
          print('successfully removed from step_submitted ', s)
        except Exception:
          print('try to remove %s from step_submitted but could not ' % s)
        try:
          del self.STEPS[s]
          print('successfully removed from STEPS ', s)
        except Exception:
          print('try to remove %s from STEPS but could not ' % s)
        try:
          del self.TASKS[s]
          print('successfully removed from TASKS ', s)
        except Exception:
          print('try to remove %s from TASKS but could not ' % s)
      self.steps_submitted = l
      # print(self.steps_submitted)
      # print(self.STEPS.keys())
#       self.steps_submitted_attempts['4-mitgcm']=0

#
#       for step in self.STEPS.keys():
#         if self.STEPS[step]['status'] == 'DONE':
#           print('processing step %s' % step)
#           fields = step.split('-')
#           (what,attempt) = "-".join(fields[:-1]),fields[-1]
#           tasks = self.STEPS[step]['array']
#           print('would check (what=%s, attempt=%s, tasks=%s)' % (what, attempt, tasks))
#           self.check_current_state(what, attempt, tasks, checking_from_console=True)
#
      for step in self.STEPS.keys():
        if not(step[0] in "01234") or step[0:2] == '10':
               print('would clean step %s' % step)
               del self.STEPS[step]
               del self.TASKS[step]
               l.remove(step)
#       self.steps_submitted = l

      for step in self.STEPS.keys():
        my_step = self.STEPS[step]
        step0 = "%s-0" % step[:-2]
        my_step0 = self.STEPS[step0]
        my_step['array'] = my_step['tasks']
        my_step['initial_array'] = my_step0['tasks'].replace('-100', '-999')
        print(step, my_step['initial_array'])
        self.STEPS[step] = my_step
#
# #       del self.STEPS['4-mitgcm-1']
#       del self.STEPS['4-mitgcm-2']
#       del self.STEPS['4-mitgcm-3']
#       for j in self.JOBS.keys():
#         job  = self.JOBS[j]
#         job['step'] = "%s-%s" % (job['job_name'],job['attempt'])
#         self.JOBS[j] =job

      self.save()

if __name__ == "__main__":
    K = decimate()
    K.start()
