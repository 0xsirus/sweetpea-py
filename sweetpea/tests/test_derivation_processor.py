import operator as op
import pytest

from itertools import permutations

from sweetpea.primitives import Factor, DerivedLevel, WithinTrial, Transition, Window
from sweetpea.constraints import NoMoreThanKInARow, Derivation
from sweetpea.derivation_processor import DerivationProcessor
from sweetpea.blocks import Block
from sweetpea import fully_cross_block


color = Factor("color", ["red", "blue"])
text  = Factor("text",  ["red", "blue"])

con_level  = DerivedLevel("con", WithinTrial(op.eq, [color, text]))
inc_level  = DerivedLevel("inc", WithinTrial(op.ne, [color, text]))
con_factor = Factor("congruent?", [con_level, inc_level])

color_repeats_factor = Factor("repeated color?", [
    DerivedLevel("yes", Transition(op.eq, [color, color])),
    DerivedLevel("no",  Transition(op.ne, [color, color]))
])

text_repeats_factor = Factor("repeated text?", [
    DerivedLevel("yes", Transition(op.eq, [text, text])),
    DerivedLevel("no",  Transition(op.ne, [text, text]))
])

design = [color, text, con_factor]
crossing = [color, text]
blk = fully_cross_block(design, crossing, [])


def two_con(i, n, t):
    return (i == "1" and n == "I" and t == "two") or \
        (i == "1" and n == "II" and t == "one") or \
        (i == "2" and n == "I" and t == "one") or \
        (i == "2" and n == "I" and t == "two") or \
        (i == "2" and n == "II" and t == "one") or \
        (i == "1" and n == "II" and t == "two")

def two_not_con(i, n, t):
    return not two_con(i, n, t)

def test_generate_derivations_within_trial():
    assert DerivationProcessor.generate_derivations(blk) == [
        Derivation(4, [[0, 2], [1, 3]]),
        Derivation(5, [[0, 3], [1, 2]])]

    integer = Factor("integer", ["1", "2"])
    numeral = Factor("numeral", ["I", "II"])
    text = Factor("text", ["one", "two"])

    twoConLevel = DerivedLevel("twoCon", WithinTrial(two_con, [integer, numeral, text]))
    twoNotConLevel = DerivedLevel("twoNotCon", WithinTrial(two_not_con, [integer, numeral, text]))
    twoConFactor = Factor("twoCon?", [twoConLevel, twoNotConLevel])

    one_two_design = [integer, numeral, text, twoConFactor]
    one_two_crossing = [integer, numeral, text]

    assert DerivationProcessor.generate_derivations(
        fully_cross_block(one_two_design, one_two_crossing, [])) == [
        Derivation(6, [[0, 2, 5], [0, 3, 4], [0, 3, 5], [1, 2, 4], [1, 2, 5], [1, 3, 4]]),
        Derivation(7, [[0, 2, 4], [1, 3, 5]])]


@pytest.mark.parametrize('design',
    [[color, text, color_repeats_factor],
     [color, color_repeats_factor, text],
     [color_repeats_factor, color, text]])
def test_generate_derivations_transition(design):
    block = fully_cross_block(design, [color, text], [])

    assert DerivationProcessor.generate_derivations(block) == [
        Derivation(16, [[0, 4], [1, 5]]),
        Derivation(17, [[0, 5], [1, 4]])
    ]


@pytest.mark.parametrize('design',
    [[color, text, color_repeats_factor, text_repeats_factor],
     [color, color_repeats_factor, text_repeats_factor, text],
     [color_repeats_factor, color, text_repeats_factor, text],
     [color_repeats_factor, text_repeats_factor, color, text]])
def test_generate_derivations_with_multiple_transitions(design):
    block = fully_cross_block([color, text, color_repeats_factor, text_repeats_factor],
                              [color, text],
                              [])

    assert DerivationProcessor.generate_derivations(block) == [
        Derivation(16, [[0, 4], [1, 5]]),
        Derivation(17, [[0, 5], [1, 4]]),
        Derivation(22, [[2, 6], [3, 7]]),
        Derivation(23, [[2, 7], [3, 6]])
    ]


def test_shift_window():
    assert DerivationProcessor.shift_window([[0, 0], [1, 1]], WithinTrial(lambda x: x, None), 0) == [[0, 0], [1, 1]]
    assert DerivationProcessor.shift_window([[0, 0], [1, 1]], Transition(lambda x: x, None), 4) == [[0, 4], [1, 5]]
    assert DerivationProcessor.shift_window([[0, 2, 4], [1, 3, 5]], Window(lambda x: x, [1, 2], 3), 6) == [[0, 8, 16], [1, 9, 17]]
    assert DerivationProcessor.shift_window([[1, 1, 1, 1], [2, 2, 2, 2]], Window(lambda x: x, [1, 2], 4), 10) == \
        [[1, 11, 21, 31], [2, 12, 22, 32]]


def __get_simple_task_switching_block() -> Block:
    color  = Factor("color",  ["red", "blue", "green"])
    motion = Factor("motion", ["up", "down"])
    task   = Factor("task",   ["color", "motion"])

    # Response Definition
    def response_left(task, color, motion):
        return (task == "color"  and color  == "red") or \
            (task == "motion" and motion == "up")

    def response_right(task, color, motion):
        return not response_left(task, color, motion)

    response = Factor("response", [
        DerivedLevel("left",  WithinTrial(response_left,  [task, color, motion])),
        DerivedLevel("right", WithinTrial(response_right, [task, color, motion]))
    ])

    response_transition = Factor("response transition", [
        DerivedLevel("repeat", Transition(op.eq, [response, response])),
        DerivedLevel("switch", Transition(op.ne, [response, response]))
    ])

    return fully_cross_block([color, motion, task, response, response_transition],
                             [color, motion, task],
                             [])


def test_generate_derivations_with_transition_that_depends_on_derived_levels():
    block = __get_simple_task_switching_block()
    derivations = DerivationProcessor.generate_derivations(block)

    assert Derivation(108, [[7, 16], [8, 17]]) in derivations
    assert Derivation(109, [[7, 17], [8, 16]]) in derivations