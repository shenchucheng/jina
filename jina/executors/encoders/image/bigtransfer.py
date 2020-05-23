import numpy as np

from ..frameworks import BaseCVTFEncoder
from ...decorators import batching, as_ndarray


class BitImageEncoder(BaseCVTFEncoder):
    """
    :class:`BitImageEncoder` encodes data from a ndarray, potentially B x (Channel x Height x Width) into a
    ndarray of `B x D`.
    Internally, :class:`BitImageEncoder` wraps the models from https://storage.googleapis.com/bit_models/.
    """
    def __init__(self, model_path: str = None, channel_axis: int = -1, *args, **kwargs):
        """
        :param model_path: the path of the model in the `SavedModel` format. `model_path` should be a directory path,
            which has the following structure. The pretrained model can be downloaded at
            wget https://storage.googleapis.com/bit_models/Imagenet21k/[model_name]/feature_vectors/saved_model.pb
            wget https://storage.googleapis.com/bit_models/Imagenet21k/[model_name]/feature_vectors/variables/variables.data-00000-of-00001
            wget https://storage.googleapis.com/bit_models/Imagenet21k/[model_name]/feature_vectors/variables/variables.index

            ``[model_name]`` includes `R50x1`, `R101x1`, `R50x3`, `R101x3`, `R152x4`

        .. highlight:: bash
        .. code-block:: bash

            .
            ├── saved_model.pb
            └── variables
                ├── variables.data-00000-of-00001
                └── variables.index

        :param channel_axis: the axis id of the channel, -1 indicate the color channel info at the last axis.
                If given other, then ``np.moveaxis(data, channel_axis, -1)`` is performed before :meth:`encode`.
        """
        super().__init__(*args, **kwargs)
        self.channel_axis = channel_axis
        self.model_path = model_path

    def post_init(self):
        self.to_device()
        import tensorflow as tf
        self.model = None
        try:
            _model = tf.saved_model.load(self.model_path)
        except Exception:
            self.logger.error(f'model initialization failed: {self.model_path}')
            return
        self.model = _model.signatures["serving_default"]
        self._get_input = tf.convert_to_tensor

    @batching
    @as_ndarray
    def encode(self, data: 'np.ndarray', *args, **kwargs) -> 'np.ndarray':
        if self.channel_axis != -1:
            data = np.moveaxis(data, self.channel_axis, -1)
        _output = self.model(self._get_input(data.astype(np.float32)))
        return _output['output_1'].numpy()
