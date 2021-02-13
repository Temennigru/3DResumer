import re
import textwrap
import sys

# check version
if sys.version_info[0] < 3:
    raise Exception("Must be run with Python 3")

def write_intro(restart_z_val, hotend_temp, bed_temp, extrusion_mode):
    intro_block = ""

    # TODO: Make these settings dynamic
    # Add print settings
    intro_block += """
    M201 X3000 Y3000 Z100 E10000 ; sets maximum accelerations, mm/sec^2
    M203 X150 Y150 Z50 E25 ; sets maximum feedrates, mm/sec
    M204 P1000 R1000 T1000 ; sets acceleration (P, T) and retract acceleration (R), mm/sec^2
    M205 X10.00 Y10.00 Z0.20 E2.50 ; sets the jerk limits, mm/sec
    M205 S0 T0 ; sets the minimum extruding and travel feed rate, mm/sec
    M107"""

    intro_block += """
    ;Start GCode begin"""

    # TODO: Add other extrusion modes
    # TODO: Make extrusion mode an enum
    # TODO: Make absolute positioning optional
    # Add extrusion mode
    intro_block += """
    M82 ;absolute extrusion mode
    """ if extrusion_mode == "absolute" else """
    M83 ;relative extrusion mode
    """

    intro_block += """
    G21 ; set units to millimeters
    G90 ; use absolute coordinates
    M140 S""" + str(bed_temp - 10) + """  ;Start Warming Bed
    M104 S160 ;Preheat Nozzle
    G28 X Y Z ; home all axes
    G90 ;absolute positioning
    G1 X-10 Y-10 F3000 ;Move outside build plate
    G1 Z""" + "{:.3f}".format(restart_z_val + 0.5) + """ F3000 ;Move to Z+0.5 to avoid crashing during restart
    M190 S""" + str(bed_temp) + """  ;Wait For Bed Temperature
    M109 S""" + str(hotend_temp) + """ ;Wait for Hotend Temperature
    G92 E0 ;Set E to 0
    ;Start GCode end
    G1 F3600 E-2 ;Slight retraction

    ;Filament code
    """
    return textwrap.dedent (intro_block)

def readlines(path):
    lines = []
    with open(path) as file:
        lines = [line.strip() for line in file]

    return lines

def write_output(string, path, kind = "w"):
    with open(path, kind) as file:
        file.write(string)

def debug_print(l):
    if type(l) == str:
        write_output(l + "\n", "output.json", "a")
    else:
        string = ""
        for i in l:
            string += str(i) + "\n"
        write_output(string, "output.json", "a")

# Steps to find z:
# 1- for each line check if it's a z move
# 2- store each z move and its temperature in a list
# 3- move through list backwards
# 4- check if each z is a z hop by comparing it to lowest value found
# 5- store best and second best z value (to ask user whether
#    they want the upper or lower z)
# Steps to find temp:
# 1- store temp for each line
# 2- save last temp stored when reaching a z move

# TODO: auto-read settings from gcode, like positioning and extrusion modes
# TODO: implement filament code cutoff

# Filament code parser:
# Finds the 2 closest z values (likely one above and one below
# the measured value) and the nozzle and bed temperature at those points.
# gcode: an in-memory list of the lines in the gcode file
# z_val: the measured z value where the print stopped
# filament_code_cutoff: whether there is something that indicates the begining
#                       of filament code. Useful for when the slicer puts
#                       something like ;Filament code before the filament code
#                       to avoid false positives in the first few lines,
#                       especially if your print stopped early on.
# Returns a list of two z moves in the following format:
# {
#     "line": index,
#     "coordinates": float(match_z_move.group(1)),
#     "bed_temp": bed_temp,
#     "hotend_temp": hotend_temp,
#     "z_hop": False|True,
# }
def parse(gcode, z_val, filament_code_cutoff = ""):

    extrusion_mode = "absolute"
    z_move_regex = re.compile(" *G1[^;]*Z([0-9]+(?:\\.[0-9]+)).*")
    bed_temp_regex = re.compile(" *M(?:140|190)[^;]*S([0-9]+).*")
    hotend_temp_regex = re.compile(" *M(?:104|109)[^;]*S([0-9]+).*")

    hotend_temp = None
    bed_temp = None
    z_moves = []

    # Populate z-moves list
    for index in range(len(gcode)):
        line = gcode[index]
        match_z_move = z_move_regex.match(line)
        match_bed_temp = bed_temp_regex.match(line)
        match_hotend_temp = hotend_temp_regex.match(line)

        if line.strip().startswith(";"):
            continue
        elif match_z_move:
            z_moves.append(
                {
                    "line": index,
                    "coordinates": float(match_z_move.group(1)),
                    "bed_temp": bed_temp,
                    "hotend_temp": hotend_temp,
                    "z_hop": False,
                }
            )
        elif match_bed_temp:
            bed_temp = float(match_bed_temp.group(1))
        elif match_hotend_temp:
            hotend_temp = float(match_hotend_temp.group(1))
    # end loop


    # Now go through the list backwards to remove z hops and find 2 closest zs
    lowest_z = None
    closest_z = [None, None]
    for index in reversed(range(len(z_moves))):
        current_z = z_moves[index]["coordinates"]
        # if new low z re-set low z
        if lowest_z == None or current_z <= lowest_z :
            lowest_z = current_z
        # if z is higher than other zs after it, this is a z hop. Ignore it.
        else:
            z_moves[index]["z_hop"] = True
            continue

        # save values for convenience

        closest_z_coords = None if closest_z[0] == None else closest_z[0]["coordinates"]
        second_closest_z_coords = None if closest_z[1] == None else closest_z[1]["coordinates"]

        # this is not a z_hop, compare it to closest zs
        # no value stored, store one
        if closest_z_coords == None:
            closest_z[0] = z_moves[index]

        # if current difference is less than stored difference, move
        elif abs(current_z - z_val) < abs(closest_z_coords - z_val):
            # first make the closest be the second closest
            closest_z[1] = closest_z[0]
            # save current as closest
            closest_z[0] = z_moves[index]

        # shouldn't happen, but better to cover our bases
        elif second_closest_z_coords == None:
            closest_z[1] = z_moves[index]

        # if it's equal, replace, since we want the first one in the file
        elif current_z == closest_z_coords:
            closest_z[0] = z_moves[index]

        # replace the second closest if it's the same. See the next case
        # to understand when this might come up
        elif current_z == second_closest_z_coords:
            closest_z[1] = z_moves[index]

        # not closest, but better than second closest.
        # This can happen when current z passes z_val,
        # and it's not closer than the value above z_val.
        # for example:
        # z_val = 40.8
        # G1 Z40.0
        # <- z_val goes here
        # G1 Z41.0
        # when it reaches Z=40, z_val is closer to 41, but 40 is second best
        elif abs(current_z - z_val) < abs(second_closest_z_coords - z_val):
            closest_z[1] = z_moves[index]
    # end loop

    return closest_z

def write_resume_gcode(gcode, z_choice, output_file):
    output = [ write_intro(
        restart_z_val=z_choice["coordinates"],
        hotend_temp=z_choice["hotend_temp"],
        bed_temp=z_choice["bed_temp"],
        extrusion_mode="absolute") ]

    output += gcode[z_choice["line"]:]

    write_output("\n".join(output), output_file)


# TODO: add exec options
# TODO: add gui

gcode = readlines(input("file: "))
z_val = float(input("measured z: "))
closest_z = parse(gcode, z_val)

z_choice = int(input("choose z:\n 0: {}\n 1: {}\nchoice: "
                     .format(str(closest_z[0]["coordinates"]), str(closest_z[1]["coordinates"]))))

if (z_choice != 0 and z_choice != 1):
    print("Invalid selection")
    exit()

output_file = input("output file: ")

print("cutting gcode in position {}".format(closest_z[z_choice]))

write_resume_gcode(gcode, closest_z[z_choice], output_file)

print("resume gcode written to {}".format(output_file))
