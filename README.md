# 3DResumer
A tool to help you cut gcode files to resume prints


# Instructions
1- Keep the failed print exactly where it stopped. Do not move the bed.
2- Measure the z height of your print by using your printer's control and getting the nozzle to touch the print
3- Run this tool with a python 3 interpreter. It will prompt you for the gcode file and your measured z height.
4- The tool will spit out the 2 best matches for the measured height. Pick one.
5- The tool will cut the gcode and produce a resume gcode file. I suggest you load it into USB stick and plug it to your printer to avoid any extra gcode intermediate software might add.
