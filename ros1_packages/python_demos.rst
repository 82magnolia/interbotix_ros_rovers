============
Python Demos
============

.. raw:: html

    <a href="https://github.com/Interbotix/interbotix_ros_rovers/tree/main/interbotix_ros_xslocobots/examples/python_demos"
        class="docs-view-on-github-button"
        target="_blank">
        <img src="../_static/GitHub-Mark-Light-32px.png"
            class="docs-view-on-github-button-gh-logo">
        View Package on GitHub
    </a>

Overview
========

This page showcases various ways of using the `Interbotix Python LoCoBot Module`_ (click the link
to see the fully documented code). Simply put, this API was created so that users with little to no
ROS experience would still have the ability to control any Interbotix LoCoBot supported by the
`interbotix_xs_sdk`. Specifically, the API also allows a user to make an arm go to desired
end-effector poses or follow Cartesian trajectories. This last feature was made possible by the
`Modern Robotics: Mechanics, Planning, and Control Code Library`_ created at Northwestern
University. It also allows the ability to move the camera pan/tilt servos and send velocity
commands to the base.

.. _`Interbotix Python LoCoBot Module`: https://github.com/Interbotix/interbotix_ros_toolboxes/blob/main/interbotix_xs_toolbox/interbotix_xs_modules/src/interbotix_xs_modules/locobot.py
.. _`Modern Robotics: Mechanics, Planning, and Control Code Library`: https://github.com/NxRLab/ModernRobotics

For the API to work, the arm and pan/tilt joints must be set to 'position' control and the gripper
set to 'PWM' control (conveniently, these are the default configs in the
`interbotix_xslocobot_control` package). Furthermore, the API assumes that all the arm-joint
motors' `Drive Mode`_ registers are set to `Time-Based-Profile`_ (this is also the default
configuration). In a nutshell, this setting makes it very easy for you as the user to customize the
duration and smoothness of an arm's motion from one pose to the next.

.. _`Drive Mode`: http://emanual.robotis.com/docs/en/dxl/x/xm430-w350/#profile-velocity112
.. _`Time-Based-Profile`: http://emanual.robotis.com/docs/en/dxl/x/xm430-w350/#drive-mode

Structure
=========

.. image:: images/xslocobot_python_demos_flowchart.png
    :align: center

The Python LoCoBot module (located in the `interbotix_xs_modules` ROS package) builds on top of the
`interbotix_xs_sdk` package. To get familiar with the other nodes in the graph above, look at the
various packages READMEs.

- **robot_manipulation** - a ROS node (operating 'behind the scenes') that takes in commands
  entered via the Python API and publishes data to various ROS topics as necessary. It is not a
  classic ROS node in the sense that it can't be launched from a ROS launch file or run from the
  terminal using a ``rosrun`` command. Rather, the Python API module contains a class that when
  instantiated, gives the node life. At the completion of a program, the object gets destroyed,
  killing the node.

Usage
=====

To get started, open up a terminal and type (assuming the locobot_wx250s is being launched with the
lidar shown but not active)...

.. code-block:: console

    $ roslaunch interbotix_xslocobot_control xslocobot_python.launch robot_model:=locobot_wx250s show_lidar:=true

In another terminal, navigate to this directory and type...

.. code-block:: console

    $ python bartender.py        # python3 bartender.py if using ROS Noetic

You should observe the robot pick up a virtual bottle (from behind a virtual bar), rotate so that
the end-effector is facing the opposite direction, pour a virtual drink (on the virtual bar), then
place the 'bottle' down, and go to its Sleep pose.

The other scripts work in a similar fashion, but you must make sure to change the robot name in the
file to the arm you have. You might also have to adjust the commanded poses/trajectories if working
with smaller arm models (like the PincherX 100) as some of them might by physically unattainable.
To make things easier, each script also outlines the commands necessary to get the robot moving!

.. note::

    If you want to test out your code first on a simulated arm, make sure to set the ``use_sim``
    arg to true like this:

    .. code-block:: console

        $ roslaunch interbotix_xslocobot_control xslocobot_python.launch robot_model:=locobot_wx250s show_lidar:=true use_sim:=true

For reference, other launch file arguments are shown below. Depending on if you are doing SLAM,
perception, or arm manipulation, you can start the launch file accordingly.

.. csv-table::
    :file: ../_data/python_demos.csv
    :header-rows: 1
    :widths: 20 60 20

.. _`xslocobot_python.launch`: https://github.com/Interbotix/interbotix_ros_rovers/blob/main/interbotix_ros_xslocobots/interbotix_xslocobot_control/launch/xslocobot_python.launch
.. _`xslocobot_nav.launch`: https://github.com/Interbotix/interbotix_ros_rovers/blob/main/interbotix_ros_xslocobots/interbotix_xslocobot_nav/launch/xslocobot_nav.launch

Video Tutorials
===============

Open Source Example Packages on the LoCoBot
-------------------------------------------

.. youtube:: xIril2gF0-Y
    :align: center
    :width: 70%
