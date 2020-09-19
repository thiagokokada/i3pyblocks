User guide
==========

Installation
------------

To install **i3pyblocks**, make sure you have Python >=3.6 installed and simply
run this simple command in your terminal of choice:

.. code-block:: sh

    $ python3 -m pip install i3pyblocks

This will install a basic installation without dependencies, so most blocks will
not work. Check ``extras_require`` section in `setup.py`_ file to see the current
available optional dependencies for each block.

For example, if you want to use :mod:`i3pyblocks.blocks.pulse` you can will need
to install the dependencies listed in ``blocks.pulse``. It is very easy to do
this using ``pip`` itself:

.. code-block:: sh

    $ python3 -m pip install 'i3pyblocks[blocks.pulse]'

You can also pass multiple blocks dependencies at the same time:

.. code-block:: sh

    $ python3 -m pip install 'i3pyblocks[blocks.dbus,blocks.i3ipc,blocks.inotify]'

If you want to install the latest version from git, you can also run something
similar to below:

.. code-block:: sh

    $ python3 -m pip install -e 'git+https://github.com/thiagokokada/i3pyblocks#egg=i3pyblocks[blocks.i3ipc,blocks.ps]'

.. _setup.py:
    https://github.com/thiagokokada/i3pyblocks/blob/master/setup.py


Configuring your i3pyblocks
---------------------------

Let's start with a basic configuration showing a simple text
(:class:`~i3pyblocks.blocks.basic.TextBlock`) and a clock
(:class:`~i3pyblocks.blocks.datetime.DateTimeBlock`):

.. code-block:: python

    from i3pyblocks import core, utils
    from i3pyblocks.blocks import basic, datetime


    async def main():
        runner = core.Runner()
        await runner.register_block(basic.TextBlock("Welcome to i3pyblocks!"))
        await runner.register_block(datetime.DateTimeBlock())

        await runner.start()


    utils.asyncio_run(main())

Save the content above in a file called ``config.py``. To test in terminal,
we can run it using:

.. code-block:: sh

    $ i3pyblocks -c config.py

Running this for ~5 seconds in terminal. You can press ``Ctrl+C`` to stop (you
may) need to press twice to exit:

.. code-block:: sh

    {"version": 1, "click_events": true}
    [
    [{"name": "TextBlock", "instance": "<random-id>", "full_text": "Welcome to i3pyblocks!"}, {"name": "DateTimeBlock", "instance": "<random-id>", "full_text": "18:02:50"}],
    [{"name": "TextBlock", "instance": "<random-id>", "full_text": "Welcome to i3pyblocks!"}, {"name": "DateTimeBlock", "instance": "<random-id>", "full_text": "18:02:51"}],
    [{"name": "TextBlock", "instance": "<random-id>", "full_text": "Welcome to i3pyblocks!"}, {"name": "DateTimeBlock", "instance": "<random-id>", "full_text": "18:02:52"}],
    [{"name": "TextBlock", "instance": "<random-id>", "full_text": "Welcome to i3pyblocks!"}, {"name": "DateTimeBlock", "instance": "<random-id>", "full_text": "18:02:53"}],
    [{"name": "TextBlock", "instance": "<random-id>", "full_text": "Welcome to i3pyblocks!"}, {"name": "DateTimeBlock", "instance": "<random-id>", "full_text": "18:02:54"}],
    ^C

Now, to start using it in your i3wm, add it to your ``$HOME/.config/i3/config``
file (or ``$HOME/.config/sway/config`` if using sway)::

    bar {
        position top
        status_command i3pyblocks -c /path/to/your/config.py
    }


Customizing blocks
------------------

Most blocks can be customized by passing optional parameters to its constructor.
Let's say that you want to use a custom formatting to show date and time in
:class:`~i3pyblocks.blocks.datetime.DateTimeBlock`, you can do something like
this:

.. code-block:: python

    from i3pyblocks import core, utils
    from i3pyblocks.blocks import datetime


    async def main():
        runner = core.Runner()
        await runner.register_block(
            datetime.DateTimeBlock(
                format_date="%Y-%m-%d",
                format_time="%H:%M:%S",
            )
        )

        await runner.start()


    utils.asyncio_run(main())

Running this for ~5 seconds in terminal results:

.. code-block:: sh

    {"version": 1, "click_events": true}
    [
    [{"name": "DateTimeBlock", "instance": "<random-id>", "full_text": "21:28:11"}],
    [{"name": "DateTimeBlock", "instance": "<random-id>", "full_text": "21:28:12"}],
    [{"name": "DateTimeBlock", "instance": "<random-id>", "full_text": "21:28:13"}],
    [{"name": "DateTimeBlock", "instance": "<random-id>", "full_text": "21:28:14"}],
    [{"name": "DateTimeBlock", "instance": "<random-id>", "full_text": "21:28:15"}],
    ^C

It is **strongly** recommended that you use keyword parameters in constructors
(i.e.: ``format_date="%Y-%m-%d"``) instead of positional parameters
(i.e.: only ``"%Y-%m-%d"``), since this will make your configuration clearer
and avoid breakage in the future.

Most packages uses an extended version of `Python's format`_ for formatting
strings, :class:`~i3pyblocks.formatter.ExtendedFormatter`, allowing a very good
degree of customization, for example:

.. code-block:: python

    from i3pyblocks import core, utils
    from i3pyblocks.blocks import ps


    async def main():
        runner = core.Runner()
        await runner.register_block(ps.VirtualMemoryBlock(format="{available}G"))
        await runner.register_block(ps.VirtualMemoryBlock(format="{available:.1f}G"))

        await runner.start()


    utils.asyncio_run(main())

Running this in terminal, results:

.. code-block:: sh

    $ i3pyblocks -c config.py
    {"version": 1, "click_events": true}
    [
    [{"name": "VirtualMemoryBlock", "instance": "<random-id>", "full_text": "9.517715454101562G"}, {"name": "VirtualMemoryBlock", "instance": "<random-id>", "full_text": "9.5G"}],
    ^C

If you want greater customization than what is available with a block constructor
parameters, you can always extend the class:

.. code-block:: python

    from datetime import datetime, timezone

    from i3pyblocks import core, utils
    from i3pyblocks.blocks import datetime as m_datetime


    class CustomDateTimeBlock(m_datetime.DateTimeBlock):
        async def run(self) -> None:
            utc_time = datetime.now(timezone.utc)
            self.update(utc_time.strftime(self.format))

    async def main():
        runner = core.Runner()
        await runner.register_block(CustomDateTimeBlock())

        await runner.start()


    utils.asyncio_run(main())

.. _`Python's format`:
    https://pyformat.info/

Clicks and signals
------------------

If you want some block to react to signals, you need to register them first by
passing ``signals`` parameter to :meth:`~i3pyblocks.core.Runner.register_block`:

.. code-block:: python

    import signal

    from i3pyblocks import core, utils
    from i3pyblocks.blocks import datetime


    async def main():
        runner = core.Runner()
        await runner.register_block(
            datetime.DateTimeBlock(
                format_date="%Y-%m-%d",
                format_time="%H:%M:%S",
            ),
            signals=(signal.SIGUSR1, signal.SIGUSR2)
        )

        await runner.start()


    utils.asyncio_run(main())

This only allow :class:`~i3pyblocks.blocks.datetime.DateTimeBlock` to receive
``SIGUSR1`` and ``SIGUSR2`` signals, it does not necessary handle them. Of
course, most blocks already have some default handler for them (i.e.: for most
blocks it triggers a force refresh), but in case you want something else you
can override :meth:`~i3pyblocks.blocks.base.Block.signal_handler`:

.. code-block:: python

    import signal

    from i3pyblocks import core, utils
    from i3pyblocks.blocks import datetime


    class CustomDateTimeBlock(datetime.DateTimeBlock):
        async def signal_handler(self, *, sig: signal.Signals) -> None:
            if sig == signal.SIGUSR1:
                self.format = self.format_time
            elif sig == signal.SIGUSR2:
                self.format = self.format_date
            # Calling the run method here so the block is updated immediately
            self.run()

    async def main():
        runner = core.Runner()
        await runner.register_block(
            CustomDateTimeBlock(),
            signals=(signal.SIGUSR1, signal.SIGUSR2)
        )

        await runner.start()


    utils.asyncio_run(main())

Running it and sending ``pkill -SIGUSR2 i3pyblocks`` in another terminal result in:

.. code-block:: sh

    $ i3pyblocks -c config.py
    {"version": 1, "click_events": true}
    [
    [{"name": "CustomDateTimeBlock", "instance": "<random-id>", "full_text": "21:58:27"}],
    [{"name": "CustomDateTimeBlock", "instance": "<random-id>", "full_text": "21:58:28"}],
    [{"name": "CustomDateTimeBlock", "instance": "<random-id>", "full_text": "09/18/20"}],
    [{"name": "CustomDateTimeBlock", "instance": "<random-id>", "full_text": "09/18/20"}],
    ^C

The same can be applied to mouse clicks overriding the
:meth:`~i3pyblocks.blocks.base.Block.click_handler`.
