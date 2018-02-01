#!/usr/bin/python

import argparse
from ClusterShell.NodeSet import RangeSet, NodeSet
import datetime
from env import MAIL_COMMAND,SUBMIT_COMMAND,SCHED_TYPE,DEFAULT_QUEUE,MY_MACHINE,MY_MACHINE_FULL_NAME,clean_line
import fcntl
import getpass
import glob
import logging
import logging.handlers
import os
import pickle
import pprint
import re
import subprocess
import sys
import time
import traceback

JOB_POSSIBLE_STATES = ('PENDING','RUNNING','SUSPENDED','COMPLETED',\
                       'CANCELLED','CANCELLED+','FAILED','TIMEOUT',\
                       'NODE_FAIL','PREEMPTED','BOOT_FAIL','COMPLETING',\
                       'CONFIGURING','RESIZING','SPECIAL_EXIT')

JOB_ACTIVE_STATES = ('PENDING','RUNNING','SUSPENDED','COMPLETING',\
                       'CONFIGURING','RESIZING')

JOB_RUNNING_STATES = ('RUNNING','COMPLETING',\
                      'CONFIGURING','RESIZING')

JOB_DONE_STATES = ("COMPLETED","FAILED", 'SUCCESS','FAILURE','MIXED')

JOB_ABORTED_STATES = ('ABORTED','CANCELLED','CANCELLED+','FAILED',\
                      'TIMEOUT',"BOOT_FAIL","FAILED","TIMEOUT")


LOCK_EX = fcntl.LOCK_EX
LOCK_SH = fcntl.LOCK_SH
LOCK_NB = fcntl.LOCK_NB

ENGINE_VERSION = '0.23'

ERROR_FILE_DOES_NOT_EXISTS = -33
ERROR_PATTERN_NOT_FOUND = -34

LOG = False

class colors(object):
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class LockException(Exception):
    # Error codes:
    LOCK_FAILED = 1


class my_list(object):
  
  def __init__(self, *args, **kwargs):
      # print_debug('Args:',args)
      # LOG.log_debug('kwargs:',kwargs)
      if not('name' in kwargs.keys()):
        self.name_of_dict = 'UNKNOWN'
      else:
        self.name_of_dict = kwargs['name']
        del kwargs['name']
      LOG.log_debug('%s_L_init %s %s' % (self.name_of_dict, \
                                         pprint.pformat(args), pprint.pformat(kwargs)),\
                                        3, trace='DIST' )
      self.list_content = []
      #self.update(*args, **kwargs)
  def __len__(self):
    LOG.log_debug('%s_L_len %s' % (self.name_of_dict, len(self.list_content)),\
                                        3, trace='DIST')
    return len(self.list_content)
  def __add__(self, other):
      self.list_content = self.list_content + other
      LOG.log_debug('%s_A_add %s' % (self.name_of_dict, pprint.pformat(self.list_content)),\
                                        3, trace='DIST')
      return self
  def __getitem__(self, index):
      LOG.log_debug('%s_L_item[%s]=%s' % (self.name_of_dict,index, self.list_content[index]),\
                                        3, trace='DIST')
      result = self.list_content[index]
      return result
  def __repr__(self):
      s = pprint.pformat(self.list_content)
      LOG.log_debug('%s_L_print[%s]' % (self.name_of_dict,s),\
                                        3, trace='DIST')
      return s
  def __getslice__(self, i, j):
      LOG.log_debug('%s_L_slice[%s]' % (self.name_of_dict,slice(i, j)),\
                                        3, trace='DIST')
      return self.list_content.__getitem__(slice(i, j))
  def update(self, *args, **kwargs):
      LOG.log_debug('%s_D_update %s %s' % (self.name_of_dict, \
                                           pprint.pformat(args), \
                                           pprint.pformat(kwargs)),\
                                        3, trace='DIST')
      for k, v in dict(*args, **kwargs).iteritems():
          self[k] = v

class my_dict(dict):

  def __init__(self, *args, **kwargs):
      # LOG.log_debug('Args:',args)
      # LOG.log_debug('kwargs:',kwargs)
      if not('name' in kwargs.keys()):
        self.name_of_dict = 'UNKNOWN'
      else:
        self.name_of_dict = kwargs['name']
        del kwargs['name']
      LOG.log_debug('%s_D_init %s %s' % (self.name_of_dict, \
                                        pprint.pformat(args),pprint.pformat(kwargs)),\
                                        3, trace='DIST')
      self.update(*args, **kwargs)

  def __getitem__(self, key):
      val = dict.__getitem__(self, key)
      LOG.log_debug('%s_D_GET[%s]' % (self.name_of_dict, key),\
                                        3, trace='DIST')
      return val

  def __setitem__(self, key, val):
      LOG.log_debug('%s_D_SET[%s]=%s' % (self.name_of_dict, key, val),\
                                        3, trace='DIST')
      dict.__setitem__(self, key, val)

  def __repr__(self):
      dictrepr = dict.__repr__(self)
      return '%s(%s)' % (type(self).__name__, dictrepr)

  def update(self, *args, **kwargs):
      LOG.log_debug('%s_D_update %s %s' % (self.name_of_dict, \
                                          pprint.pformat(args), \
                                          pprint.pformat(kwargs)),\
                                        3, trace='DIST')
      for k, v in dict(*args, **kwargs).iteritems():
          self[k] = v


    
class engine(object):

  def __init__(self,app_name="app",app_version="?",app_dir_log=False,
               engine_version_required=ENGINE_VERSION,extra_args=False):
    #########################################################################
    # set initial global variables
    #########################################################################

    self.NewLock = False
    self.CanLock = True

    self.SCRIPT_NAME = os.path.basename(__file__)

    self.APPLICATION_NAME = app_name
    self.APPLICATION_VERSION = app_version
    self.ENGINE_VERSION = ENGINE_VERSION

    self.LOG_PREFIX = ""
    self.LOG_DIR = app_dir_log

    self.WORKSPACE_FILE = "./.%s/LOGS/%s.pickle" % (app_name,'workspace')
    self.CONSOLE_SAVE_FILE = "./.%s/LOGS/%s.pickle" % (app_name,'console')
    self.JOB_DIR = os.path.abspath("./.%s/RESULTS" % app_name)
    self.SAVE_DIR = os.path.abspath("./.%s/SAVE" % app_name)
    self.LOG_DIR = os.path.abspath("./.%s/LOGS" % app_name)
    self.ARCHIVE_DIR = os.path.abspath("./.%s/ARCHIVE" % app_name)

    # saving scheduling option in the object

    self.MAIL_COMMAND = MAIL_COMMAND
    self.MAIL_SUBJECT_PREFIX = ""
    self.MAIL_CURRENT_MESSAGE = ""
    self.SUBMIT_COMMAND = SUBMIT_COMMAND
    self.SCHED_TYPE = SCHED_TYPE
    self.DEFAULT_QUEUE = DEFAULT_QUEUE

    self.last_noCR = False

    # checking
    self.check_python_version()
    self.check_engine_version(engine_version_required)

    # parse command line to eventually overload some default values
    self.parser = argparse.ArgumentParser(conflict_handler='resolve')
    self.initialize_parser()

    if extra_args:
      args = self.user_filtered_args()
    else:
      args = sys.argv[1:]
      
    self.args = self.parser.parse_args(args)

    # initialize logs
    self.initialize_log_files()

    self.log_debug('pure Decimate args:%s' % pprint.pformat(self.args), 2, trace='PARSE')

    # welcome message
    self.welcome_message()


    # check the sanity of saved hard-coded path and modify them if needed
    if not(self.args.rollback or self.args.rollback_list):
        self.check_if_directory_was_moved()

    # automated lock
    self.lock_taken = {'fake_file':-1}
    self.lock_id = {'fake_file':-1}

    # initialize scheduler
    self.initialize_scheduler()

    self.clean()

    self.already_saved = False
    self.already_loaded = False
    self.forward_mail_already_taken = False

    self.env_init()

  #########################################################################
  # clean_workspace
  #########################################################################

  def clean(self):

    # initialize job tracking arrays
    self.STEPS = my_dict(name='STEPS')  # {}
    self.TASKS = my_dict(name='TASKS')  # {}
    self.JOBS = my_dict(name='JOBS')  # {}
    self.JOB_ID = my_dict(name='JOB_ID')  # {}
    self.JOB_BY_NAME = my_dict(name='JOB_BY_NAME')  # {}
    self.JOB_WORKDIR = my_dict(name='JOB_WORKDIR')  # {}
    self.JOB_STATUS = my_dict(name='JOB_STATUS')  # {}
    self.TASK_STATUS = my_dict(name='')  # {}
    self.timing_results = my_dict(name='timing_results')  # {}
    self.SYSTEM_OUTPUTS = my_dict(name='')  # {}
    self.jobs_list = my_list(name="jobs_list")  # []
    self.jobs_submitted = [] #  my_list(name='jobs_submitted')  # []
    self.jobs_to_submit = my_list(name='jobs_to_submit')  # []
    self.last_step_submitted = -1
    self.steps_submitted_attempts = my_dict(name='steps_submitted_attempts')  # {}
    self.steps_submitted = my_list(name='steps_submitted')  # []
    self.steps_submitted_history = my_dict(name='steps_submitted_history')  # {}
    self.waiting_job_final_id = my_dict(name='')  # {}

    self.user_clean()

    self.LOCK_FILE = "%s/lock" % self.LOG_DIR
    self.LOCK_SAVING_FILE = "%s/lock_currently_saving" % self.LOG_DIR
    self.CONSOLE_LOCK_FILE = "%s/console.lock" % self.LOG_DIR
    self.KILL_LOCK_FILE = "%s/kill.lock" % self.LOG_DIR
    self.STATS_ID_FILE = "%s/stats_ids.pickle" % self.LOG_DIR

    self.tags = {}

  def start(self):

    self.log_debug('[Engine:start] entering')
    engine.run(self)

  #########################################################################
  # check for tne option on the command line
  #########################################################################

  def initialize_parser(self):

    global LOG
    
    #self.log_debug('[Engine:initialize_parser] entering',4,trace='CALL')

    self.parser.add_argument("-i","--info", action="count", default=0, help=argparse.SUPPRESS)
    self.parser.add_argument("-d","--debug", action="count", default=0, help=argparse.SUPPRESS)
    self.parser.add_argument("-f","--filter", type=str, default='no_filter', \
                             help='filtering traces')
    self.parser.add_argument("-m","--mail-verbosity", action="count", default=0,
                             help='sends a mail tracking the progression of the workflow')

    # self.parser.add_argument("--kill", action="store_true", help="Killing all processes")
    # self.parser.add_argument("--scratch", action="store_true",\
    #                 help="Restarting the whole process from scratch cleaning everything")
    # self.parser.add_argument("--restart", action="store_true", \
    #                           help="Restarting the process from where it stopped")

    self.parser.add_argument("--kill", action="store_true", help=argparse.SUPPRESS)
    self.parser.add_argument("--scratch", action="store_true", help=argparse.SUPPRESS)
    self.parser.add_argument("--restart", action="store_true", help=argparse.SUPPRESS)
    self.parser.add_argument("--nocleaning", action="store_true", default=False, \
                             help=argparse.SUPPRESS)
    self.parser.add_argument("--create-template", action="store_true", \
                             help='create template')

    self.parser.add_argument("--go-on", action="store_true", help=argparse.SUPPRESS)
    self.parser.add_argument("--log-dir", type=str, help=argparse.SUPPRESS)
    self.parser.add_argument("--mail", type=str, help=argparse.SUPPRESS)
    self.parser.add_argument("-a","--account", type=str, help='forcing the submitting account')
    self.parser.add_argument("--fake", action="store_true", help=argparse.SUPPRESS)
    self.parser.add_argument("--save", type=str, help=argparse.SUPPRESS)
    self.parser.add_argument("--load", type=str, help=argparse.SUPPRESS)
    self.parser.add_argument("--dry", action="store_true", help=argparse.SUPPRESS)
    self.parser.add_argument("--pbs", action="store_true", help=argparse.SUPPRESS)
    self.parser.add_argument("-x","--exclude-nodes", type=str, help=argparse.SUPPRESS)
    self.parser.add_argument("-r","--reservation", type=str, help='SLURM reservation')
    self.parser.add_argument("-p","--partition", type=str, help='SLURM partition')
    self.parser.add_argument("-np", "--no-pending", action="store_true",\
                             help='do not keep pending the log', default=False)

    self.parser.add_argument("--info-offset", type=int, help=argparse.SUPPRESS, default=0)
    self.parser.add_argument("--debug-offset", type=int, help=argparse.SUPPRESS, default=0)

    self.parser.add_argument("--banner", action="store_true", help=argparse.SUPPRESS, default=True)
    self.parser.add_argument("-nfu","--no-fix-unconsistent", action="store_true",\
                             help='do not fix unconsistent steps', default=False)

    LOG = self

  #########################################################################
  # main router
  #########################################################################

  def run(self):

    self.log_debug('[Engine:run] entering',4,trace='CALL')

    if self.args.info > 0:
        self.log.setLevel(logging.INFO)
    if self.args.debug > 0:
        self.log.setLevel(logging.DEBUG)

    # if self.args.scratch:
    #     self.log_info("restart from scratch")
    #     self.log_info("killing previous jobs...")
    #     self.kill_workflow()
    #     self.log_info("cleaning environment...")
    #     self.clean()

    if self.args.mail_verbosity > 0 and not(self.args.mail):
        self.args.mail = getpass.getuser()

    if self.args.kill:
        self.kill_workflow()
        sys.exit(0)

    if self.args.create_template:
        self.create_template()

  #########################################################################
  # set self.log file
  #########################################################################

  def initialize_log_files(self):

    #self.log_debug('[Engine:initialize_log_files] entering',4,trace='CALL')

    if not(self.LOG_DIR):
      self.LOG_DIR = "/scratch/%s/logs/.%s" % (getpass.getuser(),self.APPLICATION_NAME)

    if self.args.log_dir:
        self.LOG_DIR = self.args.log_dir

    self.LOG_DIR = os.path.expanduser("%s" % self.LOG_DIR)

    for d in [self.LOG_DIR]:
      if not(os.path.exists(d)):
        os.makedirs(d)

    self.log = logging.getLogger('%s.log' % self.APPLICATION_NAME)
    self.log.propagate = None
    self.log.setLevel(logging.ERROR)
    self.log.setLevel(logging.INFO)
    console_formatter = logging.Formatter(fmt='[%(levelname)-5.5s] %(message)s')
    formatter = logging.Formatter("%(asctime)s [%(levelname)-5.5s]  %(message)s")

    self.log_file_name = "%s/" % self.LOG_DIR + '%s.log' % self.APPLICATION_NAME
    if not(os.path.exists(self.log_file_name)):
      open(self.log_file_name, "a").close()
    owner_of_log = os.stat(self.log_file_name).st_uid
    if owner_of_log == os.getuid():
        handler = logging.handlers.RotatingFileHandler(self.log_file_name, \
                                                       maxBytes=20000000, backupCount=5)
        handler.setFormatter(formatter)
        self.log.addHandler(handler)

    consoleHandler = logging.StreamHandler(stream=sys.stdout)
    consoleHandler.setFormatter(console_formatter)
    self.log.addHandler(consoleHandler)

  def check_filter(self,trace):
    trace_to_search = ",%s," % trace
    for f in self.args.filter.split(','):
      if trace_to_search.find(",%s," % f) > -1:
        return True
    return False

  def log_debug(self,msg,level=0,dump_exception=0,trace='xxxxxxxxx',stack=False,timestamp=False):
    #     print trace,self.args.filter
    if timestamp:
        now = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
        msg = "%s @ (%s)" % (msg,now)
    forced = self.check_filter(trace)
    msg = colors.WARNING + msg + colors.END
    if forced:
      msg = '[%s] >>>>> %s' % (trace,msg)
    if level <= self.args.debug - self.args.debug_offset or forced:
      if len(self.LOG_PREFIX):
          msg = "%s:%s" % (self.LOG_PREFIX,msg)
      if forced:
        self.log._log(logging.DEBUG, msg,None,None)
      else:
        self.log.debug(msg)
      if (dump_exception or stack):
        self.dump_exception()

  def log_info(self,msg,level=0,dump_exception=0,trace='xxxxxx',timestamp=False):
    forced = self.check_filter(trace)
    if timestamp:
        now = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
        msg = "%s @ (%s)" % (msg,now)
    if forced:
      msg = '[%s] >>>>> %s' % (trace,msg)
    if (level <= self.args.info - self.args.info_offset) or forced:
      if self.last_noCR:
          print
          self.last_noCR = False
      if len(self.LOG_PREFIX):
          msg = "%s:%s" % (self.LOG_PREFIX,msg)
      if forced:
        self.log._log(logging.INFO, msg,None,None)
      else:
          self.log.info(msg)
      if (dump_exception):
        self.dump_exception()
      # self.log.debug("%d:%d:%s"%(self.args.debug,level,msg))

  def log_console(self,msg,level=0,dump_exception=0,trace='xxxxxx',timestamp=False, noCR=False):
    if timestamp:
        now = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
        msg = "%s:%s" % (now,msg)
    filter = ",%s," % self.args.filter
    forced = filter.find(",%s," % trace) > -1
    if forced:
      msg = '[%s] >>>>> %s' % (trace,msg)
    if level <= self.args.info or forced:
      if len(self.LOG_PREFIX):
          msg = "%s" % (msg)
      if noCR:
          print'\r[MSG  ] %s ' % (msg),
          sys.stdout.flush()
          self.last_noCR = True
      else:
          if self.last_noCR:
              print()
              self.last_noCR = False
          print '[MSG  ] %s ' % (msg)

  def dump_exception(self,where='Not known'):
    exceptionType, exceptionValue, exceptionTraceback = sys.exc_info()
    if (exceptionTraceback or exceptionType or exceptionValue):
      print('\n#######!!!!!!!!!!######## Exception occured at ',where,'############')
      traceback.print_exception(exceptionType,exceptionValue, exceptionTraceback,\
                                limit=None,file=sys.stdout)
    print('\n #######!!!!!!!!!!######## printing calling stack at ',where,'############')
    print(''.join(traceback.format_stack()[:]))
    print('#' * 80)

  def set_log_prefix(self,prefix):
      self.LOG_PREFIX = prefix

  #########################################################################
  # check the sanity of saved hard-coded path and modify them if needed
  #########################################################################
  def check_if_directory_was_moved(self):

    already_processed_job_files = glob.glob("./.%s/SAVE/*+" % self.APPLICATION_NAME)
    if len(already_processed_job_files) == 0:
        self.log_debug('No job was ever processed or submitted yet, everything should be fine',\
                       4,trace='RELOCATE')
    old_save_dir_found = False
    for f in already_processed_job_files:
        p = self.greps('PYTHONPATH=',f,[1])
        if p:
            old_save_dir_found = p[0].split(':')[1]
            self.log_debug('old_save_dir_found=%s' % old_save_dir_found)
        if old_save_dir_found:
            break

    if not(old_save_dir_found):
        self.log_debug('No old self.SAVE_DIR trace found... everything should be fine',\
                       4,trace='RELOCATE')
        return

    if old_save_dir_found == self.SAVE_DIR:
        self.log_debug('No old self.SAVE_DIR same as now... everything should be fine',\
                       4,trace='RELOCATE')
        return
    else:
        old_root = old_save_dir_found.replace('/.%s/SAVE' % self.APPLICATION_NAME,'')
        current_root = self.SAVE_DIR.replace('/.%s/SAVE' % self.APPLICATION_NAME,'')
        self.log_info('old ROOT directory(%s) is different from current(%s)' % \
                      (old_root, current_root))
        self.ask("do you want to relocate the run to the current directory (%s)" % \
                 current_root, default='n')

        self.archive('relocate','-1','before')

        for d in ['SAVE','LOGS']:
            for l in glob.glob('.%s/%s/*' % (self.APPLICATION_NAME,d)):
                f_size = os.path.getsize(l)
                if f_size:  # and l.find('.pickle')==-1:
                    flines = open(l,'r').readlines()
                    # fic_content = ''
                    # for line in flines:
                    #     p = re.compile("\s+$")
                    #     line = p.sub('', line[:-1])
                    #     fic_content = fic_content + line[:-1] + "/RELOCATE/\n"
                    fic_content = '/RELOCATE/'.join(flines)
                    for x in [',','/',' ',':',';',"'",'"']:
                        fic_content = fic_content.replace('%s%s' % (old_root, x), '%s%s' % \
                                                          (current_root,x))
                    f = open('%s' % l,'w')
                    f.write(fic_content.replace('/RELOCATE/',''))
                    f.close()
                    self.log_console('fixing file %s...           ' % l, noCR=True)

    self.log_info('rerun please')
    sys.exit(9)

  #########################################################################
  # initialize_scheduler
  #########################################################################
  def initialize_scheduler(self):
    global SCHED_TYPE

    if SCHED_TYPE == "pbs" or self.args.pbs:
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

    for d in [self.SAVE_DIR,self.LOG_DIR,self.ARCHIVE_DIR]:
      if not(os.path.exists(d)):
        os.makedirs(d)
        self.log_debug("creating directory " + d,1)

    if not(self.args.go_on or self.args.log or self.args.status or \
           self.args.status_long or self.args.status_all):
      for f in glob.glob("*.py"):
        self.log_debug("copying file %s into SAVE directory " % f,1)
        self.pre_copy(f,self.SAVE_DIR)

      if not(hasattr(self,'FILES_TO_COPY')):
        self.FILES_TO_COPY = []
      for f in self.FILES_TO_COPY:
        if not(os.path.exists(f)):
          self.log_debug('File %s does not exist... skipping its copy to safe dir' % f)
        else:
          # os.system("cp %s %s/" % (f,self.SAVE_DIR))
          self.pre_copy(f,self.SAVE_DIR)

    self.log_info('environment initialized successfully',4)

  #########################################################################
  # copy and preprocess file
  #########################################################################

  def pre_copy(self,f,dest):
    self.log_info('copying %s -> %s' % (f,dest),3,trace='COPY')
    if f[-3:] == '.py' and not(self.args.debug) and self.args.filter == 'no_filter':
      fic_content = ""
      in_log_debug = False
      for l in open("%s" % f,"r").readlines():
        l = l.replace("self.log_debug(","pass  #D# self.log_debug(")
        if in_log_debug:
            l = "#D#" + l
        if l.find("self.log_debug(") > -1 or in_log_debug:
            if len(l) > 1:
                if l[-2] == "\\":
                    in_log_debug = True
                else:
                    in_log_debug = False
        else:
            in_log_debug = False
        fic_content = fic_content + l
      try:
          fic_copy = open("%s/%s" % (dest,os.path.basename(f)),"w")
          fic_copy.write(fic_content)
          fic_copy.close()
      except Exception:
          self.log_info('has no right to copy %s content ' % f)
    else:
      os.system("cp %s  %s" % (f,dest))

  #########################################################################
  # archive_workspace
  #########################################################################

  def archive(self,step,attempt,status):

    date = '{:%Y:%m:%d::%H:%M:%S}'.format(datetime.datetime.now())

    archive_name = '%s/%s-%s-%s.%s.tgz' % (self.ARCHIVE_DIR,date,step,attempt,status)
    cmd = 'cd %s/../;   tar fcz %s LOGS SAVE' % (self.LOG_DIR,archive_name)
    output = os.system(cmd)
    self.log_debug('Archiving cmd: %s\nArchiving res: %s   ' % (cmd,output),3,trace='ARCHIVE')
    self.log_debug('step %s-%s @ status %s archived' % (step,attempt,status), \
                   0, trace='ARCHIVE')

  #########################################################################
  # list available rollback states
  #########################################################################

  def rollback_list(self,step='*', from_console=False):

    pattern = '%s/*-%s-*.tgz' % (self.ARCHIVE_DIR,step)
    self.log_debug('scanning %s' % pattern,3,trace='ROLLBACK')
    rollback_points = glob.glob(pattern)
    possibles = {}
    msgs = []
    attempt_list = []

    rollback_points.sort()
    nb = 1
    for p in rollback_points:
      f = p.replace("%s/" % self.ARCHIVE_DIR,'').split('-')
      f = f[:-1] + f[-1].split('.')[:-1]
      self.log_debug('[%s]' % ",".join(f),3,trace='ROLLBACK')
      step,attempt,status,date = f[1],f[2],f[3],f[0].split('::')[1]
      msg = "%3d -> %s-%s %s @ %s" % (nb,step,attempt,status,date)
      msgs = msgs + [msg]
      if from_console:
        self.log_console(msg)
      step_attempt = '%s-%s' % (step,attempt)
      for k in [nb,step,step_attempt, status]:
        possibles[k] = (msg,p,step_attempt)
      attempt_list = attempt_list + [step_attempt]
      nb = nb + 1

    return msgs,possibles

  #########################################################################
  # list available rollback states
  #########################################################################

  def rollback_workflow(self,key='*'):

    msgs,possibles = self.rollback_list(from_console=False)

    if not(key in possibles.keys()):
      self.log_console('Possibles choice are:\n%s' % '\n'.join(msgs))
      self.error('rollback point %s not available...' % key)

    self.archive('s','a','saved')

    msg,archive_file,step_attempt = possibles[key]
    self.ask(('Do you really want to rollback to step %s' +\
              ' and clear status and results for steps followng it? ') % \
             step_attempt, default='n')

    self.log_info('Currently rolling back internal status to get back to step %s ' % step_attempt)
    cmd = 'cd %s/..; tar xfz %s' % (self.ARCHIVE_DIR,archive_file)
    self.log_debug('rollback cmd: %s' % cmd,trace='ROLLBACK,ROLLBACK_CMD')
    os.system(cmd)
    self.log_info('done')

    self.load()
    self.compute_critical_path()

    steps = self.steps_critical_path_with_attempt
    self.log_debug('in rollback_wokflow steps [%s] ' % ",".join(steps),1,trace='ROLLBACK')
    steps_to_forget = ('__xxx__%s__xxx__' % '__xxx__'.join(steps)).\
                      split(step_attempt)[1].split('__xxx__')[1:-1]

    self.forget_steps(steps_to_forget)

    self.save()

    self.check_if_directory_was_moved()

    self.log_info('rerun please')
    sys.exit(9)

  #########################################################################
  # clean internal arrays of unwanted steps
  #########################################################################

  def forget_steps(self,steps_to_forget):

    self.ask('Do you really want to clear status and results for steps [%s] ' % \
             ",".join(steps_to_forget),\
             default='n')

    jobs_to_forget = []
    for step in steps_to_forget:
      step_without_attempt = '-'.join(step.split('-')[:-1])
      self.log_info('clearing information and result about step %s' % (step_without_attempt))
      for pattern in ['%s/%s?*' % (self.SAVE_DIR,step_without_attempt),
                      '%s/Complete-%s*' % (self.SAVE_DIR,step_without_attempt),
                      '%s/FAILURE-%s*' % (self.SAVE_DIR,step_without_attempt),
                      '%s/SUCESS-%s*' % (self.SAVE_DIR,step_without_attempt),
                      '%s/Done-%s*' % (self.SAVE_DIR,step_without_attempt)]:
          self.log_debug('removing %s' % pattern, 1,trace='ROLLBACK,RESTART,FORGET')
          cmd = '\\rm -rf %s' % pattern
          os.system(cmd)

      if step in self.steps_submitted_attempts.keys():
        del self.steps_submitted_attempts[step]
      if step in self.STEPS.keys():
        for j in self.STEPS[step]['jobs']:
          job = self.JOBS[j]
          for type in ['error','output']:
            pattern = job[type].replace('%J','*').replace('%j','*').replace('%a','*')
            pattern = pattern + '.task_???-attempt_*'
            self.log_debug('removing %s' % pattern, 1,trace='ROLLBACK,RESTART,FORGET')
            cmd = '\\rm -rf %s' % pattern
            os.system(cmd)
      if step in self.STEPS.keys():
        for j in self.STEPS[step]['jobs']:
          jobs_to_forget = jobs_to_forget + [j]
          del self.JOBS[j]
        del self.TASKS[step]
        del self.STEPS[step]
    steps = []
    for step in self.steps_submitted:
      if not(step in steps_to_forget):
        steps = steps + [step]
    self.steps_submitted = steps
    jobs = []
    for job in self.jobs_list:
      if not(job in jobs_to_forget):
        jobs = jobs + [job]
    self.jobs_list = jobs

  #########################################################################
  # save_workspace
  #########################################################################

  def save(self,take_lock=True):

    if not(self.CanLock):
        return

    self.log_debug('entering save()',4,trace='SAVE')
    #
    lock_file = self.take_lock(self.LOCK_FILE)
    self.log_debug('save: Taking the lock',4,trace='SAVE,LOCK')

    # could need to load workspace and merge it

    # print("saving variables to file "+workspace_file)
    workspace_file = self.WORKSPACE_FILE
    self.pickle_file = open(workspace_file + ".new", "wb")
    pickle.dump(self.JOB_ID, self.pickle_file)
    pickle.dump(self.JOB_BY_NAME, self.pickle_file)
    pickle.dump(self.JOB_STATUS, self.pickle_file)
    pickle.dump(self.JOB_WORKDIR, self.pickle_file)
    pickle.dump(self.JOBS, self.pickle_file)
    pickle.dump(self.STEPS, self.pickle_file)
    pickle.dump(self.TASKS, self.pickle_file)
    pickle.dump(self.jobs_list, self.pickle_file)
    pickle.dump(self.jobs_submitted, self.pickle_file)
    pickle.dump(self.jobs_to_submit, self.pickle_file)
    pickle.dump(self.last_step_submitted, self.pickle_file)
    pickle.dump(self.timing_results, self.pickle_file)
    pickle.dump(self.waiting_job_final_id, self.pickle_file)
    pickle.dump(self.steps_submitted, self.pickle_file)
    pickle.dump(self.steps_submitted_history, self.pickle_file)
    pickle.dump(self.args.yalla, self.pickle_file)
    self.user_save()
    self.pickle_file.close()

    lock_saving_file = self.take_lock(self.LOCK_SAVING_FILE)
    self.log_debug('save: Taking the saving lock',4,trace='SAVE,LOCK')
    if os.path.exists(workspace_file):
      os.rename(workspace_file,workspace_file + ".old")
    try:
      # os.system('touch %s/%s.workspace_saved.step-%s.task-%s ' % \
      #           (self.LOG_DIR,int(time.time()), self.args.step, self.args.taskid))
      os.rename(workspace_file + ".new",workspace_file)
    except Exception:
      os.system('ls -l .decimatest/LOGS/')

      self.error(workspace_file + ".new    not here anymore",
                 exit=True,exception=True)

    if self.args.save:
        trace_file = '%s/traces.%s' % (self.LOG_DIR, self.args.save)
        f = open(trace_file + ".new", "wb")
        pickle.dump(self.SYSTEM_OUTPUTS,f)
        f.close()
        if os.path.exists(trace_file):
            os.rename(trace_file,trace_file + ".old")
        os.rename(trace_file + ".new",trace_file)

    self.log_debug('save: releasing the locks',4,trace='SAVE,LOCK')
    self.release_lock(lock_saving_file)
    self.release_lock(lock_file)
    self.log_debug('leaving save()',4,trace='SAVE')

  #########################################################################
  # load_workspace
  #########################################################################

  def load(self,take_lock=True):

    self.log_debug('entering load()',4,trace='LOAD')

    if self.args.quick_launch:
        self.log_debug('exiting load() immediately: quick launch',4,trace='LOAD')

    #
    self.log_debug('load: Taking the saving lock',4,trace='LOAD,LOCK')
    lock_saving_file = self.take_lock(self.LOCK_SAVING_FILE)
    self.log_debug('load: saving lock taken',4,trace='LOAD,LOCK')
    try:
      if self.args.load:
          saved_workfile = '%s/%s.%s' % (self.LOG_DIR,\
                                         os.path.basename(self.WORKSPACE_FILE), self.args.load)
          if os.path.exists(saved_workfile):
              cmd = 'cp %s %s ' % (saved_workfile, self.WORKSPACE_FILE)
              self.system(cmd,trace=False)
          else:
              self.error('[load] problem while loading saved workfile for trace=/%s/' % \
                         self.args.load,
                         exit=True, exception=True)  # self.args.debug)

      # print("loading variables from file "+workspace_file)
      if os.path.exists(self.WORKSPACE_FILE):
          self.pickle_file = open(self.WORKSPACE_FILE, "rb")
          self.JOB_ID = pickle.load(self.pickle_file)
          self.JOB_BY_NAME = pickle.load(self.pickle_file)
          self.JOB_STATUS = pickle.load(self.pickle_file)
          self.JOB_WORKDIR = pickle.load(self.pickle_file)
          self.JOBS = pickle.load(self.pickle_file)
          self.STEPS = pickle.load(self.pickle_file)
          self.TASKS = pickle.load(self.pickle_file)
          self.jobs_list = pickle.load(self.pickle_file)
          self.jobs_submitted = pickle.load(self.pickle_file)
          self.jobs_to_submit = pickle.load(self.pickle_file)
          self.last_step_submitted = pickle.load(self.pickle_file)
          self.timing_results = pickle.load(self.pickle_file)
          self.waiting_job_final_id = pickle.load(self.pickle_file)
          self.steps_submitted = pickle.load(self.pickle_file)
          self.steps_submitted_history = pickle.load(self.pickle_file)
          self.args.yalla = pickle.load(self.pickle_file)
          self.log_debug('in load yalla=%s' % self.args.yalla,trace='LOAD,YALLA')
          self.user_load()
          self.pickle_file.close()
          if self.args.save:
            self.SYSTEM_OUTPUTS[self.args.save] = []
            if not(self.args.go_on) and not(self.already_saved):
                cmd = 'cp %s %s/%s.%s' % (self.WORKSPACE_FILE, self.LOG_DIR,\
                                          os.path.basename(self.WORKSPACE_FILE), self.args.save)
                self.system(cmd,cmd,trace=False)
                self.already_saved = True

          if self.args.load:
            if not(self.already_loaded):
              trace_file = '%s/traces.%s' % (self.LOG_DIR, self.args.load)
              if os.path.exists(trace_file):
                 f = open(trace_file,'rb')
                 self.SYSTEM_OUTPUTS = pickle.load(f)
                 self.already_loaded = True
                 f.close()
              else:
                self.error('[load] problem while loading tracing data for trace=/%s/' \
                           % self.args.load,
                           exit=True, exception=True)  # self.args.debug)

    except Exception:
        self.error('[load]  problem encountered while loading current workspace' +\
                   '\n---->  rerun with -d to have more information',
                   exit=True, exception=True)  # self.args.debug)

    self.release_lock(lock_saving_file)
    self.log_debug('load():releasing saving_lock',4,trace='SAVE,LOCK')

    self.log_debug('leaving load()',4,trace='SAVE,LOAD')

  #########################################################################
  # load_workspace user defined function
  #########################################################################

  def load_value(self):
      return pickle.load(self.pickle_file)

  #########################################################################
  # save_workspace user defined function
  #########################################################################

  def save_value(self,value):
      pickle.dump(value, self.pickle_file)

  #########################################################################
  # clean_workspace user defined function
  #########################################################################

  def user_clean(self):
      return

  #########################################################################
  # load_workspace user defined function
  #########################################################################

  def user_load(self):
      return

  #########################################################################
  # save_workspace user defined function
  #########################################################################

  def user_save(self):
      return

  #########################################################################
  # update task status
  #########################################################################

  def update_task_status(self,what,step,job_id,task_id,attempt,checking_from_console):
    status = self.TASKS[step][task_id]['status']
    self.log_debug('at start of updating task status for status=%s,step=%s,job_id=%s,task_id=%s,'\
                   % (status,step,job_id,task_id),4,trace='CHECK')
    additional_user_checking = False
    if not(self.TASKS[step][task_id]['counted']):
      if status in JOB_DONE_STATES:
          self.TASKS[step][task_id]['status'] = 'DONE'
          # self.JOBS[job_id]['completion'] = self.JOBS[job_id]['completion'] + [task_id]
          # self.JOBS[job_id]['completion_percent'] += 100./self.JOBS[job_id]['items']
          # self.STEPS[step]['completion'] = self.STEPS[step]['completion'] + [task_id]
          # self.STEPS[step]['completion_percent'] += 100./self.STEPS[step]['items']

          additional_user_checking = True
      elif status in JOB_ABORTED_STATES:
          self.TASKS[step][task_id]['status'] = 'ABORTED'
          self.STEPS[step]['status'] = 'ABORTED'
          self.JOBS[job_id]['status'] = 'ABORTED'
          self.TASKS[step][task_id]['counted'] = True
          additional_user_checking = True
      elif status in JOB_RUNNING_STATES:
          self.TASKS[step][task_id]['status'] = 'RUNNING'
          self.STEPS[step]['status'] = 'RUNNING'
          self.JOBS[job_id]['status'] = 'RUNNING'
      elif status == 'PENDING':
          self.TASKS[step][task_id]['status'] = 'PENDING'
          self.STEPS[step]['status'] = 'PENDING'
          self.JOBS[job_id]['status'] = 'PENDING'
      else:
          self.TASKS[step][task_id]['status'] = 'UNKNOWN'
          additional_user_checking = True

      if additional_user_checking:
          task_to_check = [task_id]
          # checking actual result with a user checking procedure
          (is_user_checked,tasks_not_completed) = \
                  self.check_current_state(what, attempt, task_to_check,
                                           checking_from_console=checking_from_console)

          # has this task already been checked globally?
          # if yes removing from global accounting first
          if task_id in self.STEPS[step]['global_completion']:
              for stuff in ['global_completion','global_success','global_failure',
                            'completion','success','failure']:
                if not(task_id in self.STEPS[step][stuff]):
                  continue
                self.STEPS[step]['%s_percent' % stuff] -= 100. / self.STEPS[step]['global_items']
                i = self.STEPS[step][stuff]
                previous_stuff = ",%s," % (",".join(map(lambda x:str(x),i)))
                self.log_debug('for %s before cleaning previous_stuff=/%s/' % \
                               (stuff,previous_stuff), 4, \
                               trace='CLEAN')
                previous_stuff = previous_stuff.replace(",%s," % task_id,',')
                if previous_stuff in ["",",",",,"]:
                  self.STEPS[step][stuff] = []
                else:
                  self.STEPS[step][stuff] = map(lambda x:int(x),previous_stuff[1:-1].split(","))
                self.log_debug('for %s after cleaning self.STEPS[step][%s]=/%s/' % \
                               (stuff,stuff, self.STEPS[step][stuff]), 4, \
                               trace='CLEAN')

          # poor workaround
          if not(job_id in self.JOBS.keys()):
            job = {}
            job['status'] = 'UNKNOWN'
            job['completion'] = []
            job['success'] = []
            job['failure'] = []
            job['completion_percent'] = 0
            job['success_percent'] = 0
            job['failure_percent'] = 0
            job['items'] = self.STEPS[step]['items']
            self.JOBS[job_id] = job

          if is_user_checked is True:
              self.JOBS[job_id]['success'] = self.JOBS[job_id]['success'] + [task_id]
              self.STEPS[step]['success'] = self.STEPS[step]['success'] + [task_id]
              self.STEPS[step]['global_success'] = self.STEPS[step]['global_success'] + [task_id]
              self.JOBS[job_id]['success_percent'] += 100. / self.JOBS[job_id]['items']
              self.STEPS[step]['success_percent'] += 100. / self.STEPS[step]['items']
              self.STEPS[step]['global_success_percent'] += 100. / self.STEPS[step]['global_items']
              self.TASKS[step][task_id]['status'] = 'SUCCESS'
              self.JOBS[job_id]['completion'] = self.JOBS[job_id]['completion'] + [task_id]
              self.JOBS[job_id]['completion_percent'] += 100. / self.JOBS[job_id]['items']
              self.STEPS[step]['completion'] = self.STEPS[step]['completion'] + [task_id]
              self.STEPS[step]['completion_percent'] += 100. / self.STEPS[step]['items']
              self.STEPS[step]['global_completion'] = self.STEPS[step]['global_completion'] \
                                                      + [task_id]
              self.STEPS[step]['global_completion_percent'] \
                += 100. / self.STEPS[step]['global_items']

          elif is_user_checked is False:
              self.JOBS[job_id]['failure'] = self.JOBS[job_id]['failure'] + [task_id]
              self.STEPS[step]['failure'] = self.STEPS[step]['failure'] + [task_id]
              self.STEPS[step]['global_failure'] = self.STEPS[step]['global_failure'] + [task_id]
              self.JOBS[job_id]['failure_percent'] += 100. / self.JOBS[job_id]['items']
              self.STEPS[step]['failure_percent'] += 100. / self.STEPS[step]['items']
              self.STEPS[step]['global_failure_percent'] += 100. / self.STEPS[step]['global_items']
              self.TASKS[step][task_id]['status'] = 'FAILURE'
              self.JOBS[job_id]['completion'] = self.JOBS[job_id]['completion'] + [task_id]
              self.JOBS[job_id]['completion_percent'] += 100. / self.JOBS[job_id]['items']
              self.STEPS[step]['completion'] = self.STEPS[step]['completion'] + [task_id]
              self.STEPS[step]['global_completion'] = self.STEPS[step]['global_completion'] + \
                                                      [task_id]
              self.STEPS[step]['completion_percent'] += 100. / self.STEPS[step]['items']
              self.STEPS[step]['global_completion_percent'] \
                += 100. / self.STEPS[step]['global_items']

          if (100. - self.JOBS[job_id]['completion_percent']) < 1.e-6:
              self.JOBS[job_id]['status'] = 'DONE'
              if (100. - self.JOBS[job_id]['success_percent']) < 1.e-6:
                self.JOBS[job_id]['status'] = 'SUCCESS'
              elif (100. - self.JOBS[job_id]['failure_percent']) < 1.e-6:
                self.JOBS[job_id]['status'] = 'FAILURE'
              else:
                self.JOBS[job_id]['status'] = 'MIXED'
          else:
              self.JOBS[job_id]['status'] = 'RUNNING'

          if (100. - self.STEPS[step]['completion_percent']) < 1.e-6:
               self.STEPS[step]['status'] = 'DONE'
               if (100. - self.STEPS[step]['success_percent']) < 1.e-6:
                 self.STEPS[step]['status'] = 'SUCCESS'
               elif (100. - self.STEPS[step]['failure_percent']) < 1.e-6:
                 self.STEPS[step]['status'] = 'FAILURE'
               else:
                 self.STEPS[step]['status'] = 'MIXED'
          else:
               self.STEPS[step]['status'] = 'RUNNING'
          self.TASKS[step][task_id]['counted'] = True

    self.log_debug(("at the end updating task status self.STEPS[step]['status']=%s" + \
                    "self.JOBS[job_id]['status']=%s self.TASKS[step][task_id]['status']=%s") %\
                   (self.STEPS[step]['status'], self.JOBS[job_id]['status'],\
                    self.TASKS[step][task_id]['status']),4,trace='CHECK')

  #########################################################################
  # get status of all jobs ever launched
  #########################################################################
  def get_current_jobs_status(self,in_queue_only=False,take_lock=True,
                              from_heal_workflow=True,from_resubmit=False):

    # lock_file = self.take_lock(self.FEED_LOCK_FILE)
    lock_file = self.take_lock(self.LOCK_FILE)
    self.log_debug('get_current_jobs_status: Taking the lock',4,trace='SAVE')

    self.load()

    status_error = False

    jobs_to_check = {}
    steps_to_check = {}
#     self.log_debug("get_status:beg -> STEPS=\n%s " % pprint.pformat(self.STEPS),3)
#     self.log_debug("get_status:beg -> JOBS=\n%s " % pprint.pformat(self.JOBS),3)
#     self.log_debug("get_status:beg -> TASKS=\n%s " % pprint.pformat(self.TASKS),3)

    for step in self.STEPS.keys():
      self.log_debug("step=>%s<, self.STEPS[step]['status']=>%s<, self.STEPS[step]['completion_percent']=>%s<" % \
                     (step, self.STEPS[step]['status'], self.STEPS[step]['completion_percent']),\
                     1,trace='STATUS_DETAIL')
      self.log_debug("self.STEPS[step]['jobs']=%s" % pprint.pformat(self.STEPS[step]['jobs']),\
                     4,trace='STATUS_DETAIL')
      status = self.STEPS[step]['status']
      self.log_info('get_current_job_status: status of step %s : %s' % (step,status),1)
      if not(status in ['ABORTED','WAITING']):
        #  if self.STEPS[step]['completion_percent']<100.:
          steps_to_check[step] = True
          for job_id in self.STEPS[step]['jobs']:
            if ("%s" % job_id).find('-') == -1:
              job = self.JOBS[job_id]
              self.log_debug(("step=>%s<,job_id=>%s<," + \
                              "job['completion_percent']=>%s<,job['status']=>%s<") %\
                             (step,job_id,job['completion_percent'],job['status']),\
                             1,trace='STATUS_DETAIL')
              if job['completion_percent'] < 100. and not(job['status'] in JOB_DONE_STATES \
                                                          or job['status'] == 'WAITING'):
                  jobs_to_check[job_id] = True

    self.log_debug('%d jobs to check:  %s' % \
                   (len(jobs_to_check),",".join(map(str,jobs_to_check.keys()))),\
                   4,trace='STATUS_DETAIL')

    if len(jobs_to_check) == 0 and in_queue_only:
         #
        self.release_lock(lock_file)
        return []

    if len(jobs_to_check) > 0:
      cmd = 'squeue -r -o "%i %T" -j ' + ",".join(map(lambda x: str(x),jobs_to_check))
      self.log_debug('cmd to get new status via squeue : %s' % "".join(cmd),\
                     4,trace='STATUS_DETAIL')
      jobs_gone = []
      output = self.system(cmd,force=1)
      self.log_debug('squeue results>>\n%s<<' % output,2,trace='STATUS_DETAIL')
      jobs_in_queue = output[:-1].split("\n")
      if in_queue_only:
          self.release_lock(lock_file)
          if len(jobs_in_queue) > 1:
            return jobs_in_queue[1:]
          else:
            return []

      for j in jobs_to_check:
          if output.find("%s" % j) == -1:
              jobs_gone = jobs_gone + [j]

      self.log_info('jobs_gone=%s' % ",".join(map(lambda x: str(x),jobs_gone)),1)

      job_to_check_filtered = jobs_to_check.keys()
      cmd = ";".join(map(lambda x: 'sacct -n -p -j %s' % x, job_to_check_filtered))
      # cmd = ["sacct","-n","-p","-j",",".join(map(lambda x : str(x),jobs_to_check))]
      # cmd = " ".join(cmd)
      self.log_debug('cmd to get new status via sacct : %s' % "".join(cmd),\
                     1,trace='STATUS_DETAIL,STATUS')
      try:
        sacct_attempt = 0
        error_in_sacct = True
        sacct_waiting_time = 2
        while error_in_sacct and sacct_attempt < 3:
            output = self.system(cmd,force=1)
            sacct_worked = True
            self.log_debug('sacct results>>\n%s<<' % output,2,trace='STATUS_DETAIL')
            error_in_sacct = False
            for j in jobs_to_check:
                if output.find("%s" % j) == -1:
                    error_in_sacct = True
                    self.log_debug('sacct does not scan job>>%s<<' % j,2,trace='STATUS')
            sacct_attempt = sacct_attempt + 1
            if error_in_sacct:
                self.log_debug('pb to get sacct,  \n \t\tretrying in %d sec..' % \
                               (sacct_waiting_time),1,trace='STATUS_DETAIL,STATUS')
                time.sleep(sacct_waiting_time)
                sacct_waiting_time = sacct_waiting_time * 2
        if error_in_sacct:
            self.error('too many sacct failed',exit=True)

        # ",".join(map(str,NodeSet('81567_[5-6,45-59]')))
      except Exception:
        if self.args.debug:
          self.error('WARNING [get_current_job_status] subprocess with ' + \
                     " ".join(cmd),exception=self.args.debug)
        else:
          status_error = True
        output = ""
        sacct_worked = False
        self.log_info('[get_current_job_status] sacct could not be used')

      if sacct_worked:
        tasks_checked = {}
        # first pass to get the status of the last command in the job
        for l in output[:-1].split("\n"):
            task = 'Not yet'
            try:
              self.log_debug('l=%s' % l, 2)
              sacct_fields = l.split("|")
              status = sacct_fields[5].split(' ')[0]
              if sacct_fields[0].find('.') == -1:
                task_field = sacct_fields[0].split('.')[0]
                if not(task_field in tasks_checked.keys()):
                  tasks_checked[task_field] = status
                elif not(tasks_checked[task_field] == 'RUNNING'):
                  tasks_checked[task_field] = status
            except Exception:
              self.error(('[get_current_job_status] parse job_status with task=%s ' + \
                          '\n job_id = %s \n job status : l=%s') % \
                         (task,job_id,l),exception=True,exit=False)
              status_error = True
              pass

        self.log_debug('tasks_checked=\n%s' % pprint.pformat(tasks_checked),3,trace='KILL')

        # then processing on final status observed for each job
        for task_field in tasks_checked.keys():
            status = tasks_checked[task_field]
            try:
              if task_field.find('_') == -1:
                job_id = int(task_field)
                if status in JOB_ABORTED_STATES:
                  step = self.JOBS[job_id]['step']
                  self.STEPS[step]['status'] = 'ABORTED'
                  self.JOBS[job_id]['status'] = 'ABORTED'
                  continue
              if self.args.yalla:
                task_field = "%s_[%s]" % (task_field, self.JOBS[job_id]['array'])
              self.log_debug('task_field=\n%s' % task_field,3,trace='KILL,STATUS_DETAIL')
              tasks = NodeSet(task_field)
              if status in JOB_POSSIBLE_STATES:
                self.log_debug('tasks=%s step=%s' % (tasks,step),2,trace='STATUS_DETAIL')
                for task in tasks:
                  self.log_debug('status=%s task=%s' % (status,task),2,trace='STATUS_DETAIL')
                  if status[-1] == '+':
                    status = status[:-1]
                  if task.find('.') > -1:
                    continue
                  # p = re.compile("\..+$")
                  # task = p.sub('', task)
                  
                  job_id = int(task.split('_')[0])
                  if not(job_id in self.JOBS.keys()):
                      self.error('job_id=%s received from sacct and not registered\n' % job_id +\
                                 ('[get_current_job_status] parse job_status with task=%s' + \
                                  '\n job_id=%s\n job status: l=%s\noutput=>%s< \n cmd=>%s<') % \
                                 (task,job_id,l,output,cmd),exception=True,exit=False)
                      continue

                  step = self.JOBS[job_id]['step']
                  task_id = int(task.split('_')[1].split('.')[0])
                  items = step.split('-')
                  what = "-".join(items[:-1])
                  attempt = items[-1]

                  self.log_debug('step=%s job=%s task=%s status=%s   task=>>%s<< ' % \
                                 (step,job_id,task_id,status,task),2,trace='STATUS_DETAIL')
                  self.log_debug('is_task_counted?=>>%s<<' % \
                                 (self.TASKS[step][task_id]['counted']),2,trace='STATUS_DETAIL')
                  self.TASKS[step][task_id]['status'] = status
                  self.update_task_status(what,step,job_id,task_id,attempt,
                                          checking_from_console=True)
                  self.flush_mail()
              else:
                  self.log_info('unknown status got for tasks %s' % ','.join(tasks),\
                                1,trace='STATUS_DETAIL')
            except Exception:
              self.error(('[get_current_job_status] parse job_status with task=%s ' +\
                          '\n job_id = %s \n job status : l=%s') % (task,job_id,l),\
                         exception=True,exit=False)
              status_error = True
              pass

      # checking status from Stub files
      self.save(take_lock=False)

    # checking coherency of result
    unconsistent_steps = []
    for step_name in self.STEPS.keys():
      step = self.STEPS[step_name]
#      if self.STEPS[step_name]['status'] in ['SUCCESS', 'WAITING','PENDING','FAILURE','ABORTED']:
      if self.STEPS[step_name]['status'] in ['WAITING','PENDING','RUNNING']:
        continue
      if self.STEPS[step_name]['status'] == 'DONE':
        self.log_debug('step %s found DONE : %s' % \
                       (step_name, self.print_job(step,print_only=step.keys())),\
                       4,trace='UNCONSISTENT')
        if self.args.ends < 0:
            unconsistent_steps = unconsistent_steps + [step_name]
        elif int(step_name.split('-')[0]) <= int(self.args.ends):
            unconsistent_steps = unconsistent_steps + [step_name]
        continue
      if not(len(step['completion']) == int(step['items'])) or \
         abs(step['completion_percent'] - 100.) > 1.e-6:
          self.log_debug('step %s found unconsistent: %s' % \
                         (step_name, self.print_job(step,print_only=step.keys())),\
                         4,trace='UNCONSISTENT')
          if self.args.ends < 0:
            unconsistent_steps = unconsistent_steps + [step_name]
          elif int(step_name.split('-')[0]) <= int(self.args.ends):
              unconsistent_steps = unconsistent_steps + [step_name]

    if len(unconsistent_steps) and not(self.args.no_fix_unconsistent):
      self.log_info('%d unconsistent steps were found: [%s]' % (len(unconsistent_steps),\
                                                                ",".join(unconsistent_steps)))
      for step_name in unconsistent_steps:
        self.log_debug('processing step %s' % step_name,4,trace='UNCONSISTENT')
        self.log_debug('self.TASK[%s]=%s' % (step_name,pprint.pformat(self.TASKS[step_name])),\
                       4,trace='UNCONSISTENT')
        fields = step_name.split('-')
        (what,attempt) = "-".join(fields[:-1]),fields[-1]
        tasks = self.STEPS[step_name]['array']
        self.log_debug('checking actual state potentially user tested  (what=%s, attempt=%s, tasks=%s)' % \
                       (what, attempt, RangeSet(tasks)),4,trace='UNCONSISTENT')
        actual_status = self.check_current_state(what, attempt, tasks, checking_from_console=True,\
                                                 from_heal_workflow=from_heal_workflow)
        self.log_debug('------------------------------------------------> status=%s for  (what=%s, attempt=%s, tasks=%s)' % \
                       (actual_status,what, attempt, RangeSet(tasks)),4,trace='UNCONSISTENT')
        # recomputing status of step and job
        self.STEPS[step_name]['status'] = 'SUBMITTED'
        self.STEPS[step_name]['completion'] = []
        self.STEPS[step_name]['success'] = []
        self.STEPS[step_name]['completion_percent'] = 0
        self.STEPS[step_name]['success_percent'] = 0
        self.STEPS[step_name]['failure'] = []
        self.STEPS[step_name]['failure_percent'] = 0
        for job_id in self.STEPS[step_name]['jobs']:
            job = self.JOBS[job_id]
            job['status'] = 'SUBMITTED'
            job['completion'] = []
            job['success'] = []
            job['failure'] = []
            job['completion_percent'] = 0
            job['success_percent'] = 0
            job['failure_percent'] = 0
            self.JOBS[job_id] = job
        for task_id in RangeSet(self.STEPS[step_name]['initial_array']):
            job_id = self.TASKS[step_name][task_id]['job']
            if not(job_id == 'UNKNOWN'):
              self.TASKS[step_name][task_id]['status'] = 'WAITING'
              self.TASKS[step_name][task_id]['counted'] = False
              self.update_task_status(what,step_name,job_id,task_id,attempt,\
                                      checking_from_console=True)
        step = self.STEPS[step_name]
        self.log_debug('step %s fixed to (status=%s, completion=%s, completion_percent=%s success=%s success_percent=%s failure=%s failure_percent=%s items=%s' % \
                         (step_name, self.STEPS[step_name]['status'],\
                          step['completion'],step['completion_percent'],\
                          step['success'],step['success_percent'],\
                          step['failure'],step['failure_percent'],\
                          step['items']),\
                         4,trace='UNCONSISTENT')
    # 2. check if any job is running at all, susceptible to activate the waiting one
    #
    nb_jobs_active = 0
    for job_id in jobs_to_check:
        job = self.JOBS[job_id]
        if not((job['status'] in JOB_DONE_STATES)) and not((job['status'] in JOB_ABORTED_STATES)):
            self.log_debug('active found job  %s  step %s  status %s ' % \
                           (job_id,job['step'],job['status']),\
                           1,trace='STATUS_DETAIL,ACTIVE')
            nb_jobs_active = nb_jobs_active + 1

    if nb_jobs_active == 0 and not(self.args.spawned) \
       and not(self.args.decimate) and not(from_resubmit):
      self.log_info('no active job in the queue, changing all WAITING in ABORTED???')
    if False:
      for step in self.STEPS.keys():
        self.log_debug('step %s  status= %s' % (step, self.STEPS[step]['status']),\
                       2,trace='STATUS_DETAIL')
        if self.STEPS[step]['status'] in ['SUBMITTED','WAITING','RUNNING']:
          self.STEPS[step]['status'] = 'ABORTED'
          for job_id in self.STEPS[step]['jobs']:
              self.log_debug('step %s/job=%s  status= %s' % \
                             (step,job_id, self.STEPS[step]['status']),\
                             2,trace='STATUS_DETAIL')
              if self.JOBS[job_id]['status'] in ['SUBMITTED','WAITING','RUNNING']:
                  self.JOBS[job_id]['status'] = 'ABORTED'

      for job_id in self.JOBS.keys():
          status = self.JOBS[job_id]['status']
          self.log_debug('job %s  status= %s' % (job_id,status),2,trace='STATUS_DETAIL')
          if status in ['SUBMITTED','WAITING','RUNNING']:
              self.log_debug('job %s  ----> status= ABORTED (was %s)' % (job_id,status),\
                             2,trace='STATUS_DETAIL')
              self.JOBS[job_id]['status'] = 'ABORTED'

    # 3. update step
    #
    if len(steps_to_check):
      self.log_info('fixing steps (%s) ', ','.join(steps_to_check.keys()))
      for step in steps_to_check.keys():
        if self.STEPS[step]['status'] in ['WAITING','RUNNING','SUBMITTED']:
          # step_status_found = False
          jobs_status = {'RUNNING':0, 'ABORTED':0, 'DONE':0}
          for job_id in self.STEPS[step]['jobs']:
            status = self.JOBS[job_id]['status']
            if not(status in jobs_status.keys()):
              jobs_status[status] = 0
            jobs_status[status] = jobs_status[status] + 1
          # if at least one job is running, the step is running
          if jobs_status['RUNNING'] > 0:
              self.STEPS[step]['status'] = 'RUNNING'
              continue
          if jobs_status['ABORTED'] > 0:
              self.STEPS[step]['status'] = 'ABORTED'
              continue
          self.STEPS[step]['status'] = 'UNKNOWN'

    self.save(take_lock)

#     self.log_debug("get_status:end -> JOBS=\n%s " % pprint.pformat(self.JOBS),3)
#     self.log_debug("get_status:end -> STEPS=\n%s " % pprint.pformat(self.STEPS),3)
#     self.log_info("get_status:end -> TASKS=\n%s " % pprint.pformat(self.TASKS),3)

    self.release_lock(lock_file)
    self.log_debug('get_current_jobs_status: releasing the lock',4,trace='SAVE')

    if status_error:
      self.log_info('!WARNING! Error encountered scanning job status,' +\
                    'run with --debug to know more')

  #########################################################################
  # add step to history
  #########################################################################
  def add_step_to_history(self,step,step_dep):
    self.log_debug('add_step_to_history called (step=%s,step_dep=%s)' %\
                   (step,step_dep),3,trace='HISTORY')
    # updating list of submitted steps and their history
    if not(step in self.steps_submitted):
      self.steps_submitted = self.steps_submitted + [step, ]
      self.steps_submitted_history[step] = {'previous':None, 'next':None}
      if step_dep:
        self.steps_submitted_history[step] = {'previous':step_dep, 'next':None}
        if not(step_dep in self.steps_submitted_history.keys()):
          self.error('for step %s on job dependency %s not found in self.steps_submitted_history %s' %\
                     (step,step_dep,pprint.pformat(self.steps_submitted_history)),\
                     exit=True,exception=True)
        current_next = self.steps_submitted_history[step_dep]['next']
        if current_next:
          self.steps_submitted_history[step_dep]['next'] = step
          self.steps_submitted_history[step]['next'] = current_next
        self.steps_submitted_history[step_dep]['next'] = step
    else:
      self.log_debug('ZZZZZZZ warning (step=%s,step_dep=%s) already registered in history' %\
                     (step,step_dep),3,trace='HISTORY')

  #########################################################################
  # welcome message
  #########################################################################

  def welcome_message(self,print_header=True,print_cmd=True):
      """welcome message"""

      if print_header:
        print()
        print("          ########################################")
        print("          #                                      #")
        print("          #   Welcome to %11s version %3s!#" % \
              (self.APPLICATION_NAME, self.APPLICATION_VERSION))
        print("          #    (using ENGINE Framework %3s)     #" % self.ENGINE_VERSION)
        print("          #                                      #")
        print("          ########################################")
        print("       ")

      if print_cmd and self.args.banner:
        print("\trunning on %s (%s) " % (MY_MACHINE_FULL_NAME,MY_MACHINE))
        print("\t\tpython " + " ".join(sys.argv))
        print()

      self.machine = self.MY_MACHINE = MY_MACHINE

  #########################################################################
  # dumping error report ...
  #########################################################################

  def error(self,message=None, error_detail="", exit=True,exception=False, killall=False, where='Not Known'):
      """helping message"""
      print(colors.FAIL)
      if message:
        message = str(message) + "\n"
        if len(error_detail):
          print("[ERROR] Error %s : " % error_detail)
        for m in message.split("\n"):
          try:
            # print("[ERROR]  %s : " % m)
            if len(self.LOG_PREFIX):
                m = "%s:%s" % (self.LOG_PREFIX,m)
            self.log.error(m)
          except Exception:
            print("[ERROR Pb processing] %s" % m)
        print("[ERROR] add -h as a second parameter to the command line for the list of available options...")
      else:
        try:
          self.usage(exit=False)
        except Exception:
          self.dump_exception()
          print("\n  usage: \n \t python %s \
               \n\t\t[ --help ] \
               \n\t\t[ --info  ] [ --info-level=[0|1|2] ]  \
               \n\t\t[ --debug ] [ --debug-level=[0|1|2] ]  \
             \n" % self.APPLICATION_NAME)

      if not(exception is False):
        self.dump_exception(where='Not Known')

      print(colors.END)
      if killall:
        time.sleep(killall)
        self.kill_workflow(force=True)
      if exit:
        self.keep_probing = False
        sys.exit(1)

  #########################################################################
  # checking methods
  #########################################################################

  def check_python_version(self):
    try:
      subprocess.check_output(["ls"])
    except Exception:
      self.error("Please use a more recent version of Python > 2.7.4")

  def check_engine_version(self,version):
    current = int(("%s" % self.ENGINE_VERSION).split('.')[1])
    asked = int(("%s" % version).split('.')[1])
    if (asked > current):
        self.error("Current Engine version is %s while requiring %s, please fix it!" % \
                   (current,asked))

  #########################################################################
  # locking methods
  #########################################################################

  def lock(self, file, flags):
      try:
        fcntl.flock(file.fileno(), flags)
      except IOError as exc_value:
        self.dump_exception('in lock problem')
        #  IOError: [Errno 11] Resource temporarily unavailable
        if exc_value[0] == 11:
          raise LockException(LockException.LOCK_FAILED, exc_value[1])
        else:
          raise

  def unlock(self,file):
    fcntl.flock(file.fileno(), fcntl.LOCK_UN)

  def take_lock(self,filename,write_flag="a+"):

    self.log_debug('self.log_taken=%s' % pprint.pformat(self.lock_taken),4,trace='LOCK')
    if filename in self.lock_taken.keys():
        self.log_debug('take_log: lock already taken %s times on %s ' % \
                       (self.lock_taken[filename],filename),4,trace='LOCK')
        self.lock_taken[filename] = self.lock_taken[filename] + 1
    else:
        if self.NewLock:
          self.lock_id[filename] = Lock(filename)
          self.lock_id[filename].lock()
        else:
          try:
              self.lock_id[filename] = open(filename,write_flag)
              self.lock(self.lock_id[filename], LOCK_EX)
          except Exception:
              self.log_info('cannot take lock... will not try to save then')
              self.CanLock = False

        self.log_debug('lock taken on %s' % filename,4,trace='LOCK')
        self.lock_taken[filename] = 1

    self.log_debug('self.lock_taken=%s %s times' % \
                   (filename, self.lock_taken[filename]),4,trace='LOCK_DETAIL',stack=True)

    return filename

  def release_lock(self,filename):

    if not(self.CanLock):
        return

    if not(filename in self.lock_taken.keys()):
        self.log_debug('release_log: lock was not taken yet on %s ......' % filename,\
                       4,trace='LOCK')
        self.error('release_log: lock was not taken yet......', exception=True, exit=True)
    else:
        self.log_debug('lock about to be released  and already taken %s times on %s ' % \
                       (self.lock_taken[filename],filename),4,trace='LOCK',stack=True)
        self.lock_taken[filename] = self.lock_taken[filename] - 1
        if self.lock_taken[filename] == 0:
            if self.NewLock:
              self.lock_id[filename].unlock()
            else:
              self.lock_id[filename].close()

            del self.lock_taken[filename]
            self.log_debug('lock completely released  on %s ' % \
                           (filename),4,trace='LOCK')
            self.log_debug('lock completely released  on %s ' % \
                           (filename),4,trace='LOCK_DETAIL',stack=True)
            return

    self.log_debug('self.lock_released=%s %s times' % \
                   (filename, self.lock_taken[filename]),4,trace='LOCK_DETAIL',stack=True)

  #########################################################################
  # os.system wrapped to enable Trace if needed
  #########################################################################

  def system(self,cmd,comment="No comment",fake=False,verbosity=1,
             force=False,trace=True,return_code=False):

    self.log_info('in system cmd=/%s/ ' % cmd,2)
    self.log_debug("\tcurrently executing /%s/ :\n\t\t%s" % (comment,cmd),verbosity,trace='SYSTEM')

    if trace and self.args.load:
        self.log_info('reading from trace file / output = /%s/' % \
                      len(self.SYSTEM_OUTPUTS[self.args.load]),2)
        output = self.SYSTEM_OUTPUTS[self.args.load].pop(0)
        self.log_info('reading from trace file / output = /%s/' % output,3)
        return output

    output = 'FAKE EXECUTION'
    if force or (not(fake) and not(self.args.fake)):
      # os.system(cmd)
      # subprocess.call(cmd,shell=True,stderr=subprocess.STDOUT)
      proc = subprocess.Popen(cmd, shell=True, bufsize=1, stdout=subprocess.PIPE, \
                              stderr=subprocess.STDOUT)
      proc.wait()
      output = ""
      while (True):
          # Read line from stdout, break if EOF reached, append line to output
          line = proc.stdout.readline()
          # line = line.decode()
          if (line == ""):
            break
          output += line
      if len(output):
        self.log_debug("output=+" + output,verbosity + 1,trace='SYSTEM')
      if trace and self.args.save:
          self.SYSTEM_OUTPUTS[self.args.save].append(output)
          self.log_info('writing to trace file / output = /%s/' % output,3)
    if (return_code):
      return (proc.returncode,output)
    else:
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

    if level > self.args.mail_verbosity:
        self.log_info('%s not sent because level=%s > %s' % \
                      (msg,level, self.args.mail_verbosity),4)
        return

    if not(self.MAIL_COMMAND):
      self.error("No mail command available on this machine")

    # sendmail only works from a node on shaheen 2 via an ssh connection to cdl via gateway...

    mail_file = os.path.abspath("%s/mail.txt_%s_%s" % (self.MAIL_DIR,os.getpid(),int(time.time())))

    if not(to):
        to = self.args.mail

    to = to.replace('kortass','samuel.kortas@kaust.edu.sa')
    f = open(mail_file,'w')
    #  via file
    f.write("Subject:%s\nTo: %s\n" % (self.MAIL_SUBJECT_PREFIX + subject, to))

    s = self.MAIL_CURRENT_MESSAGE + "\n" + msg
    for m in s.split("\n"):
        f.write(m + "\n")
    f.close()
    self.MAIL_CURRENT_MESSAGE = ""

    # waiting the mail to be taken  from the filesystem
    # cmd = (self.MAIL_COMMAND+"2> /dev/null") % (self.MAIL_SUBJECT_PREFIX+subject, to, mail_file)
    #
    # self.log_debug("self.args.mail cmd : "+cmd,2,trace='MAIL')
    # os.system(cmd)

    time.sleep(3)

    if not(self.args.nocleaning):
        pass
        # os.unlink(mail_file)

  def append_mail(self,msg,level=0):

    if not(self.args.mail) or level > self.args.mail_verbosity:
      return False

    self.MAIL_CURRENT_MESSAGE = self.MAIL_CURRENT_MESSAGE + "\n" + msg

  def flush_mail(self,msg=''):

    if len(self.MAIL_CURRENT_MESSAGE):
        self.send_mail(msg)

  def forward_mail(self):
    files = glob.glob('%s/mail.txt*' % self.MAIL_DIR)

    if len(files) == 0:
      return

    lock_file = self.take_lock(self.MAIL_LOCK_FILE)
    self.forward_mail_already_taken = True

    cmd = ""
    for f in files:
      self.log_debug('sending mail %s' % f,4, trace='MAIL')
      cmd = cmd + 'mail -t <  %s; rm %s ;' % (f,f)
    os.system(cmd)

    self.release_lock(lock_file)

  #########################################################################
  # create template (matrix and job)
  #########################################################################

  def create_template(self,path='.'):

    for dirpath, dirs, files in os.walk("%s/templates" % path):
       for filename in files:
         filename_from = os.path.join(dirpath,filename)
         filename_to = filename_from.replace("%s/templates/" % path,"./")
         if os.path.exists(filename_to):
           self.log_info("\t file %s already exists... skipping it!" % filename_to)
         else:
           dirname = os.path.dirname(filename_to)
           self.log_debug('working on file %s in dir %s' % (filename_to,dirname))

           if not(os.path.exists(dirname)):
             self.system("mkdir -p %s" % dirname,comment="creating dir %s" % dirname)
           self.system("cp %s %s" % (filename_from,filename_to),\
                       comment="creating file %s" % filename_to)
           self.log_info('creating file %s' % (filename_to))
    sys.exit(0)

  #########################################################################
  # tail log file
  #########################################################################

  def tail_log_file(self,filename=None,keep_probing=-999,
                    nb_lines_tailed=20,message=True,no_timestamp=False,stop_tailing=False):

    if keep_probing == -999:
        keep_probing = not(self.args.no_pending)

    self.keep_probing = keep_probing
    try:
      if filename is None:
          filename = self.log_file_name

      if not os.path.isfile(filename):
          self.error_report("no logfile %s yet..." % filename,exit=True)

      if message and self.keep_probing:
          print()
          print("=" * 80)
          print('Currently Tailing ... \n %s' % filename)
          print('\t\tHit CTRL-C to exit...' * 2)
          print('=' * 80)
          print('...')

      fic = open(filename, "r")
      lines = fic.readlines()
      for line in lines[-nb_lines_tailed:]:
          if no_timestamp:
              line = re.sub('^.*\[','[',line[:-1])
          print(line)
      # if str.find(lines[-1], "goodbye") >=0:
      #    good_bye_reached = True
      while True:
          if not(self.keep_probing):
              break
          where = fic.tell()
          line = fic.readline()
          self.forward_mail()
          if not line:
              time.sleep(10)
              fic.seek(where)
          else:
              if no_timestamp:
                  line = re.sub('^.*\[','[',line)
              print line,  # already has newline
              sys.stdout.flush()
              if isinstance(stop_tailing, str):
                  if line.find(stop_tailing) > -1:
                      self.keep_probing = False
                      return True
              if type(stop_tailing) == type(["string1","string2"]):
                  for pattern in stop_tailing:
                      if line.find(pattern) > -1:
                          self.keep_probing = False
                          return True
    except KeyboardInterrupt:
        print("\n bye bye come back anytime!   To resume this monitoring type :")
        print("\t\tpython %s --log" % sys.argv[0])
        print()
        self.keep_probing = False
        return False

  #########################################################################
  # look for a pattern in a set of files
  #########################################################################

  def check_for_pattern(self,pattern,file_mask=None,files=None,return_all=False,col=None):

      error = 0

      if not(file_mask) and not(files):
          self.error("in check_for_pattern('%s') on must add at least file_mask or files parameter"\
                     % pattern)
      self.log_debug('current directory %s ' % (os.getcwd()),2)
      filter_success = 0
      pattern_found = {}
      if file_mask:
          files = glob.glob(file_mask)
          self.log_debug('filtered from mask %s --> files : [%s] ' % (file_mask,",".join(files)),2)
      else:
          files_to_scan = files
          files = []
          for f in files_to_scan:
              if os.path.isfile(f):
                  files = files + [f]
          self.log_debug('filtered from candidate files [%s] --> files : [%s] ' % \
                         (",".join(files_to_scan),",".join(files)),2)

      if len(files) == 0:
          error = ERROR_FILE_DOES_NOT_EXISTS

      for f in files:
          (p, return_code) = self.greps(pattern,f,col,return_all=True)
          if p:
              pattern_found[f] = [p,len(p)]
              filter_success = filter_success + len(p)
          else:
              pattern_found[f] = [None,0]

      if error < 0:
          filter_success = error

      if return_all:
           return (filter_success,files,pattern_found,error)
      else:
           return filter_success

  #########################################################################
  # look for a pattern in a file
  #########################################################################

  def greps(self,motif, file_name, col=None, nb_lines=-1, \
            return_all=False, exclude_patterns=[]):
      """Fonction qui retourne toute ligne contenant un motif dans un fichier

       et renvoie le contenu d'une colonne de cette ligne
       fic             --> Nom du fichier
       motif         --> Motif a chercher
       col             --> La liste des Numeros de colonne a extraire
       endroit     --> Un objet de type situation
       nb_lines  --> nb_lines max a renvoyer
       Renvoie la colonne col et un indicateur indiquant si le motif a y trouver

      """

      self.log_debug("greps called for searching %s in %s " % (motif, file_name),2)

      trouve = -1
      rep = []
      motif0 = str.replace(motif, '\\MOT', '[^\s]*')
      motif0 = str.replace(motif0, '\\SPC', '\s*')

      # col can be    Nothing,         one figure,     or    a list of figures
      type_matching = "Columns"
      if col is None:
          type_matching = "Grep"
      if isinstance(col, int):
          col = [col]
      if isinstance(col, str):
          type_matching = "Regexp"
          masque0 = str.replace(col, '\\MOT', '[^\s]*')
          masque0 = str.replace(masque0, '\\SPC', '\s*')

      file_name_full_path = MY_MACHINE_FULL_NAME + ":" + os.getcwd()

      if not(os.path.isfile(file_name)):
          if col is None:
              self.log_debug("file '%s' read \n\t from path '%s' \
                                                  \n\t searched for motif '%s' does not exist!!!!"\
                             % (file_name, file_name_full_path, motif))
          else:
              self.log_debug("file '%s' read \n\t from path '%s' \
                                                  \n\t searched for motif '%s' to get column #[%s]\
                                                  \n\t  file does not exist!!!"\
                           % (file_name, file_name_full_path, motif, ",".join(map(str,col))))
          if return_all:
              return (None,ERROR_FILE_DOES_NOT_EXISTS)
          else:
              return None
      else:
          if len(exclude_patterns):
            if isinstance(exclude_patterns, str):
                exclude_patterns = [exclude_patterns]

          file_scanned = open(file_name, "r")
          for ligne in file_scanned.readlines():
              if False:
                  print(ligne,motif0)
              if (len(ligne) >= 1):
                  for pattern in exclude_patterns:
                      if ligne.find(pattern) > -1:
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

  def ask(self,msg,default='n', answers='(y/n)', yes='y', no='n'):

    if self.args.yes:
        if self.args.banner:
          self.log_info('%s --> %s (automated user answer)' % (msg,yes))
        return

    if self.args.no:
        self.log_info('%s --> %s (automated user answer)' % (msg,no))
        self.log_info("ABORTING: No clear confirmation... giving up!")
        sys.exit(1)

    answers = answers.replace(default,'[%s]' % default)
    input_var = raw_input('[QUESTION] >>>> ' + msg + answers + " ")

    self.log_debug('received answer=>%s< default=>%s< no=>%s<' % (input_var,default,no),3)

    if (str(input_var) == str(yes)) or (len(input_var) == 0 and default == yes):
        return
    else:
        self.log_info("ABORTING: No clear confirmation... giving up!")
        sys.exit(1)

  #########################################################################
  # apply_tags
  #########################################################################

  def apply_tags(self, file=False, input=False, include_path=['.']):

    self.log_debug('apply_tags run on file=%s' % file, 4, trace='TEMPLATE,EVAL')
    self.log_debug('tags=%s' % pprint.pformat(self.tag_value), 4, trace='TAGS')
    lines = open(file,'r').readlines()
    input = "ZZ%ZZ".join(lines)
    output = input
    for t in self.tag_value.keys():
      input = input.replace("__%s__" % t,"%s" % self.tag_value[t])

    output = ""
    lines_to_process = input.split("ZZ%ZZ")
    while len(lines_to_process):
      l = lines_to_process.pop(0)
      self.log_debug('avant clean l = >%s<' % l,4, trace='PROCESS')
      # l = clean_line(l)
      self.log_debug('apres clean l = >%s<' % l,4, trace='PROCESS')
      fields = l.split('___IF___')
      if len(fields) == 2:
        try:
          expression = clean_line(fields[0])
          if expression == '#':
              then_present = (len(l.split('___THEN___')) == 2)
              if (then_present):
                  self.log_debug('IF THEN ELSE found at %s' % (l), 4, trace='TEMPLATE,IF,LONGIF')
                  fields[1] = fields[1].replace('___THEN___','')
              else:
                  self.log_debug('one line IF found at %s' % (l), 4, trace='TEMPLATE,IF,LONGIF')
              expression_found = False
              endif_found = False
              output_to_add = ""
              while len(lines_to_process) and not(expression_found and then_present and endif_found) \
                    and not(expression_found and not(then_present)):
                l = lines_to_process.pop(0)
                if not(re.search(r"^\s*#", l)):
                  expression_found = True
                  if l.find('___INCLUDE___') > -1:
                    self.error('ERROR: including file inside and ___IF___ long zone is not yet supported! \n\t check line  (%s)' % \
                               (l),exit=True)
                  if l.find('___IF___') > -1:
                    self.error('ERROR: imbricated ___IF___ zones are  not yet supported! \n\t check line  (%s)' % \
                               (l),exit=True)
                  while ((len(l) > 0) and (l[-1] == '#' or l[-1] == ' ')):
                      l = l[:-1]
                  output_to_add = output_to_add + l
                else:
                  if (len(l.split('___ENDIF___')) == 2):
                    endif_found = True
                  else:
                    output_to_add = output_to_add + l

              self.log_debug('output to add: %s' % (output_to_add), 4, trace='TEMPLATE,IF,LONGIF')

          else:
              self.log_debug('IF at the end of line found at %s' % (l), \
                             4, trace='TEMPLATE,IF,SHORTIF')
              l = fields[0]
              while ((len(l) > 0) and (l[-1] == '#' or l[-1] == ' ')):
                  l = l[:-1]
              output_to_add = l
              self.log_debug('output to add: %s' % (output_to_add), 4, trace='TEMPLATE,IF,SHORTIF')
          cond = fields[1][:-1]
          self.log_debug('for l=%s\n evaluating (%s)= %s' % (l,cond,eval(cond)),\
                         4, trace='TEMPLATE')
          self.log_debug('evaluating (%s)= %s' % (cond,eval(cond)), 4, trace='EVAL')
          if not(eval(cond)):
            continue
          l = output_to_add
        except Exception:
          self.error('ERROR: could not evaluate %s for template file %s' % (cond,file),
                     exit=True)
      fields = l.split('___INCLUDE___')
      if len(fields) == 2:
        file_to_include = fields[1][:-1]
        if not(file_to_include[0] == '/'):
          include_file_found = False
          include_dir_candidates = [os.path.dirname(file)] + include_path
          for d in include_dir_candidates:
            included_file = '%s/%s' % (d,file_to_include)
            if os.path.exists(included_file):
              include_file_found = True
              break
          if not(include_file_found):
            self.error('ERROR: could not find included file %s for template file %s in possible directories (%s)' % \
                       (file_to_include,file,",".join(include_dir_candidates)),
                       exit=True)
        output = output + self.apply_tags(included_file)
        continue
      output = output + l
    self.log_debug('result template :\n----- %s -----------\n%s\n-------------------' % (file,output),4,\
                   trace='TEMPLATE,TEMPLATE_RESULT')

    output_test = "".join(output.split('___INCLUDE___'))
    output_test = "".join(output_test.split('___IF___'))
    output_test = "".join(output_test.split('___ENDIF___'))
    output_test = "".join(output_test.split('___THEN___'))
    mo = re.search(r"(__[\w.]+__)", output_test)
    if mo:
        s = '%s was still found in template %s and cannot be valued' % (mo.group(1),file)
        self.log_debug('ERROR:%s\n----- in ----------\n%s\n-----------------' %\
                       (s,output_test.replace('ZZ%ZZ','')),4,trace='TEMPLATE,EVAL')
        self.error(s)

    return output

if __name__ == "__main__":
  D = application("my_app")
