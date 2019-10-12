#
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# This software is distributed under the terms of the MIT License.
#

import argparse
import asyncio
import contextlib
import pathlib
import typing
from unittest.mock import patch

import pytest

import fixtures
import fixtures.simulators
import nanaimo
from nanaimo.connections.uart import ConcurrentUart
from nanaimo.instruments.bkprecision import Series1900BUart


@pytest.fixture
def paths_for_test():  # type: ignore
    return fixtures.Paths(__file__)


def create_dummy_serial_port_factory(fake_lines: typing.List[str],
                                     event_loop: typing.Optional[asyncio.AbstractEventLoop] = None,
                                     loop_fake_data: bool = False) \
        -> Series1900BUart.UartFactoryType:

    @contextlib.contextmanager
    def dummy_serial_port(port: typing.Union[str, pathlib.Path]) -> typing.Generator:
        nonlocal fake_lines, event_loop
        with ConcurrentUart(fixtures.simulators.Serial(fake_lines, '\r'), event_loop, '\r', loop_fake_data) as bk_uart:
            print('''Yielding context with a simulated serial port set to emit {} line(s) of
fake output.'''.format(len(fake_lines)))
            yield bk_uart

    return dummy_serial_port


def to_namespace(fixture_type: typing.Type[nanaimo.Fixture], command: str) -> nanaimo.Namespace:
    parser = argparse.ArgumentParser()
    fixture_type.on_visit_test_arguments(nanaimo.Arguments(parser))
    return nanaimo.Namespace(parser.parse_args(args=['--bk-port', 'dummy_port', '--bk-command', command]))


@pytest.mark.asyncio
@patch('nanaimo.FixtureManager')
async def test_turn_off(MockFixtureManager: typing.Any,
                        paths_for_test: fixtures.Paths,
                        event_loop: asyncio.AbstractEventLoop) -> None:
    dummy_serial_port_factory = create_dummy_serial_port_factory(['OK'], event_loop)
    args = to_namespace(Series1900BUart, '0')
    bk = Series1900BUart(nanaimo.FixtureManager(), args, event_loop, uart_factory=dummy_serial_port_factory)
    assert 0 == int(await bk.gather())


@pytest.mark.asyncio
@patch('nanaimo.FixtureManager')
async def test_turn_on(MockFixtureManager: typing.Any,
                       paths_for_test: fixtures.Paths,
                       event_loop: asyncio.AbstractEventLoop) -> None:
    dummy_serial_port_factory = create_dummy_serial_port_factory(['OK'], event_loop)
    args = to_namespace(Series1900BUart, '1')
    bk = Series1900BUart(nanaimo.FixtureManager(), args, event_loop, uart_factory=dummy_serial_port_factory)
    assert 0 == int(await bk.gather())


@pytest.mark.asyncio
@pytest.mark.timeout(10)
@patch('nanaimo.FixtureManager')
async def test_turn_on_timeout(MockFixtureManager: typing.Any,
                               paths_for_test: fixtures.Paths,
                               event_loop: asyncio.AbstractEventLoop) -> None:
    args = to_namespace(Series1900BUart, '1')
    dummy_serial_port_factory = create_dummy_serial_port_factory(['NOPE'], event_loop, loop_fake_data=False)
    bk = Series1900BUart(nanaimo.FixtureManager(), args, event_loop, uart_factory=dummy_serial_port_factory)
    with pytest.raises(asyncio.TimeoutError):
        await bk.gather()


@pytest.mark.asyncio
@pytest.mark.timeout(10)
@patch('nanaimo.FixtureManager')
async def test_turn_on_wait_for_voltage(MockFixtureManager: typing.Any,
                                        paths_for_test: fixtures.Paths,
                                        event_loop: asyncio.AbstractEventLoop) -> None:
    args = to_namespace(Series1900BUart, '1')
    mock_session = ['OK',
                    '000000000', 'OK',
                    '000100000', 'OK',
                    '001000000', 'OK',
                    '010000000', 'OK',
                    '010000000', 'OK',
                    '010000000', 'ERROR']
    dummy_serial_port_factory = create_dummy_serial_port_factory(mock_session, event_loop, loop_fake_data=False)
    bk = Series1900BUart(nanaimo.FixtureManager(), args, event_loop, uart_factory=dummy_serial_port_factory)
    assert 0 == int(await bk.gather(bk_target_voltage=1))


@pytest.mark.asyncio
@pytest.mark.timeout(10)
@patch('nanaimo.FixtureManager')
async def test_turn_on_wait_for_voltage_timeout(MockFixtureManager: typing.Any,
                                                paths_for_test: fixtures.Paths,
                                                event_loop: asyncio.AbstractEventLoop) -> None:
    args = to_namespace(Series1900BUart, '1')
    mock_session = ['OK',
                    '000000000', 'OK',
                    '090000000', 'OK']
    dummy_serial_port_factory = create_dummy_serial_port_factory(mock_session, event_loop, loop_fake_data=True)
    bk = Series1900BUart(nanaimo.FixtureManager(), args, event_loop, uart_factory=dummy_serial_port_factory)
    with pytest.raises(asyncio.TimeoutError):
        await bk.gather(bk_target_voltage=10, bk_target_voltage_threshold_rising=.5)


@pytest.mark.asyncio
@patch('nanaimo.FixtureManager')
async def test_get_display(MockFixtureManager: typing.Any,
                           paths_for_test: fixtures.Paths,
                           event_loop: asyncio.AbstractEventLoop) -> None:
    dummy_serial_port_factory = create_dummy_serial_port_factory(['030201451', 'OK'], event_loop)
    args = to_namespace(Series1900BUart, '?')
    bk = Series1900BUart(nanaimo.FixtureManager(), args, event_loop, uart_factory=dummy_serial_port_factory)
    artifacts = await bk.gather()
    display = artifacts.display
    assert 3.02 == display[0]
    assert 1.45 == display[1]
    assert Series1900BUart.ModeCC == display[2]
