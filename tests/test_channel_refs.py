from niveristand import exceptions
from niveristand import RealTimeSequence
import pytest
from testutilities import rtseqrunner, testfunctions
from NationalInstruments.VeriStand.RealTimeSequenceDefinitionApi import Expression  # noqa: E501, I100 We need these C# imports to be out of order.


def test_channel_ref_type_string():
    rtseq = RealTimeSequence(testfunctions.channel_ref_type_string)
    assert rtseq._rtseq.Variables.LocalVariables.Variables.Length is 0
    assert rtseq._rtseq.Variables.ChannelReferences.Channels.Length is 1
    assert rtseq._rtseq.Variables.ChannelReferences.Channels[0].Channel.Channel \
        == "Aliases/DesiredRPM"


def test_channel_ref_setter():
    rtseq = RealTimeSequence(testfunctions.channel_ref_setter)
    assert rtseq._rtseq.Code.Main.Body.Statements.Length is 1
    expression = Expression('ch_a = 5')
    assert rtseq._rtseq.Code.Main.Body.Statements[0].Equals(expression)


def test_channel_ref_return():
    testfunc = testfunctions.channel_ref_return
    with pytest.raises(exceptions.TranslateError):
        RealTimeSequence(testfunc)


def test_channel_ref_run():
    result = rtseqrunner.run_rtseq_in_VM(testfunctions.channel_ref_validate_getter)
    assert result == 5


def test_channel_ref_run_python():
    result = testfunctions.channel_ref_validate_getter()
    assert result == 5