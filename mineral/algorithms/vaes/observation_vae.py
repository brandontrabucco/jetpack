"""Author: Brandon Trabucco, Copyright 2019"""


import tensorflow as tf
from mineral.algorithms.vaes.vae import VAE


class ObservationVAE(VAE):

    def __init__(
        self,
        *args,
        **kwargs
    ):
        VAE.__init__(
            self,
            *args,
            **kwargs
        )

    def update_algorithm(
        self,
        observations,
        actions,
        rewards,
        terminals
    ):
        def loss_function():
            log_probs_vae = self.vae_network.get_log_probs(
                observations,
                observations,
                training=True
            )
            loss_vae = -1.0 * tf.reduce_mean(
                log_probs_vae
            )
            if self.monitor is not None:
                self.monitor.record(
                    "vae_target",
                    observations[0, (-1):, ...]
                )
                self.monitor.record(
                    "vae_reconstruction",
                    self.vae_network.get_expected_value(observations[0, (-1):, ...])
                )
                self.monitor.record(
                    "vae_prior",
                    self.vae_network.sample_from_prior()
                )
                self.monitor.record(
                    "log_probs_vae_mean",
                    tf.reduce_mean(log_probs_vae)
                )
                self.monitor.record(
                    "loss_vae",
                    loss_vae
                )
            return loss_vae
        self.vae_network.minimize(
            loss_function,
            observations
        )
