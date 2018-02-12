import sys
from niveristand import decorators, RealTimeSequence
from niveristand.clientapi.datatypes import I32Value
from niveristand.exceptions import TranslateError, VeristandError
from niveristand.library.tasks import multitask, nivs_yield
import pytest
from testutilities import rtseqrunner, validation


@decorators.NivsParam('param', I32Value(0), decorators.NivsParam.BY_REF)
@decorators.nivs_rt_sequence
def _increase_param_by_ref(param):
    param.value += 1


@decorators.nivs_rt_sequence
def multitask_pass():
    a = I32Value(1)
    with multitask() as mt:
        def f1():
            pass

        def f2():
            pass
        mt.append(f1)
        mt.append(f2)
    return a.value


@decorators.nivs_rt_sequence
def multitask_access_local():
    a = I32Value(0)
    with multitask() as mt:
        def f1():
            a.value = 5

        def f2():
            a.value *= 7
        mt.append(f1)
        mt.append(f2)
    return a.value


@decorators.nivs_rt_sequence
def multitask_nested():
    a = I32Value(0)
    with multitask() as mt:
        def f1():
            with multitask() as mt:
                def fa():
                    a.value = 5

                def fb():
                    a.value *= 7
                mt.append(fa)
                mt.append(fb)

        def f2():
            a.value *= 13

        mt.append(f1)
        mt.append(f2)
    return a.value


@decorators.nivs_rt_sequence
def multitask_task_with_yield():
    a = I32Value(0)
    with multitask() as mt:
        def f1():
            nivs_yield()
            a.value = 1

        def f2():
            a.value = 2
            nivs_yield()
        mt.append(f1)
        mt.append(f2)
    return a.value


@decorators.nivs_rt_sequence
def multitask_call_subroutine_params_byref():
    a = I32Value(0)
    b = I32Value(1)
    with multitask() as mt:
        def f1():
            _increase_param_by_ref(a)

        def f2():
            _increase_param_by_ref(b)

        def f3():
            a.value += b.value
        mt.append(f1)
        mt.append(f2)
        mt.append(f3)
    return a.value


@decorators.nivs_rt_sequence
def multitask_duplicate_name_fails():
    a = I32Value(0)
    with multitask() as mt:
        def f1():
            a.value = 1

        def f1():  # noqa: F811 redefinition is exactly what we're testing here.
            a.value = 2
        mt.append(f1)
        mt.append(f1)
    return a.value


@decorators.nivs_rt_sequence
def multitask_redefine_var_fails():
    a = I32Value(0)
    with multitask() as mt:
        def f1():
            a = I32Value(1)
            a.value = 2
        mt.append(f1)
    return a.value


@decorators.nivs_rt_sequence
def multitask_return_fails():
    a = I32Value(0)
    with multitask() as mt:
        def f1():
            a = I32Value(1)
            a.value = 2
        mt.append(f1)
        return a.value


@decorators.nivs_rt_sequence
def multitask_with_param_fails():
    a = I32Value(1)
    with multitask(a) as mt:
        def f1():
            pass

        def f2():
            pass
        mt.append(f1)
        mt.append(f2)
    return a.value


@decorators.nivs_rt_sequence
def multitask_task_with_param_fails():
    a = I32Value(1)
    with multitask(a) as mt:
        def f1(x):
            pass

        def f2():
            pass
        mt.append(f1)
        mt.append(f2)
    return a.value


@decorators.nivs_rt_sequence
def multitask_return_in_task_fails():
    a = I32Value(0)
    with multitask() as mt:
        def f1():
            a = I32Value(1)
            return a.value
        mt.append(f1)
    return a.value


@decorators.nivs_rt_sequence
def multitask_funcdef_in_task_fails():
    a = I32Value(0)
    with multitask() as mt:
        def f1():
            def f2():
                pass
        mt.append(f1)
    return a.value


run_tests = [
    (multitask_pass, (), 1),
    (multitask_nested, (), 455),
    (multitask_access_local, (), 35),
    (multitask_task_with_yield, (), 1),
    (multitask_call_subroutine_params_byref, (), 3),
]

skip_tests = [
    (multitask_redefine_var_fails, (), "Redefine restrictions not implemented yet"),
    (_increase_param_by_ref, (), "Parameter passing can't be faked yet."),
]

fail_transform_tests = [
    (multitask_duplicate_name_fails, (), VeristandError),
    (multitask_return_fails, (), TranslateError),
    (multitask_with_param_fails, (), TranslateError),
    (multitask_task_with_param_fails, (), TranslateError),
    (multitask_return_in_task_fails, (), TranslateError),
    (multitask_funcdef_in_task_fails, (), TranslateError),
]


def idfunc(val):
    return val.__name__


@pytest.mark.parametrize("func_name, params, expected_result", run_tests, ids=idfunc)
def test_transform(func_name, params, expected_result):
    RealTimeSequence(func_name)


@pytest.mark.skip("Python multitasking not properly implemented yet")
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
