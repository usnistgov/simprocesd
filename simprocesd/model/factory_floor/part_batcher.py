from .batch import Batch
from .part_handler import PartHandler


class PartBatcher(PartHandler):
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
        Name of the Asset. If name is None then a default name will be
        used: <class_name>_<asset_id>
    upstream: list of PartFlowController, default=None
        List of devices from which Parts can be received.
    value: float, default=0
        Starting value of the Asset.
    output_batch_size: int, default=None
        Specify the batch size for the output. If set to None then
        the output will be individual Parts.
    '''

    def __init__(self, name = None, upstream = None, value = 0, output_batch_size = None):
        super().__init__(name, upstream, 0, value)
        assert output_batch_size == None or output_batch_size > 0, \
                    f'output_batch_size ({output_batch_size}) cannot be 0 or less.'
        self._output_batch_size = output_batch_size
        self._in_progress_batch = None

    @property
    def output_batch_size(self):
        '''Output Batch size. If None then the output will be individual
        Parts instead of Batches.
        '''
        return self._output_batch_size

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

    def _pass_part_downstream(self):
        super()._pass_part_downstream()
        if self._output == None:
            self._try_move_part_to_output()

