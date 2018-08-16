#!/bin/bash
ROOT=`pwd`
export node1=`hostname`
export nodes=$SLURM_NODELIST
export MY_SLURM_INSTALL=/home/kortass/opt/slurm2
export MULTIJOB_PATH=/home/kortass/DECIMATE_DEBUG/decimate/yalla

SLURM_NEW_ROOT=$ROOT/.slurm_$node1

export CORES_PER_SLURMD=$1

echo CORES_PER_SLURMD: $CORES_PER_SLURMD

export SLURMD_PER_NODE=$((32/$CORES_PER_SLURMD))

echo SLURMD_PER_NODE: $SLURMD_PER_NODE
			  
\rm -rf $SLURM_NEW_ROOT
\mkdir -p $SLURM_NEW_ROOT/etc $SLURM_NEW_ROOT/var/run $SLURM_NEW_ROOT//var/log $SLURM_NEW_ROOT//var/spool/slurm

nnodes=0
for n in `scontrol show hostname $nodes`; do
    mkdir -p $SLURM_NEW_ROOT/var/spool/slurmd.$n
    ((nnodes++))
done


port_start=25000
port_end=$(($port_start+$SLURMD_PER_NODE*$nnodes-1))

NODE_HOSTNAME=""
INDEXED_NODE_HOSTNAME=""
echo SLURM_NODELIST:$SLURM_NODELIST
for i in `seq 0  $CORES_PER_SLURMD 31`; do
    NODE_HOSTNAME="$NODE_HOSTNAME,$SLURM_NODELIST"
    INDEXED_NODE_HOSTNAME="$INDEXED_NODE_HOSTNAME,$i-xxx$SLURM_NODELIST"
done
NODE_HOSTNAME=${NODE_HOSTNAME:1:2000}
INDEXED_NODE_HOSTNAME=${INDEXED_NODE_HOSTNAME:1:2000}
echo INDEXED_NODE_HOSTNAME=$INDEXED_NODE_HOSTNAME

sed "s|__PORTS__|$port_start-$port_end|;s|__INDEXED_NODE_HOSTNAME__|$INDEXED_NODE_HOSTNAME|g;s|__NODE_HOSTNAME__|$NODE_HOSTNAME,|g;s|__HOSTNAME__|$node1|g;s|__USER__|$USER|g;s|__SLURM_CONFDIR__|$SLURM_NEW_ROOT|g" $MULTIJOB_PATH/sam32/slurm.conf.template >$SLURM_NEW_ROOT/etc/slurm.conf



cat > start_daemons.$node1 << END
export PATH=$MY_SLURM_INSTALL/bin:$MY_SLURM_INSTALL/sbin:\$PATH
export SLURM_CONF=$SLURM_NEW_ROOT/etc/slurm.conf
export HOSTNAME=\`hostname\`
export NUM_SLAVE=\$1
export NUM_SLAVEp1=\$((\$1+1))
if [ \${NUM_SLAVE} == '0' ] ; then
   echo launching \`which slurmctld\` on \$HOSTNAME,\$SLURM_CONF
   slurmctld 
   #echo launching \`which slurmd\` $SLURMD_PER_NODE times on $SLURM_NODELIST
fi
# for i in \`seq 0 $CORES_PER_SLURMD 31\`; do
#    echo launching \`which slurmd\` on \$i-xxxsam-\$NUM_SLAVEp1,\$SLURM_CONF  

#   slurmd  -N \$i-xxxsam\-\$NUM_SLAVEp1  
# done

for i in \`seq 1 24\`; do
  sleep 3600   
done 

END


echo 0-$((${SLURM_NNODES}-1)) bash ./start_daemons.$node1 %o >  start_daemons.master.conf 

echo Available nodes: $SLURM_NODELIST

echo Launching daemons...
srun -N $SLURM_NNODES -n $SLURM_NNODES --multi-prog start_daemons.master.conf &

sleep 10

ROOT=`pwd`
export node1=`hostname`
export nodes=$SLURM_NODELIST
SLURM_NEW_ROOT=$ROOT/.slurm_$node1

export SINFO_FORMAT="%P %.5a %.10l %.6D %.6t %N"
export SQUEUE_FORMAT="%.10i %.9P %.15j %.8u %.8T %.10M %.9l %.6D %R" 

export PATH=$MY_SLURM_INSTALL/sbin:$PATH
export PATH=$MY_SLURM_INSTALL/bin:$PATH
export SLURM_CONF=$SLURM_NEW_ROOT/etc/slurm.conf
export CORES_PER_SLURMD=$1


for n in `scontrol show hostname $nodes`; do
    for i in `seq 0 $CORES_PER_SLURMD 31`; do
	echo scontrol update NodeName=$i-$n State=RESUME
	scontrol update NodeName=$i-$n State=RESUME
    done
done

scan_queue() {
    for i in `seq 1 100`; do
    echo --------------------------------------------------------
    squeue
    sinfo
    sinfo -R
    sleep 1
done
}


echo SLURM started...
sinfo 


