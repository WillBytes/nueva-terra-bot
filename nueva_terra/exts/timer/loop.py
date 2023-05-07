from __future__ import annotations

from asyncio import sleep
from collections.abc import Callable, Coroutine
from datetime import datetime, timedelta
from logging import getLogger
from typing import Any, TypeVar

from botbase import CogBase
from nextcord import ChannelType
from nextcord.ext import tasks
from nextcord.utils import MISSING, utcnow

from nueva_terra.bot import NuevaTerra
from nueva_terra.db import Message
from nueva_terra.image import generate_content
from nueva_terra.time import time_since_anp

log = getLogger(__name__)

# ext.tasks does not execute precisely on time, it loses tens of ms every time it
# loops. Over time, this loses quite a lot.


LF = TypeVar("LF", bound=Callable[..., Coroutine[Any, Any, Any]])
T = TypeVar("T")
HALF_SECOND = 500_000


class Loop(tasks.Loop[LF]):
    def _get_next_sleep_time(self) -> datetime:
        if self._last_iteration.microsecond > HALF_SECOND:
            last_iteration = self._last_iteration.replace(microsecond=HALF_SECOND)
        else:
            last_iteration = self._last_iteration.replace(microsecond=0)
        return last_iteration + timedelta(seconds=self._sleep)

    def __get__(self, obj: T, objtype: type[T]) -> Loop[LF]:
        if obj is None:
            return self

        copy: Loop[LF] = Loop(
            self.coro,
            seconds=self._seconds,
            hours=self._hours,
            minutes=self._minutes,
            time=self._time,
            count=self.count,
            reconnect=self.reconnect,
            loop=self.loop,
        )
        copy._injected = obj
        copy._before_loop = self._before_loop
        copy._after_loop = self._after_loop
        copy._error = self._error
        setattr(obj, self.coro.__name__, copy)
        return copy


def loop(*, seconds: float) -> Callable[[LF], Loop[LF]]:
    def decorator(func: LF) -> Loop[LF]:
        return Loop[LF](
            func,
            seconds=seconds,
            minutes=MISSING,
            hours=MISSING,
            time=MISSING,
            count=None,
            reconnect=True,
            loop=MISSING,
        )

    return decorator


class LoopCog(CogBase[NuevaTerra]):
    def __init__(self, bot: NuevaTerra) -> None:
        super().__init__(bot)

    @CogBase.listener()
    async def on_ready(self) -> None:
        if not self.loop.is_running():
            log.info("Starting loop.")
            self.loop.start()

    def cog_unload(self) -> None:
        self.loop.stop()

    @loop(seconds=7.5)
    async def loop(self) -> None:
        messages = await Message.objects.all()

        for message in messages:
            log.debug(
                "Updating message %d in %d", message.message_id, message.channel_id
            )
            channel = self.bot.get_partial_messageable(
                message.channel_id, type=ChannelType.text
            )
            file, embed = generate_content()

            # There is a limit on edits to messages older than an hour.
            # Delete the message and send a new one if it is older than an hour.
            if utcnow() - message.time >= timedelta(hours=1):
                log.debug(
                    "Deleting message %d in %d", message.message_id, message.channel_id
                )
                old_message = channel.get_partial_message(message.message_id)
                await old_message.delete()

                msg = await channel.send(file=file, embed=embed)
                await message.update(message_id=msg.id, time=msg.created_at)
                log.debug(
                    "Created message %d in %d", message.message_id, message.channel_id
                )
            else:
                log.debug(
                    "Editing message %d in %d", message.message_id, message.channel_id
                )
                # For some reason, PartialMessage.edit() does not allow files.
                msg = await channel.fetch_message(message.message_id)
                await msg.edit(file=file, embed=embed)

    @loop.before_loop
    async def before_loop(self) -> None:
        real_seconds_since_anp = time_since_anp().total_seconds()
        remainder = real_seconds_since_anp % 7.5
        wait_seconds = 7.5 - remainder
        log.info("Sleeping for %f seconds.", wait_seconds)
        await sleep(wait_seconds)

    @loop.error
    async def loop_error(self, error: BaseException) -> None:
        log.exception("Loop error.", exc_info=error)


def setup(bot: NuevaTerra) -> None:
    bot.add_cog(LoopCog(bot))
