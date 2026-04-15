===============
LoCoBot Control
===============

.. raw:: html

    <a href="https://github.com/Interbotix/interbotix_ros_rovers/tree/main/interbotix_ros_xslocobots/interbotix_xslocobot_control"
        class="docs-view-on-github-button"
        target="_blank">
        <img src="../_static/GitHub-Mark-Light-32px.png"
            class="docs-view-on-github-button-gh-logo">
        View Package on GitHub
    </a>

Overview
========

This package contains the configuration and launch files necessary to easily start the various
components of the X-Series LoCoBot platform. This includes launching the **xs_sdk** node
responsible for driving the DYNAMIXEL motors on the robot, loading the URDF to the
``robot_description`` parameter, starting the mobile base, and activating the RealSense D435 camera
and RPLidar 2D laser scanner. Essentially, this package is what all 'downstream' ROS packages
should reference to get the robot up and running.

Structure
=========

.. image:: images/xslocobot_control_flowchart.png
    :align: center

As shown in the image above, the *interbotix_xslocobot_control* package builds on top of the
*interbotix_xslocobot_descriptions* and *interbotix_xs_sdk* packages among many others. To get
familiar with the nodes not described below, just hop over to the ROS packages in this repo that
launches them.

-   **rplidarNode**: responsible for starting the `A2 RPlidar`_ sensor and publishing
    `LaserScan`_ messages on the ``/<robot_name>/scan`` topic. See the `RPLidar ROS Wiki`_ for
    parameter descriptions. All parameters were left at their default values except for the
    following:

    -   *frame_id*: ``/<robot_name>/laser_frame_link``
    -   *serial_port*: ``/dev/rplidar``
    -   *angle_compensate*: ``true``

-   **kobuki nodes**: a group of three nodes responsible for starting the Kobuki base. See the
    `Kobuki ROS Wiki`_ for parameter descriptions. All parameters were left at their default values
    except for the following:

    -   *odom_frame*: ``/<robot_name>/odom``
    -   *base_frame*: ``/<robot_name>/base_footprint``
    -   *acceleration_limiter*: ``true``

-   **rs_rgbd.launch**: launches four nodes to run the `RealSense D435`_ camera and publish a
    variety of image topics. Note that the `base_link` frame of the camera is in the depth frame
    and is called ``/<robot_name>/camera_link``. See the `realsense_ros`_ repository for parameter
    descriptions. All parameters were left at their default values except for the following:

    - *tf_prefix*: ``/<robot_name>/camera``
    - *enable_infra1*: ``true``
    - *enable_infra2*: ``true``

You will also notice a `config`_ directory containing many YAML files. Each file (beside the
modes.yaml one) specifies the names and initial register values for all the motors that make up a
specific locobot. There is also some 'meta-info' like names of joint groups, the desired
joint-topic name and publishing frequency, etc... For a full explanation of each of these
parameters, check out the `Motor Config file template`_. The other file located in that directory
is the Mode Config one (a.k.a mode.yaml). The parameters in there define the desired operating
modes for either a group of joints or single joints, and whether or not they should be torqued
on/off at node startup. See more by referencing the `Mode Config file template`_. Typically, the
Motor Config file is only defined here while the Mode Config file is also defined in any
'downstream' ROS package. This makes it easy for users to configure their desired motor operating
modes depending on their project.

.. _`A2 RPlidar`: https://www.slamtec.com/en/Lidar/A2
.. _`LaserScan`: http://docs.ros.org/latest/api/sensor_msgs/html/msg/LaserScan.html
.. _`RPLidar ROS Wiki`: http://wiki.ros.org/rplidar
.. _`Kobuki ROS Wiki`: http://wiki.ros.org/kobuki_node
.. _`RealSense D435`: https://www.intelrealsense.com/depth-camera-d435/
.. _`realsense_ros`: https://github.com/IntelRealSense/realsense-ros
.. _`config`: https://github.com/Interbotix/interbotix_ros_rovers/blob/main/interbotix_ros_xslocobots/interbotix_xslocobot_control/config
.. _`Motor Config file template`: https://github.com/Interbotix/interbotix_ros_core/blob/main/interbotix_ros_xseries/interbotix_xs_sdk/config/motor_configs_template.yaml
.. _`Mode Config file template`: https://github.com/Interbotix/interbotix_ros_core/blob/main/interbotix_ros_xseries/interbotix_xs_sdk/config/mode_configs_template.yaml

Usage
=====

To run this package on the physical robot, type the line below in a terminal
(assuming the ``locobot_wx200`` is being launched with the onboard lidar and
camera).

.. code-block:: console

    $ roslaunch interbotix_xslocobot_control xslocobot_control.launch robot_model:=locobot_wx200 use_base:=true use_lidar:=true use_camera:=true

If you are working from a remote computer and would like to visualize the robot using RViz, open a
terminal on your remote and type...

.. code-block:: console

    $ roslaunch interbotix_xslocobot_descriptions remote_view.launch

Note that in order for this to work, you must first run the `remote installation`_ script on your
remote computer.

.. _`remote installation`: https://docs.trossenrobotics.com/interbotix_xslocobots_docs/ros_interface/ros1/software_setup.html#remote-install

To further customize the launch file at run-time, refer to the table below.

.. csv-table::
    :file: ../_data/locobot_control.csv
    :header-rows: 1
    :widths: 20, 60, 20

.. _`refer to xslocobot_control.launch`: https://github.com/Interbotix/interbotix_ros_rovers/blob/main/interbotix_ros_xslocobots/interbotix_xslocobot_control/launch/xslocobot_control.launch
