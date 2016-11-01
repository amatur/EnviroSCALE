found=0

i=0
res=$(dmesg | grep -c "FTDI USB Serial Device converter now attached to ttyUSB$i")
if [ $res -eq 1 ]; then
	found=$i
fi

i=1
res=$(dmesg | grep -c "FTDI USB Serial Device converter now attached to ttyUSB$i")
if [ $res -eq 1 ]; then
	found=$i
fi

i=2
res=$(dmesg | grep -c "FTDI USB Serial Device converter now attached to ttyUSB$i")
if [ $res -eq 1 ]; then
	found=$i
fi

i=3
res=$(dmesg | grep -c "FTDI USB Serial Device converter now attached to ttyUSB$i")
if [ $res -eq 1 ]; then
	found=$i
fi

echo $found
