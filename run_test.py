#!/sw/xc40/python/2.7.11/sles11.3_gnu5.1.0/bin/python
from decimate import *
import datetime,time

from dart_mitgcm_init import *

  
import glob
import traceback
import pprint

class decimate_test(decimate):

  def __init__(self):

    self.DART_MITGCM_DIR = os.getenv('DART_MITGCM_PATH')
    self.FILES_TO_COPY = ['%s/dart_mitgcm.py' % (self.DART_MITGCM_DIR),'%s/dart_mitgcm_init.py' % (self.DART_MITGCM_DIR) ]    
    decimate.__init__(self,app_name='dart_mitgcm', decimate_version_required='0.2',app_version='0.3')


    

  #########################################################################


  def user_initialize_parser(self):
    self.parser.add_argument("-l", "--log", action="store_true", help='display and tail current log')
    self.parser.add_argument("-s", "--status", action="store_true", help='list status of jobs and of the whole workflow')
    self.parser.add_argument("--launch", action="store_true", help='start/continue a simulation')
    self.parser.add_argument("-b", "--begins", type=int, help='run simulation up to this step',default=1)
    self.parser.add_argument("-e", "--ends", type=int, help='run simulation up to this step',default=10)
    self.parser.add_argument("-a", "--array", type=int, help='size of the array submitted at each step',default=3)
    self.parser.add_argument("-n", "--ntasks", type=int, help='number of tasks for the jobs',default=1)
    self.parser.add_argument("-t", "--time", type=str, help='ellapse time',default='00:05:00')
    self.parser.add_argument("--nogen",  action="store_true", help=argparse.SUPPRESS)

    # showing some hidden engine options
    self.parser.add_argument("-m", action="count", default=0, \
                             help='if activated sends a mail tracking the progression of the workflow')

    # hidding some engine options
    self.parser.add_argument("--create-template", action="store_true", help=argparse.SUPPRESS)
    self.parser.add_argument("--generate", action="store_true", help=argparse.SUPPRESS)
    self.parser.add_argument("-r","--reservation", type=str , help=argparse.SUPPRESS)
    self.parser.add_argument("-p","--partition", type=str , help=argparse.SUPPRESS)
    
  #########################################################################
  # inititalizing values needed to interact with model
  #########################################################################

  def init_jobs(self):

    #self.args.max_retry = 1

    self.log_debug('in init_jobs',2)

    self.user_run()

  #########################################################################
  # main loop
  #########################################################################

  def user_run(self):

    if self.args.log:
      self.tail_log_file(keep_probing=True,no_timestamp=True,stop_tailing=['workflow is finishing','workflow is aborting'])
      sys.exit(0)
    elif self.args.status:
      print self.print_workflow()
      sys.exit(0)

    elif (self.args.launch):
      self.launch_jobs()

    if not(self.args.spawned):
      print self.launch_jobs()
      sys.exit(0)


  #########################################################################
  # create job files
  #########################################################################
  
  def create_job_files(self):


      self.log_debug('from step=%s to %s ' % (self.args.begins,self.args.ends))

      for step in range(self.args.begins,self.args.ends):

        self.log_info('creating job files for step %d' % step)

        output = """\
######################
# Begin work section #
######################

# Print this sub-job's task ID
echo "My SLURM_ARRAY_TASK_ID: " $SLURM_ARRAY_TASK_ID

sleep 10
"""
        
        
        input_file = '%s/templates/filter_first.job.template' 
        open("%s/%d.job" % (self.SAVE_DIR,step), "w").write(output)


      # finish job
      open("%s/%d-finish.job" % (self.SAVE_DIR,step), "w").write(output)

  
  #########################################################################
  # checking initial state of the workflow
  #########################################################################

  def start_workflow_from_scratch(self,files_to_move_or_remove):

    self.ask("Do you want to start the whole process from scratch now?", default='y' )

    self.log_info('cleaning directory')
    for f in files_to_move_or_remove:
      os.system('rm -rf %s' % f)

    self.log_info('launching jobs')
    self.launch_jobs()

  #########################################################################
  # submitting all the first jobs
  #########################################################################

  def user_launch_jobs(self,reading_input = True):


    #self.log_info('ZZZZZZZZZZZZZ setting max_retry to 1 ZZZZZZZZZZZZ')
    self.load_workspace()

    # claning SAVE directory
    self.system('rm %s/Done*'% self.SAVE_DIR)
    self.system('rm %s/Complete*'% self.SAVE_DIR)
    self.system('rm %s/*job*'% self.SAVE_DIR)

      
    self.create_job_files()

    self.ask("Ready... All set... Go? ", default='y' )

    dep = step_before = job_before = last_task_id_before =  None
                     
    for step in range(self.args.begins,self.args.ends):

        last_task_id = 1
        array_item = None
        
        job_name = '%s'  % (step)
        job_script = '%s/%s.job' % (self.SAVE_DIR,job_name)
        
        array_item = "1-%s" % self.args.array

        new_job = { 'name' : job_name,
                    'comes_before': None,
                    'comes_after': dep,
                    'make_depend' : None,
                    'depends_on' : dep,
                    'step_before' : step_before,
                    'script' : os.path.abspath("%s" % job_script),
                    'ntasks' : self.args.ntasks,
                    'time'   : self.args.time,
                    'account' : 'k01',
                    'output_name' : '%s.out' % step,
                    'error_name' :  '%s.err' % step,
                    'submit_dir' : os.getcwd(),
                    'array_item' : array_item,
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
        
        
        if step_before:
          self.JOBS[step_before]['comes_before'] = self.JOBS[self.JOBS[step_before]['job_id']]['comes_before'] =  job_id
          self.JOBS[step_before]['make_depend'] = self.JOBS[self.JOBS[step_before]['job_id']]['make_depend'] =  job_id

        self.JOBS[job_id] = self.JOBS[job_name] = new_job
        
        dep = job_id
        step_before = job_name
        last_task_id_before = last_task_id


    self.log_debug("Saving Job Ids...",1)
    self.save_workspace()

    self.tail_log_file(keep_probing=True, nb_lines_tailed=1, no_timestamp=True, stop_tailing=['workflow is finishing','workflow is aborting'])
    sys.exit(0)



  #########################################################################
  # checking job correct completion
  #########################################################################

  def check_job(self,what,task_id,running_dir,output_file,error_file,is_job_completed):

    s = "CHECKING step : %s   task : %s " % (what,task_id) + "\n" + \
        "Output file : %s" % (output_file) + "\n" +\
        "Error file : %s" % (error_file) + "\n" +\
        "Running dir : %s" % (running_dir) + "\n" 
    self.log_info(s,4)

    with working_directory(running_dir):

      everything_ok = True

      for error in ['STOP ABNORMAL END','Problem opening','Problem while opening file','ERROR','Killed','MPI_Abort']:
        is_error = self.greps(error,error_file,exclude_patterns=['[INFO','[DEBUG'])
        #print >> sys.stderr, 'error', is_error
        #self.log_info('user error detected --> '+pprint.pformat(is_error))
        if (is_error):
          s = '%s detected %d times in %s --> \n\t\t ERROR DETECTED: %s ' % \
              (error,len(is_error),error_file,pprint.pformat(is_error[0]))
          self.log_info(s)
          self.append_mail('---------- problem in error file ------')
          self.append_mail(s)
          self.append_mail('%s was detected in %s' % (error,error_file))
          self.append_mail('-------------------------------- ------\n\n')
          everything_ok =  False
        is_error = self.greps(error,output_file,error_file,exclude_patterns=['[INFO','[DEBUG'])
        #print >> sys.stderr, 'error', is_error
        #self.log_info('user error detected --> '+pprint.pformat(is_error))
        if (is_error):
          s = '%s detected %d times in %s --> \n\t\t ERROR DETECTED: %s ' % \
              (error,len(is_error),output_file,pprint.pformat(is_error[0]))
          self.log_info(s)
          self.append_mail('---------- problem in output file ------')
          self.append_mail(s)
          self.append_mail('%s was detected in %s' % (error,output_file))
          self.append_mail('-------------------------------- ------\n\n')
          everything_ok =  False
    
      if what.find('filter')>=0:
        is_filter_ok = self.greps('Filter done',output_file)
        if (is_filter_ok):
          s = 'Despite of everything filter finished was found in %s --> everything ok  ' % (output_file)
          if not(everything_ok):
            self.log_info(s)
            self.append_mail('---------- but it is ok!!!!!!    ------')
            self.append_mail(s)
            self.append_mail('-------------------------------- ------\n\n')
          everything_ok =  True
          return True
        else:
          s = 'String "Filter Done" not found in %s --> something went wrong  ' % (output_file)
          self.log_info(s)
          self.append_mail('---------- problem in output file ------')
          self.append_mail(s)
          self.append_mail('-------------------------------- ------\n\n')
          everything_ok = False

      if what.find('mitgcm')>=0:
        #is_mitgcm_ok = self.greps(' Finished ... at YYYY MM DD HH MM SS = .',output_file)
        is_mitgcm_ok = self.greps('filter finished.',output_file)
        if (is_mitgcm_ok):
          s = 'Despite of everything filter finished was found in %s --> everything ok  ' % (output_file)
          if not(everything_ok):
            self.log_info(s)
            self.append_mail('---------- but it is ok!!!!!!    ------')
            self.append_mail(s)
            self.append_mail('-------------------------------- ------\n\n')
          everything_ok =  True
          return True
        else:
          s = 'String "filter finished" not found in %s --> something went wrong  ' % (output_file)
          self.log_info(s)
          self.append_mail('---------- problem in output file ------')
          self.append_mail(s)
          self.append_mail('-------------------------------- ------\n\n')
          everything_ok = False
            

      if not(everything_ok):
        return False

      return is_job_completed
    
if __name__ == "__main__":
    K=decimate_test()
    K.start()
