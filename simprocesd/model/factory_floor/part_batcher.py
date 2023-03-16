from .batch import Batch
from .device import Device


class PartBatcher(Device):
    '''Organize input items into Batches of specific size or into
    individual Parts.

    Can accept Parts and Batches of Parts and re-organize them into the
    specified output format. PartBatcher has an internal buffer where
    it keeps excess input Parts and incomplete output Batches.

    Notes
    -----
    Output Batches are always newly created even if input is made up of
    Batches.
    Input Batch is always lost while Parts contained within it are kept.

    Arguments
    ---------
    name: str, default=None
        Name of the Device. If name is None then the Device's name will
        be changed to Device_<id>
    upstream: list, default=None
        A list of upstream Device objects.
    value: float, default=0
        Starting value of the Device.
    output_batch_size: int, default=None
        Specify the batch size for the output. If set to None then
        the output will be individual Parts.
    '''

    def __init__(self, name = None, upstream = None, value = 0, output_batch_size = None):
        super().__init__(name, upstream, value)
        assert output_batch_size == None or output_batch_size > 0, \
                    f'output_batch_size ({output_batch_size}) cannot be 0 or less.'
        self._output_batch_size = output_batch_size
        self._in_progress_batch = None

    def initialize(self, env):
        super().initialize(env)

    def _try_move_part_to_output(self):
        if not self.is_operational() or self._part == None or self._output != None:
            return
        # If input Batch has no Parts then delete it.
        if isinstance(self._part, Batch) and len(self._part.parts) <= 0:
            self._part = None
            return

        while self._output == None and self._part != None:
            part_in_transition = self._get_part_from_input()
            self._add_part_to_output(part_in_transition)

        if self._output != None:
            self._schedule_pass_part_downstream()

    def _get_part_from_input(self):
        if isinstance(self._part, Batch):
            part = self._part.parts.pop(0)
            if len(self._part.parts) <= 0:
                self._part = None
        else:  # self._part is a single Part
            part = self._part
            self._part = None
        return part

    def _add_part_to_output(self, part):
        if self._output_batch_size == None:
            self._output = part
        else:  # Output is a Batch
            if self._in_progress_batch == None:
                self._in_progress_batch = Batch()
                self._in_progress_batch.initialize(self.env)
            self._in_progress_batch.parts.append(part)

            if len(self._in_progress_batch.parts) >= self._output_batch_size:
                self._output = self._in_progress_batch
                self._in_progress_batch = None

