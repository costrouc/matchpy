# -*- coding: utf-8 -*-
import pytest

from patternmatcher.expressions import Operation, Symbol, Variable, Arity, Wildcard
from patternmatcher.matching import ManyToOneMatcher
from patternmatcher.functions import match as match_one_to_one


@pytest.fixture(autouse=True)
def add_default_expressions(doctest_namespace):
    doctest_namespace['f'] = Operation.new('f', Arity.variadic)
    doctest_namespace['a'] = Symbol('a')
    doctest_namespace['b'] = Symbol('b')
    doctest_namespace['c'] = Symbol('c')
    doctest_namespace['x_'] = Variable.dot('x')
    doctest_namespace['_'] = Wildcard.dot()
    doctest_namespace['__'] = Wildcard.plus()
    doctest_namespace['___'] = Wildcard.star()
    doctest_namespace['__name__'] = '__main__'

def pytest_generate_tests(metafunc):
    if 'match' in metafunc.fixturenames:
        metafunc.parametrize('match', ['one-to-one', 'many-to-one'], indirect=True)


def match_many_to_one(expression, pattern):
    matcher = ManyToOneMatcher(pattern)
    for _, substitution in matcher.match(expression):
        yield substitution

@pytest.fixture
def match(request):
    if request.param == 'one-to-one':
        return match_one_to_one
    elif request.param == 'many-to-one':
        return match_many_to_one
    else:
        raise ValueError("Invalid internal test config")