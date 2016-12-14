#!/sw/xc40/python/2.7.11/sles11.3_gnu5.1.0/bin/python
#from breakit import *
from engine import *
import datetime,time



import glob
import pprint


from contextlib import contextmanager

DECIMATE_VERSION = '0.3'

@contextmanager
def working_directory(directory):
    owd = os.getcwd()
    try:
        os.chdir(directory)
        yield directory
    finally:
        os.chdir(owd)

        

class decimate(engine):

  def __init__(self,app_name='decimate', app_version='???', decimate_version_required=DECIMATE_VERSION):

    self.DECIMATE_VERSION = DECIMATE_VERSION 
    self.APPLICATION_NAME=app_name
    self.APPLICATION_VERSION=app_version

    self.JOBS = {}
    self.JOBS_DEPENDS_ON = {}

    self.DECIMATE_DIR = os.getenv('DECIMATE_PATH')

    if not(hasattr(self,'FILES_TO_COPY')):
        self.FILES_TO_COPY = []
    for f in ['decimate.py','engine.py','env.py','decimate.pyc','engine.pyc','env.pyc',]:
        self.FILES_TO_COPY = self.FILES_TO_COPY + ['%s/%s' % (self.DECIMATE_DIR,f) ]
    
    # checking
    self.check_python_version()
    self.check_decimate_version(decimate_version_required)

    engine.__init__(self,engine_version_required='0.21',app_name=app_name, app_version=app_version)


  #########################################################################
  # welcome message
  #########################################################################

  def welcome_message(self,print_header=True, print_cmd=True):
    """ welcome message"""

    if print_header:  
      print
      print("          ########################################")
      print("          #                                      #")
      print("          # Welcome to %11s version %5s!#" % (self.APPLICATION_NAME, self.APPLICATION_VERSION))
      print("          #   (using DECIMATE Framework %3s)     #" % self.DECIMATE_VERSION)
      print("          #                                      #")
      print("          ########################################")
      print("       ")

    engine.welcome_message(self,print_header=False, print_cmd=print_cmd)

    
  #########################################################################
  # checking methods
  #########################################################################
      

  def check_decimate_version(self,version):
    current = int(("%s" % self.DECIMATE_VERSION).split('.')[1])
    asked   = int(("%s" % version).split('.')[1])
    if (asked>current):
        self.error("Current Decimate version is %s while requiring %s, please fix it!" % (current,asked))




  #########################################################################
  # starting the dance
  #########################################################################
    
  def start(self):

    self.log_debug('[Decimate:start] entering')
    engine.start(self)
    self.run()

  #########################################################################
  # check for tne option on the command line
  #########################################################################


  def initialize_parser(self):
    engine.initialize_parser(self)
    
    self.parser.add_argument("-l", "--log", action="store_true", help='display and tail current log')
    self.parser.add_argument("-s", "--status", action="store_true", help='list status of jobs and of the whole workflow')
    self.parser.add_argument("-k", "--kill", action="store_true", help='kills job of this study')
    self.parser.add_argument("-c", "--cont", action="store_true",
                             help='continue the already launched workflow in this directory', default=False)
    self.parser.add_argument("--scratch", action="store_true",
                             help='relaunch a neww workflow, erasing all trace from the previous one',default=False)


    self.parser.add_argument("--generate", action="store_true", help='generate the workflow')
    self.parser.add_argument("--launch", action="store_true", help='launch the workflow')
    self.parser.add_argument("-z","--max-retry", type=int, default=3, help='Number of time a step can fail successively')

    self.parser.add_argument("-q","--max-queued-steps", type=int, help='maximum number of steps to be queued',default=3)
    self.parser.add_argument("-p","--max-jobs", type=int, default=3, help='Maximimum number of total jobs accepted in the queue')
    
    self.parser.add_argument("--finalize", action="store_true", help=argparse.SUPPRESS)
    self.parser.add_argument("--test", type=str, help=argparse.SUPPRESS)

    self.parser.add_argument("-j", "--job_status", action="store_true", help=argparse.SUPPRESS)
    self.parser.add_argument("--spawned", action="store_true", help=argparse.SUPPRESS)
    self.parser.add_argument("--check-previous-step", type=str , help=argparse.SUPPRESS)
    self.parser.add_argument("--step", default='launch',type=str , help=argparse.SUPPRESS)
    self.parser.add_argument("--taskid", type=str , help=argparse.SUPPRESS)
    self.parser.add_argument("--jobid", type=int , help=argparse.SUPPRESS)
    self.parser.add_argument("--attempt", type=int , default=0, help=argparse.SUPPRESS)
    self.parser.add_argument("--array-first", type=int , help=argparse.SUPPRESS)
    self.parser.add_argument("--workflowid", type=str , default="0", help=argparse.SUPPRESS)

    self.parser.add_argument("-y","--yes",  action="store_true", help=argparse.SUPPRESS)
    self.parser.add_argument("-n","--no",  action="store_true", help=argparse.SUPPRESS)


    self.user_initialize_parser()

    
  def user_initialize_parser(self):
      pass
    
  def run(self):

    self.init_jobs()

    self.set_mail_subject_prefix('Re: %s' % (self.args.workflowid))    
    
    self.relaunching = False

    # initialization of some parameters appearing in traces

    if self.args.check_previous_step:
      try:
        args = self.args.check_previous_step.split(",")
        self.CHECK = args[0]
        self.CHECK_LAST_TASK_ID = int(args[1])
      except:
        self.CHECK_LAST_ID = 1
        self.CHECK_LAST_TASK_ID = 1
        
    if self.args.taskid:
      try:
        args = self.args.taskid.split(',')
        self.TASK_ID = int(args[0])
        self.LAST_TASK_ID = int(args[1])
      except:
        self.TASK_ID = 1
        self.LAST_TASK_ID = 1
    else:
        self.TASK_ID = 0
        self.LAST_TASK_ID = 1

    if self.args.array_first:
      self.MY_ARRAY_CURRENT_FIRST = int(self.args.array_first)

    self.set_log_prefix("%s-%s-%s" % (self.args.step,self.TASK_ID,self.args.attempt))

    # initialization of mail feature

    if self.args.mail:
      self.init_mail()
        

    # in case of testing mode, reads the scenario file that will simulate a use case
    # to run
    
    if self.args.test:
      self.read_scenario_file()
    else:
      self.SCENARIO = ""


    #
    # Main loop of possible actions
    #
      
    if self.args.kill:
      self.kill_workflow()
      sys.exit(0)

    if self.args.log:
      self.tail_log_file(keep_probing=True,no_timestamp=True,stop_tailing=['workflow is finishing','workflow is aborting'])
      sys.exit(0)

    if self.args.status:
      self.print_workflow()
      sys.exit(0)
      
    if self.args.finalize:
      self.finalize()
      sys.exit(0)

    if self.args.check_previous_step:
      self.check_current_state(self.CHECK)
      sys.exit(0)
      
    if self.args.generate:
      self.generate_jobs()
      sys.exit(0)
      
    if self.args.launch:
      self.launch_jobs()
      sys.exit(0)


    if self.args.job_status:
      self.get_current_jobs_status()
      sys.exit(0)

    s = 'starting Task %s-%s (out of %ss Job_id=%s) ' % \
        (self.args.step,self.args.taskid,self.LAST_TASK_ID,self.args.jobid)
    self.log_info(s,2)

    self.send_mail('%s' % s,2)

    if self.args.fake and self.args.step:
      self.fake_actual_job()

    self.load()
    
    if not(self.args.spawned):
      if len(self.steps_list)>0 and self.args.cont:
          self.ask("Adding jobs to the current workflow? ", default='y' )
      if len(self.steps_list)>0 and self.args.scratch:
          self.ask("Forgetting the previous workflow and starting from scratch? ", default='n' )
          self.clean()
          if os.path.exists(self.WORKSPACE_FILE):
              os.unlink(self.WORKSPACE_FILE)

      elif len(self.steps_list)>0:
          print """
                ----------> <      WARNING     > <--------------
                Some workflow has already been launched from this
                    directory and may be still running

                   following options : 
                   --kill     to kill the ongoing workflow 
                              and keep previous results   
                   --status   to obtain a detailed status on 
                              ongoing workflow
                   --continue to add jobs to the current  
                              worklfow.
                   --scratch  to kill an eventual ongoing 
                              workflow and start a new one
                              from scratch, deleting any 
                              tracking information about the
                              previous workflow
                Please modify your command
                ---------->  END OF COMMAND   <-------------
                """ 
          sys.exit(0)
      print self.launch_jobs()
      sys.exit(0)

    
    try:
      if not(self.JOBS[int(self.args.jobid)]['comes_before']) and not(self.relaunching):
        self.log_info('Normal end of this batch',2)
        self.log_info('=============== workflow is finishing ==============')
        if self.args.mail:
          self.send_mail('Workflow has just completed successfully')
    except:
        self.error("ZZZZZZZZ problem in decimate main loop ",exit=False,exception=True)
        pass
          
  #########################################################################
  # get job id
  #########################################################################

  def get_jobids(self):

    job_id = {}
    job_id_keys = []
    for s in self.steps_list:  #self.STEPS.keys():
        for jid in self.STEPS[s]['arrays']:
            job_id[jid] = s
            job_id_keys.append(jid)
    #job_id_keys.sort()
    return (job_id_keys,job_id)

     
  #########################################################################
  # print workflow 
  #########################################################################

  def print_workflow(self):

    self.load()
    self.get_current_jobs_status()

    (jk,job_id) = self.get_jobids()

    if len(jk)==0:
        self.log_info('No workflow has been submitted yet')

    for j in jk:
        s = job_id[j]
        status = self.STEPS[s]['status']
        comment =""
        if status in ['DONE','RUNNING','ABORTED']:
            comment = " COMPLETED: %3d%%  SUCCESS: %3d%%" % \
                      (self.STEPS[s]['completion'],self.STEPS[s]['success'])
        self.log_info('step %s: %-8s  %s' % (s,status,comment))


  #########################################################################
  # kill job
  #########################################################################

  def kill_workflow(self):

    self.ask("Do you want to kill all jobs related to this current workflow now? ", default='n' )
    s = 'killing all the dependent jobs...'
    self.log_info(s)
    self.send_mail(s)

    self.load()
    self.get_current_jobs_status()


    (jk,job_id) = self.get_jobids()

    jobs_to_kill = []
    for jid in jk:
        if self.ARRAYS[jid]['completion']<100.:
            jobs_to_kill = jobs_to_kill + [jid]
            
    self.log_info('%s jobs to kill...' % (len(jobs_to_kill)))
    for job_id in jobs_to_kill:
      step = self.ARRAYS[job_id]['step']
      cmd = ' scancel %s ' % job_id
      self.ARRAYS[job_id]['status'] = 'ABORTED'
      self.STEPS[step]['status'] = 'ABORTED'
      os.system(cmd)
      self.log_info('killing the job %s (step %s)...' % (job_id,step))

    # self.log_info('Abnormal end of this batch... waiting 15 s for remaining job to be killed')
    # time.sleep(15)
    s = '=============== workflow is aborting =============='
    self.save()

#    self.log_debug("get_status:end -> JOBS=\n%s " % pprint.pformat(self.JOBS),2)
    self.log_debug("get_status:end -> STEPS=\n%s " % pprint.pformat(self.STEPS),1)
    self.log_debug("get_status:end -> ARRAYS=\n%s " % pprint.pformat(self.ARRAYS),1)
 #   self.log_info("get_status:end -> TASKS=\n%s " % pprint.pformat(self.TASKS),2)
    
    self.log_info(s)
    self.send_mail(s)
    sys.exit(1)


  #########################################################################
  # finalize the job, putting a stamp somewhere
  #########################################################################

  def finalize(self):
    if not(self.SCENARIO.find(",%s," % self.args.step)>=0 or \
           self.SCENARIO.find(",%s-%s," % (self.args.step,self.TASK_ID))>=0 or \
           self.SCENARIO.find(",%s-%s-%s," % (self.args.step,self.TASK_ID,self.args.attempt))>=0):
      self.log_info("finalizing job : %s-%s " % (self.args.step,self.TASK_ID),2)
      filename = '%s/Done-%s-%s' % (self.SAVE_DIR,self.args.step,self.TASK_ID)
      open(filename,'w')

      self.send_mail('%s-%s Done' % (self.args.step,self.TASK_ID),2)
      
      self.log_info('Done! -> creating stub file %s' % filename,3)

  #########################################################################
  # check the state  of the current jobs and heal them
  #########################################################################

  def check_current_state(self,what):

    filename_all_ok = '%s/Done-%s-all' % (self.SAVE_DIR,what)
    filename_all_nok = '%s/Done-%s-_%s_nok' % (self.SAVE_DIR,what,self.args.attempt)
    if self.TASK_ID==1:
      self.log_info("checking status of previous job : %s [%s-%s] " % \
                    (what,1,self.CHECK_LAST_TASK_ID),2)

      all_complete = True
      not_complete = []
      user_check = True
      user_rejected = []
      
      for i in range(1,self.CHECK_LAST_TASK_ID+1):
        filename_complete = '%s/Complete-%s-%s' % (self.SAVE_DIR,what,i)
        is_complete = os.path.exists(filename_complete)
        if is_complete:
            continue
        
        filename_done = '%s/Done-%s-%s' % (self.SAVE_DIR,what,i)
        is_done = os.path.exists(filename_done)
        self.log_info('checking presence of file %s : %s ' % (filename_done,is_done),3)

        user_check = self.prepare_user_defined_check_job(what,i,self.args.attempt,is_done)

        
        if user_check:
            if not(is_done) and user_check:
                s = 'ZZZZZZZ step %s-%s was not complete but was validated successfully by a check made by a user defined function' \
                    % (what,i)
                self.log_info(s)
                self.send_mail(s)
                
            open(filename_complete,'w')
            continue
        
        if not(is_done) or not(user_check):
          not_complete = not_complete + ["%s" % i]
          all_complete = False
          if is_done:
              os.unlink(filename_done)
          
        if not(user_check):
          self.log_info('task %s_%s rejected by user check' %  (what,i))

        #self.log.info('all_complete=%s' % all_complete,1)
        #self.log.info('not_complete=%s' %  pprint.pformat(not_complete),1)
          
      if not(all_complete):
        s = '!!!!!!!! oooops pb : job missing or uncomplete at last step %s : (%s)' % (what,",".join(not_complete))
        self.log_info(s)
        self.append_mail('Will restart the uncomplete step and fix the workflow')
        open(filename_all_nok,"w")
        self.heal_workflow(what,not_complete)
      else:
        open(filename_all_ok,"w")
        print what,self.args.step
        s = 'ok everything went fine for the step %s! --> Step %s is starting...' % (what,self.args.step)
        self.log_info(s)
        self.send_mail(s.replace('--> ','\n'))
        return 0

    else:
      self.log_info("waiting for the checking of previous job : %s [%s-%s] " % \
                          (what,1,self.CHECK_LAST_TASK_ID),3)
      for i in range(10):
        if os.path.exists(filename_all_ok) or os.path.exists(filename_all_nok):
          break
        self.log_info('waiting...',3)
        time.sleep(10)
        
      if os.path.exists(filename_all_ok):
          self.log_info('ok done!',1)
          return 0

      s = 'something went wrong when checking last level...giving it up!'
      self.log_info(s,4)
      self.send_mail(s,4)
      sys.exit(1)

  #########################################################################
  # prepare to call user defined function to check if the job actually passed
  #########################################################################

  def prepare_user_defined_check_job(self,what,task_id,attempt,is_done):
    self.load()

    job_id = self.STEPS['%s-%s' % (what,attempt)]['arrays'][0]
    pattern =  "%s.task_%s-attempt_%s" % (self.JOBS[job_id]['output_name'],task_id,attempt)
    output_file_pattern = pattern.replace('%a',str(task_id)).replace('%j','*')

    pattern =  "%s.task_%s-attempt_%s" % (self.JOBS[job_id]['error_name'],task_id,attempt)
    error_file_pattern = pattern.replace('%a',str(task_id)).replace('%j','*')

    running_dir = self.JOBS[job_id]['submit_dir']

    s = "CHECKING step: %s   Task: %s Attempt: %s" % (what,task_id,attempt) + "\n" + \
        "Output file pattern : %s" % (output_file_pattern) + "\n" +\
        "Error file pattern : %s" % (error_file_pattern) + "\n" +\
        "Running dir : %s" % (running_dir) + "\n" 
    self.log_info(s,4)

    with working_directory(running_dir):
      output_file_candidates = glob.glob(output_file_pattern)
      if len(output_file_candidates):
          output_file_candidates.sort()
          output_file =output_file_candidates[-1]
          self.log_info('output_file to be scanned : >%s< chosen from [%s]' % (output_file,",".join(output_file_candidates)),2)
      else:
          self.log_info('ZZZZZZ weird... no output file produced of pattern %s' % output_file_pattern)
          output_file = 'No_output_file_found'
          
      error_file_candidates = glob.glob(error_file_pattern)
      if len(error_file_candidates):
          error_file_candidates.sort()
          error_file = error_file_candidates[-1]
          self.log_info('error_file to be scanned : >%s< chosen from [%s]' % (error_file,",".join(error_file_candidates)),2)
      else:
          self.log_info('ZZZZZZ weird... no error file produced of pattern %s' % error_file_pattern)
          error_file = 'No_error_file_found'
              
    s = "CHECKING step : %s-%s " % (what,task_id) 
    
    self.log_info(s,2)
    if self.args.debug > 3:
        print >> sys.stderr, pprint.pformat(self.JOBS)
    user_check = self.check_job(what,task_id,running_dir,output_file,error_file,is_done)


    if not(user_check):
        self.append_mail('User error detected!!! for step %s  task %s  attempt %s' % (what,task_id,attempt))
        #self.send_mail('','User error detected!!! for step %s  task %s  attempt %s' % (what,task_id,attempt))

    
    return user_check

                

  #########################################################################
  # fixing workflow after a failure
  #########################################################################

  def heal_workflow(self,what,not_present):
    s = "restarting the wrong part previous job : %s (%s) and fixing dependency (Attempt %s of %s)  current_dir=->%s<-" % \
                    (what,",".join(not_present),self.args.attempt,self.args.max_retry,os.getcwd())
    self.log_info(s)
    self.append_mail(s)

    self.load()
    #print self.JOBS.keys()

       
    if self.args.jobid in self.JOBS.keys():
      job = self.JOBS[self.args.jobid]

      if int(self.args.attempt)>=self.args.max_retry:
        s = 'Too much failed attempt for step %s my_joid is %s' % (what,self.args.jobid)
        self.log_info(s)
        self.append_mail(s)
        self.log_info('killing all the dependent jobs...')
        self.send_mail('killing all the dependent jobs...')
        #self.log_info(self.print_workflow(job['job_id']))
        while job['comes_before']:
          next_job_id = job['comes_before']
          cmd = ' scancel %s ' % next_job_id
          os.system(cmd)
          self.log_info('killing the job %s...',next_job_id,2)
          job  = self.JOBS[next_job_id]
        self.log_info('Abnormal end of this batch... waiting 15 s for remaining job to be killed')
        time.sleep(15)
        s = '=============== workflow is aborting =============='
        self.log_info(s)
        self.send_mail(s)
        time.sleep(5)
        sys.exit(1)

      #print 'job'
      #print job
      next_job_id = job['comes_before']
      if next_job_id:
        next_job = self.JOBS[next_job_id]
      else:
        next_job = None
      previous_job_id =job['comes_after']
      previous_job = self.JOBS[previous_job_id]
      previous_job['attempt'] = previous_job['attempt'] + 1
      previous_job['array'] = ",".join(not_present)

      self.log_debug('previous job:'+pprint.pformat(previous_job),3)

      previous_job_file = previous_job['script']
      previous_submit_cmd = previous_job['submit_cmd']
      previous_submit_dir = previous_job['submit_dir']
      self.log_info("previous job is # %s, next job is # %s " % (previous_job_id,next_job_id),2)
      self.log_info("previous job file is >>%s<< " % (previous_job_file),2)

      self.args.attempt = int(self.args.attempt)+1
      (job_previous_id_new,cmd_previous_new) = self.submit_job(previous_job)
      
      job['comes_after'] = job['dependency'] = job_previous_id_new

      self.log_debug('new current job created by heal_workflow:'+pprint.pformat(job),3)
      
      (job_id_new,cmd_new) = self.submit_job(job)
      job['job_id'] = job_id_new
      job['submit_cmd'] = cmd_new
      self.JOBS[job_id_new] = job

      previous_job['comes_before'] = previous_job['make_depends'] = job_id_new
      if next_job_id:
        job['comes_before'] = job['make_depends'] = next_job_id
        next_job['comes_after'] = job['dependency'] = job_id_new
        cmd = 'scontrol update jobid=%s dependency=afterany:%s' % (next_job_id,job_id_new)
        self.log_info('update cmd >%s< ' % cmd,3)
        os.system(cmd)

        self.relaunching = True
        
      self.JOBS[job_previous_id_new] = previous_job

      self.save()
    else:
      self.log_info('strange... for job %s no dependency recorded???' % self.args.jobid)
      self.log_info("heal workflow end -> JOBS=\n%s " % pprint.pformat(self.JOBS))
      
    self.log_info('end of heal_workflow',2)
    self.log_info('committing suicide in 5 seconds....')

    self.flush_mail('Job has been fixed and is restarting')

    time.sleep(5)
    sys.exit(1)

  #########################################################################
  # fake computation in order to test
  #########################################################################

  def fake_actual_job(self):
    if self.SCENARIO.find(",%s," % self.args.step)>=0 or \
       self.SCENARIO.find(",%s-%s," % (self.args.step,self.TASK_ID))>=0 or \
       self.SCENARIO.find(",%s-%s-%s," % (self.args.step,self.TASK_ID,self.args.attempt))>=0:
      s = "According to test file FAILING the step : %s-%s " % (self.args.step, self.TASK_ID)
      self.log_info(s,2)
      s= "******* I AM OUT OF HERE ********* CRASHING step : %s-%s !!!!" % (self.args.step, self.TASK_ID)
      self.log_info(s)
      sys.exit(1)
    else:
      self.log_info("faking the step : %s-%s " % (self.args.step,self.TASK_ID),4)
      self.fake_job(self.args.step,self.TASK_ID,self.args.attempt)
    
  #########################################################################
  # read the scenario file in order to fake a behavior
  #########################################################################

  def read_scenario_file(self):
    self.log_debug('reading scenario files %s' % self.args.test,2)

    if self.args.test and not(os.path.exists(self.args.test)):
      self.error_report('Scenario Test file %s does not exist!!!' % self.args.test)
      
    if os.path.exists(self.args.test):
      l = open(self.args.test,"r").readlines()
      self.SCENARIO = ",%s," % ",".join(l).replace('\n','')
      self.log_info("Have just read the scenario file : %s : %d error (%s)" % \
                    (self.args.test,len(l),self.SCENARIO),4)

      

  #########################################################################
  # submitting one job
  #########################################################################

  def submit_job(self,job):

    self.log_debug('in submit JOBS start: %s',','.join(map(str,self.JOBS.keys())))

    cmd = [self.SCHED_SUB]
    prolog = []
    
    if (job['dependency']) :
      prolog = prolog + [self.SCHED_DEP+":%s"%job['dependency'] ]

    if self.args.exclude_nodes:
      prolog = prolog + ["-x",self.args.exclude_nodes]

    if self.args.partition:
      prolog = prolog + ["--partition=%s" % self.args.partition]

    if self.args.reservation:
      prolog = prolog + ["--reservation=%s" % self.args.reservation]

    if job['array']:
      prolog = prolog + [self.SCHED_ARR+" "+job['array']]
      array_range = job['array']
    else:
      prolog = prolog + [self.SCHED_ARR+' 1-1']
      array_range = '1-1'
      
    if job['account'] and not(self.MY_MACHINE=="sam"):  
      prolog = prolog +  ['--account=%s'        % job['account'] ]
      
    prolog = prolog + \
          ['--time=%s'            % job['time'],
           '--job-name=%s'     % (job['name']),
           '--error=%s.task_%%a-attempt_%s'   % (job['error_name'],self.args.attempt)                       ,
           '--output=%s.task_%%a-attempt_%s'  % (job['output_name'],self.args.attempt)                       ,
           '--ntasks=%s'          % job['ntasks']]
    cmd = cmd +[ '%s_%s'                % (job['script_file'], self.args.attempt) ]


    job_content_template = "#!/bin/bash\n"
    if self.args.pbs:
        scheduler_flag = "#PBS"
    else:
        scheduler_flag = "#SBATCH"
    for p in prolog:
        job_content_template = job_content_template + "%s %s " % (scheduler_flag,p)+"\n"

    job_content_template = job_content_template + "".join(open(job['script_file'],"r").readlines())
    job_content_updated  = job_content_template.replace('__ATTEMPT__',"%s" % self.args.attempt)
    job_script_updated  = open('%s_%s' % (job['script_file'], self.args.attempt), "w")
    job_script_updated.write(job_content_updated)
    job_script_updated.close()
    
    step =  '%s-%s' % (job['name'],self.args.attempt)
    job['step'] = step

    self.log_debug("submitting cmd: "+" ".join(cmd))
    job_id = '%s-%s' %  (step,time.strftime('%Y-%b-%d-%H:%M:%S'))
    self.log_debug("job submitted : %s depends on %s" % (job_id,job['dependency']),1)


    job_script_updated  = open('%s_%s_%s' % (job['script_file'], self.args.attempt,job_id), "w")
    job_script_updated.write(job_content_updated.replace('${SLURM_ARRAY_JOB_ID}','%s'%job_id))
    job_script_updated.close()
  

    job['job_id'] = job_id
    job['submit_cmd'] = cmd
    job['content'] = job_content_updated
    
    job_before = job['comes_after']
    if job_before:
      self.JOBS[job_before]['comes_before'] =  job_id
      self.JOBS[job_before]['make_depend']  =  job_id

    self.JOBS[job_id] = job
    #self.JOB_ID[job['name']] = job_id

    for i in RangeSet(array_range):
        self.JOB_STATUS['%s_%s' % (job_id,i)]  = 'WAITING'
    
      
    self.steps_list = self.steps_list + [step]
    self.steps_submitted = self.steps_submitted + [step]
    self.last_step_submitted = step

    self.STEPS[step] = {}
    self.STEPS[step]['arrays'] = [job_id]
    self.STEPS[step]['status'] = 'WAITING'
    self.STEPS[step]['completion'] = 0
    self.STEPS[step]['success'] = 0
    self.STEPS[step]['items'] = float(len(RangeSet(array_range)))

    self.ARRAYS[job_id] = {}
    self.ARRAYS[job_id]['step'] = step
    self.ARRAYS[job_id]['range'] = array_range
    self.ARRAYS[job_id]['range_all'] = array_range
    self.ARRAYS[job_id]['status'] = 'WAITING'
    self.ARRAYS[job_id]['completion'] = 0
    self.ARRAYS[job_id]['success'] = 0
    self.ARRAYS[job_id]['items'] = float(len(RangeSet(array_range)))


    self.TASKS[step] = {}
    for task in RangeSet(array_range):
        self.TASKS[step][task] = {}
        self.TASKS[step][task]['status'] = 'WAITING'
        self.TASKS[step][task]['counted'] = False
        

    self.log_debug("Saving Job Ids...",1)
    self.save()

      
    self.log_info('submitting job %s (for %s) --> Job # %s <-depends-on %s' % (job['name'],job['array'],job_id,job['dependency']))

    return (job_id,cmd)

  #########################################################################
  # activate job taking constraints into account
  #########################################################################

  def activate_job(self,job):
    step =  '%s-%s' % (job['name'],self.args.attempt)

    self.steps_list = self.steps_list + [step]
    self.steps_submitted = self.steps_submitted + [step]
    self.last_step_submitted = step

    self.STEPS[step] = {}
    self.STEPS[step]['arrays'] = [job_id]
    self.STEPS[step]['status'] = 'SUBMITTED'
    self.STEPS[step]['completion'] = 0
    self.STEPS[step]['success'] = 0
    self.STEPS[step]['items'] = float(len(RangeSet(array_range)))

    self.ARRAYS[job_id] = {}
    self.ARRAYS[job_id]['step'] = step
    self.ARRAYS[job_id]['range'] = array_range
    self.ARRAYS[job_id]['range_all'] = array_range
    self.ARRAYS[job_id]['status'] = 'SUBMITTED'
    self.ARRAYS[job_id]['completion'] = 0
    self.ARRAYS[job_id]['success'] = 0
    self.ARRAYS[job_id]['items'] = float(len(RangeSet(array_range)))


    self.TASKS[step] = {}
    for task in RangeSet(array_range):
        self.TASKS[step][task] = {}
        self.TASKS[step][task]['status'] = 'SUBMITTED'
        self.TASKS[step][task]['counted'] = False
        

    self.log_debug("Saving Job Ids...",1)
    self.save()

    self.log_debug('in submit JOBS end: %s',','.join(map(str,self.JOBS.keys())))

    return (job_id,cmd)

    job['job_id'] = job_id
    job['submit_cmd'] = cmd
        

    job_before = job['comes_after']
    if job_before:
      self.JOBS[job_before]['comes_before'] =  job_id
      self.JOBS[job_before]['make_depend']  =  job_id

    self.JOBS[job_id] = job
    #self.JOB_ID[job['name']] = job_id

    for i in RangeSet(array_range):
        self.JOB_STATUS['%s_%s' % (job_id,i)]  = 'SUBMITTED'
    
      
    self.log_info('submitting job %s (for %s) --> Job # %s <-depends-on %s' % (job['name'],job['array'],job_id,job['dependency']))


    step =  '%s-%s' % (job['name'],self.args.attempt)

    self.steps_list = self.steps_list + [step]
    self.steps_submitted = self.steps_submitted + [step]
    self.last_step_submitted = step

    self.STEPS[step] = {}
    self.STEPS[step]['arrays'] = [job_id]
    self.STEPS[step]['status'] = 'SUBMITTED'
    self.STEPS[step]['completion'] = 0
    self.STEPS[step]['success'] = 0
    self.STEPS[step]['items'] = float(len(RangeSet(array_range)))

    self.ARRAYS[job_id] = {}
    self.ARRAYS[job_id]['step'] = step
    self.ARRAYS[job_id]['range'] = array_range
    self.ARRAYS[job_id]['range_all'] = array_range
    self.ARRAYS[job_id]['status'] = 'SUBMITTED'
    self.ARRAYS[job_id]['completion'] = 0
    self.ARRAYS[job_id]['success'] = 0
    self.ARRAYS[job_id]['items'] = float(len(RangeSet(array_range)))


    self.TASKS[step] = {}
    for task in RangeSet(array_range):
        self.TASKS[step][task] = {}
        self.TASKS[step][task]['status'] = 'SUBMITTED'
        self.TASKS[step][task]['counted'] = False
        

    self.log_debug("Saving Job Ids...",1)
    self.save()

    self.log_debug('in submit JOBS end: %s',','.join(map(str,self.JOBS.keys())))


    
  #########################################################################
  # wrapping job to put control over it
  #########################################################################

  def wrap_job_script(self,job):
    self.log_debug("adding prefix and suffix to job %s : " % job['script'])
      
    l = "".join(open(job['script'],'r').readlines())

    l0 = ""
    for env_var in ['PATH','LD_LIBRARY_PATH','DECIMATE_PATH']:
        l0 = l0+ "export %s=%s \n" % (env_var,os.getenv(env_var))
    for env_var in ['PYTHONPATH']:
        l0 = l0+ "export %s=/tmp:%s:%s \n" % (env_var,self.SAVE_DIR,os.getenv(env_var))

    l0 = l0+ "cp %s/*py* /tmp \n" % (self.SAVE_DIR)
    
    #(self.SAVE_DIR,
    l0 = l0+ "sleep 1\n python %s/%s --step %s --attempt __ATTEMPT__ --log-dir %s  %s %s %s--spawned " % \
         ("/tmp",
          os.path.basename(sys.argv[0]),\
                                         job['name'],self.LOG_DIR,"-d "*self.args.debug,"-i "*self.args.info,"-m "*self.args.mail_verbosity)
    l0 = l0 + "--taskid ${SLURM_ARRAY_TASK_ID},%s --jobid ${SLURM_ARRAY_JOB_ID}" % job['last_task_id']
    l0 = l0 + " --max-retry=%s" % self.args.max_retry
    l0 = l0 + " --workflowid='%s'" % self.args.workflowid
    
    if self.args.mail:
      l0 = l0 + " --mail %s " % self.args.mail

    if self.args.nocleaning:
      l0 = l0 + " --nocleaning "
    
    if self.args.test:
      l0 = l0 + " --test %s" % self.args.test
    
    if self.args.fake:
      l = '#!/bin/bash\n#JOB_FAKE\n'
      l = l + """echo "I am task ${SLURM_ARRAY_TASK_ID} on node `hostname`" \n"""+\
          """echo "Main jobid is: ${SLURM_JOB_ID}" \n"""

      l = l + l0 + " --fake "

    reconnecting_cmd = "#reconnect"
    prefix = ""
    
    if job['step_before']:
      prefix = '#!/bin/bash\n'
      prefix = prefix + '#JOB_CHECKING\n%s  --check-previous-step=%s,%s ' % (l0,job['step_before'],job['last_task_id_before'])
      
      if self.args.fake:
        prefix = prefix + ' --fake'
        self.log_debug('prefix = %s' % prefix)
      
      prefix = prefix + """
       if [ $? -ne 0 ] ; then
           echo "[ERROR] FAILED in precedent step : stopping current job and reconnecting..."
           %s 
           exit 1
       else \n""" % reconnecting_cmd
      
    l = prefix  + "#!/bin/bash\n\n# ---------------- START OF ORIGINAL USER SCRIPT  -------------------\n" + l \
        + "\n# ----------------   END OF ORIGINAL USER SCRIPT  -------------------\n\n" 

    l = l + """
          if [ $? -ne 0 ] ; then
              echo "[ERROR] FAILED in current step : exiting immediately..."
              exit 1
          else """ + '\n\n ################# finalizing job ####################\n'
    if self.args.fake:
        l = l + l0 + ' --finalize \n'
    else:
        l = l + '      touch %s/Done-%s-${SLURM_ARRAY_TASK_ID}\n' % (self.SAVE_DIR,job['name'])

    l = l + "              fi       # closing if of successfull job \n"

    if job['step_before']:
      l = l + "\n           fi       # closing if of successfull previous job check"

    l = l+ '\\rm -rf /tmp/*py'
    
    return l
    
  #########################################################################
  # generation of the jobs to be submitted
  #########################################################################

  def init_jobs(self):

    pass
    #self.error_report("init_jobs needs to be valued",exit=True)

  #########################################################################
  # generation of the jobs to be submitted
  #########################################################################

  def generate_jobs(self):

    self.error_report("generate_jobs needs to be valued",exit=True)


  #########################################################################
  # submitting all the first jobs
  #########################################################################

  def launch_jobs(self,**optional_parameters):
      self.log_info('=============== New workflow starting ==============')
      self.log_info('ZZZ cleaning workspace before launching ...',2)
      self.log_info('=============== New workflow starting ==============',2)

      os.system('\\rm -rf *.err *.out *.pickle *.pickle.old .%s/SAVE/*.pcy* .%s/SAVE/Done* .%s/SAVE/*job+_*' % \
                 (self.APPLICATION_NAME,self.APPLICATION_NAME,self.APPLICATION_NAME))

      for f in glob.glob("*.py"):
        self.log_debug("copying file %s into SAVE directory " % f,1)
        os.system("cp ./%s  %s" % (f,self.SAVE_DIR))

      epoch_time = int(time.time())
      st = "%s+%s+%s" % (self.APPLICATION_NAME,os.getcwd(),epoch_time)
      self.args.workflowid =  "%s at %s %s " % (self.APPLICATION_NAME,epoch_time, reduce(lambda x,y:x+y, map(ord, st)))
      self.set_mail_subject_prefix('Re: %s' % (self.args.workflowid))    
      self.send_mail('=============== New workflow starting ==============')

      
      self.user_launch_jobs(**optional_parameters)

      if self.args.mail:
        self.send_mail('Workflow has just been submitted')

  def user_launch_jobs(self):
    self.error_report("launch_jobs needs to be valued",exit=True)

    
if __name__ == "__main__":
    K=decimate()
    K.start()  
