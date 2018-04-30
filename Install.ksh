# to install decimate in a virtual environment in  the current directory


virtualenv out
source out/bin/activate
pip install numpy
pip install pandas
pip install sphinx
pip install sphinx_rtd_theme
pip install redis

python setup.py install



# then the module file should be

#%Module

module-whatis "decimate"

proc ModulesHelp { } {
    puts stderr "
experimental decimate SLURM extension.  try
    dbatch --help
or 
    man decimate
"
}

set prefix __CURRENT_DIRECTORY__      # <-  TO BE SET UP....


set-alias de        "dconsole"
set-alias db        "dbatch"
set-alias dk        "dkill"
set-alias dky       "dkill -y"
set-alias ds        "dstat "
set-alias dsa       "dstat -sa"
set-alias dsl       "dstat -sl"
set-alias dl        "dlog"

prepend-path PATH $prefix/out/bin
prepend-path PYTHONPATH $prefix
prepend-path MANPATH $prefix/docs/_build/man:$prefix/man






# to compile the documentation


python -m compileall -f .
cd docs
make html;
\rm rf ~/public_html/DOCS/decimate
cp -R _build/html ~/public_html/DOCS/decimate
make man



dbatch -P decimate/test/my_params.txt decimate/test/nodes_job.sh
