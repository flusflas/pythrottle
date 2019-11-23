============================================
Welcome to Throttling-Utils's documentation!
============================================

This project offers some convenient tools for throttling and controlling
the execution of functions or iterative blocks of Python code.

Key Features
============

 - Simple and time-accurate loop iterations
 - Support for synchronous and asynchronous programming
 - Rate limiting consecutive function calls
 - Rate measurement for loops

Library Installation
====================

.. code-block:: bash

   $ pip install throttling-utils

Getting started
===============

A basic use for throttling the execution of a code block is using
:func:`Throttle.sleep_loop() <throttle.Throttle.sleep_loop>`
(or :func:`Throttle.wait_loop() <throttle.Throttle.wait_loop>` for
asynchronous mode). This will allow execution of the code every ``1 / rate``
seconds:

.. code-block:: python3

    from throttle import Throttle

    rate = 24.0     # Target rate
    t = Throttle(interval=(1 / rate))

    for i in t.sleep_loop():
        # Do something
        print(f"Iteration {i}")


The next example code records a video file from the default video source at an
accurate frame rate of 24 fps using OpenCV.

.. code-block:: python3

    import cv2
    from throttle import Throttle

    rate = 24.0     # Target frame rate
    cap = cv2.VideoCapture(0)
    out = cv2.VideoWriter('output.avi', cv2.VideoWriter_fourcc(*'XVID'),
                          rate, (640, 480))

    t = Throttle(interval=(1 / rate))

    for _ in t.sleep_loop():
        ret, frame = cap.read()    # Frame capture
        out.write(frame)           # Save frame to output file

        # Display the resulting frame
        cv2.imshow('frame', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

If you simply `sleep() <https://docs.python.org/3/library/time.html?highlight=time%20sleep#time.sleep>`_ for ``1 / 24`` seconds between frame capture, there
would be a difference between the capture rate and the output video rate
because of the time required for frame capture. If you also add image
processing (motion detection, text overlay...), the delay could cause the
output to be completely out of sync.


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   modules/throttle
   modules/rate_meter


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
