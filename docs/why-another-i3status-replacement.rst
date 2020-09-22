Why another i3status replacement?
=================================

Let me tell a history about a long time i3wm user and Python programmer.

When I started using i3wm, like many of you, I kept hopping between `i3status`_
implementations. I started at `py3status`_, used `i3pystatus`_ for years, tried
`i3blocks`_, used `bumblebee-status`_ for a while, played with `polybar`_, until
eventually settling down on `i3status-rust`_ more recently.

I really liked some of the design choices of *i3status-rust*. For example, the
fact that it uses events like D-Bus instead of `polling`_ to update the i3bar.
This helped removed all my configuration hacks for sending signals after i.e.:
increasing the volume.

But I yearned for the flexibility of a real programming language, something that
the configuration of *i3status-rust* (that is configured using `TOML`_) didn't
bring to me. I wrote a Python script just to generate my *i3status-rust*
configuration because *i3status-rust* never seemed flexible enough for my needs.

This was always something that I loved in *i3pystatus*, and for some time I
thought about going back. But since changing distros (from Arch to NixOS), I
needed to do some fixes so my previous setup would work, and the PRs I opened
in *i3pystatus* were never reviewed (it used to be very fast). The project
itself seemed quite dead [1]_. At that point, I decided I had two options:

- Maintain my own fork of *i3pystatus*
- Create a new project from scratch

I tried the first option, but *i3pystatus* project is huge and I didn't want
to maintain everything. But even trying to reduce the project to just what I
needed seemed to be a huge task. I also wanted a modern Python codebase,
while *i3pystatus* had many solutions that predates some of the later features
introduced on Python's stdlib [2]_.

So I decided to start a new project that it is this one. I was also interested
in testing `asyncio`_ and this seemed to be the perfect project to use it,
since by definition each block must be independent from another. After playing
with it a little and making a proof-of-concept, I started to implement
multiple ``blocks`` (still called ``modules`` at the time) for my necessities
and also new features accordingly I was needing it. Eventually, I substituted
my old *i3status-rust* config and **i3pyblocks** was officialy born.

Many of the design choices are inspired from *i3pystatus*, specially the strong
focus on customization and usage of Python's `format`_ string when possible to
make the design of i3bar really flexible. Also the fact that this is a library
and not a Python's program, meaning that you can extend it as you want if you
have the right skills.

But of course not everything is the same. For one, the usage of asyncio vs.
the more traditional threading approach from *i3pystatus* makes for some really
interesting techniques to update the i3bar. AFAIK, i3pyblocks is the only
Python-based i3bar's protocol implementation that have a completely asynchronous
update of each individual block.

In i3pyblocks, a `Queue`_ is responsible to receive any updates from each
block, and once there is something to update the i3bar is refreshed. If you
have a bar with blocks that only update at each minute, for example, the number
of drawings in i3bar will be much less than other polling-based solutions.

Also, inspired by *i3status-rs* many blocks does a much smarter update technique
than simply polling. For example, :class:`i3pyblocks.blocks.inotify.BacklightBlock`
uses `inotify`_ to listen to any updates to ``/sys/class/backlight/*`` before
updating the i3bar. This brings two advantages:

- More efficient, since the i3bar is only updated when necessary
- Faster updates, since any change in backlight will trigger a i3bar update
  instantaneously

So this is basically it. If I didn't convice you to use i3pyblocks with
this text probably this project is not for you. But if the text above made
you interested about this project, then maybe this is the project for you.

.. [1] This was around mid~end of 2019. The *i3pystatus* project seems much
   better nowadays (mid 2020).
.. [2] I am not saying that *i3pystatus* codebase is bad, just some solutions
   are old and I wanted to avoid them. Actually, the core code from *i3pystatus*
   seems to be very high quality.
.. _i3status:
   https://i3wm.org/i3status/manpage.html
.. _py3status:
   https://github.com/ultrabug/py3status
.. _i3pystatus:
   https://github.com/enkore/i3pystatus
.. _i3blocks:
   https://github.com/vivien/i3blocks
.. _bumblebee-status:
   https://github.com/tobi-wan-kenobi/bumblebee-status
.. _polybar:
   https://github.com/polybar/polybar
.. _i3status-rust:
   https://github.com/greshake/i3status-rust
.. _polling:
   https://en.wikipedia.org/wiki/Polling_(computer_science)
.. _TOML:
   https://en.wikipedia.org/wiki/TOML
.. _format:
   https://pyformat.info/
.. _Queue:
   https://docs.python.org/3/library/asyncio-queue.html
.. _inotify:
   https://en.wikipedia.org/wiki/Inotify
.. _asyncio:
   https://docs.python.org/3/library/asyncio.html
