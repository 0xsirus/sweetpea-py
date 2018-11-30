import operator as op
import pytest

from sweetpea import fully_cross_block, __decode
from sweetpea.primitives import Factor, DerivedLevel, WithinTrial, Transition
from sweetpea.constraints import NoMoreThanKInARow
from sweetpea.logic import to_cnf_tseitin


# Common variables for stroop.
color = Factor("color", ["red", "blue"])
text  = Factor("text",  ["red", "blue"])

con_level  = DerivedLevel("con", WithinTrial(op.eq, [color, text]))
inc_level  = DerivedLevel("inc", WithinTrial(op.ne, [color, text]))
con_factor = Factor("congruent?", [con_level, inc_level])

color_repeats_factor = Factor("color repeats?", [
    DerivedLevel("yes", Transition(op.eq, [color, color])),
    DerivedLevel("no",  Transition(op.ne, [color, color]))
])

text_repeats_factor = Factor("text repeats?", [
    DerivedLevel("yes", Transition(op.eq, [text, text])),
    DerivedLevel("no",  Transition(op.ne, [text, text]))
])

design = [color, text, con_factor]
crossing = [color, text]
blk = fully_cross_block(design, crossing, [])


def test_decode():
    solution = [-1,   2,  -3,   4,   5,  -6,
                -7,   8,   9, -10, -11,  12,
                13, -14, -15,  16, -17,  18,
                19, -20,  21, -22,  23, -24]
    assert __decode(blk, solution) == {
        'color':      ['blue', 'blue', 'red',  'red'],
        'text':       ['blue', 'red',  'blue', 'red'],
        'congruent?': ['con',  'inc',  'inc',  'con']
    }

    solution = [ -1,   2, -3,   4,   5,  -6,
                  7,  -8, -9,  10, -11,  12,
                 13, -14, 15, -16,  17, -18,
                -19,  20, 21, -22, -23,  24]
    assert __decode(blk, solution) == {
        'color':      ['blue', 'red',  'red', 'blue'],
        'text':       ['blue', 'blue', 'red', 'red'],
        'congruent?': ['con',  'inc',  'con', 'inc']
    }

    solution = [-1,   2,   3,  -4,  -5,   6,
                -7,   8,  -9,  10,  11, -12,
                13, -14,  15, -16,  17, -18,
                19, -20, -21,  22, -23,  24]
    assert __decode(blk, solution) == {
        'color':      ['blue', 'blue', 'red', 'red'],
        'text':       ['red',  'blue', 'red', 'blue'],
        'congruent?': ['inc',  'con',  'con', 'inc']
    }

    f1 = Factor("a", ["b", "c", "d"])
    f2 = Factor("e", ["f"])
    f_blk = fully_cross_block([f1, f2], [f1, f2], [])
    solution = [-1,  2, -3, 4,
                -1, -2,  3, 4,
                 1, -2  -3, 4]
    assert __decode(f_blk, solution) == {
        'a': ['c', 'd', 'b'],
        'e': ['f', 'f', 'f']
    }


def test_decode_with_transition():
    block = fully_cross_block([color, text, color_repeats_factor],
                              [color, text],
                              [])

    solution = [ 1,  -2,  3,  -4,
                 5,  -6, -7,   8,   #  17, -18
                -9,  10,  11, -12,  # -19,  20
                -13, 14, -15,  16,  #  21, -22
                17, -18, -19, 20, 21, -22] # color_repeats_factor
    decoded = __decode(block, solution)
    assert decoded['color'] ==          ['red', 'red',  'blue', 'blue']
    assert decoded['text']  ==          ['red', 'blue', 'red',  'blue']
    assert decoded['color repeats?'] == ['',    'yes',  'no',   'yes' ]


    solution = [ 1,  -2,  -3,   4,
                -5,   6,   7,  -8,
                -9,   10, -11,  12,
                 13, -14,  15, -16,
                -17,  18,  19, -20, -21, 22]
    decoded = __decode(block, solution)
    assert decoded['color'] ==          ['red',  'blue', 'blue', 'red']
    assert decoded['text']  ==          ['blue', 'red',  'blue', 'red']
    assert decoded['color repeats?'] == ['',     'no',   'yes',  'no' ]


def test_desugar_with_constraint():
    from sweetpea import __desugar

    constraints = [NoMoreThanKInARow(1, ("congruent?", "con"))]
    blk = fully_cross_block(design, crossing, constraints)

    # This was blowing up with an error.
    __desugar(blk)


def test_desugar_with_factor_constraint():
    from sweetpea import __desugar

    constraints = [NoMoreThanKInARow(1, con_factor)]
    blk = fully_cross_block(design, crossing, constraints)

    __desugar(blk)


def test_desugar_with_derived_transition_levels():
    from sweetpea import __desugar

    color_transition = Factor("color_transition", [
        DerivedLevel("repeat", Transition(op.eq, [color, color])),
        DerivedLevel("switch", Transition(op.ne, [color, color]))
    ])

    design.append(color_transition)
    constraints = [NoMoreThanKInARow(2, color_transition)]
    blk = fully_cross_block(design, crossing, constraints)

    __desugar(blk)
