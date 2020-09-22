Creating a new block
====================

Development setup
-----------------

If you want to quick start the development of **i3pyblocks**, make sure you
have Python >=3.6 installed and run:

.. code-block:: sh

   $ git clone https://github.com/thiagokokada/i3pyblocks
   $ cd i3pyblocks
   $ python3 -m venv venv
   $ source venv/bin/activate
   $ make dev-install

To test if everything is working, you try to run ``i3pyblocks -c example.py``
in your terminal.

Let's start with a "Hello World!"
---------------------------------

Creating a new block ("thing that display something in **i3pyblocks**") is
reasonable easy. Let's start with a simple, "Hello World!" example:

.. code-block:: python

    from i3pyblocks import Runner, blocks, utils

    class HelloWorldBlock(blocks.Block):
        """Block that shows a 'Hello World!' text."""
        async def start(self) -> None:
            self.update("Hello World!")


    async def main():
        runner = Runner()
        await runner.register_block(HelloWorldBlock())
        await runner.start()


    utils.asyncio_run(main())

It is a very silly example, but it should be sufficient to illustrate. We are
using the :class:`~i3pyblocks.blocks.base.Block`, that is the root of all blocks
in **i3pyblocks**.

Save the content above in a file called ``hello_world.py``. To test in terminal,
we can run it using:

.. code-block:: sh

    $ i3pyblocks -c hello_world.py

And we should saw the following being printed in terminal:

.. code-block:: sh

    {"version": 1, "click_events": true}
    [
    [{"name": "HelloWorldBlock", "instance": "<random-id>", "full_text": "Hello World!"}],
    ^C

There is only one update since this block doesn't do anything interesting. Use
``Ctrl+C`` (you may need to press twice) to exit.

A more advanced example
-----------------------

To do something more interesting, we need to have some kind of event that will
trigger block events. One of the easiest ways to do it is to use time, for
example:

.. code-block:: python

  import asyncio

  from i3pyblocks import Runner, blocks, utils

  class CounterBlock(blocks.Block):
      """Block that's count at each second."""
      def __init__(self):
          super().__init__()
          self.counter = 0

      async def start(self) -> None:
          while True:
              self.update(f"Counter: {self.counter}")
              self.counter += 1
              await asyncio.sleep(1)


  async def main():
      runner = Runner()
      await runner.register_block(CounterBlock())
      await runner.start()


  utils.asyncio_run(main())

Running it in terminal for ~5 seconds results in:

.. code-block:: sh

    $ i3pyblocks -c example.py
    {"version": 1, "click_events": true}
    [
    [{"name": "HelloWorldBlock", "instance": "<random-id>", "full_text": "Counter: 0"}],
    [{"name": "HelloWorldBlock", "instance": "<random-id>", "full_text": "Counter: 1"}],
    [{"name": "HelloWorldBlock", "instance": "<random-id>", "full_text": "Counter: 2"}],
    [{"name": "HelloWorldBlock", "instance": "<random-id>", "full_text": "Counter: 3"}],
    [{"name": "HelloWorldBlock", "instance": "<random-id>", "full_text": "Counter: 4"}],
    [{"name": "HelloWorldBlock", "instance": "<random-id>", "full_text": "Counter: 5"}],
    ^C

As we would expect. Actually, blocks that run an update at each *X* seconds are
so common that **i3pyblocks** has an abstraction for it, the
:class:`~i3pyblocks.blocks.base.PollingBlock` [1]_:

.. code-block:: python

    import asyncio

    from i3pyblocks import Runner, blocks, utils

    class ImprovedCounterBlock(blocks.PollingBlock):
        """Block that shows a 'Hello World!' text."""
        def __init__(self):
            super().__init__(sleep=1)
            self.counter = 0

        async def run(self) -> None:
            self.update(f"Counter: {self.counter}")
            self.counter += 1


    async def main():
        runner = Runner()
        await runner.register_block(ImprovedCounterBlock())
        await runner.start()


    utils.asyncio_run(main())


:class:`~i3pyblocks.blocks.base.PollingBlock` will call
:meth:`~i3pyblocks.blocks.base.PollingBlock.run` at each second, exactly like
our previous example. We can increase the interval between each update by passing
``super.__init__(sleep=X)``, where ``X`` is the seconds between each update.

.. [1] Since both :class:`~i3pyblocks.blocks.base.Block` and
   :class:`~i3pyblocks.blocks.base.PollingBlock` are blocks used to construct
   other blocks, they're kept in the same namespace, :mod:`i3pyblocks.blocks.base`.
   There is also some other base blocks that will be shown later on.

Clicks and signals
------------------

Let's expand our ``HelloWorldBlock`` to change the text when the user sends
a common `Unix signal`_, ``SIGUSR1``, to the **i3pyblocks** process. To do this
we will implement :meth:`~i3pyblocks.blocks.base.Block.signal_handler`:

.. code-block:: python

    import signal

    from i3pyblocks import Runner, blocks, utils

    class HelloWorldBlock(blocks.Block):
        async def signal_handler(self, *, sig: signal.Signals) -> None:
            if sig == signal.SIGUSR1:
                self.update("Bye!")

        async def start(self) -> None:
            self.update("Hello World!")


    async def main():
        runner = Runner()
        await runner.register_block(HelloWorldBlock(), signals=(signal.SIGUSR1,))
        await runner.start()


    utils.asyncio_run(main())

Now running this in one terminal and running ``pkill -SIGUSR1 i3pyblocks``
results in:

.. code-block:: sh

    $ i3pyblocks -c example.py
    {"version": 1, "click_events": true}
    [
    [{"name": "HelloWorldBlock", "instance": "<random-id>", "full_text": "Hello World!"}],
    [{"name": "HelloWorldBlock", "instance": "<random-id>", "full_text": "Bye!"}],
    ^C

To handle mouse clicks, there is a similar method called
:meth:`~i3pyblocks.blocks.base.Block.click_handler` that you can implement.
in a similar way.

.. _`Unix signal`:
    https://en.wikipedia.org/wiki/Signal_(IPC)

When to use each base block?
----------------------------

Generally using :class:`~i3pyblocks.blocks.base.PollingBlock` is the easiest
way to start. However it is not necessary the most efficient way.

For example, volume is not something that is changed frequently. You may
change the volume of your system once or twice until you find a confortable
volume for what you're currently listening, and keep the same volume for
hours. So, querying the system each second for the current volume seems
unnecessary.

If you want to be efficient, in those cases you need to have an `event loop`_.
An event loop waits for some kind of event (for example, increase or decrease
in volume), and after we receives this event we trigger an update. This is
exactly what :class:`~i3pyblocks.blocks.pulse.PulseAudioBlock` does, waiting
for any change in the `PulseAudio`_ configuration to trigger updates.

Implementing an event loop goes out the scope of this tutorial, but keep in mind
that there is generally a `Python package`_ that does it for you, and all you need
is to add it as a dependency to **i3pyblocks** and integrate it inside a block.
For this, you can use :class:`~i3pyblocks.blocks.base.Block` as we saw before,
for projects that integrates well with `asyncio`_. Just implement
:meth:`~i3pyblocks.blocks.base.Block.start` with something like this:

.. code-block:: python

    async def start(self):
        while True:
            result = await wait_for_event_loop()
            self.update(result)

However, some projects doesn't integrate well with *asyncio* (i.e.: their
methods are not *async*). Using them with :class:`~i3pyblocks.blocks.base.Block`
would freeze **i3pyblocks** completely until some update on them happened.
In those cases, you can use :class:`~i3pyblocks.blocks.base.ExecutorBlock`.
It runs the code inside an `Executor`_, that can be either a thread or a process,
so the updates inside this block doesn't affect the rest of **i3pyblocks**. The
usage ends up being very similar to before, just without *async/await* keywords:

.. code-block:: python

    def start(self):
        while True:
            result = wait_for_event_loop()
            self.update(result)

.. _`event loop`:
     https://en.wikipedia.org/wiki/Event_loop
.. _`PulseAudio`:
     https://en.wikipedia.org/wiki/PulseAudio
.. _`Python package`:
     https://pypi.org/
.. _`asyncio`:
     https://docs.python.org/3/library/asyncio.html
.. _`Executor`:
    https://docs.python.org/3/library/concurrent.futures.html

Handling dependencies
---------------------

To add a new dependency to **i3pyblocks**, add it to ``setup.py`` file in
``extras_require`` section, using the namespace of your module without
``i3pyblocks``. For example, if your module depend on ``foo`` version ``>=1.0``
and any version of ``bar`` and it uses the namespace ``i3pyblocks.blocks.spam``,
add the following to ``setup.py``:

.. code-block:: python

    extras_require={
        # ...
        "blocks.spam": ["foo>=1.0", "bar"],
    }

Don't forget to add your module to ``requirements/dev.in`` file and run
``make deps`` to update the dev/CI dependencies.

Collaborating
-------------

i3pyblocks use `Continuous Integration (CI)`_ to ensure the quality of codebase.
We use `Black`_ to automatically format the code, `Read the Docs`_ to
automatically generate the documentation and multiple linters to check possible
issues of the code.

Also, writing automated tests are **strongly** recommended for new blocks since
they're the only way to ensure that we don't break something in case of changes.

If you want to test your modifications locally, you can use:

.. code-block:: sh

    $ make

This will run everything that the CI run. If you want to run only tests, use:

.. code-block:: sh

    $ make test

To run linters, use:

.. code-block:: sh

    $ make lint

To automatically fix code issues, run:

.. code-block:: sh

    $ make lint-fix

But keep in mind that not all fixes are automatically, so running ``make lint``
is still necessary.

.. _`Continuous Integration (CI)`:
    https://en.wikipedia.org/wiki/Continuous_integration
.. _`Black`:
    https://github.com/psf/black
.. _`Read the Docs`:
    https://readthedocs.org/
