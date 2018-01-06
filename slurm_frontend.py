7#!/sw/xc40/python/2.7.11/sles11.3_gnu5.1.0/bin/python

import argparse
from decimate import *
import pprint

DEBUG = False

cmd_line = (" ".join(sys.argv)).split("--decimate")
cmd_line = (" ".join(sys.argv))

if 'DPARAM' in os.environ.keys():
  cmd_line = clean_line(os.environ['DPARAM']) + " " + cmd_line

if len(cmd_line) >= 2:
  if cmd_line.find(" API ") > -1 or cmd_line.find("API,") > -1\
     or cmd_line.find(",API") > -1:
    DEBUG = True


class slurm_frontend(decimate):

  def __init__(self):

    decimate.__init__(self,app_name='decimate', decimate_version_required='0.5',
                      app_version='0.1',extra_args=True)

  #########################################################################
  def user_filtered_args(self):

    self.job_script = None
    index = 1
    args = []
    decimate_args = []
    is_decimate = False
    is_job_parameter = False
    self.job_parameter = []
    
    for f in sys.argv[1:]:
      if DEBUG:
        print 'testing:',f
      if os.path.exists(f) and not is_decimate:
        self.job_script = f
        print 'job_script found:', f
        is_job_parameter = True
        continue
      if f == "--decimate":
        is_decimate = True
        continue
      if is_decimate:
        decimate_args = decimate_args + [f]
      elif is_job_parameter:
        self.job_parameter = self.job_parameter + [f]
      else:
        args = args + [f]
      index = index + 1

    self.create_slurm_parser(DEBUG)
    self.slurm_args = self.slurm_parser.parse_args(args)

    if DEBUG:
      print('command line slurm_args: %s' % pprint.pformat(self.slurm_args))

    if (self.slurm_args.help):
      print(HELP_MESSAGE)
      sys.exit(1)

    decimate_extra_config = []
    if 'DPARAM' in os.environ.keys():
      decimate_extra_config = clean_line(os.environ['DPARAM']).split(" ")

    if (self.slurm_args.decimate_help or decimate_extra_config == ["-h"]):
      return ['-h']

    if not(self.job_script) and len(decimate_args) == 0:
      self.error('job script missing...', exit=True)

    if self.slurm_args.yalla:
      decimate_extra_config = decimate_extra_config + ['--yalla']

    if self.slurm_args.filter:
      decimate_extra_config = decimate_extra_config + ['--filter',self.slurm_args.filter]

    if self.slurm_args.max_retry:
      decimate_extra_config = decimate_extra_config + \
                              ['--max-retry', "%s" % self.slurm_args.max_retry]

    if self.slurm_args.yalla_parallel_runs:
      decimate_extra_config = decimate_extra_config + \
                              ['--yalla-parallel-runs', "%s" % self.slurm_args.yalla_parallel_runs]

    if self.slurm_args.use_burst_buffer_size:
      decimate_extra_config = decimate_extra_config + ['--use-burst-buffer-size']

    if DEBUG:
      print('job_file=/%s/\nargs=/%s/\nparams=/%s/\ndecimate_args=/%s/' % \
            (self.job_script,args,self.job_parameter,decimate_extra_config + decimate_args))

    return ['--decimate'] + decimate_extra_config + decimate_args

  #########################################################################

  def user_initialize_parser(self):

    self.parser.add_argument("-e", "--ends", type=int,
                             help=argparse.SUPPRESS,default=-1)
    self.parser.add_argument("--banner", action="store_true",
                             help=argparse.SUPPRESS, default=False)
    self.parser.add_argument("-np", "--no-pending", action="store_true",

                             help='do not keep pending the log', default=True)


  #########################################################################
  # submitting all the first jobs
  #########################################################################

  def user_launch_jobs(self):

    # self.log_info('ZZZZZZZZZZZZZ setting max_retry to 1 ZZZZZZZZZZZZ')
    self.load()

    new_job = {}

    p_slurm_args = vars(self.slurm_args)
    self.slurm_args.script = os.path.abspath("%s" % self.job_script)

    # does the checking script exist?
    if self.slurm_args.check:
      if not(os.path.exists(self.slurm_args.check)):
        self.error('checking job script %s missing...' % self.slurm_args.check, exit=True)
      self.slurm_args.check = os.path.abspath("%s" % self.slurm_args.check)
              
    for k,v in p_slurm_args.items():
      new_job[k] = v

    self.log_debug('job submitted:\n%s' % \
                   self.print_job(new_job,allkey=False,\
                                  print_all=True,except_none=True), \
                   4, trace='API')

    if self.args.yalla:
      new_job['yalla'] = self.args.yalla_parallel_runs
    if self.args.use_burst_buffer_size:
      new_job['burst_buffer_size'] = self.args.burst_buffer_size
    if self.args.use_burst_buffer_space:
      new_job['burst_buffer_space'] = self.args.burst_buffer_space
      
    (job_id, cmd) = self.submit_job(new_job)

    self.log_debug("Saving Job Ids...",1)
    self.save()

    print('Submitted batch job %s' % job_id)

  #########################################################################
  # checking job correct completion
  #########################################################################

  def check_job_old(self, what, attempt, task_id, running_dir, output_file, error_file,
                is_done, fix, job_tasks,step_tasks):

    self.log_info(("check_job(what=>%s<, attempt=>%s<, task_id=>%s<, running_dir=>%s<," +\
                   "output_file=>%s<, error_file=>%s<, is_done=>%s<, fix=>%s<, " +\
                   "job_tasks=>%s<,step_tasks=>%s<") % \
                  (what, attempt, task_id, running_dir, output_file, error_file,
                   is_done, fix, job_tasks,step_tasks))

    return SUCCESS


  #########################################################################
  # checking job correct completion
  #########################################################################

  def check_job(self,step, attempt, task_id,running_dir,output_file,error_file,\
                is_job_completed,fix=True,job_tasks=None,step_tasks=None):

    s = "CHECKING step : %s attempt : %s   task : %s " % \
        (step,attempt,task_id) + "\n" + \
        "job_tasks : %s  \t step_tasks : %s" % (job_tasks,step_tasks) + "\n" +\
        "Output file : %s" % (output_file) + "\n" +\
        "Error file : %s" % (error_file) + "\n" +\
        "Running dir : %s" % (running_dir) + "\n"
    self.log_info(s,4,trace='CHECK,USER_CHECK')

    done = 'job DONE'
    is_done = self.greps(done,output_file,exclude_patterns=['[INFO','[DEBUG'])
    if not(is_done):
      return FAILURE
    else:
      return SUCCESS

  
if __name__ == "__main__":
    K = slurm_frontend()
    K.start()
