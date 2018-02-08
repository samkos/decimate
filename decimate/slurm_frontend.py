#!/bin/env/python

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
    is_waiting_param_file = False
    self.job_parameter = []

    for f in sys.argv[1:]:
      if DEBUG:
        print('testing:/%s/ (is_waiting_param_file=%s,is_decimate=%s' % \
              (f,is_waiting_param_file,is_decimate))
      if f == "-P" or f == "--parameter-file" or f == "--check":
        args = args + [f]
        is_waiting_param_file = True
        continue
      elif os.path.exists(f) and not is_waiting_param_file and not is_decimate:
        if self.job_script:
          args = args + [f]
        else:
          self.job_script = f
          if DEBUG:
            print('job_script found:', f)
      elif os.path.exists(f) and is_waiting_param_file:
        args = args + [f]
        is_waiting_param_file = False
      elif f == "--decimate":
        is_decimate = True
        continue
      elif is_decimate:
        decimate_args = decimate_args + [f]
      else:
        args = args + [f]
      index = index + 1

    if DEBUG:
      print('ARGS:',args)
      print('DECIMATE_ARGS:',decimate_args)
      print('index:',index)

    self.create_slurm_parser(DEBUG)
    self.slurm_parser.add_argument('--debug', action="count", default=0, help=argparse.SUPPRESS)
    self.slurm_parser.add_argument('--info', action="count", default=0, help=argparse.SUPPRESS)

    self.slurm_parser.add_argument("-xy", "--yalla", action="store_true",
                                   help='Use yalla container', default=False)
    self.slurm_parser.add_argument("-xyp", "--yalla-parallel-runs", type=int,
                                   help='# of job to run in parallel in a container', default=4)

    self.parser.add_argument("-P", "--parameter-file", type=str,
                             help='file listing all parameter combinations to cover')
    self.parser.add_argument("-Pl", "--parameter-list", action="store_true",
                                   help='lists all parameters combination to scan and exit', default=False)
    self.parser.add_argument("-PF", "--parameter-filter", type=str,
                             help='filter to apply on combinations to cover')
    self.parser.add_argument("-Pa", "--parameter-range", type=str,
                             help='filtered range to apply on combinations to cover')

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

    if not(self.job_script) and not(self.slurm_args.parameter_list) and len(decimate_args) == 0:
      self.error('job script missing...', exit=True)

    if self.slurm_args.yalla:
      decimate_extra_config = decimate_extra_config + ['--yalla']

    if self.slurm_args.filter:
      decimate_extra_config = decimate_extra_config + ['--filter',self.slurm_args.filter]

    if self.slurm_args.max_retry:
      decimate_extra_config = decimate_extra_config + \
                              ['--max-retry', "%s" % self.slurm_args.max_retry]

    if self.slurm_args.max_retry:
      decimate_extra_config = decimate_extra_config + \
                              ['--max-retry', "%s" % self.slurm_args.max_retry]

    if self.slurm_args.yalla_parallel_runs:
      decimate_extra_config = decimate_extra_config + \
                              ['--yalla-parallel-runs', "%s" % self.slurm_args.yalla_parallel_runs]

    if self.slurm_args.parameter_file:
      decimate_extra_config = decimate_extra_config + \
                              ['--parameter-file', "%s" % os.path.abspath(self.slurm_args.parameter_file) ]

    if self.slurm_args.parameter_filter:
      decimate_extra_config = decimate_extra_config + \
                              ['--parameter-filter', "%s" % self.slurm_args.parameter_filter]

    if self.slurm_args.parameter_range:
      decimate_extra_config = decimate_extra_config + \
                              ['--parameter-range', "%s" % self.slurm_args.parameter_range]

    if self.slurm_args.parameter_list:
      decimate_extra_config = decimate_extra_config + \
                              [ '--parameter-list' ]

    if self.slurm_args.use_burst_buffer_size:
      decimate_extra_config = decimate_extra_config + ['--use-burst-buffer-size']

    if self.slurm_args.info:
      decimate_extra_config = decimate_extra_config + ['--info' * self.slurm_args.info]

    if self.slurm_args.debug:
      decimate_extra_config = decimate_extra_config + ['--debug' * self.slurm_args.debug]

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

    # does the checking script exist?
    if self.slurm_args.parameter_file:
      if not(os.path.exists(self.slurm_args.parameter_file)):
        self.error('parameter file %s missing...' % self.slurm_args.parameter_file, exit=True)
      self.slurm_args.parameter_file = os.path.abspath("%s" % self.slurm_args.parameter_file)

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

    if self.slurm_args.parameter_file:
      new_job['array'] = '0-%d' % (len(self.parameters)-1)
      self.log_debug('setting array to %s' % new_job['array'], 4, trace='TEMPLATE')

    (job_id, cmd) = self.submit_job(new_job)

    self.log_debug('Submitted batch job %s' % job_id)

    if self.slurm_args.check:
      final_checking_job = copy.deepcopy(new_job)
      for n in ['job_name','error','output']:
        final_checking_job[n] = 'chk_' + new_job[n]
      final_checking_job['ntasks'] = 1
      final_checking_job['dependency'] = job_id
      final_checking_job['time'] = "05:00"
      final_checking_job['script'] = "%s/bin/end_job.sh" % self.DECIMATE_DIR
      del final_checking_job['script_file']
      final_checking_job['array'] = "1-1"

      self.slurm_args.script = self.args.script = final_checking_job['script']
      self.slurm_args.error = final_checking_job['error']
      self.slurm_args.output = final_checking_job['output']
      self.slurm_args.job_name = final_checking_job['job_name']
      self.log_debug('*********** final_checking_job **********',\
                     4,trace='SUBMIT,CHECK_FINAL')
      self.log_debug('final_checking_job=%s' % pprint.pformat(final_checking_job),\
                     4,trace='CHECK,FINAL_DETAIL')
      (job_id, cmd) = self.submit_job(final_checking_job)


    self.log_debug("Saving Job Ids...",1)
    self.save()



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

def batch():
    K = slurm_frontend()
    K.start()

def kill():
    sys.argv[1:] = ["--decimate", "--kill"] + sys.argv[1:]
    K = slurm_frontend()
    K.start()

def stat():
    sys.argv[1:] = ["--decimate", "--status"] + sys.argv[1:]
    K = slurm_frontend()
    K.start()

def console():
    sys.argv[1:] = ["--decimate", "--explore"] + sys.argv[1:]
    K = slurm_frontend()
    K.start()

  
if __name__ == "__main__":
    K = slurm_frontend()
    K.start()
