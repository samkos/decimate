#!/sw/xc40/python/2.7.11/sles11.3_gnu5.1.0/bin/python
from decimate import *
import datetime,time

  
import glob
import traceback
import pprint

class decimate_test(decimate):

  def __init__(self):

    decimate.__init__(self,app_name='decimatest', decimate_version_required='0.3',app_version='0.1')


    

  #########################################################################


  def user_initialize_parser(self):
    self.parser.add_argument("--launch", action="store_true", help='start/continue a simulation')
    self.parser.add_argument("-b", "--begins", type=int, help='run simulation up to this step',default=1)
    self.parser.add_argument("-e", "--ends", type=int, help='run simulation up to this step',default=10)
    self.parser.add_argument("-a", "--array", type=str, help='size of the array submitted at each step',default='1-3')
    self.parser.add_argument("-n", "--ntasks", type=int, help='number of tasks for the jobs',default=1)
    self.parser.add_argument("-t", "--time", type=str, help='ellapse time',default='00:05:00')

    # showing some hidden engine options
    self.parser.add_argument("-m", action="count", default=0, \
                             help='if activated sends a mail tracking the progression of the workflow')

    # hidding some engine options
    self.parser.add_argument("--create-template", action="store_true", help=argparse.SUPPRESS)
    self.parser.add_argument("--generate", action="store_true", help=argparse.SUPPRESS)
    self.parser.add_argument("-r","--reservation", type=str , help=argparse.SUPPRESS)
    self.parser.add_argument("-p","--partition", type=str , help=argparse.SUPPRESS)
    
  #########################################################################
  # create job files
  #########################################################################
  
  def create_job_files(self):


      self.log_debug('from step=%s to %s ' % (self.args.begins,self.args.ends))

      for step in range(self.args.begins,self.args.ends+1):

        self.log_info('creating job files for step %d' % step)

        output = """\
######################
# Begin work section #
######################

# Print this sub-job's task ID
echo "My SLURM_ARRAY_TASK_ID: " $SLURM_ARRAY_TASK_ID

#sleep 10
"""
        
        
        input_file = '%s/templates/filter_first.job.template' 
        open("%s/%d.job" % (self.SAVE_DIR,step), "w").write(output)


      # finish job
      open("%s/%d-finish.job" % (self.SAVE_DIR,step), "w").write(output)

  
  #########################################################################
  # submitting all the first jobs
  #########################################################################

  def user_launch_jobs(self,reading_input = True):


    #self.log_info('ZZZZZZZZZZZZZ setting max_retry to 1 ZZZZZZZZZZZZ')
    self.load()

    # claning SAVE directory
    self.system('rm %s/Done*'% self.SAVE_DIR)
    self.system('rm %s/Complete*'% self.SAVE_DIR)
    self.system('rm %s/*job*'% self.SAVE_DIR)

      
    self.create_job_files()

    self.ask("Ready... All set... Go? ", default='y' )

    dep = step_before = job_before = last_task_id_before =  None
                     
    for step in range(self.args.begins,self.args.ends+1):

        last_task_id = 1
        array_item = None
        
        job_name = '%s'  % (step)
        job_script = '%s/%s.job' % (self.SAVE_DIR,job_name)
        
        array_item = "%s" % self.args.array

        new_job = { 'name' : job_name,
                    'comes_before': None,
                    'comes_after': dep,
                    'make_depend' : None,
                    'dependency' : dep,
                    'step_before' : step_before,
                    'script' : os.path.abspath("%s" % job_script),
                    'ntasks' : self.args.ntasks,
                    'time'   : self.args.time,
                    'account' : 'k01',
                    'output_name' : '%s.out' % step,
                    'error_name' :  '%s.err' % step,
                    'submit_dir' : os.getcwd(),
                    'array' : array_item,
                    'last_task_id' : last_task_id,
                    'last_task_id_before' : last_task_id_before,
                    'attempt' : 0
        }

        # if self.DEBUG:
        #   print 'new_job',step
        #   print new_job

        new_job_script_content = self.wrap_job_script(new_job)

        f = open("%s+" % job_script,'w')
        f.write(new_job_script_content)
        f.close()

        new_job['script_file'] = job_script+'+'


        (job_id, cmd) = self.submit_job(new_job)
        
        new_job['job_id'] = job_id
        new_job['submit_cmd'] = cmd
        
        
        if dep:
          self.JOBS[dep]['comes_before']  = job_id
          self.JOBS[dep]['make_depend'] = job_id

        self.JOBS[job_id] = new_job
        
        dep = job_id
        step_before = job_name
        last_task_id_before = last_task_id


    self.log_debug("Saving Job Ids...",1)
    self.save()

    self.tail_log_file(nb_lines_tailed=1, no_timestamp=True,
                       stop_tailing=['workflow is finishing','workflow is aborting'])
    sys.exit(0)

  #########################################################################
  # checking job correct completion
  #########################################################################

  def fake_job(self,step,task,attempt):

    self.log_info('faking step %s task %s attempt %s' % (step,task,attempt))


  #########################################################################
  # checking job correct completion
  #########################################################################

  def check_job(self,what,task_id,running_dir,output_file,error_file,is_job_completed):

    return is_job_completed
    
if __name__ == "__main__":
    K=decimate_test()
    K.start()
