import numpy as np
import threading


class ReplayBuffer:
    """
    The buffer is stored in self.buffers.

    Keys:
        o: observation of all agents
        u: actions agents chose
        s: state of environment
        r: reward
        o_next: next observation
        s_next: next state of environment
        avail_u: actions that were available for all agents
        avail_u_next: next actions that are available for all agents
        u_onehot: onehot representation of actions agents chose
        padded: whether this step is a padded data
        terminated: whether game terminates in this step

    *Key for maven:
        z: hidden state
    """
    def __init__(self, args):
        self.args = args
        self.n_actions = self.args.n_actions
        self.n_agents = self.args.n_agents
        self.state_shape = self.args.state_shape
        self.obs_shape = self.args.obs_shape
        self.size = self.args.buffer_size
        self.episode_limit = self.args.episode_limit
        # memory management
        self.current_idx = 0
        self.current_size = 0
        # create the buffer to store info
        self.buffers = {'o': np.empty([self.size, self.episode_limit, self.n_agents, self.obs_shape]),
                        'u': np.empty([self.size, self.episode_limit, self.n_agents, 1]),
                        's': np.empty([self.size, self.episode_limit, self.state_shape]),
                        'r': np.empty([self.size, self.episode_limit, 1]),
                        'o_next': np.empty([self.size, self.episode_limit, self.n_agents, self.obs_shape]),
                        's_next': np.empty([self.size, self.episode_limit, self.state_shape]),
                        'avail_u': np.empty([self.size, self.episode_limit, self.n_agents, self.n_actions]),
                        'avail_u_next': np.empty([self.size, self.episode_limit, self.n_agents, self.n_actions]),
                        'u_onehot': np.empty([self.size, self.episode_limit, self.n_agents, self.n_actions]),
                        'padded': np.empty([self.size, self.episode_limit, 1]),
                        'terminated': np.empty([self.size, self.episode_limit, 1])
                        }
        if self.args.alg == 'maven':
            self.buffers['z'] = np.empty([self.size, self.args.noise_dim])
        # thread lock
        self.lock = threading.Lock()

        # store the episode
    def store_episode(self, episode_batch: dict):
        batch_size = episode_batch['o'].shape[0]  # episode_number
        with self.lock:
            idxs = self._get_storage_idx(inc=batch_size)
            # store the informations
            for key in episode_batch.keys():
                self.buffers[key][idxs] = episode_batch[key]

    def sample(self, batch_size):
        temp_buffer = {}
        idx = np.random.randint(0, self.current_size, batch_size)
        for key in self.buffers.keys():
            temp_buffer[key] = self.buffers[key][idx]
        return temp_buffer

    def _get_storage_idx(self, inc=None):
        inc = inc or 1
        if self.current_idx + inc <= self.size:
            idx = np.arange(self.current_idx, self.current_idx + inc)
            self.current_idx += inc
        elif self.current_idx < self.size:
            overflow = inc - (self.size - self.current_idx)
            idx_a = np.arange(self.current_idx, self.size)
            idx_b = np.arange(0, overflow)
            idx = np.concatenate([idx_a, idx_b])
            self.current_idx = overflow
        else:
            idx = np.arange(0, inc)
            self.current_idx = inc
        self.current_size = min(self.size, self.current_size + inc)
        if inc == 1:
            idx = idx[0]
        return idx
