stoprunning=0
while [ "$stoprunning" -eq "0" ]
do
   python main.py "$@"

   ecode=$?

   if [ "$ecode" -eq "0" ]
   then
    stoprunning=1
   fi
done