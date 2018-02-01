#!/sw/xc40/python/2.7.11/sles11.3_gnu5.1.0/bin/python
from decimate import *
import time


class decimate_test(decimate):

  def __init__(self):

    decimate.__init__(self,app_name='decimate',
                      decimate_version_required='0.3',app_version='0.1')

    self.tasks_to_check = []

    self.prefix = ""

  #########################################################################

  def user_initialize_parser(self):
    self.parser.add_argument("-b", "--begins", type=int,
                             help='run simulation up to this step',default=1)
    self.parser.add_argument("-e", "--ends", type=int,
                             help='run simulation up to this step',default=2)
    self.parser.add_argument("-a", "--array", type=str,
                             help='size of the array submitted at each step',default='1-3')
    self.parser.add_argument("-n", "--ntasks", type=int,
                             help='number of tasks for the jobs',default=1)
    self.parser.add_argument("-t", "--time", type=str,
                             help='ellapse time',default='00:05:00')
    self.parser.add_argument("-np", "--no-pending", action="store_true",
                             help='do not keep pending the log', default=False)
    self.parser.add_argument("-fp", "--fake-pause", type=int,
                             help='time to sleep in a fake job', default=0)

    self.slurm_args = argparse.Namespace(a=1)
    
  #########################################################################
  # create job files
  #########################################################################

  def create_job_files(self):

      self.log_debug('from step=%s to %s ' % (self.args.begins,self.args.ends))

      for stepnb in range(self.args.begins,self.args.ends+1):

        step = "%s%s" % (self.prefix,stepnb)
        self.log_info('creating job files for step %s' % step)

        output = """\
######################
# Begin work section #
######################

# Print this sub-job's task ID
echo "My SLURM_ARRAY_TASK_ID: " $SLURM_ARRAY_TASK_ID

echo job DONE
#sleep 10
"""
        open("%s/%s.job" % (self.SAVE_DIR,step), "w").write(output)

      # finish job
      open("%s/%s-finish.job" % (self.SAVE_DIR,step), "w").write(output)

  #########################################################################
  # submitting all the first jobs
  #########################################################################

  def user_launch_jobs(self,reading_input=True):

    # self.log_info('ZZZZZZZZZZZZZ setting max_retry to 1 ZZZZZZZZZZZZ')
    self.load()

    # cleaning SAVE directory
    self.system('rm %s/Done*' % self.SAVE_DIR)
    self.system('rm %s/Complete*' % self.SAVE_DIR)
    self.system('rm %s/*job*' % self.SAVE_DIR)

    self.create_job_files()
    self.check_workflow_and_start()

    self.ask("Ready... All set... Go? ", default='y')

    dep = None

    for stepnb in range(self.args.begins,self.args.ends+1):

        step = '%s%s' % (self.prefix,stepnb)

        job_name = '%s' % (step)
        job_script = '%s/%s.job' % (self.SAVE_DIR,job_name)

        array_item = "%s" % self.args.array

        new_job = {'job_name': job_name,
                   'make_depend': None,
                   'dependency': dep,
                   'script': os.path.abspath("%s" % job_script),
                   'ntasks': self.args.ntasks,
                   'time': self.args.time,
                   'account': 'k01',
                   # 'output': '%s.out' % step,
                   # 'error':  '%s.err' % step,
                   'output': '%s.%%J.out' % step,
                   'error': '%s.%%J.err' % step,
                   'submit_dir': os.getcwd(),
                   'array': array_item,
                   'attempt': 0}

        (job_id, cmd) = self.submit_job(new_job)

        dep = job_id

  #########################################################################
  # checking job correct completion
  #########################################################################

  def fake_job(self,step,task,attempt):

    s = 'faking step %s task %s attempt %s' % (step,task,attempt)
    self.log_info(s,1,trace='FAKE')
    if self.args.fake_pause:
      self.log_info('pausing for %s seconds...' % self.args.fake_pause,1,trace='FAKE')
      time.sleep(self.args.fake_pause)
    self.log_info('job DONE',0,trace='FAKE')

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

    if task_id == step_tasks[0]:
      self.tasks_to_check = []

    self.tasks_to_check = self.tasks_to_check + [task_id]

    if task_id == step_tasks[-1]:
      self.log_debug('self.tasks_to_check = [%s] ' % \
                     ",".join(map(lambda x: str(x),self.tasks_to_check)),\
                     trace='CHECK')

    done = 'job DONE'
    is_done = self.greps(done,output_file,exclude_patterns=['[INFO','[DEBUG'])
    if not(is_done):
      return False
    else:
      return True

    return is_job_completed


if __name__ == "__main__":
    K = decimate_test()
    K.start()
