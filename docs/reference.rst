Simantha Reference
==================


Manufacturing Objects
---------------------

The following classes make up the core manufacturing objects provided by Simantha. After
intatiating the objects of a system, the ``define_routing`` method must be called for
each object. The additional methods listed below are provided for extending the behavior
of these objects in various ways. 


.. warning::
   Currently there is no verification of system routing validity. A system with an 
   invalid routing may result in unexpected behavior with raising an error or warning.
   For instance, a buffer with no downstream machine may become full and cause a "dead 
   end" in the system of which the user will not be notified. 


simantha.Source class
^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: simantha.Source


simantha.Machine class
^^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: simantha.Machine


simantha.Buffer class
^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: simantha.Buffer


simantha.Sink class
^^^^^^^^^^^^^^^^^^^

.. autoclass:: simantha.Sink


Maintainer
----------

simantha.Maintainer class
^^^^^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: simantha.Maintainer


System
------

simantha.System class
^^^^^^^^^^^^^^^^^^^^^

A ``System`` object contains the configured manufacturing objects.

.. autoclass:: simantha.System


Simulation
----------

simantha.simulation module
--------------------------

.. automodule:: simantha.simulation
   :members:


Utilities
---------

simantha.utils module
^^^^^^^^^^^^^^^^^^^^^

.. automodule:: simantha.utils
   :members:
