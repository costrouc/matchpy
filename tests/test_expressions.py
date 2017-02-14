# -*- coding: utf-8 -*-
import inspect
import itertools

import pytest
from multiset import Multiset

from matchpy.expressions.expressions import (Arity, Operation, Symbol, SymbolWildcard, Variable, Wildcard, Expression)
from matchpy.expressions.constraints import MultiConstraint
from .utils import MockConstraint
from .common import *

constraint1 = MockConstraint(True)
constraint2 = MockConstraint(True)

both_constraints = MultiConstraint.create(constraint1, constraint2)

SIMPLE_EXPRESSIONS = [
    a,
    b,
    f(a, b),
    x_,
    ___,
    Variable('x', f(_)),
    s_,
    _s,
]


class TestExpression:
    @pytest.mark.parametrize(
        '   expression,                                                         simplified',
        [
            (f_i(a),                                                            a),
            (f_i(a, b),                                                         f_i(a, b)),
            (f_i(_),                                                            _),
            (f_i(___),                                                          f_i(___)),
            (f_i(__),                                                           f_i(__)),
            (f_i(x_),                                                           x_),
            (f_i(x___),                                                         f_i(x___)),
            (f_i(x__),                                                          f_i(x__)),
            (f_a(f_a(a)),                                                       f_a(a)),
            (f_a(f_a(a, b)),                                                    f_a(a, b)),
            (f_a(a, f_a(b)),                                                    f_a(a, b)),
            (f_a(f_a(a), b),                                                    f_a(a, b)),
            (f_a(f(a)),                                                         f_a(f(a))),
            (f_c(a, b),                                                         f_c(a, b)),
            (f_c(b, a),                                                         f_c(a, b)),
            (f_a(a, f_a(b, constraint=constraint1)),                            f_a(a, b, constraint=constraint1)),
            (f_a(a, f_a(b, constraint=constraint1), constraint=constraint2),    f_a(a, b, constraint=both_constraints)),
        ]
    )  # yapf: disable
    def test_operation_simplify(self, expression, simplified):
        assert expression == simplified

    @pytest.mark.parametrize(
        '   operation,                                              operands,   expected_error',
        [
            (Operation.new('f', Arity.unary),                       [],         ValueError),
            (Operation.new('f', Arity.unary),                       [a, b],     ValueError),
            (Operation.new('f', Arity.variadic),                    [],         None),
            (Operation.new('f', Arity.variadic),                    [a],        None),
            (Operation.new('f', Arity.variadic),                    [a, b],     None),
            (Operation.new('f', Arity.binary, associative=True),    [a, a, b],  ValueError),
            (Operation.new('f', Arity.binary),                      [x_, x___], ValueError),
            (Operation.new('f', Arity.binary),                      [x_, x_],   None),
        ]
    )  # yapf: disable
    def test_operation_errors(self, operation, operands, expected_error):
        if expected_error is not None:
            with pytest.raises(expected_error):
                operation(*operands)
        else:
            _ = operation(*operands)

    @pytest.mark.parametrize(
        '   expression,     is_constant',
        [
            (a,             True),
            (x_,            False),
            (_,             False),
            (f(a),          True),
            (f(a, b),       True),
            (f(x_),         False),
        ]
    )  # yapf: disable
    def test_is_constant(self, expression, is_constant):
        assert expression.is_constant == is_constant

    @pytest.mark.parametrize(
        '   expression,     is_syntactic',
        [
            (a,             True),
            (x_,            True),
            (_,             True),
            (x___,          False),
            (___,           False),
            (x__,           False),
            (__,            False),
            (f(a),          True),
            (f(a, b),       True),
            (f(x_),         True),
            (f(x__),        False),
            (f_a(a),        False),
            (f_a(a, b),     False),
            (f_a(x_),       False),
            (f_a(x__),      False),
            (f_c(a),        False),
            (f_c(a, b),     False),
            (f_c(x_),       False),
            (f_c(x__),      False),
            (f_ac(a),       False),
            (f_ac(a, b),    False),
            (f_ac(x_),      False),
            (f_ac(x__),     False),
        ]
    )  # yapf: disable
    def test_is_syntactic(self, expression, is_syntactic):
        assert expression.is_syntactic == is_syntactic

    @pytest.mark.parametrize(
        '   expression,         is_linear',
        [
            (a,                 True),
            (x_,                True),
            (_,                 True),
            (f(a),              True),
            (f(a, b),           True),
            (f(x_),             True),
            (f(x_, x_),         False),
            (f(x_, y_),         True),
            (f(x_, _),          True),
            (f(_, _),           True),
            (f(x_, f(x_)),      False),
            (f(x_, a, f(x_)),   False),
        ]
    )  # yapf: disable
    def test_is_linear(self, expression, is_linear):
        assert expression.is_linear == is_linear

    @pytest.mark.parametrize(
        '   expression,         symbols',
        [
            (a,                 ['a']),
            (x_,                []),
            (_,                 []),
            (f(a),              ['a', 'f']),
            (f(a, b),           ['a', 'b', 'f']),
            (f(x_),             ['f']),
            (f(a, a),           ['a', 'a', 'f']),
            (f(f(a), f(b, c)),  ['a', 'b', 'c', 'f', 'f', 'f']),
        ]
    )  # yapf: disable
    def test_symbols(self, expression, symbols):
        assert expression.symbols == Multiset(symbols)

    @pytest.mark.parametrize(
        '   expression,             variables',
        [
            (a,                     []),
            (x_,                    [x_]),
            (_,                     []),
            (f(a),                  []),
            (f(x_),                 [x_]),
            (f(x_, x_),             [x_, x_]),
            (f(x_, a),              [x_]),
            (f(x_, a, y_),          [x_, y_]),
            (f(f(x_), f(b, x_)),    [x_, x_]),
        ]
    )  # yapf: disable
    def test_variables(self, expression, variables):
        assert expression.variables == Multiset(variables)

    @pytest.mark.parametrize(
        '   expression,     predicate,                  preorder_list',
        [                                               # expression        position
            (f(a, x_),      None,                       [(f(a, x_),         ()),
                                                         (a,                (0, )),
                                                         (x_,               (1, )),
                                                         (_,                (1, 0))]),
            (f(a, f(x_)),   lambda e: e.head is None,   [(x_,               (1, 0)),
                                                         (_,                (1, 0, 0))]),
            (f(a, f(x_)),   lambda e: e.head == f,      [(f(a, f(x_)),      ()),
                                                         (f(x_),            (1, ))])
        ]
    )  # yapf: disable
    def test_preorder_iter(self, expression, predicate, preorder_list):
        result = list(expression.preorder_iter(predicate))
        assert result == preorder_list

    GETITEM_TEST_EXPRESSION = f(a, f(x_, b), _)

    @pytest.mark.parametrize(
        '   position,       expected_result',
        [
            ((),            GETITEM_TEST_EXPRESSION),
            ((0, ),         a),
            ((0, 0),        IndexError),
            ((1, ),         f(x_, b)),
            ((1, 0),        x_),
            ((1, 0, 0),     _),
            ((1, 0, 1),     IndexError),
            ((1, 1),        b),
            ((1, 1, 0),     IndexError),
            ((1, 2),        IndexError),
            ((2, ),         _),
            ((3, ),         IndexError),
        ]
    )  # yapf: disable
    def test_getitem(self, position, expected_result):
        if inspect.isclass(expected_result) and issubclass(expected_result, Exception):
            with pytest.raises(expected_result):
                _ = self.GETITEM_TEST_EXPRESSION[position]
        else:
            result = self.GETITEM_TEST_EXPRESSION[position]
            assert result == expected_result

    @pytest.mark.parametrize(
        '   expression1,    expression2,    first_is_bigger_than_second',
        [
            (a,             b,              True),
            (a,             a,              False),
            (a,             x_,             True),
            (x_,            y_,             True),
            (x_,            x_,             False),
            (x__,           x_,             False),
            (x_,            x__,            False),
            (f(a),          f(b),           True),
            (f(a),          f(a),           False),
            (f(b),          f(a, a),        True),
            (f(a),          f(a, a),        True),
            (f(a, a),       f(a, b),        True),
            (f(a, a),       f(a, a),        False),
            (a,             f(a),           True),
            (x_,            f(a),           True),
            (_,             f(a),           True),
            (x_,            _,              True),
            (a,             _,              True),
        ]
    )  # yapf: disable
    def test_lt(self, expression1, expression2, first_is_bigger_than_second):
        if first_is_bigger_than_second:
            assert expression1 < expression2, "{!s} < {!s} did not hold".format(expression1, expression2)
            assert not (expression2 < expression1), "{!s} < {!s} but should not be".format(expression2, expression1)
        else:
            assert not (expression1 < expression2), "{!s} < {!s} but should not be".format(expression1, expression2)

    @pytest.mark.parametrize('expression', [a, f(a), x_, _])
    def test_lt_error(self, expression):
        with pytest.raises(TypeError):
            expression < object()

    def test_operation_new_error(self):
        with pytest.raises(ValueError):
            _ = Operation.new('if', Arity.variadic)

        with pytest.raises(ValueError):
            _ = Operation.new('+', Arity.variadic)

    def test_variable_error(self):
        with pytest.raises(ValueError):
            _ = Variable('x', Variable.fixed('y', 2))

        with pytest.raises(ValueError):
            _ = Variable('x', a)

    def test_wildcard_error(self):
        with pytest.raises(ValueError):
            _ = Wildcard(-1, False)

        with pytest.raises(ValueError):
            _ = Wildcard(0, True)

    def test_symbol_wildcard_error(self):
        with pytest.raises(TypeError):
            _ = SymbolWildcard(object)

    @pytest.mark.parametrize(
        '   expression,                                                     expected_result',
        [
            (a,                                                             a),
            (x_,                                                            x_),
            (Variable.dot('x', constraint1),                                x_),
            (Variable.dot('x', constraint1),                                x_),
            (SymbolWildcard(constraint=constraint1),                        SymbolWildcard()),
            (f(a, constraint=constraint1),                                  f(a)),
            (f(Variable.dot('x', constraint1)),                             f(x_)),
            (f(Variable.dot('x', constraint1), constraint=constraint2),     f(x_)),
        ]
    )  # yapf: disable
    def test_without_constraints(self, expression, expected_result):
        new_expr = expression.without_constraints
        assert new_expr == expected_result

    @pytest.mark.parametrize(
        '   expression,                         renaming,       expected_result',
        [
            (a,                                 {},             a),
            (a,                                 {'x': 'y'},     a),
            (x_,                                {},             x_),
            (x_,                                {'x': 'y'},     y_),
            (Variable.dot('x', constraint1),    {'x': 'y'},     Variable.dot('y', constraint1)),
            (SymbolWildcard(),                  {},             SymbolWildcard()),
            (SymbolWildcard(),                  {'x': 'y'},     SymbolWildcard()),
            (f(x_),                             {},             f(x_)),
            (f(x_),                             {'x': 'y'},     f(y_)),
            (f(x_, constraint=constraint1),     {'x': 'y'},     f(y_, constraint=constraint1)),
        ]
    )  # yapf: disable
    def test_with_renamed_vars(self, expression, renaming, expected_result):
        new_expr = expression.with_renamed_vars(renaming)
        assert new_expr == expected_result

    @pytest.mark.parametrize('expression', SIMPLE_EXPRESSIONS)
    @pytest.mark.parametrize('other', SIMPLE_EXPRESSIONS)
    def test_hash(self, expression, other):
        expression = expression
        other = other
        if expression != other:
            assert hash(expression) != hash(other), "hash({!s}) == hash({!s})".format(expression, other)
        else:
            assert hash(expression) == hash(other), "hash({!s}) != hash({!s})".format(expression, other)

    @pytest.mark.parametrize('expression', SIMPLE_EXPRESSIONS)
    def test_copy(self, expression):
        other = expression.__copy__()
        assert other == expression
        assert other is not expression


class TestOperation:
    def test_one_identity_error(self):
        with pytest.raises(TypeError):
            Operation.new('Invalid', Arity.unary, one_identity=True)
        with pytest.raises(TypeError):
            Operation.new('Invalid', Arity.binary, one_identity=True)

    def test_infix_error(self):
        with pytest.raises(TypeError):
            Operation.new('Invalid', Arity.unary, infix=True)
