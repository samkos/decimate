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


anaconda login
samuel_kortas


anaconda login
anaconda upload /home/kortass/APPS/miniconda2/conda-bld/broken/decimate-0.9.7.1-py27_0.tar.bz2


conda install -c samuel_kortas decimate 

man decimate
man workflow









# push in anaconda 3

# create dist and wheel file
\rm -rf dist/*
python setup.py sdist
python setup.py bdist_wheel
twine upload -r test dist/*


conda  activate /home/kortass/DECIMATE_DEBUG/out3

conda install anaconda-client -y
conda install conda-build -y
conda install setuptools -y
conda config --set anaconda_upload no
#conda config --add channels auto

export CONDA_PY=36

#export PYTHONPATH=/home/kortass/APPS/anaconda2/lib/python2.7/site-packages:


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


anaconda login
samuel_kortas


anaconda login
anaconda upload /home/kortass/APPS/miniconda2/conda-bld/broken/decimate-0.9.7.1-py27_0.tar.bz2


conda install -c samuel_kortas decimate 

man decimate
man workflow



d run -d -t -i continuumio/anaconda3
db conda3
conda install anaconda-client -y
conda install conda-build -y
conda install setuptools -y
conda config --set anaconda_upload no

conda skeleton pypi decimate --pypi-url https://testpypi.python.org/pypi/decimate
conda build decimate


anaconda login
samuel_kortas


anaconda login
anaconda upload /home/kortass/APPS/miniconda2/conda-bld/broken/decimate-0.9.7.1-py27_0.tar.bz2






# testing in conda environment


ml miniconda/3.7
cd /project/k01/kortass/CLE6/DECIMATE_TEST
conda create -p /project/k01/kortass/CLE6/DECIMATE_TEST/out3 numpy pandas pip python>=3 -y
source /project/k01/kortass/CLE6/DECIMATE_TEST/out3/bin/activate
pip install clustershell



pip install --extra-index-url https://testpypi.python.org/pypi decimate

