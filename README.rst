pythrottle
==========

|pipeline status| |coverage report|

.. |pipeline status| image:: https://travis-ci.com/flusflas/pythrottle.svg?branch=master
   :target: https://travis-ci.com/github/flusflas/pythrottle
.. |coverage report| image:: https://codecov.io/gh/flusflas/pythrottle/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/flusflas/pythrottle

This project offers some convenient tools for throttling and controlling
the execution timing of functions or iterative blocks of Python code.

Key Features
------------

-  Simple and time-accurate loop iterations.
-  Support for synchronous and asynchronous programming.
-  Rate limiting consecutive function calls.
-  Rate measurement for loops.

Installation
------------

.. code:: console

    $ pip install pythrottle

Getting started
---------------

Throttle
~~~~~~~~

A basic use for throttling the execution of a code block is using
``Throttle.loop()`` (or ``Throttle.aloop()`` for asynchronous mode).
This will allow execution of the code every ``1 / rate`` seconds:

.. code:: python

    from throttle import Throttle

    rate = 2.0     # Target rate
    t = Throttle(interval=(1 / rate))

    for i in t.loop():
        # Do something
        print(f"Iteration {i}")

The next example code records a 15-seconds video file from the default
video source at an accurate frame rate of 24 fps using
`OpenCV <https://opencv-python-tutroals.readthedocs.io/en/latest/>`__.

.. code:: python

    import cv2
    from throttle import Throttle

    rate = 24.0             # Target frame rate
    cap = cv2.VideoCapture(0)
    out = cv2.VideoWriter('output.avi', cv2.VideoWriter_fourcc(*'XVID'),
                          rate, (640, 480))

    t = Throttle(interval=(1 / rate))

    for _ in t.loop(duration=15.0):
        ret, frame = cap.read()    # Frame capture
        out.write(frame)           # Save frame to output file

        # Display the resulting frame
        cv2.imshow('frame', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

If you simply
`sleep() <https://docs.python.org/3/library/time.html?highlight=time%20sleep#time.sleep>`__
for ``1 / 24`` seconds between frame capture, there would be a
difference between the capture rate and the output video rate because of
the time required for frame capture. If you also add image processing
(motion detection, text overlay...), the delay could cause the output to
be completely out of sync.

Throttle decorators
~~~~~~~~~~~~~~~~~~~

You can also use ``throttle.throttle()`` and ``throttle.athrottle()``
decorators to limit the number of calls to a function. In the next
example, the function ``hello()`` is decorated to rate-limit the
``/throttled`` endpoint, using a
`Flask <https://palletsprojects.com/p/flask/>`__ server. Only 2 requests
will be served every 5 seconds.

.. code:: python

    from flask import Flask
    from throttle import throttle

    app = Flask(__name__)

    @app.route("/throttled")
    @throttle(limit=2, interval=5, on_fail=("Limit reached :(", 429))
    def hello():
        return "Hi, Throttle!"

    if __name__ == '__main__':
        app.run()

Decorators can be nested to create more complex throttling rules.

Rate Meter
~~~~~~~~~~

``RateMeter`` class is useful for measuring the rate of an iterative
code taking into account only the last few seconds, so the measured
value is kept updated.

The next code block prints the execution rate of a loop that starts
looping at 10 ips (iterations per second) and decreases up to 5 ips. In
each iteration, the rate is displayed and updated taking into account
the iterations history of the last 2 seconds.

.. code:: python

    import time
    from rate_meter import RateMeter

    rate_meter = RateMeter(interval=2.0)

    for i in range(100):
        rate_meter.update()
        measured_rate = rate_meter.rate()
        print(f"Rate: {rate_meter.rate()}")
        time.sleep(0.1 + i * 0.001)

License
-------

Distributed under the terms of the `MIT License <LICENSE>`__.
