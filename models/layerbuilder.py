import torch.nn as nn
from torch import nn as nn


def conv_output_shape(h_w, kernel_size=1, stride=1, pad=0, dilation=1):
    """
    Utility function for computing output of convolutions
    takes a tuple of (h,w) and returns a tuple of (h,w)
    """
    from math import floor
    if type(kernel_size) is int:
        kernel_size = (kernel_size, kernel_size)
    h = floor(((h_w[0] + (2 * pad) - (dilation * (kernel_size[0] - 1)) - 1) / stride) + 1)
    w = floor(((h_w[1] + (2 * pad) - (dilation * (kernel_size[1] - 1)) - 1) / stride) + 1)
    return h, w

"""
M -> MaxPooling
L -> Capture Activations for Perceptual loss
U -> Bilinear upsample
"""


class LayerBuilder:
    def __init__(self):
        self.layers = []
        self.shape = ()
        self.output_channels = None
        self.nonlinearity = None

    @staticmethod
    def initialize_weights(f):
        pass

    def make_block(self, in_channels, v):
        pass

    def make_layers(self, cfg, input_shape, nonlinearity=None, nonlinearity_kwargs=None):
        self.layers = []
        self.shape = input_shape
        self.output_channels = nonlinearity_kwargs
        self.nonlinearity = nonlinearity

        nonlinearity_kwargs = {} if nonlinearity_kwargs is None else nonlinearity_kwargs
        self.nonlinearity = nn.ReLU(inplace=True) if nonlinearity is None else nonlinearity(**nonlinearity_kwargs)

        self.shape = input_shape

        in_channels = cfg[0]
        for v in cfg[1:]:
            if v == 'M':
                self.layers += [nn.MaxPool2d(kernel_size=2, stride=2)]
                self.shape = (self.shape[0], *conv_output_shape(self.shape[1:3], kernel_size=2, stride=2))
                if min(*self.shape[1:3]) <= 0:
                    raise Exception('Image downsampled to 0 or less, use less downsampling')

            elif v == 'U':
                self.layers += [nn.UpsamplingBilinear2d(scale_factor=2)]
                self.shape = (self.shape[0], self.shape[1] * 2, self.shape[2] * 2)
            else:
                self.make_block(in_channels, v)
                in_channels = v

        layer = nn.Sequential(*self.layers)
        self.initialize_weights(layer)
        return layer, self.shape


class FCBuilder(LayerBuilder):

    @staticmethod
    def initialize_weights(f):
        for m in f.modules():
            if isinstance(m, nn.Linear):
                nn.init.normal_(m.weight)
                nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.BatchNorm1d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)

    def make_block(self, in_channels, v):
        self.layers += [nn.Linear(in_channels, v)]
        self.layers += [nn.BatchNorm1d(v)]
        self.layers += [self.nonlinearity]
        self.shape = (v,)