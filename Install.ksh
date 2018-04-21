python -m compileall -f .
cd docs
make html;
\rm rf ~/public_html/DOCS/decimate
cp -R _build/html ~/public_html/DOCS/decimate
make man



dbatch -P decimate/test/my_params.txt decimate/test/nodes_job.sh
