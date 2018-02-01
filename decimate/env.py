#-*-coding:iso-8859-1-*-
#
#

"""
module finding the environment in where program is called
"""

import datetime
import fnmatch
import os
import re
import socket
import sys

ERROR = "err"
CRITICAL = "critical"
WARNING = "warning"
INFO = "info"

SCHEDULER = {"neser": ("loadleveler", 8,
                       " -l nodes=1:ppn=4,walltime=12:00:00"),
             "localhost": ("unix", 10, "")}

TMPDIR = "/tmp"
PYTHON_EXE = "python"

if os.name == "nt":
    PYTHON_EXE = "e:/python25/python.exe"


CORE_PER_NODE_REGARDING_QUEUE = {}
DEFAULT_QUEUE = "default"

NODES_FAILED = False
MAIL_COMMAND = False
SCHED_TYPE = "slurm"
SUBMIT_COMMAND = 'sbatch'
EXCLUSIVE = False

def get_machine():
    global CORE_PER_NODE_REGARDING_QUEUE, NODES_FAILED,\
        MAIL_COMMAND, SCHED_TYPE, DEFAULT_QUEUE, SUBMIT_COMMAND

    """
    determines the machine maestro is running on and sets
    proper local variable (name of the machine and path
    to the local working directory
    """

    tmp_directory = "/tmp"
    machine = socket.gethostname()

    if (machine[:4] == "fen3" or machine[:4] == "fen4" or machine[:2] == "cn"):
        machine = "neser"
        tmp_directory = "/scratch/tmp/"
        CORE_PER_NODE_REGARDING_QUEUE["highmem"] = 4
    elif (machine[:5] == "rcfen" or machine[:2] == "ca"):
        machine = "noor2"
        tmp_directory = "/scratch/tmp/"
        NODES_FAILED = "ca116,ca130,ca124,ca141"
        MAIL_COMMAND = """ "/usr/bin/ssh"  rcfen01 'mail -s %s %s < %s' """
    elif (machine[:4] == "cdl5" or machine[:4] == "cdl6"):
        machine = "osprey"
        tmp_directory = "/scratch/tmp/"
        MAIL_COMMAND = """ssh gateway1 "ssh cdl3 'mail -s \\"%s\\" %s < %s'" """
        SUBMIT_COMMAND = 'sbatch'
        EXCLUSIVE = True
    elif (machine[:3] == "nid" or machine[:3] == "cdl" or machine[:7] == "gateway"):
        machine = "shaheen"
        tmp_directory = "/scratch/tmp/"
        CORE_PER_NODE_REGARDING_QUEUE["highmem"] = 4
        CORE_PER_NODE_REGARDING_QUEUE["workq"] = 32
        MAIL_COMMAND = """ssh cdl2.hpc.kaust.edu.sa 'mail -s "%s" %s < %s' """
        DEFAULT_QUEUE = "workq"
        SUBMIT_COMMAND = 'sbatch'
        EXCLUSIVE = True
    elif (machine[:2] == "db"):
        machine = "ibex"
        tmp_directory = "/scratch/dragon/intel/"
        MAIL_COMMAND = """mail -s "%s" %s < %s """
        DEFAULT_QUEUE = "batch"
        SUBMIT_COMMAND = 'sbatch'
        EXCLUSIVE = False
    elif (machine[:7] == "kw14425"):
        machine = "sam"
        CORE_PER_NODE_REGARDING_QUEUE["debug"] = 4
        MAIL_COMMAND = """mail -s "%s" %s < %s """
        # SCHED_TYPE = "pbs"
        DEFAULT_QUEUE = "debug"
        EXCLUSIVE = False
    else:
        machine = "localhost"
        tmp_directory = "/tmp"
    # print 'Mail command:' + MAIL_COMMAND
    return machine, tmp_directory


MY_MACHINE, TMPDIR = get_machine()
MY_MACHINE_FULL_NAME = socket.gethostname()


############################################################################
#
# FONCTION FICHIERS
#
############################################################################
#
#
#


def greps(motif, file_name, col=-99, nb_lines=-1):
    """Fonction qui retourne toute ligne contenant un motif dans un fichier

     et renvoie le contenu d'une colonne de cette ligne
       fic             --> Nom du fichier
       motif         --> Motif a chercher
       col             --> La liste des Numeros de colonne a extraire
       endroit     --> Un objet de type situation
       nb_lines  --> nb_lines max a renvoyer
       Renvoie la colonne col et un indicateur indiquant si le motif a y trouver

     """

    if False:
        print("greps called for searching %s in %s " % (motif, file_name))
    trouve = -1
    rep = []
    motif0 = str.replace(motif, '\\MOT', '[^\s]*')
    motif0 = str.replace(motif0, '\\SPC', '\s*')

    # col can be    Nothing,         one figure,     or    a list of figures
    type_matching = "Columns"
    if col == -99:
        type_matching = "Grep"
    if isinstance(col, 2):
        col = [col]
    if isinstance(col, type("chaine")):
        type_matching = "Regexp"
        masque0 = str.replace(col, '\\MOT', '[^\s]*')
        masque0 = str.replace(masque0, '\\SPC', '\s*')

    file_name_full_path = MY_MACHINE_FULL_NAME + ":" + os.getcwd()

    if not(os.path.isfile(file_name)):
        if col == -99:
            print("file '%s' read \n\t from path '%s' \
                   \n\t searched for motif '%s' does not exist!!!!"\
                         % (file_name, file_name_full_path, motif))
        else:
            print(("file '%s' read \n\t from path '%s'" + \
                   "\n\t searched for motif '%s' to get column # %s" +\
                   "\n\t  file does not exist!!!") \
                   % (file_name, file_name_full_path, motif, col))
            sys.exit(1)
        return None
    else:
        file_scanned = open(file_name, "r")
        for ligne in file_scanned.readlines():
            if False:
                print(ligne, motif0)
            if (len(ligne) >= 1):
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
            return None

    return rep


#########################################################################
# chunk a list into sub list
#########################################################################
def splitList(initialList, chunkSize, only=None):
    """This function chunks a list into sub lists

    that have a length equals to chunkSize.

    Example:
    lst = [3, 4, 9, 7, 1, 1, 2, 3]
    print(chunkList(lst, 3))
    returns
    [[3, 4, 9], [7, 1, 1], [2, 3]]

    taken from http://stackoverflow.com/questions/312443\
                 /how-do-you-split-a-list-into-evenly-sized-chunks-in-python
    answer Feb 28'15 by Ranaivo
    """
    if only:
        filteredList = []
        for c in initialList:
            if c.find(only) >= 0:
                  filteredList = filteredList + [c]
    else:
        filteredList = initialList
    finalList = []
    for i in range(0, len(filteredList), chunkSize):
        finalList.append(filteredList[i:i + chunkSize])
    return finalList


#########################################################################
# geting the date
#########################################################################

def getDate():
    date_now = datetime.datetime.now()
    # now = date_now.strftime("%H:%M (%y/%m/%d)")
    # second = date_now.strftime("%S")
    # minute = date_now.strftime("%M")
    # hour = date_now.strftime("%H")
    # day = date_now.strftime("%d")
    return date_now.strftime("%Y-%m-%d %H:%M:%S")


# RANDOM_FILENAME = '/home/kortass/ABDOU/DECIME2/my/random_values_octave.txt'
# f = file(RANDOM_FILENAME,'r')

# NB_RANDOM = 0

# def rand_restart():
#     global f
#     f = file(RANDOM_FILENAME,'r')
#     NB_RANDOM = 0

# def rand(x,y):
#     global NB_RANDOM,f

#     l = f.readline();
#     #print ' %.5f' % float(l[:-1])
#     NB_RANDOM = NB_RANDOM +1
#     # if NB_RANDOM > 9:
#     #     sys.exit(1)
#     return float(l)


def find_files(directory, pattern):
  res = []
  for root, dirs, files in os.walk(directory):
    for basename in files:
      if fnmatch.fnmatch(basename, pattern):
         filename = os.path.join(root, basename)
         res.append(filename)
  return res

#########################################################################
# clean a line from the output
#########################################################################


def clean_line(line, debug=False):
    if debug:
        print("[DEBUG] analyzing line !!" + line + "!!")
    # replace any multiple blanks by one only
    p = re.compile("\s+")
    line = p.sub(' ', line)
    # get rid of blanks at the end of the line
    p = re.compile("\s+$")
    line = p.sub('', line)
    # get rid of blanks at the beginning of the line
    p = re.compile("^\s+")
    line = p.sub('', line)
    # line is clean!
    if debug:
        print("[DEBUG] analyzing  line cleaned !!" + line + "!!")
    return line
