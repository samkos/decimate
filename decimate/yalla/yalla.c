#include <mpi.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>

#define WORKTAG 1
#define DIETAG 2
#define DIETAG_OK 3
#define MASQUE_LEN 4
#define MASQUE 5
#define WORK_TOTAL 6
#define WAITING_TIME_BEFORE_CLOSING 10


/* Local functions */

typedef int unit_of_work_t;
typedef int unit_result_t;

static void master(void);
static void slave(void);
static unit_of_work_t get_next_work_item(void);
static void process_results(int nbSlave, unit_result_t result);
static unit_result_t do_work(unit_of_work_t work);

int nb_work_total, nb_work_current=0;
char *masque;
int myrank;

int
main(int argc, char **argv)
{

/*
 *
   if (argc!=3) {
    printf("Usage:  maestro <Mask of job with %%d> <nb_jobs to do>\n");
    exit(1);
  }

 */

  masque=argv[1];
  nb_work_total=atoi(argv[2]);


  /* Initialize MPI */

  MPI_Init(&argc, &argv);

  /* Find out my identity in the default communicator */

  MPI_Comm_rank(MPI_COMM_WORLD, &myrank);
  
  #ifdef DEBUG
  printf ("\n===MAESTRO=== MPI task # %d started OK",myrank);
  fflush(stdout);
  #endif 


  if (myrank == 0) {
    master();
  } else {
    slave();
  }

  #ifdef DEBUG
  printf("\n===MAESTRO=== Task %d ; Bye bye",myrank);
  fflush(stdout);
  #endif
  /* Shut down MPI */

  sleep(WAITING_TIME_BEFORE_CLOSING);
  
  MPI_Finalize();
  return 0;
}


static void
master(void)
{
  int ntasks, rank, nb_jobs_first_wave, len;
  unit_of_work_t work;
  unit_result_t result;
  MPI_Status status;
  double buffer;


  #ifdef DEBUG
  printf("\n===MAESTRO=== ===PROC %d=== masque  /%s/ \n nb_work_total=%d",myrank,masque,nb_work_total);
  #endif

  /* Find out how many processes there are in the default
     communicator */

  MPI_Comm_size(MPI_COMM_WORLD, &ntasks);
  printf("\n===MAESTRO=== Nb Tasks in the pool %d ",ntasks);
  fflush(stdout);


  /* send masque and work_total to all slave. */
  
  #ifdef DEBUG
  printf("\n===MAESTRO=== Master ; sending nb_work_total to every one");
  fflush(stdout);
  #endif

  for (rank = 1; rank < ntasks; rank++) {
    MPI_Send(&nb_work_total, 1, MPI_INTEGER, rank, WORK_TOTAL, MPI_COMM_WORLD);
    len=strlen(masque);
    MPI_Send(&len, 1, MPI_INTEGER, rank, MASQUE_LEN, MPI_COMM_WORLD);
    MPI_Send(masque, len+1, MPI_CHAR, rank, MASQUE, MPI_COMM_WORLD);
  }

  /* Seed the slaves; send one unit of work to each slave. */

  for (rank = 1; rank < ntasks; ++rank) {

    /* Find the next item of work to do */

    work = get_next_work_item();


    /* Send it to each rank */
  #ifdef DEBUG
    printf("\n===MAESTRO=== Master ; Asking slave %d to do work %d",rank,work);
    fflush(stdout);
  #endif

    buffer =(double) work;

    MPI_Send(&buffer,             /* message buffer */
             1,                 /* one data item */
             MPI_DOUBLE,           /* data item is an integer */
             rank,              /* destination process rank */
             WORKTAG,           /* user chosen message tag */
             MPI_COMM_WORLD);   /* default communicator */
  }

  /* Loop over getting new work requests until there is no more work
     to be done */

  work = get_next_work_item();
  while (work>=0) {

    /* Receive results from a slave */

    MPI_Recv(&buffer,           /* message buffer */
             1,                 /* one data item */
             MPI_DOUBLE,        /* of type double real */
             MPI_ANY_SOURCE,    /* receive from any sender */
             MPI_ANY_TAG,       /* any type of message */
             MPI_COMM_WORLD,    /* default communicator */
             &status);          /* info about the received message */    result=(int) buffer;

  #ifdef DEBUG
    
    /* Send the slave a new work unit */
    printf("\n===MAESTRO=== Master ; Asking slave %d to do work %d",status.MPI_SOURCE,work);
    #endif

	buffer=(double) work;

    MPI_Send(&buffer,             /* message buffer */
             1,                 /* one data item */
             MPI_DOUBLE,        /* data item is an integer */
             status.MPI_SOURCE, /* to who we just received from */
             WORKTAG,           /* user chosen message tag */
             MPI_COMM_WORLD);   /* default communicator */

    process_results(status.MPI_SOURCE,result);


    /* Get the next unit of work to be done */

    work = get_next_work_item();

    #ifdef DEBUG
    printf("\n===MAESTRO=== Master ; next work todo : %d",work);
    #endif
  }

  printf("\n===MAESTRO=== Master ; I am done! waiting for %d tasks",ntasks);

  /* There's no more work to be done, so receive all the outstanding
     results from the slaves. */

  for (rank = 1; rank < ntasks; rank++) {
    MPI_Recv(&buffer, 1, MPI_DOUBLE, MPI_ANY_SOURCE,
             MPI_ANY_TAG, MPI_COMM_WORLD, &status);
    result=(int) buffer;
    #ifdef DEBUG
    printf("\n===MAESTRO=== Master ; received last job from node %d",status.MPI_SOURCE);
    fflush(stdout);
    #endif
  }

  /* Tell all the slaves to exit by sending an empty message with the
     DIETAG. */

  printf("\n===MAESTRO=== Master ; sending DieTag to every one");
  fflush(stdout);

  buffer=0.;
  for (rank = 1; rank < ntasks; rank++) {
    MPI_Send(&buffer, 1, MPI_DOUBLE, rank, DIETAG, MPI_COMM_WORLD);
  }




  printf("\n===MAESTRO=== Master ; expecting DieTag Acknowledgment from every one");
  fflush(stdout);

  for (rank = 1; rank < ntasks; rank++) {
    MPI_Recv(&buffer, 1, MPI_DOUBLE, MPI_ANY_SOURCE,
             DIETAG_OK, MPI_COMM_WORLD, &status);
  }


  printf("\n===MAESTRO=== Master ; I am out of here");
  fflush(stdout);

}


static void
slave(void)
{
  unit_of_work_t work;
  unit_result_t result;
  MPI_Status status;
  double buffer;
  int len;

  /* Receive a message from the master */
  
  MPI_Recv(&nb_work_total, 1, MPI_INTEGER, 0, WORK_TOTAL,
	   MPI_COMM_WORLD, &status);

  MPI_Recv(&len, 1, MPI_INTEGER, 0, MASQUE_LEN,
	   MPI_COMM_WORLD, &status);

  MPI_Recv(masque, len+1, MPI_CHAR, 0, MASQUE,
	   MPI_COMM_WORLD, &status);

  #ifdef DEBUG
  printf("\n===MAESTRO=== ===PROC %d=== masque  /%s/ \n nb_work_total=%d",myrank,masque,nb_work_total);
  #endif




  while (1) {

    /* Receive a message from the master */

    MPI_Recv(&buffer, 1, MPI_DOUBLE, 0, MPI_ANY_TAG,
             MPI_COMM_WORLD, &status);
    work=(int) buffer;

    /* Check the tag of the received message. */

    if (status.MPI_TAG == DIETAG) {
      buffer=0;
      MPI_Send(&buffer, 1, MPI_DOUBLE, 0, DIETAG_OK, MPI_COMM_WORLD);
      return;
    }

    /* Do the work */

    if (work>=0) {
        #ifdef DEBUG
        printf("\n===MAESTRO=== Node %d received job %d, doing the job......  ",myrank,work);
        fflush(stdout);
        #endif
	result = do_work(work);
    } else {
      #ifdef DEBUG
      printf("\n===MAESTRO=== Node %d received job -1, doing nothing...... and waiting for Die order ",myrank);
      fflush(stdout);
      #endif
    }

    /* Send the result back */
    buffer=(double) result;
    MPI_Send(&buffer, 1, MPI_DOUBLE, 0, 0, MPI_COMM_WORLD);
  }
}


static unit_of_work_t
get_next_work_item(void)
{
  /* Fill in with whatever is relevant to obtain a new unit of work
     suitable to be given to a slave. */

  int nb_job;


  #ifdef DEBUG
  printf("\n===MAESTRO=== in get next_work_item nb_work_current=%d nb_work_total=%d",nb_work_current,nb_work_total);
  #endif
  nb_job=nb_work_current;
  nb_work_current++;

  if (nb_job<nb_work_total) {
    return  nb_job;
  }
  else {
    return -1;
  }
}


void process_results(int nbSlave, unit_result_t result)
{
  /* Fill in with whatever is relevant to process the results returned
     by the slave */
  #ifdef DEBUG
  printf("\n===MAESTRO=== %d slave resulted : %d",nbSlave,result);
  #endif
  return;
}


static unit_result_t
do_work(unit_of_work_t work)
{
  /* Fill in with whatever is necessary to process the work and
     generate a result */
  char command[256];

  // sprintf(command,"/bin/ksh /home/cont002/kortas/P5_GALICE/FDV/MAESTRO/run.ksh %d",work);
  sprintf(command,masque,work+1,myrank);

  #ifdef DEBUG
  printf("\n===MAESTRO=== MPI task # %d executing %s ",myrank,command);
  fflush(stdout);
  #endif
  system(command);

  return work*10;
}
