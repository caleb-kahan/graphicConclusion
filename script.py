import mdl
from display import *
from matrix import *
from draw import *

"""======== first_pass( commands ) ==========

  Checks the commands array for any animation commands
  (frames, basename, vary)

  Should set num_frames and basename if the frames
  or basename commands are present

  If vary is found, but frames is not, the entire
  program should exit.

  If frames is found, but basename is not, set name
  to some default value, and print out a message
  with the name being used.
  ==================== """
def first_pass( commands ):

    name = 'snap'
    num_frames = 1

    vary = False
    baseName = False
    frames = False

    for command in commands:
        c = command['op']
        args = command['args']
        if c == "vary":
            vary = True
        elif c == "basename":
            baseName = True
            name = args[0]
        elif c == "frames":
            frames = True
            num_frames = int(args[0])
    if vary and not frames:
        print("SYNTAX ERROR: vary is present while frames is not.")
        return ()
    if frames and not baseName:
        print('WARNING: basename not set.\n basename preset to "anim"')

    return (name, num_frames)

"""======== second_pass( commands ) ==========

  In order to set the knobs for animation, we need to keep
  a seaprate value for each knob for each frame. We can do
  this by using an array of dictionaries. Each array index
  will correspond to a frame (eg. knobs[0] would be the first
  frame, knobs[2] would be the 3rd frame and so on).

  Each index should contain a dictionary of knob values, each
  key will be a knob name, and each value will be the knob's
  value for that frame.

  Go through the command array, and when you find vary, go
  from knobs[0] to knobs[frames-1] and add (or modify) the
  dictionary corresponding to the given knob with the
  appropirate value.
  ===================="""
def second_pass( commands, num_frames ):
    frames = [ {} for i in range(num_frames) ]

    for command in commands:
        c = command['op']
        if c == "vary":
            knob = command['knob']
            args = command['args']

            start_frame = int(args[0])
            end_frame = int(args[1])
            start_val = args[2]
            end_val = args[3]
            if not start_frame < end_frame:
                print("SYNTAX ERROR: start_frame is not before end_frame")
                return
            if not end_frame < num_frames:
                print("SYNTAX ERROR: end_frame occurs after total number of frames")
                return
            current_val = start_val
            change = (end_val - start_val)/(end_frame - start_frame)
            for i in range(start_frame,end_frame+1):
                if knob in frames[i]:
                    print("SYNTAX ERROR: MULTIPLE vary commands for same frame")
                    return
                frames[i][knob] = current_val
                current_val+=change
    return frames


def run(filename):
    """
    This function runs an mdl script
    """
    p = mdl.parseFile(filename)

    if p:
        (commands, symbols) = p
    else:
        print("Parsing failed.")
        return

    view = [0,
            0,
            1];
    ambient = [50,
               50,
               50]
    light = [[0.5,
              0.75,
              1],
             [255,
              255,
              255]]

    color = [0, 0, 0]
    symbols['.white'] = ['constants',
                         {'red': [0.2, 0.5, 0.5],
                          'green': [0.2, 0.5, 0.5],
                          'blue': [0.2, 0.5, 0.5]}]
    reflect = '.white'

    try:
        (basename, num_frames) = first_pass(commands)
    except ValueError:
        print("MDL compiling failed")
        return

    frames = second_pass(commands, num_frames)
    if not frames:
        print("MDL compiling failed")
        return

    for i in range(num_frames):

        for knob in frames[i]:
            symbols[knob] = ['knob',frames[i][knob]]

        tmp = new_matrix()
        ident( tmp )
        stack = [ [x[:] for x in tmp] ]
        screen = new_screen()
        zbuffer = new_zbuffer()
        tmp = []
        step_3d = 100
        consts = ''
        coords = []
        coords1 = []

        for command in commands:
            c = command['op']
            args = command['args']

            knob_value = 1
            if 'knob' in command:
                knob_value = symbols[command['knob']][1]

            if c == 'box':
                if command['constants']:
                    reflect = command['constants']
                add_box(tmp,
                        args[0], args[1], args[2],
                        args[3], args[4], args[5])
                matrix_mult( stack[-1], tmp )
                draw_polygons(tmp, screen, zbuffer, view, ambient, light, symbols, reflect)
                tmp = []
                reflect = '.white'
            elif c == 'sphere':
                if command['constants']:
                    reflect = command['constants']
                add_sphere(tmp,
                           args[0], args[1], args[2], args[3], step_3d)
                matrix_mult( stack[-1], tmp )
                draw_polygons(tmp, screen, zbuffer, view, ambient, light, symbols, reflect)
                tmp = []
                reflect = '.white'
            elif c == 'torus':
                if command['constants']:
                    reflect = command['constants']
                add_torus(tmp,
                          args[0], args[1], args[2], args[3], args[4], step_3d)
                matrix_mult( stack[-1], tmp )
                draw_polygons(tmp, screen, zbuffer, view, ambient, light, symbols, reflect)
                tmp = []
                reflect = '.white'
            elif c == 'line':
                add_edge(tmp,
                         args[0], args[1], args[2], args[3], args[4], args[5])
                matrix_mult( stack[-1], tmp )
                draw_lines(tmp, screen, zbuffer, color)
                tmp = []
            elif c == 'move':
                tmp = make_translate(args[0]*knob_value, args[1]*knob_value, args[2]*knob_value)
                matrix_mult(stack[-1], tmp)
                stack[-1] = [x[:] for x in tmp]
                tmp = []
            elif c == 'scale':
                tmp = make_scale(args[0]*knob_value, args[1]*knob_value, args[2]*knob_value)
                matrix_mult(stack[-1], tmp)
                stack[-1] = [x[:] for x in tmp]
                tmp = []
            elif c == 'rotate':
                theta = args[1] * (math.pi/180) * knob_value
                if args[0] == 'x':
                    tmp = make_rotX(theta)
                elif args[0] == 'y':
                    tmp = make_rotY(theta)
                else:
                    tmp = make_rotZ(theta)
                matrix_mult( stack[-1], tmp )
                stack[-1] = [ x[:] for x in tmp]
                tmp = []
            elif c == 'push':
                stack.append([x[:] for x in stack[-1]] )
            elif c == 'pop':
                stack.pop()
            elif c == 'display':
                if num_frames == 1:
                    display(screen)
            elif c == 'save':
                if num_frames == 1:
                    save_extension(screen, args[0])
            # end operation loop
        name = "anim/" + basename + (str(i)).rjust(3,'0')
        save_extension(screen,name)
    make_animation(basename)
