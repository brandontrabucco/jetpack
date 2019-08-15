"""Author: Brandon Trabucco, Copyright 2019"""


import tensorflow as tf
from mineral.algorithms.critics.q_learning import QLearning
from mineral import discounted_sum


class SoftQLearning(QLearning):

    def __init__(
        self,
        *args,
        alpha=1.0,
        **kwargs
    ):
        QLearning.__init__(
            self,
            *args,
            **kwargs)
        self.alpha = alpha

    def bellman_target_values(
        self,
        observations,
        actions,
        rewards,
        terminals
    ):
        next_actions = self.policy.get_expected_value(
            observations[:, 1:, ...],
            training=True)
        next_log_probs = self.policy.get_log_probs(
            next_actions,
            observations[:, 1:, ...],
            training=True)
        epsilon = tf.clip_by_value(
            self.std * tf.random.normal(
                tf.shape(next_actions),
                dtype=tf.float32), -self.clip_radius, self.clip_radius)
        noisy_next_actions = next_actions + epsilon
        next_target_qvalues = self.target_qf.get_expected_value(
            observations[:, 1:, ...],
            noisy_next_actions,
            training=True)
        target_values = rewards + (
            terminals[:, 1:] * self.gamma * (
                next_target_qvalues[:, :, 0] - self.alpha * next_log_probs))
        self.record(
            "bellman_target_values_mean",
            tf.reduce_mean(target_values))
        return target_values

    def discount_target_values(
        self,
        observations,
        actions,
        rewards,
        terminals
    ):
        log_probs = terminals[:, :(-1)] * self.policy.get_log_probs(
            actions,
            observations[:, :(-1), ...],
            training=True)
        discount_target_values = discounted_sum((
            rewards - self.alpha * log_probs), self.gamma)
        self.record(
            "discount_target_values_mean",
            tf.reduce_mean(discount_target_values))
        return discount_target_values

    def update_critic(
        self,
        observations,
        actions,
        rewards,
        terminals,
        bellman_target_values,
        discount_target_values
    ):
        QLearning.update_critic(
            self,
            observations,
            actions,
            rewards,
            terminals,
            bellman_target_values,
            discount_target_values)
