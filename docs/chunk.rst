

> dbatch -J 1 -a 1-200 --max-jobs=20 job_noname.sh
[INFO ] launch-0!0:submitting job 1 (for 1-10) --> Job # 1-0-1-10 <-depends-on None
[INFO ] launch-0!0:submitting job 1 (for 11-20) --> Job # 1-0-11-20 <-depends-on None
[INFO ] launch-0!0:submitting job 1 (for 21-30) --> Job # 1-0-21-30 <-depends-on None
[INFO ] launch-0!0:submitting job 1 (for 31-40) --> Job # 1-0-31-40 <-depends-on None
[INFO ] launch-0!0:submitting job 1 (for 41-50) --> Job # 1-0-41-50 <-depends-on None
[INFO ] launch-0!0:submitting job 1 (for 51-60) --> Job # 1-0-51-60 <-depends-on None
[INFO ] launch-0!0:submitting job 1 (for 61-70) --> Job # 1-0-61-70 <-depends-on None
[INFO ] launch-0!0:submitting job 1 (for 71-80) --> Job # 1-0-71-80 <-depends-on None
[INFO ] launch-0!0:submitting job 1 (for 81-90) --> Job # 1-0-81-90 <-depends-on None
[INFO ] launch-0!0:submitting job 1 (for 91-100) --> Job # 1-0-91-100 <-depends-on None
[INFO ] launch-0!0:submitting job 1 (for 101-110) --> Job # 1-0-101-110 <-depends-on None
[INFO ] launch-0!0:submitting job 1 (for 111-120) --> Job # 1-0-111-120 <-depends-on None
[INFO ] launch-0!0:submitting job 1 (for 121-130) --> Job # 1-0-121-130 <-depends-on None
[INFO ] launch-0!0:submitting job 1 (for 131-140) --> Job # 1-0-131-140 <-depends-on None
[INFO ] launch-0!0:submitting job 1 (for 141-150) --> Job # 1-0-141-150 <-depends-on None
[INFO ] launch-0!0:submitting job 1 (for 151-160) --> Job # 1-0-151-160 <-depends-on None
[INFO ] launch-0!0:submitting job 1 (for 161-170) --> Job # 1-0-161-170 <-depends-on None
[INFO ] launch-0!0:submitting job 1 (for 171-180) --> Job # 1-0-171-180 <-depends-on None
[INFO ] launch-0!0:submitting job 1 (for 181-190) --> Job # 1-0-181-190 <-depends-on None
[INFO ] launch-0!0:submitting job 1 (for 191-200) --> Job # 1-0-191-200 <-depends-on None
> squeue -u $USER
Tue Mar 13 00:49:17 2018
     JOBID PARTITION            NAME     USER    STATE       TIME TIME_LIMI  NODES NODELIST(REASON)
 5112086_1     workq               1  kortass  RUNNING       0:01      3:00      1 nid00072
5112087_11     workq               1  kortass  RUNNING       0:01      3:00      1 nid00217
 5112086_2     workq               1  kortass  RUNNING       0:01      3:00      1 nid00215
 5112086_3     workq               1  kortass  RUNNING       0:01      3:00      1 nid00360
 5112086_4     workq               1  kortass  RUNNING       0:01      3:00      1 nid00867
 5112086_5     workq               1  kortass  RUNNING       0:01      3:00      1 nid01590
 5112086_6     workq               1  kortass  RUNNING       0:01      3:00      1 nid06900
 5112086_7     workq               1  kortass  RUNNING       0:01      3:00      1 nid07182
 5112086_8     workq               1  kortass  RUNNING       0:01      3:00      1 nid07653
 5112086_9     workq               1  kortass  RUNNING       0:01      3:00      1 nid00149
5112086_10     workq               1  kortass  RUNNING       0:01      3:00      1 nid00150
5112087_12     workq               1  kortass  RUNNING       0:01      3:00      1 nid00218
5112087_13     workq               1  kortass  RUNNING       0:01      3:00      1 nid00347
5112087_14     workq               1  kortass  RUNNING       0:01      3:00      1 nid00348
5112087_15     workq               1  kortass  RUNNING       0:01      3:00      1 nid01049
5112087_16     workq               1  kortass  RUNNING       0:01      3:00      1 nid01050
5112087_17     workq               1  kortass  RUNNING       0:01      3:00      1 nid01067
5112087_18     workq               1  kortass  RUNNING       0:01      3:00      1 nid01068
5112087_19     workq               1  kortass  RUNNING       0:01      3:00      1 nid01085
5112087_20     workq               1  kortass  RUNNING       0:01      3:00      1 nid01086
> squeue -u $USER
Tue Mar 13 00:49:19 2018
     JOBID PARTITION            NAME     USER    STATE       TIME TIME_LIMI  NODES NODELIST(REASON)
 5112086_1     workq               1  kortass  RUNNING       0:03      3:00      1 nid00072
5112087_11     workq               1  kortass  RUNNING       0:03      3:00      1 nid00217
 5112086_2     workq               1  kortass  RUNNING       0:03      3:00      1 nid00215
 5112086_3     workq               1  kortass  RUNNING       0:03      3:00      1 nid00360
 5112086_4     workq               1  kortass  RUNNING       0:03      3:00      1 nid00867
 5112086_5     workq               1  kortass  RUNNING       0:03      3:00      1 nid01590
 5112086_6     workq               1  kortass  RUNNING       0:03      3:00      1 nid06900
 5112086_7     workq               1  kortass  RUNNING       0:03      3:00      1 nid07182
 5112086_8     workq               1  kortass  RUNNING       0:03      3:00      1 nid07653
 5112086_9     workq               1  kortass  RUNNING       0:03      3:00      1 nid00149
5112086_10     workq               1  kortass  RUNNING       0:03      3:00      1 nid00150
5112087_12     workq               1  kortass  RUNNING       0:03      3:00      1 nid00218
5112087_13     workq               1  kortass  RUNNING       0:03      3:00      1 nid00347
5112087_14     workq               1  kortass  RUNNING       0:03      3:00      1 nid00348
5112087_15     workq               1  kortass  RUNNING       0:03      3:00      1 nid01049
5112087_16     workq               1  kortass  RUNNING       0:03      3:00      1 nid01050
5112087_17     workq               1  kortass  RUNNING       0:03      3:00      1 nid01067
5112087_18     workq               1  kortass  RUNNING       0:03      3:00      1 nid01068
5112087_19     workq               1  kortass  RUNNING       0:03      3:00      1 nid01085
5112087_20     workq               1  kortass  RUNNING       0:03      3:00      1 nid01086
> squeue -u $USER
Tue Mar 13 00:49:20 2018
     JOBID PARTITION            NAME     USER    STATE       TIME TIME_LIMI  NODES NODELIST(REASON)
 5112086_1     workq               1  kortass  RUNNING       0:04      3:00      1 nid00072
5112087_11     workq               1  kortass  RUNNING       0:04      3:00      1 nid00217
 5112086_2     workq               1  kortass  RUNNING       0:04      3:00      1 nid00215
 5112086_3     workq               1  kortass  RUNNING       0:04      3:00      1 nid00360
 5112086_4     workq               1  kortass  RUNNING       0:04      3:00      1 nid00867
 5112086_5     workq               1  kortass  RUNNING       0:04      3:00      1 nid01590
 5112086_6     workq               1  kortass  RUNNING       0:04      3:00      1 nid06900
 5112086_7     workq               1  kortass  RUNNING       0:04      3:00      1 nid07182
 5112086_8     workq               1  kortass  RUNNING       0:04      3:00      1 nid07653
 5112086_9     workq               1  kortass  RUNNING       0:04      3:00      1 nid00149
5112086_10     workq               1  kortass  RUNNING       0:04      3:00      1 nid00150
5112087_12     workq               1  kortass  RUNNING       0:04      3:00      1 nid00218
5112087_13     workq               1  kortass  RUNNING       0:04      3:00      1 nid00347
5112087_14     workq               1  kortass  RUNNING       0:04      3:00      1 nid00348
5112087_15     workq               1  kortass  RUNNING       0:04      3:00      1 nid01049
5112087_16     workq               1  kortass  RUNNING       0:04      3:00      1 nid01050
5112087_17     workq               1  kortass  RUNNING       0:04      3:00      1 nid01067
5112087_18     workq               1  kortass  RUNNING       0:04      3:00      1 nid01068
5112087_19     workq               1  kortass  RUNNING       0:04      3:00      1 nid01085
5112087_20     workq               1  kortass  RUNNING       0:04      3:00      1 nid01086
> squeue -u $USER
Tue Mar 13 00:49:21 2018
     JOBID PARTITION            NAME     USER    STATE       TIME TIME_LIMI  NODES NODELIST(REASON)
 5112086_1     workq               1  kortass  RUNNING       0:05      3:00      1 nid00072
5112087_11     workq               1  kortass  RUNNING       0:05      3:00      1 nid00217
 5112086_2     workq               1  kortass  RUNNING       0:05      3:00      1 nid00215
 5112086_3     workq               1  kortass  RUNNING       0:05      3:00      1 nid00360
 5112086_4     workq               1  kortass  RUNNING       0:05      3:00      1 nid00867
 5112086_5     workq               1  kortass  RUNNING       0:05      3:00      1 nid01590
 5112086_6     workq               1  kortass  RUNNING       0:05      3:00      1 nid06900
 5112086_7     workq               1  kortass  RUNNING       0:05      3:00      1 nid07182
 5112086_8     workq               1  kortass  RUNNING       0:05      3:00      1 nid07653
 5112086_9     workq               1  kortass  RUNNING       0:05      3:00      1 nid00149
5112086_10     workq               1  kortass  RUNNING       0:05      3:00      1 nid00150
5112087_12     workq               1  kortass  RUNNING       0:05      3:00      1 nid00218
5112087_13     workq               1  kortass  RUNNING       0:05      3:00      1 nid00347
5112087_14     workq               1  kortass  RUNNING       0:05      3:00      1 nid00348
5112087_15     workq               1  kortass  RUNNING       0:05      3:00      1 nid01049
5112087_16     workq               1  kortass  RUNNING       0:05      3:00      1 nid01050
5112087_17     workq               1  kortass  RUNNING       0:05      3:00      1 nid01067
5112087_18     workq               1  kortass  RUNNING       0:05      3:00      1 nid01068
5112087_19     workq               1  kortass  RUNNING       0:05      3:00      1 nid01085
5112087_20     workq               1  kortass  RUNNING       0:05      3:00      1 nid01086
> squeue -u $USER
Tue Mar 13 00:49:22 2018
     JOBID PARTITION            NAME     USER    STATE       TIME TIME_LIMI  NODES NODELIST(REASON)
 5112086_1     workq               1  kortass  RUNNING       0:06      3:00      1 nid00072
5112087_11     workq               1  kortass  RUNNING       0:06      3:00      1 nid00217
 5112086_2     workq               1  kortass  RUNNING       0:06      3:00      1 nid00215
 5112086_3     workq               1  kortass  RUNNING       0:06      3:00      1 nid00360
 5112086_4     workq               1  kortass  RUNNING       0:06      3:00      1 nid00867
 5112086_5     workq               1  kortass  RUNNING       0:06      3:00      1 nid01590
 5112086_6     workq               1  kortass  RUNNING       0:06      3:00      1 nid06900
 5112086_7     workq               1  kortass  RUNNING       0:06      3:00      1 nid07182
 5112086_8     workq               1  kortass  RUNNING       0:06      3:00      1 nid07653
 5112086_9     workq               1  kortass  RUNNING       0:06      3:00      1 nid00149
5112086_10     workq               1  kortass  RUNNING       0:06      3:00      1 nid00150
5112087_12     workq               1  kortass  RUNNING       0:06      3:00      1 nid00218
5112087_13     workq               1  kortass  RUNNING       0:06      3:00      1 nid00347
5112087_14     workq               1  kortass  RUNNING       0:06      3:00      1 nid00348
5112087_15     workq               1  kortass  RUNNING       0:06      3:00      1 nid01049
5112087_16     workq               1  kortass  RUNNING       0:06      3:00      1 nid01050
5112087_17     workq               1  kortass  RUNNING       0:06      3:00      1 nid01067
5112087_18     workq               1  kortass  RUNNING       0:06      3:00      1 nid01068
5112087_19     workq               1  kortass  RUNNING       0:06      3:00      1 nid01085
5112087_20     workq               1  kortass  RUNNING       0:06      3:00      1 nid01086
> squeue -u $USER
Tue Mar 13 00:49:23 2018
     JOBID PARTITION            NAME     USER    STATE       TIME TIME_LIMI  NODES NODELIST(REASON)
 5112086_1     workq               1  kortass  RUNNING       0:07      3:00      1 nid00072
5112087_11     workq               1  kortass  RUNNING       0:07      3:00      1 nid00217
 5112086_2     workq               1  kortass  RUNNING       0:07      3:00      1 nid00215
 5112086_3     workq               1  kortass  RUNNING       0:07      3:00      1 nid00360
 5112086_4     workq               1  kortass  RUNNING       0:07      3:00      1 nid00867
 5112086_5     workq               1  kortass  RUNNING       0:07      3:00      1 nid01590
 5112086_6     workq               1  kortass  RUNNING       0:07      3:00      1 nid06900
 5112086_7     workq               1  kortass  RUNNING       0:07      3:00      1 nid07182
 5112086_8     workq               1  kortass  RUNNING       0:07      3:00      1 nid07653
 5112086_9     workq               1  kortass  RUNNING       0:07      3:00      1 nid00149
5112086_10     workq               1  kortass  RUNNING       0:07      3:00      1 nid00150
5112087_12     workq               1  kortass  RUNNING       0:07      3:00      1 nid00218
5112087_13     workq               1  kortass  RUNNING       0:07      3:00      1 nid00347
5112087_14     workq               1  kortass  RUNNING       0:07      3:00      1 nid00348
5112087_15     workq               1  kortass  RUNNING       0:07      3:00      1 nid01049
5112087_16     workq               1  kortass  RUNNING       0:07      3:00      1 nid01050
5112087_17     workq               1  kortass  RUNNING       0:07      3:00      1 nid01067
5112087_18     workq               1  kortass  RUNNING       0:07      3:00      1 nid01068
5112087_19     workq               1  kortass  RUNNING       0:07      3:00      1 nid01085
5112087_20     workq               1  kortass  RUNNING       0:07      3:00      1 nid01086
> squeue -u $USER
Tue Mar 13 00:49:37 2018
     JOBID PARTITION            NAME     USER    STATE       TIME TIME_LIMI  NODES NODELIST(REASON)
5112106_21     workq               1  kortass  RUNNING       0:08      3:00      1 nid00072
5112106_22     workq               1  kortass  RUNNING       0:08      3:00      1 nid01335
5112106_23     workq               1  kortass  RUNNING       0:08      3:00      1 nid01336
5112106_24     workq               1  kortass  RUNNING       0:08      3:00      1 nid01352
5112106_25     workq               1  kortass  RUNNING       0:08      3:00      1 nid01353
5112106_26     workq               1  kortass  RUNNING       0:08      3:00      1 nid01502
5112106_27     workq               1  kortass  RUNNING       0:08      3:00      1 nid01503
5112106_28     workq               1  kortass  RUNNING       0:08      3:00      1 nid06009
5112106_29     workq               1  kortass  RUNNING       0:08      3:00      1 nid06010
5112106_30     workq               1  kortass  RUNNING       0:08      3:00      1 nid06011
5112116_31     workq               1  kortass  RUNNING       0:01      3:00      1 nid00215
5112116_32     workq               1  kortass  RUNNING       0:01      3:00      1 nid00360
5112116_33     workq               1  kortass  RUNNING       0:01      3:00      1 nid00867
5112116_34     workq               1  kortass  RUNNING       0:01      3:00      1 nid01590
5112116_35     workq               1  kortass  RUNNING       0:01      3:00      1 nid06900
5112116_36     workq               1  kortass  RUNNING       0:00      3:00      1 nid07182
5112116_37     workq               1  kortass  RUNNING       0:00      3:00      1 nid07653
5112116_38     workq               1  kortass  RUNNING       0:00      3:00      1 nid00149
5112116_39     workq               1  kortass  RUNNING       0:00      3:00      1 nid00150
5112116_40     workq               1  kortass  RUNNING       0:00      3:00      1 nid00217
> squeue -u $USER
Tue Mar 13 00:49:59 2018
     JOBID PARTITION            NAME     USER    STATE       TIME TIME_LIMI  NODES NODELIST(REASON)
5112116_34     workq               1  kortass  RUNNING       0:23      3:00      1 nid01590
5112116_40     workq               1  kortass  RUNNING       0:22      3:00      1 nid00217
5112136_51     workq               1  kortass  RUNNING       0:10      3:00      1 nid00150
5112136_52     workq               1  kortass  RUNNING       0:10      3:00      1 nid00215
5112136_53     workq               1  kortass  RUNNING       0:10      3:00      1 nid00360
5112136_54     workq               1  kortass  RUNNING       0:10      3:00      1 nid01335
5112136_55     workq               1  kortass  RUNNING       0:10      3:00      1 nid01336
5112136_56     workq               1  kortass  RUNNING       0:10      3:00      1 nid01352
5112136_57     workq               1  kortass  RUNNING       0:10      3:00      1 nid01353
5112136_58     workq               1  kortass  RUNNING       0:10      3:00      1 nid01502
5112136_59     workq               1  kortass  RUNNING       0:10      3:00      1 nid01503
5112136_60     workq               1  kortass  RUNNING       0:10      3:00      1 nid06009
5112146_61     workq               1  kortass  RUNNING       0:02      3:00      1 nid00072
5112146_62     workq               1  kortass  RUNNING       0:02      3:00      1 nid00149
5112146_63     workq               1  kortass  RUNNING       0:02      3:00      1 nid00218
5112146_64     workq               1  kortass  RUNNING       0:02      3:00      1 nid00867
5112146_65     workq               1  kortass  RUNNING       0:02      3:00      1 nid06900
5112146_66     workq               1  kortass  RUNNING       0:02      3:00      1 nid07182
5112146_67     workq               1  kortass  RUNNING       0:02      3:00      1 nid07653
5112146_68     workq               1  kortass  RUNNING       0:02      3:00      1 nid00347
5112146_69     workq               1  kortass  RUNNING       0:02      3:00      1 nid00348
5112146_70     workq               1  kortass  RUNNING       0:02      3:00      1 nid01049
> squeue -l -u $USER
Tue Mar 13 00:51:44 2018
               JOBID PARTITION                 NAME     USER    STATE       TIME TIME_LIMI  NODES NODELIST(REASON)
         5112266_181     workq                    1  kortass  RUNNING       0:05      3:00      1 nid00072
         5112266_182     workq                    1  kortass  RUNNING       0:05      3:00      1 nid00215
         5112266_183     workq                    1  kortass  RUNNING       0:05      3:00      1 nid00217
         5112266_184     workq                    1  kortass  RUNNING       0:05      3:00      1 nid00360
         5112266_185     workq                    1  kortass  RUNNING       0:05      3:00      1 nid01068
         5112266_186     workq                    1  kortass  RUNNING       0:05      3:00      1 nid01086
         5112266_187     workq                    1  kortass  RUNNING       0:05      3:00      1 nid01335
         5112266_188     workq                    1  kortass  RUNNING       0:05      3:00      1 nid01502
         5112266_189     workq                    1  kortass  RUNNING       0:05      3:00      1 nid01590
         5112266_190     workq                    1  kortass  RUNNING       0:05      3:00      1 nid06900
         5112276_191     workq                    1  kortass  RUNNING       0:02      3:00      1 nid00218
         5112276_192     workq                    1  kortass  RUNNING       0:02      3:00      1 nid00867
         5112276_193     workq                    1  kortass  RUNNING       0:02      3:00      1 nid01067
         5112276_194     workq                    1  kortass  RUNNING       0:02      3:00      1 nid01085
         5112276_195     workq                    1  kortass  RUNNING       0:02      3:00      1 nid01336
         5112276_196     workq                    1  kortass  RUNNING       0:02      3:00      1 nid01503
         5112276_197     workq                    1  kortass  RUNNING       0:02      3:00      1 nid07182
         5112276_198     workq                    1  kortass  RUNNING       0:02      3:00      1 nid07653
         5112276_199     workq                    1  kortass  RUNNING       0:02      3:00      1 nid00149
         5112276_200     workq                    1  kortass  RUNNING       0:02      3:00      1 nid00150


> squeue -l -u $USER
Tue Mar 13 00:51:54 2018
               JOBID PARTITION                 NAME     USER    STATE       TIME TIME_LIMI  NODES NODELIST(REASON)
         5112266_186     workq                    1  kortass  RUNNING       0:15      3:00      1 nid01086
         5112276_192     workq                    1  kortass  RUNNING       0:12      3:00      1 nid00867
         5112276_193     workq                    1  kortass  RUNNING       0:12      3:00      1 nid01067
         5112276_194     workq                    1  kortass  RUNNING       0:12      3:00      1 nid01085
         5112276_195     workq                    1  kortass  RUNNING       0:12      3:00      1 nid01336
         5112276_196     workq                    1  kortass  RUNNING       0:12      3:00      1 nid01503
         5112276_197     workq                    1  kortass  RUNNING       0:12      3:00      1 nid07182
         5112276_198     workq                    1  kortass  RUNNING       0:12      3:00      1 nid07653


> squeue -l -u $USER
Tue Mar 13 00:51:58 2018
               JOBID PARTITION                 NAME     USER    STATE       TIME TIME_LIMI  NODES NODELIST(REASON)
         5112276_194     workq                    1  kortass  RUNNING       0:16      3:00      1 nid01085



> dstat
[MSG  ] step 1-0:1-200                RUNNING   SUCCESS:    0% 	FAILURE:  99% -> [1-193,195-200] 





> dstat
[MSG  ] step 1-0:1-200                RUNNING   SUCCESS:    0% 	FAILURE:  99% -> [1-193,195-200] 


>










> dbatch -J 4 -a 1-2000 --yalla --yalla-parallel-runs=320 --ntasks=1 job_yalla.sh
[INFO ] launch-0!0:job['yalla_parallel_runs']=320
[INFO ] launch-0!0:submitting job 4 (for 1-2000) --> Job # 4-0-1-2000 <-depends-on None




> squeue -u $USER
Tue Mar 13 01:13:19 2018
     JOBID PARTITION            NAME     USER    STATE       TIME TIME_LIMI  NODES NODELIST(REASON)
   5112505     workq               4  kortass  RUNNING       0:02     21:00     11 nid0[5648-5658]



   
> squeue -u $USER
Tue Mar 13 01:13:23 2018
     JOBID PARTITION            NAME     USER    STATE       TIME TIME_LIMI  NODES NODELIST(REASON)
   5112505     workq               4  kortass  RUNNING       0:06     21:00     11 nid0[5648-5658]
> squeue -u $USER
Tue Mar 13 01:13:24 2018
     JOBID PARTITION            NAME     USER    STATE       TIME TIME_LIMI  NODES NODELIST(REASON)
   5112505     workq               4  kortass  RUNNING       0:07     21:00     11 nid0[5648-5658]
> squeue -u $USER
Tue Mar 13 01:13:27 2018
     JOBID PARTITION            NAME     USER    STATE       TIME TIME_LIMI  NODES NODELIST(REASON)
   5112505     workq               4  kortass  RUNNING       0:10     21:00     11 nid0[5648-5658]
> squeue -u $USER
Tue Mar 13 01:13:27 2018
     JOBID PARTITION            NAME     USER    STATE       TIME TIME_LIMI  NODES NODELIST(REASON)
   5112505     workq               4  kortass  RUNNING       0:10     21:00     11 nid0[5648-5658]
> squeue -u $USER
Tue Mar 13 01:13:37 2018
     JOBID PARTITION            NAME     USER    STATE       TIME TIME_LIMI  NODES NODELIST(REASON)
   5112505     workq               4  kortass  RUNNING       0:20     21:00     11 nid0[5648-5658]
> squeue -u $USER
Tue Mar 13 01:13:38 2018
     JOBID PARTITION            NAME     USER    STATE       TIME TIME_LIMI  NODES NODELIST(REASON)
   5112505     workq               4  kortass  RUNNING       0:21     21:00     11 nid0[5648-5658]
> ds
[MSG  ] step 4-0:1-2000               RUNNING   SUCCESS:    0% 	FAILURE:   0% -> [] 
> squeue -u $USER
Tue Mar 13 01:14:19 2018
     JOBID PARTITION            NAME     USER    STATE       TIME TIME_LIMI  NODES NODELIST(REASON)
   5112505     workq               4  kortass  RUNNING       1:02     21:00     11 nid0[5648-5658]
> 


> squeue -u $USER

Tue Mar 13 01:19:30 2018
     JOBID PARTITION            NAME     USER    STATE       TIME TIME_LIMI  NODES NODELIST(REASON)



> dstat
[MSG  ] step 4-0:1-2000               SUCCESS   SUCCESS:  100% 	FAILURE:   0% -> [] 
 
