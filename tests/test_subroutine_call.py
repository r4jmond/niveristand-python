import sys

from niveristand import decorators, RealTimeSequence
from niveristand.clientapi.datatypes import BooleanValue, DoubleValue, DoubleValueArray
from niveristand.exceptions import TranslateError, VeristandError
import pytest
from testutilities import rtseqrunner, validation

a = 1
b = 2


@decorators.nivs_rt_sequence
def return_constant():
    a = DoubleValue(5)
    return a.value


@decorators.nivs_rt_sequence
def finite_recursion(x):
    res = BooleanValue(False)
    if x < 0:
        res.value = True
        return res.value
    else:
        finite_recursion(x - 1)


@decorators.nivs_rt_sequence
def circular_call_a():
    circular_call_b()


@decorators.nivs_rt_sequence
def circular_call_b():
    circular_call_a()


@decorators.nivs_rt_sequence
def return_parameter(param):
    return param


@decorators.nivs_rt_sequence
def return_arr_element(param):
    return param[0]


@decorators.nivs_rt_sequence
def return_arr_element_plus1_by_ref(param):
    param[0] += 1


@decorators.nivs_rt_sequence
def return_parameter_plus1_byref(param):
    param.value += 1
    return param.value


@decorators.nivs_rt_sequence
def call_return_constant_as_assignment():
    a = DoubleValue(0)
    a.value = return_constant()
    return a.value


@decorators.nivs_rt_sequence
def call_return_constant_as_expr():
    a = BooleanValue(0)
    return_constant()
    a.value = True
    return a.value


@decorators.nivs_rt_sequence
def call_return_parameter():
    a = DoubleValue(0)
    a.value = return_parameter(5)
    return a.value


@decorators.nivs_rt_sequence
def call_parameter_nivsdatatype():
    a = DoubleValue(5)
    return_parameter_plus1_byref(a)
    return a.value


@decorators.nivs_rt_sequence
def call_parameter_builtin_math():
    a = DoubleValue(-5)
    a.value = return_parameter(abs(5))
    return a.value


@decorators.nivs_rt_sequence
def call_parameter_array_elem():
    a = DoubleValueArray([1, 2, 3])
    b = DoubleValue(0)
    b.value = return_arr_element(a)
    return b.value


@decorators.nivs_rt_sequence
def call_parameter_array_elem_byref():
    a = DoubleValueArray([1, 2, 3])
    return a[1]


@decorators.nivs_rt_sequence
def recursive_call():
    recursive_call()


@decorators.nivs_rt_sequence
def invalid_call():
    fake_call()  # noqa: F821 this is supposed to be an undefined call.


run_tests = [
    (return_constant, (), 5),
    (call_return_constant_as_assignment, (), return_constant()),
    (call_return_constant_as_expr, (), True),
    (call_return_parameter, (), 5),
    (call_parameter_nivsdatatype, (), 6),
    (call_parameter_builtin_math, (), 5),
]

skip_tests = [
    (return_parameter_plus1_byref, (), "This call receives a parameter and it can't be faked without a caller."),
    (return_parameter, (), "This call receives a parameter and it can't be faked without a caller."),
    (return_arr_element, (), "This call receives a parameter and it can't be faked without a caller."),
    (return_arr_element_plus1_by_ref, (), "This call receives a parameter and it can't be faked without a caller."),
    (call_parameter_array_elem, (), "Subscript not implemented. Expected: 1"),
    (call_parameter_array_elem_byref, (), "Subscript not implemented. Expected: 2"),
]

fail_transform_tests = [
    (recursive_call, (), RuntimeError),
    (circular_call_a, (), RuntimeError),
    (circular_call_b, (), RuntimeError),
    (finite_recursion, (), RuntimeError),
    (invalid_call, (), TranslateError),
]


def idfunc(val):
    return val.__name__


@pytest.mark.parametrize("func_name, params, expected_result", run_tests, ids=idfunc)
def test_transform(func_name, params, expected_result):
    RealTimeSequence(func_name)


@pytest.mark.parametrize("func_name, params, expected_result", run_tests, ids=idfunc)
def test_runpy(func_name, params, expected_result):
    actual = func_name(*params)
    assert actual == expected_result


@pytest.mark.parametrize("func_name, params, expected_result", run_tests, ids=idfunc)
def test_run_in_VM(func_name, params, expected_result):
    actual = rtseqrunner.run_rtseq_in_VM(func_name)
    assert actual == expected_result


@pytest.mark.parametrize("func_name, params, expected_result", fail_transform_tests, ids=idfunc)
def test_failures(func_name, params, expected_result):
    try:
        RealTimeSequence(func_name)
    except expected_result:
        pass
    except VeristandError as e:
        pytest.fail('Unexpected exception raised:' +
                    str(e.__class__) + ' while expected was: ' + expected_result.__name__)
    except Exception as exception:
        pytest.fail('ExpectedException not raised: ' + str(exception))


@pytest.mark.parametrize("func_name, params, reason", skip_tests, ids=idfunc)
def test_skipped(func_name, params, reason):
    pytest.skip(func_name.__name__ + ": " + reason)


def test_check_all_tested():
    validation.test_validate(sys.modules[__name__])