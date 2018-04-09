
job_step=$1
attempt=$2
task_id=$3
running_dir=$4
output_file=$5
error_file=$5
is_job_completed=$6


echo job_step=$job_step  attempt=$attempt task_id=$task_id
echo running_dir=$running_dir
echo output_file=$output_file
echo error_file=$error_file
echo is_job_completed=$is_job_completed


SUCCESS=0
FAILURE=-1
ABORT=-9999

grep 'job DONE' $output_file



