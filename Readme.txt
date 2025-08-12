The code is the LED control communication protocol for optogenetic animal behavior experient and other potential usage based on cyclops LED driver and Motive, software for Optitrack system.

This folder considers three scenarios, the first is to trigger the LED while the target moves into a certain circle region, which you can set the radius and coordinate. The second is periodically generate a Guassian wave of stimulation, which you can adjust the duration and interval. The last but none the least is the upgrade version of the second one, which needs the communcation of .ino file and python to record the target position, time and LED state in real time of Motive. I will describe how to operate these programme in the following part .

Required Softwares:
1.Arduino IDE
2.Python compiler 
3.NatNet SDK
4.Motive

Required Hardwares:
1.Cyclops Driver
2.Suitable LED 
3.Optitrack environment

Note: if you don't have Optitrack env, you can only use the "periodic_stimulation" for Cyclops LED 

This project used Python USB Serial as main connection of the LED driver and Motive, but feel free to develop the communication protocol by other sample mentioned by NatNet. 



