#
# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# This software is distributed under the terms of the MIT License.
#
import asyncio
import logging
import pathlib
import typing


class ProgramUploaderJLink:
    """
    Async manager of a JLinkExe subprocess.
    """
    def __init__(self,
                 jlink_executable: pathlib.Path = pathlib.Path('JLinkExe'),
                 extra_arguments: typing.Optional[typing.List[str]] = None):
        self._logger = logging.getLogger(__name__)
        self._jlink_exe = jlink_executable
        self._extra_arguments = extra_arguments

    async def upload(self, jlink_script: pathlib.Path) -> int:
        cmd = '{} -CommanderScript {}'.format(self._jlink_exe, jlink_script)
        if self._extra_arguments is not None:
            cmd += ' ' + ' '.join(self._extra_arguments)

        self._logger.info('starting upload: %s', cmd)
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )  # type: asyncio.subprocess.Process

        stdout, stderr = await proc.communicate()

        self._logger.info('%s exited with %i', cmd, proc.returncode)

        if stdout:
            self._logger.debug(stdout.decode())
        if stderr:
            self._logger.error(stderr.decode())

        return proc.returncode