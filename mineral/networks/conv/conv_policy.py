"""Author: Brandon Trabucco, Copyright 2019"""


from mineral.networks.conv.conv_network import ConvNetwork
from mineral.core.functions.policy import Policy


class ConvPolicy(ConvNetwork, Policy):

    def __init__(
        self,
        *args,
        **kwargs
    ):
        ConvNetwork.__init__(self, *args, **kwargs)

    def get_stochastic_actions(
        self,
        observations,
        **kwargs
    ):
        return self.sample(observations, **kwargs)

    def get_deterministic_actions(
        self,
        observations,
        **kwargs
    ):
        return self.get_expected_value(observations, **kwargs)
