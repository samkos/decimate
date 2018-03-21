python -m compileall -f .
cd docs
make html; cp -R _build/html/ ~/public_html/DOCS/
make man



dbatch -P decimate/test/my_params.txt decimate/test/nodes_job.sh
