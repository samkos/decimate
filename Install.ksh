python -m compileall -f .
cd docs
make html
make man


dbatch -P decimate/test/my_params.txt decimate/test/nodes_job.sh
