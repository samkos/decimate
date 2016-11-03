#!/usr/bin/python

import glob,os,re
import getopt, traceback
import time, datetime, sys, threading
import subprocess
import logging
import logging.handlers
import warnings
import shutil
from os.path import expanduser
from env     import *
import fcntl
import getpass
import pickle
import argparse
import pprint
from ClusterShell.NodeSet import *

JOB_POSSIBLE_STATES = ('PENDING','RUNNING','SUSPENDED','COMPLETED',\
                       'CANCELLED','CANCELLED+','FAILED','TIMEOUT',\
                       'NODE_FAIL','PREEMPTED','BOOT_FAIL','COMPLETING',\
                       'CONFIGURING','RESIZING','SPECIAL_EXIT')

JOB_ACTIVE_STATES   = ('PENDING','RUNNING','SUSPENDED','COMPLETING',\
                       'CONFIGURING','RESIZING')

JOB_RUNNING_STATES   = ('RUNNING','COMPLETING',\
                       'CONFIGURING','RESIZING')

JOB_DONE_STATES = ("CANCELLED","COMPLETED","FAILED","TIMEOUT")

LOCK_EX = fcntl.LOCK_EX
LOCK_SH = fcntl.LOCK_SH
LOCK_NB = fcntl.LOCK_NB

ENGINE_VERSION = '0.21'

ERROR_FILE_DOES_NOT_EXISTS = -33
ERROR_PATTERN_NOT_FOUND = -34

class LockException(Exception):
    # Error codes:
    LOCK_FAILED = 1


  
class engine:

  def __init__(self,app_name="app",app_version="?",app_dir_log=False,engine_version_required=ENGINE_VERSION):
    #########################################################################
    # set initial global variables
    #########################################################################


    self.SCRIPT_NAME = os.path.basename(__file__)

    self.APPLICATION_NAME=app_name
    self.APPLICATION_VERSION=app_version
    self.ENGINE_VERSION=ENGINE_VERSION

    self.LOG_PREFIX=""
    self.LOG_DIR = app_dir_log
   
    self.WORKSPACE_FILE = "./.%s/SAVE/%s.pickle" % (app_name,'workspace')
    self.JOB_DIR = os.path.abspath("./.%s/RESULTS" % app_name)
    self.SAVE_DIR = os.path.abspath("./.%s/SAVE" % app_name)
    self.LOG_DIR = os.path.abspath("./.%s/LOGS" % app_name)


    # saving scheduling option in the object
    
    self.MAIL_COMMAND = MAIL_COMMAND
    self.MAIL_SUBJECT_PREFIX = ""
    self.MAIL_CURRENT_MESSAGE = ""
    self.SUBMIT_COMMAND = SUBMIT_COMMAND
    self.SCHED_TYPE = SCHED_TYPE
    self.DEFAULT_QUEUE = DEFAULT_QUEUE
    

    # initilization
    
    self.welcome_message()

    # checking
    self.check_python_version()
    self.check_engine_version(engine_version_required)

    # parse command line to eventually overload some default values
    self.parser = argparse.ArgumentParser(conflict_handler='resolve')
    self.initialize_parser()
    self.args = self.parser.parse_args()
    
    # initialize logs
    self.initialize_log_files()

    # initialize scheduler
    self.initialize_scheduler()

    # initialize job tracking arrays
    self.JOBS = {}
    self.JOB_ID = {}
    self.JOB_BY_NAME = {}
    self.JOB_WORKDIR = {}
    self.JOB_STATUS = {}
    self.TASK_STATUS = {}
    self.timing_results = {}
    self.SYSTEM_OUTPUTS = {}
    
    self.LOCK_FILE = "%s/lock" % self.LOG_DIR
    self.STATS_ID_FILE = "%s/stats_ids.pickle" % self.LOG_DIR

    self.already_saved = False
    self.already_loaded = False

    self.env_init()
    
  def start(self):

    self.log_debug('[Engine:start] entering')
    engine.run(self)


  #########################################################################
  # check for tne option on the command line
  #########################################################################


  def initialize_parser(self):
    self.parser.add_argument("-i","--info",  action="count", default=0, help=argparse.SUPPRESS)
    self.parser.add_argument("-d","--debug", action="count", default=0, help=argparse.SUPPRESS)
    self.parser.add_argument("-m","--mail-verbosity", action="count", default=0, help=argparse.SUPPRESS)

    # self.parser.add_argument("--kill", action="store_true", help="Killing all processes")
    # self.parser.add_argument("--scratch", action="store_true", help="Restarting the whole process from scratch cleaning everything")
    # self.parser.add_argument("--restart", action="store_true", help="Restarting the process from where it stopped")

    self.parser.add_argument("--kill", action="store_true", help=argparse.SUPPRESS)
    self.parser.add_argument("--scratch", action="store_true", help=argparse.SUPPRESS)
    self.parser.add_argument("--restart", action="store_true", help=argparse.SUPPRESS)
    self.parser.add_argument("--nocleaning", action="store_true", default=False, help=argparse.SUPPRESS)
    self.parser.add_argument("--create-template", action="store_true", help='create template')

    self.parser.add_argument("--go-on", action="store_true", help=argparse.SUPPRESS)
    self.parser.add_argument("--log-dir", type=str, help=argparse.SUPPRESS)
    self.parser.add_argument("--mail", type=str, help=argparse.SUPPRESS)
    self.parser.add_argument("--fake", action="store_true", help=argparse.SUPPRESS)
    self.parser.add_argument("--save", type=str, help=argparse.SUPPRESS)
    self.parser.add_argument("--load", type=str,  help=argparse.SUPPRESS)    
    self.parser.add_argument("--dry", action="store_true", help=argparse.SUPPRESS)
    self.parser.add_argument("--pbs", action="store_true", help=argparse.SUPPRESS)
    self.parser.add_argument("-x","--exclude-nodes", type=str , help=argparse.SUPPRESS)
    self.parser.add_argument("-r","--reservation", type=str , help='SLURM reservation')
    self.parser.add_argument("-p","--partition", type=str , help='SLURM partition')
        

  #########################################################################
  # main router
  #########################################################################

  def run(self):

    if self.args.info>0:
        self.log.setLevel(logging.INFO)
    if self.args.debug>0:
        self.log.setLevel(logging.DEBUG)

    if self.args.scratch:
        self.log_info("restart from scratch")
        self.log_info("killing previous jobs...")
        self.kill_jobs()
        self.log_info("cleaning environment...")
        self.clean()


    if self.args.mail_verbosity>0 and not(self.args.mail):
        self.args.mail = getpass.getuser()
        
    if self.args.kill:
        self.kill_jobs()
        sys.exit(0)

    if self.args.create_template:
        self.create_template()
        
  #########################################################################
  # set self.log file
  #########################################################################


  def initialize_log_files(self):
      
    if not(self.LOG_DIR):
      self.LOG_DIR= "/scratch/%s/logs/.%s" % (getpass.getuser(),self.APPLICATION_NAME)


    if self.args.log_dir:
        self.LOG_DIR = self.args.log_dir

    self.LOG_DIR = expanduser("%s" % self.LOG_DIR)
    
    for d in [ self.LOG_DIR]:
      if not(os.path.exists(d)):
        os.makedirs(d)
        

    self.log = logging.getLogger('%s.log' % self.APPLICATION_NAME)
    self.log.propagate = None
    self.log.setLevel(logging.ERROR)
    self.log.setLevel(logging.INFO)
    console_formatter=logging.Formatter(fmt='[%(levelname)-5.5s] %(message)s')
    formatter = logging.Formatter("%(asctime)s [%(levelname)-5.5s]  %(message)s")

    self.log_file_name = "%s/" % self.LOG_DIR+'%s.log' % self.APPLICATION_NAME
    open(self.log_file_name, "a").close()
    handler = logging.handlers.RotatingFileHandler(
         self.log_file_name, maxBytes = 20000000,  backupCount = 5)
    handler.setFormatter(formatter)
    self.log.addHandler(handler)


    consoleHandler = logging.StreamHandler(stream=sys.stdout)
    consoleHandler.setFormatter(console_formatter)
    self.log.addHandler(consoleHandler)



  def log_debug(self,msg,level=0,dump_exception=0):
    if level<=self.args.debug:
      if len(self.LOG_PREFIX):
          msg = "%s:%s" % (self.LOG_PREFIX,msg)
      self.log.debug(msg)
      if (dump_exception):
        self.dump_exception()
      #self.log.debug("%d:%d:%s"%(self.args.debug,level,msg))

  def log_info(self,msg,level=0,dump_exception=0):
    if level<=self.args.info:
      if len(self.LOG_PREFIX):
          msg = "%s:%s" % (self.LOG_PREFIX,msg)
      self.log.info(msg)
      if (dump_exception):
        self.dump_exception()
      #self.log.debug("%d:%d:%s"%(self.args.debug,level,msg))

  def dump_exception(self,where=None):
    if where:
      print '\n#######!!!!!!!!!!######## Exception occured at ',where,'############'
    exceptionType, exceptionValue, exceptionTraceback = sys.exc_info()
    traceback.print_exception(exceptionType,exceptionValue, exceptionTraceback,\
                                file=sys.stdout)
    print '#'*80


  def set_log_prefix(self,prefix):
      self.LOG_PREFIX = prefix

    
  #########################################################################
  # initialize_scheduler
  #########################################################################
  def initialize_scheduler(self):
    global SCHED_TYPE

    if SCHED_TYPE=="pbs" or self.args.pbs:
      self.PBS = True
      self.SCHED_TAG = "#PBS"
      self.SCHED_SUB = "qsub"
      self.SCHED_ARR = "-t"
      self.SCHED_KIL = "qdel"
      self.SCHED_Q = "qstat"
      self.SCHED_DEP = "-W depend=afteranyarray"
    else:
      self.SCHED_TAG = "#SBATCH"
      self.SCHED_SUB = "sbatch"
      self.SCHED_ARR = "-a"
      self.SCHED_KIL = "scancel"
      self.SCHED_Q = "squeue"
      self.SCHED_DEP = "--dependency=afterany"
      self.SCHED_DEP_OK = "--dependency=afterok"
      self.SCHED_DEP_NOK = "--dependency=afternotok"


  #########################################################################
  # initialize job environment
  #########################################################################

  def env_init(self):

    self.log_debug('initialize environment ',4)

    for d in [self.SAVE_DIR,self.LOG_DIR]:
      if not(os.path.exists(d)):
        os.makedirs(d)
        self.log_debug("creating directory "+d,1)

    if not(self.args.go_on):
      for f in glob.glob("*.py"):
        self.log_debug("copying file %s into SAVE directory " % f,1)
        os.system("cp ./%s  %s" % (f,self.SAVE_DIR))


      if not(hasattr(self,'FILES_TO_COPY')):
        self.FILES_TO_COPY = []
      for f in self.FILES_TO_COPY:
        os.system("cp %s %s/" % (f,self.SAVE_DIR))

    self.log_info('environment initialized successfully',4)


  #########################################################################
  # submitting one job   the definitive one
  #########################################################################

  def submit(self,job):

    cmd = [self.SCHED_SUB]

    if (job['depends_on']) :
      cmd = cmd + [self.SCHED_DEP+":%s"%job['depends_on'] ]

    if self.args.exclude_nodes:
      cmd = cmd + ["-x",self.args.exclude_nodes]

    if not(job['array']):
      job['array'] = '1-1'
      
    if self.MY_MACHINE=="sam":
      job['account'] = None

    jk = job.keys()
    for param in ['partition','reservation','time','job-name',
                  'error','output','ntasks','array','account']:
      if param in jk:
        if job[param]:
          cmd = cmd + ['--%s=%s' % (param,job[param])]
        
    if self.args.attempt:
      cmd = cmd + \
            ['%s_%s'                % (job['command'], self.args.attempt) ]
      job_content_template = "".join(open(job['command'],"r").readlines())
      job_content_updated  = job_content_template.replace('__ATTEMPT__',"%s" % self.args.attempt)
      job_script_updated  = open('%s_%s' % (job['command'], self.args.attempt), "w")
      job_script_updated.write(job_content_updated)
      job_script_updated.close()
    else:
      cmd = cmd + \
            ['%s'                % (job['command']) ]

    if not self.args.dry:
      self.log_debug("submitting : "+" ".join(cmd))
      output = subprocess.check_output(cmd)
      if self.args.pbs:
        #print output.split("\n")
        job_id = output.split("\n")[0].split(".")[0]
        #print job_id
      else:
        for l in output.split("\n"):
          self.log_debug(l,1)
          #print l.split(" ")
          if "Submitted batch job" in l:
            job_id = l.split(" ")[-1]
      self.log_debug("job submitted : %s depends on %s" % (job_id,job['depends_on']),1)
    else: 
      self.log_debug("should submit job %s" % job['name'])
      self.log_debug(" with cmd = %s " % " ".join(cmd))
      job_id = "%s" % job['name']

    job['job_id'] = job_id
    job['submit_cmd'] = cmd
        

    if 'step_before' in jk:
      step_before = job['step_before']
      if step_before:
        self.JOBS[self.JOBS[step_before]['job_id']]['comes_before'] =  job_id
        self.JOBS[self.JOBS[step_before]['job_id']]['make_depend'] =  job_id

    # self.JOBS[job_id] = self.JOBS[job['name']] = job
    # self.JOB_WORKDIR[job_id]  =   os.getcwd()
    # self.JOB_STATUS[job_id] = 'SPAWNED'

    
    for ja in RangeSet(job['array']):
      ka = "%s_%s" % (job_id,ja)
      self.log_debug('adding job %s to statistics' % ka)
      self.JOB_WORKDIR[ka]  =   os.getcwd()
      self.JOB_STATUS[ka] = 'SPAWNED'
      
    self.log_info('submitting job %s --> Job # %s ' % (job['name'],job_id))

    self.log_debug("Saving Job Ids...",1)
    self.save()

    return (job_id,cmd)





  #########################################################################
  # save_workspace
  #########################################################################

  def save(self):
      
    #
    lock_file = self.take_lock(self.LOCK_FILE)

    # could need to load workspace and merge it
    
    #print "saving variables to file "+workspace_file
    workspace_file = self.WORKSPACE_FILE
    f = open(workspace_file+".new", "wb" )
    pickle.dump(self.JOB_ID    ,f)
    pickle.dump(self.JOB_BY_NAME ,f)
    pickle.dump(self.JOB_STATUS,f)
    pickle.dump(self.JOB_WORKDIR,f)
    pickle.dump(self.JOBS,f)
    pickle.dump(self.timing_results,f)
    f.close()
    if os.path.exists(workspace_file):
      os.rename(workspace_file,workspace_file+".old")
    os.rename(workspace_file+".new",workspace_file)

    if self.args.save:
        trace_file = '%s/traces.%s' % (self.LOG_DIR,self.args.save)
        f = open(trace_file+".new", "wb" )
        pickle.dump(self.SYSTEM_OUTPUTS,f)
        f.close()
        if os.path.exists(trace_file):
            os.rename(trace_file,trace_file+".old")
        os.rename(trace_file+".new",trace_file)
        
    
    self.release_lock(lock_file)


  #########################################################################
  # load_workspace
  #########################################################################

  def load(self):

    try:
      if self.args.load:
          saved_workfile = '%s/%s.%s' % (self.LOG_DIR,os.path.basename(self.WORKSPACE_FILE),self.args.load)
          if os.path.exists(saved_workfile):
              cmd = 'cp %s %s ' % (saved_workfile,self.WORKSPACE_FILE)
              self.system(cmd,trace=False)
          else:
              self.error('[load]  problem encountered while loading saved workfile for  trace=/%s/' % self.args.load,
                         exit=True, exception=True)  #self.args.debug)

      #print "loading variables from file "+workspace_file
      if os.path.exists(self.WORKSPACE_FILE):
          f = open( self.WORKSPACE_FILE, "rb" )
          self.JOB_ID    = pickle.load(f)
          self.JOB_BY_NAME = pickle.load(f)
          self.JOB_STATUS = pickle.load(f)
          self.JOB_WORKDIR = pickle.load(f)
          self.JOBS = pickle.load(f)
          self.timing_results = pickle.load(f)
          f.close()
          if self.args.save:
            self.SYSTEM_OUTPUTS[self.args.save] = []
            if not(self.args.go_on) and not(self.already_saved):
                cmd = 'cp %s %s/%s.%s' % (self.WORKSPACE_FILE,self.LOG_DIR,os.path.basename(self.WORKSPACE_FILE),self.args.save)
                self.system(cmd,cmd,trace=False)
                self.already_saved = True

          if self.args.load:
            if not(self.already_loaded):  
              trace_file = '%s/traces.%s' % (self.LOG_DIR,self.args.load)
              if os.path.exists(trace_file):
                 f = open(trace_file,'rb')
                 self.SYSTEM_OUTPUTS = pickle.load(f)
                 self.already_loaded = True
                 f.close()
              else:
                self.error('[load]  problem encountered while loading tracing data for trace=/%s/' % self.args.load,
                          exit=True, exception=True)  #self.args.debug)

    except:
        self.error('[load]  problem encountered while loading current workspace\n---->  rerun with -d to have more information',
                          exit=True, exception=True)  #self.args.debug)

  #########################################################################
  # get status of all jobs ever launched
  #########################################################################
  def get_current_jobs_status(self):

    status_error = False
    self.JOB_STATS = {}
    for status in JOB_POSSIBLE_STATES:
        self.JOB_STATS[status] = []

    keys = self.JOB_STATUS.keys()
    print keys,'---keys---'
    for k in self.JOB_STATUS.keys():
        if not k in keys:
            keys = keys + [k]

    self.log_debug('%s jobs to scan' % len(keys))
    jobs_to_check = list()
    for job_id in keys:
      if job_id in self.JOB_STATUS.keys():
        status = self.JOB_STATUS[job_id]
      else:
          status = self.JOB_STATUS[job_id] = 'UNKNOWN'
          
      self.log_debug('status : /%s/ for job %s ) ' % (status,job_id))
      if status in ("CANCELLED","COMPLETED","FAILED","TIMEOUT"):
        self.log_debug ('--> not updating status')
        self.JOB_STATS[status].append(job_id)
      else:
        job_array_id = job_id.split('_')[0]
        if not(job_id in jobs_to_check):
            jobs_to_check.append(job_array_id)

    if len(jobs_to_check)==0:
      self.log_debug('%s' % self.JOB_STATS)
      return
    
    cmd = ["sacct","-n","-p","-j",",".join(jobs_to_check)+'.batch']
    cmd = " ".join(cmd)
    self.log_info('cmd so get new status : %s' % " ".join(cmd))
    try:
      output = self.system(cmd)
      sacct_worked = True
      self.log_debug('sacct results>>\n%s<<' % output)
      #",".join(map(str,NodeSet('81567_[5-6,45-59]')))
    except:
      if self.args.debug:
        self.error('WARNING [get_current_job_status] subprocess with ' + " ".join(cmd),exception=self.args.debug)
      else:
        status_error = True
      output=""
      sacct_worked = False
      self.log_info('[get_current_job_status] sacct could not be used')
    if sacct_worked:
      for l in output[:-1].split("\n"):
          task = 'Not yet'
          try:
            self.log_debug('l=%s'%l,2)
            sacct_fields = l.split("|")
            tasks=NodeSet(sacct_fields[0])
            status=sacct_fields[5].split(' ')[0]
            if status in JOB_POSSIBLE_STATES:
              for task in tasks:
                self.log_debug('status=%s task=%s' % (status,task),1)
                if status[-1]=='+':
                  status  = status[:-1]
                self.TASK_STATUS[task] = status
                self.JOB_STATS[status].append(task)
                task_id = task.split('_')[1].split('.')[0]
                if task_id in self.TASK_STATUS.keys():
                    if self.TASK_STATUS[task_id] in ['OK','NOK']:
                        continue
                self.TASK_STATUS[task_id] = status
            else:
                log_info('unknown status got for tasks %s' % ','.join(tasks))
          except:
            if self.args.debug:
              self.dump_exception('[get_current_job_status] parse job_status with task=%s' % task +"\n job status : "+l)
            else:
              status_error = True
            pass


    # checking status from Stub files
    

    self.log_debug('%s' % self.JOB_STATS)
    
    self.save()

    if status_error:
      self.log_info('!WARNING! Error encountered scanning job status, run with --debug to know more')
      
  #########################################################################
  # get current job status
  #########################################################################
  def job_status(self,id_or_file):

    self.log_debug("[job_status] job_status on %s " % id_or_file)
    dirname="xxx"
    if os.path.isfile(id_or_file):
      dirname = os.path.abspath(os.path.dirname(id_or_file))
    if os.path.isdir(id_or_file):
      dirname = os.path.abspath(id_or_file)

    for key in [id_or_file,dirname]:
      if key in self.JOB_STATUS.keys():
        status = self.JOB_STATUS[key]
        self.log_debug("[job_status] job_status on %s --> %s" % (id_or_file,status))
        return status
    self.log_debug("[job_status] job_status on %s --> UNKNOWN" % id_or_file)
    return "NOINFO"




      
  #########################################################################
  # welcome message
  #########################################################################

  def welcome_message(self,print_header=True,print_cmd=True):
      """ welcome message"""

      if print_header:
        print
        print("          ########################################")
        print("          #                                      #")
        print("          #   Welcome to %11s version %3s!#" % (self.APPLICATION_NAME, self.APPLICATION_VERSION))
        print("          #    (using ENGINE Framework %3s)     #" % self.ENGINE_VERSION)
        print("          #                                      #")
        print("          ########################################")
        print("       ")

      if print_cmd:
        print   ("\trunning on %s (%s) " %(MY_MACHINE_FULL_NAME,MY_MACHINE))
        print   ("\t\tpython " + " ".join(sys.argv))
        print
        
      self.MY_MACHINE = MY_MACHINE

  #########################################################################
  # dumping error report ...
  #########################################################################
      
   
  def error(self,message = None, error_detail = "", exit=True,exception=False):
      """ helping message"""
      if message:
        message = str(message)+"\n"
        if len(error_detail):
          print "[ERROR] Error %s : " % error_detail
        for m in message.split("\n"):
          try:
            #print "[ERROR]  %s : " % m
            if len(self.LOG_PREFIX):
                m = "%s:%s" % (self.LOG_PREFIX,m)
            self.log.error(m)
          except:
            print "[ERROR Pb processing] %s" % m
        print "[ERROR] type python %s -h for the list of available options..." % \
          self.APPLICATION_NAME
      else:
        try:
          self.usage(exit=False)
        except:
          self.dump_exception()
          print "\n  usage: \n \t python %s \
               \n\t\t[ --help ] \
               \n\t\t[ --info  ] [ --info-level=[0|1|2] ]  \
               \n\t\t[ --debug ] [ --debug-level=[0|1|2] ]  \
             \n"  % self.APPLICATION_NAME

      if not(exception==False):
        self.dump_exception()
          
      if exit:
        sys.exit(1)


  #########################################################################
  # checking methods
  #########################################################################
      

  def check_python_version(self):
    try:
      subprocess.check_output(["ls"])
    except:
      self.error("Please use a more recent version of Python > 2.7.4")



  def check_engine_version(self,version):
    current = int(("%s" % self.ENGINE_VERSION).split('.')[1])
    asked   = int(("%s" % version).split('.')[1])
    if (asked>current):
        self.error("Current Engine version is %s while requiring %s, please fix it!" % (current,asked))


  #########################################################################
  # locking methods
  #########################################################################

  def lock(self, file, flags):
      try:
        fcntl.flock(file.fileno(), flags)
      except IOError, exc_value:
        #  IOError: [Errno 11] Resource temporarily unavailable
        if exc_value[0] == 11:
          raise LockException(LockException.LOCK_FAILED, exc_value[1])
        else:
          raise
    
  def unlock(self,file):
    fcntl.flock(file.fileno(), fcntl.LOCK_UN)


  def take_lock(self,filename,write_flag="a+"):
    install_lock = open(filename,write_flag)
    self.lock(install_lock, LOCK_EX)
    return install_lock

  def release_lock(self,install_lock):
    install_lock.close()
    
  #########################################################################
  # os.system wrapped to enable Trace if needed
  #########################################################################

  def system(self,cmd,comment="No comment",fake=False,verbosity=1,force=False,trace=True):

    self.log_info('in system cmd=/%s/ ' % cmd,2)
    self.log_debug("\tcurrently executing /%s/ :\n\t\t%s" % (comment,cmd),verbosity)

    if trace and self.args.load:
        self.log_info('reading from trace file / output = /%s/' % len(self.SYSTEM_OUTPUTS[self.args.load]),2)
        output = self.SYSTEM_OUTPUTS[self.args.load].pop(0)
        self.log_info('reading from trace file / output = /%s/' % output,3)
        return output

    output='FAKE EXECUTION'
    if force or (not(fake) and not(self.args.fake)):
      #os.system(cmd)
      #subprocess.call(cmd,shell=True,stderr=subprocess.STDOUT)
      proc = subprocess.Popen(cmd, shell=True, bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
      output = ""
      while (True):
          # Read line from stdout, break if EOF reached, append line to output
          line = proc.stdout.readline()
          #line = line.decode()
          if (line == ""): break
          output += line
      if len(output):
        self.log_debug("output=+"+output,verbosity+1)
      if trace and self.args.save:
          self.SYSTEM_OUTPUTS[self.args.save].append(output)
          self.log_info('writing to trace file / output = /%s/' % output,3)

    return output


  #########################################################################
  # send mail back to the user
  #########################################################################

  def init_mail(self):

    if not(self.args.mail):
      return False
    
    # sendmail only works from a node on shaheen 2 via an ssh connection to cdl via gateway...

    if not(self.args.mail):
      self.args.mail = getpass.getuser()

  def set_mail_subject_prefix(self,prefix):
      self.MAIL_SUBJECT_PREFIX = prefix


  def send_mail(self,msg='',level=0,subject='',to=None):

    if not(self.args.mail):
      return False
  
    if level>self.args.mail_verbosity:
        self.log_info('%s not sent because level=%s > %s' % (msg,level,self.args.mail_verbosity),4)
        return


    if not(self.MAIL_COMMAND):
      self.error("No mail command available on this machine")

    # sendmail only works from a node on shaheen 2 via an ssh connection to cdl via gateway...

    mail_file = os.path.abspath("./mail.txt_%s_%s" % (os.getpid(),int(time.time())))
 
    f = open(mail_file,'w')
    s = self.MAIL_CURRENT_MESSAGE + "\n" + msg
    for m in s.split("\n"):
        f.write(m+"\n")
    f.close()
    self.MAIL_CURRENT_MESSAGE = ""
    
    if not(to):
        to = self.args.mail
        
    cmd = (self.MAIL_COMMAND+"2> /dev/null") % (self.MAIL_SUBJECT_PREFIX+subject, to, mail_file)
    self.log_debug("self.args.mail cmd : "+cmd,2)
    os.system(cmd)

    time.sleep(3)
    
    if not(self.args.nocleaning):
        pass
        #os.unlink(mail_file)

  def append_mail(self,msg,level=0):
      
    if not(self.args.mail) or level>self.args.mail_verbosity:
      return False

    self.MAIL_CURRENT_MESSAGE = self.MAIL_CURRENT_MESSAGE + "\n" + msg


  def flush_mail(self,msg=''):

    if len(self.MAIL_CURRENT_MESSAGE):
        self.send_mail(msg)
        
  #########################################################################
  # create template (matrix and job)
  #########################################################################

  def create_template(self,path='.'):

    for dirpath, dirs, files in os.walk("%s/templates" %  path): 
       for filename in files:
         filename_from = os.path.join(dirpath,filename)
         filename_to   = filename_from.replace("%s/templates/" %  path,"./")
         if os.path.exists(filename_to):
           self.log_info("\t file %s already exists... skipping it!" % filename_to)
         else:
           dirname = os.path.dirname(filename_to)
           self.log_debug('working on file %s in dir %s' % (filename_to,dirname))

           if not(os.path.exists(dirname)):
             self.system("mkdir -p %s" % dirname,comment="creating dir %s" % dirname)
           self.system("cp %s %s" % (filename_from,filename_to),comment="creating file %s" % filename_to)
           self.log_info('creating file %s' % (filename_to))
    sys.exit(0)
      

  #########################################################################
  # tail log file
  #########################################################################

  def tail_log_file(self,filename=None,keep_probing=False,nb_lines_tailed=20,message=True,no_timestamp=False,stop_tailing=False):

    try:
      if filename==None:
          filename = self.log_file_name
        
      if not os.path.isfile(filename):
          self.error_report("no logfile %s yet..." % filename,exit=True)

      if message:
          print 
          print "="*80
          print('Currently Tailing ... \n %s' % filename)
          print('\t\tHit CTRL-C to exit...' * 2)
          print('='*80)
          print('...')
          
      fic = open(filename, "r")
      lines = fic.readlines()
      for line in lines[-nb_lines_tailed:]:
          if no_timestamp:
              line = re.sub('^.*\[','[',line[:-1])
          print line
      #if str.find(lines[-1], "goodbye") >=0:
      #    good_bye_reached = True
      while True:
          where = fic.tell()
          line = fic.readline()
          if not line:
              time.sleep(10)
              fic.seek(where)
          else:
              if no_timestamp:
                  line = re.sub('^.*\[','[',line)
              print line, # already has newline
              sys.stdout.flush()
              if type(stop_tailing)==type("chaine"):
                  if line.find(stop_tailing)>-1:
                      keep_probing = False
                      return True
              if type(stop_tailing)==type(["string1","string2"]):
                  for pattern in stop_tailing:
                      if line.find(pattern)>-1:
                          keep_probing = False
                          return True
          if not(keep_probing):
              break
    except KeyboardInterrupt:
        print "\n bye bye come back anytime!   To resume this monitoring type :"
        print   ("\t\tpython %s --log" % sys.argv[0])
        print 
        keep_probing = False
        return False
    
  #########################################################################
  # look for a pattern in a set of files
  #########################################################################

  def check_for_pattern(self,pattern,file_mask=None,files=None,return_all=False,col=None):

      error = 0
      
      if not(file_mask) and not(files):
          self.error("in check_for_pattern('%s') on must add at least file_mask or files parameter" %\
                     pattern)
      
      filter_success = 0
      pattern_found = {}
      if file_mask:
          files = glob.glob(file_mask)
      else:
          files_to_scan = files
          files = []
          for f in files_to_scan:
              if os.path.isfile(f):
                  files = files + [f]
                  
      self.log_debug('files : [%s] ' % ",".join(files),2)

      if len(files)==0:
          error = ERROR_FILE_DOES_NOT_EXISTS
      
      for f in files:
          (p, return_code) = self.greps(pattern,f,col,return_all=True)
          if p:
              pattern_found[f] = [p,len(p)]
              filter_success = filter_success+len(p)
          else:
              pattern_found[f] = [None,0]

      if error<0:
          filter_success = error
          
      if return_all:
           return (filter_success,files,pattern_found,error)
      else:
           return filter_success


  #########################################################################
  # look for a pattern in a file
  #########################################################################

  def greps(self,motif, file_name, col = None, nb_lines = -1, return_all=False, exclude_patterns=[]):
      """
       Fonction qui retourne toute ligne contenant un motif dans un fichier
       et renvoie le contenu d'une colonne de cette ligne
       
       fic             --> Nom du fichier
       motif         --> Motif a chercher
       col             --> La liste des Numeros de colonne a extraire
       endroit     --> Un objet de type situation
       nb_lines  --> nb_lines max a renvoyer
       Renvoie la colonne col et un indicateur indiquant si le motif a y trouver

       """
      #
      self.log_debug("greps called for searching %s in %s " % (motif, file_name),2)

      
      trouve = -1
      rep = []
      motif0 = str.replace(motif,    '\\MOT',    '[^\s]*')
      motif0 = str.replace(motif0,    '\\SPC',    '\s*')

      # col can be    Nothing,         one figure,     or    a list of figures
      type_matching = "Columns"
      if col == None:
          type_matching = "Grep"
      if type(col) == type(2):
          col = [col] 
      if type(col) == type("chaine"):
          type_matching = "Regexp"
          masque0 = str.replace(col,    '\\MOT',    '[^\s]*')
          masque0 = str.replace(masque0,    '\\SPC',    '\s*')

      file_name_full_path = MY_MACHINE_FULL_NAME+":"+os.getcwd()

      if os.path.isfile(file_name)==False:
          if col == None:
              self.log_debug("file '%s' read \n\t from path '%s' \
                                                  \n\t searched for motif '%s' does not exist!!!!"\
                             %(file_name, file_name_full_path, motif))
          else:
              self.log_debug("file '%s' read \n\t from path '%s' \
                                                  \n\t searched for motif '%s' to get column # [%s] \
                                                  \n\t  file does not exist!!!"\
                           %(file_name, file_name_full_path, motif, ",".join(map(str,col))))
          if return_all:
              return (None,ERROR_FILE_DOES_NOT_EXISTS)
          else:
              return None
      else:
          if len(exclude_patterns):
            if type(exclude_patterns)==type('string'):
                exclude_patterns = [exclude_patterns]
             
          
          file_scanned = open(file_name, "r")
          for ligne in file_scanned.readlines():
              if False:
                  print ligne,motif0
              if (len(ligne) >= 1):
                  for pattern in exclude_patterns:
                      if ligne.find(pattern)>-1:
                          continue
                  if (re.search(motif0, ligne)):
                      trouve = 1
                      if type_matching == "Columns":
                          file_scanned.close()
                          colonnes = str.split(ligne)
                          col_out = []
                          for i in col:
                              col_out.append(colonnes[i])
                          if len(col_out) == 1:
                              rep.append(col_out[0])
                              continue
                          else:
                              rep.append(col_out)
                              continue
                          break
                      elif type_matching == "Grep":
                          file_scanned.close()
                          rep.append(ligne[:-1])
                          continue
                      elif type_matching == "Regexp":
                          matched = re.search(masque0, ligne, re.VERBOSE)
                          if matched:
                              file_scanned.close()
                              rep.append(matched.groups())
                              continue
          file_scanned.close()

          if (trouve == -1):
              if return_all:
                  return (None,ERROR_PATTERN_NOT_FOUND)
              else:
                  return None


      self.log_debug("rep=%s " % pprint.pformat(rep),4)
      self.log_debug("%s matching results " % len(rep),3)
      
      if return_all:
          return (rep,0)
      else:
          return rep


  #########################################################################
  # look for a pattern in a set of files
  #########################################################################

  def ask(self,msg,default='n',answers = '(y/n)', yes='y', no='n'):

    if self.args.yes:
        self.log_info('%s --> %s (automated user answer)' % (msg,yes))
        return

    answers = answers.replace(default,'[%s]' % default)
    input_var = raw_input(msg + answers + " ")

    self.log_debug('received answer=>%s< default=>%s< no=>%s<' % (input_var,default,no),3)

    if (str(input_var) == str(yes)) or (len(input_var)==0 and default==yes):
        return
    else:
        self.log_info("ABORTING: No clear confirmation... giving up!")
        sys.exit(1)


    
  #########################################################################
  # apply_tags
  #########################################################################

  def apply_tags(self, file=False, input=False):

    lines = open(file,'r').readlines()
    input = "ZZ%ZZ".join(lines)
    output = input
    for t in self.tag_value.keys():
      input = input.replace("__%s__" % t,"%s" % self.tag_value[t])
    output = ""
    for l in input.split("ZZ%ZZ"):
      fields = l.split('___IF___')
      if len(fields)==2:
        try:
          cond = fields[1]
          if not(eval(cond)):
            continue
          l = fields[0]
          while ((len(l)>0) and (l[-1]=='#' or l[-1]==' ')):
            l = l[:-1]
        
          l = l +'\n'
        except:
          self.error('ERROR: could not evaluate %s for template file %s' % (cond,file),
                     exit=True)
      fields = l.split('___INCLUDE___')
      if len(fields)==2:
        included_file = fields[1][:-1]
        if not(included_file[0]=='/'):
          included_file = '%s/%s' % (os.path.dirname(file),included_file)
        output = output + self.apply_tags(included_file)
        continue
      output = output + l
    return output
      

      
if __name__ == "__main__":
  D = application("my_app")
