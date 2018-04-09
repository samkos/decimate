# testing on shaheen

ml python/2.7.14
gc
virtualenv out
source out/bin/activate
pip install numpy
pip install pandas

python setup.py install

#pip install -e .


# develing in one environment  on worstation
module purge
ml python/optim

gC
#python setup.py buil



virtualenv out

source out/bin/activate
pip install numpy
pip install pandas

python setup.py install

pip install -e .

# prepare env
pip install twine
pip install wheel

# create ~/.pypirc file
[distutils]
index-servers =
  pypi
  test

[pypi]
username = xxxxxxxxx
password = yyyyyyyyy


[test]
repository: https://test.pypi.org/legacy/
username = xxxxxxxx
password = yyyyyyyy


[pypi]
username = <username>
password = <password>
# remember to chmod 600 ~/.pypirc

# create dist and wheel file
\rm -rf dist/*
python setup.py sdist
python setup.py bdist_wheel
twine upload -r test dist/*

# deploy on conda
# from https://docs.anaconda.com/anaconda-cloud/user-guide/getting-started

ml python/miniconda2
conda update -n base conda

cd
#\rm -rf ~/PUSH_CONDA27
mkdir -p PUSH_CONDA27
cd ~/PUSH_CONDA27


# conda create -p /home/kortass/PUSH_CONDA27/env -y

# source activate /home/kortass/PUSH_CONDA27/env
conda install anaconda-client -y
conda install conda-build -y
conda install setuptools -y
conda config --set anaconda_upload no
#conda config --add channels auto

#export CONDA_PY=27

export PYTHONPATH=/home/kortass/APPS/anaconda2/lib/python2.7/site-packages:


# be sure that
requirements:
  host:
    - python
    - setuptools=36.5.0 <<<<
    - clustershell
    - pandas

also modify url of source in decimate/meta.yaml
    
conda skeleton pypi decimate --pypi-url https://testpypi.python.org/pypi/decimate
conda build decimate


could not find setuptools:
This seems to happen because although the correct PATH is set, the python in that path is a symlink, and does not set sys.path to what you would expect.

mv /home/kortass/PUSH_CONDA27/env/bin/python /home/kortass/PUSH_CONDA27/env/bin/python-old
cp /home/kortass/PUSH_CONDA27/env/bin/python2.7 /home/kortass/PUSH_CONDA27/env/bin/python






export CONDA_PY=27
conda skeleton pypi decimate


modify decimate/meta.yaml with
  host:
    - python=2.7               <<<<<<<<<<<<
    - setuptools
    - clustershell
    - pandas
  run:
    - python=2.7              <<<<<<<<<<<<<<<<<
    - clustershell
    - pandas



    conda build decimate


    --single-version-externally-managed --record=record.txt



    Anaconda Client:
#conda install anaconda-client
#Log into your Cloud account:

anaconda login
samuel_kortas

#At the prompt, enter your Cloud username and password.

#Choose the package you would like to build. For this example, download our public devel package:

git clone https://github.com/Anaconda-Platform/anaconda-client
cd anaconda-client/example-packages/conda/
#To build your devel package, first install conda-build and turn off automatic Client uploading, then run the conda build command:

conda build .
Find the path to where the newly-built file was placed so you can use it in the next step:

conda build . --output
Upload your newly-built devel package to your Cloud account:

anaconda login
anaconda upload /your/path/conda-package.tar.bz2







conda skeleton pypi --pypi-url https://test.pypi.org/pypi/decimate decimate
conda build decimate




conda skeleton pypi skyfield


conda skeleton pypi pyinstrument


