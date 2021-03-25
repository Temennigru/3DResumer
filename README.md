# 3DResumer
A tool to help you cut gcode files to resume prints. Highly experimental. Requires PySimpleGui to be run. Prebuilts are provided in bin/, but windows thinks the executable is a virus, so you will have to add it to the exceptions in windows defender.

# Instructions
1. Keep the failed print exactly where it stopped. Do not move the bed.
2. Measure the z height of your print by using your printer's control software and getting the nozzle to lightly touch the print (from above, obviously). The software should tell you your current z height.
3. Run this tool with a python 3 interpreter. It will prompt you for the gcode file and your measured z height.
4. The tool will spit out the closest matches for the measured height. Pick one.
5. The tool will cut the gcode and produce a resume gcode file. I suggest you load it into USB stick and plug it to your printer to avoid any extra gcode intermediate software might add.

These instructions should not supercede the normal operation of your printer. Each printer is different and you should be familiar with how to operate yours safely before trying this.

This software is experimental and is provided as-is. Use at your own risk.
