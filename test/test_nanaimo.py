#
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# This software is distributed under the terms of the MIT License.
#

import fixtures
import nanaimo
import os
import pytest
import asyncio


@pytest.mark.timeout(10)
def test_uart_monitor() -> None:
    """
    Verify the nanaimo.ConcurrentUartMonitor class using a mock serial port.
    """
    serial = fixtures.MockSerial(fixtures.FAKE_TEST_SUCCESS)
    last_line = fixtures.FAKE_TEST_SUCCESS[-1]
    with nanaimo.ConcurrentUartMonitor(serial) as monitor:
        while True:
            line = monitor.readline()
            if line is None:
                os.sched_yield()
                continue
            elif line == last_line:
                break


@pytest.mark.asyncio
async def test_program_uploader() -> None:
    uploader = nanaimo.ProgramUploader(fixtures.get_s32K144_jlink_script(), fixtures.get_mock_JLinkExe())
    assert 0 == await uploader.upload()


@pytest.mark.asyncio
async def test_program_uploader_failure() -> None:
    uploader = nanaimo.ProgramUploader(fixtures.get_s32K144_jlink_script(), fixtures.get_mock_JLinkExe(), ['--simulate-error'])
    assert 0 != await uploader.upload()


@pytest.mark.asyncio
async def test_program_while_monitoring() -> None:
    uploader = nanaimo.ProgramUploader(fixtures.get_s32K144_jlink_script(), fixtures.get_mock_JLinkExe())
    serial = fixtures.MockSerial(fixtures.FAKE_TEST_SUCCESS)
    with nanaimo.ConcurrentUartMonitor(serial) as monitor:
        results = await asyncio.gather(
            nanaimo.GTestParser(10).read_test(monitor),
            uploader.upload()
        )
    assert 2 == len(results)

    for result in results:
        assert 0 == result


@pytest.mark.asyncio
async def test_failed_test() -> None:
    serial = fixtures.MockSerial(fixtures.FAKE_TEST_FAILURE)
    with nanaimo.ConcurrentUartMonitor(serial) as monitor:
        assert 1 == await nanaimo.GTestParser(10).read_test(monitor)


@pytest.mark.asyncio
async def test_timeout_while_monitoring() -> None:
    serial = fixtures.MockSerial(['gibberish'])
    with nanaimo.ConcurrentUartMonitor(serial) as monitor:
        assert 0 != await nanaimo.GTestParser(1.0).read_test(monitor)