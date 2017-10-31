from __future__ import print_function
from __future__ import division
import gym
import numpy as np
import math
import time
import os
import random
import BLM
from cntk import distributed
from cntk.train import *

import cntk as C

isFast = False
TOTAL_EPISODES = 2000 if isFast else 20000
OBSERVE = TOTAL_EPISODES / 2

env = BLM.BLM(3)

STATE_COUNT = env.observation_space.shape
ACTION_COUNT = env.action_space.n

# Targetted reward
REWARD_TARGET = 5000
# Averaged over these these many episodes
BATCH_SIZE_BASELINE = 50

H = STATE_COUNT * 3 / 4 # hidden layer size

MEMORY_CAPACITY = 100000 # KBW: Number of steps saved
BATCH_SIZE = 8 # KBW: Relative amount of memory to reserve?? Keeping it low seems faster.

GAMMA = 0.95

MAX_EPSILON = .99 # KBW: Don't change!
MIN_EPSILON = 0.01 # KBW: keep non-zero to stay a bit curious even when getting old
#TARGET_EPSILON = 0.01
#LAMBDA = math.log((TARGET_EPSILON - MIN_EPSILON)/(MAX_EPSILON - MIN_EPSILON)) / -TOTAL_EPISODES  #0.001    # exponent of speed of decay

class Brain:
    def __init__(self):
        self.params = {}
        self.model, self.trainer, self.loss = self._create()
        # self.model.load_weights("cartpole-basic.h5")

    def _create(self):
        observation = C.sequence.input_variable(STATE_COUNT, np.float32, name="s")
        q_target = C.sequence.input_variable(ACTION_COUNT, np.float32, name="q")

        # Following a style similar to Keras
        l1 = C.layers.Dense(H, activation=C.sigmoid)
        l2 = C.layers.Dense(ACTION_COUNT)
        unbound_model = C.layers.Sequential([l1, l2])
        model = unbound_model(observation)

        self.params = dict(W1=l1.W, b1=l1.b, W2=l2.W, b2=l2.b)

        # loss='mse'
        loss = C.reduce_mean(C.square(model - q_target), axis=0)
        meas = C.reduce_mean(C.square(model - q_target), axis=0)

        # optimizer
        lr = 1
        lr_schedule = C.learning_rate_schedule(lr, C.UnitType.minibatch)
        learner = C.sgd(model.parameters, lr_schedule, gradient_clipping_threshold_per_sample=10)

		# <Parallel>
   #     distributed_learner = distributed.data_parallel_distributed_learner(
			#learner = learner,
			#num_quantization_bits = 32,
			#distributed_after = 0)
		# </Parallel>

        trainer = C.Trainer(model, (loss, meas), learner)

        # CNTK: return trainer and loss as well
        return model, trainer, loss

    def train(self, x, y, epoch=1, verbose=0):
        #self.model.fit(x, y, batch_size=64, nb_epoch=epoch, verbose=verbose)
        arguments = dict(zip(self.loss.arguments, [x,y]))
        updated, results =self.trainer.train_minibatch(arguments, outputs=[self.loss.output])

    def predict(self, s):
        return self.model.eval([s])

    def save(self, path):
        self.model.save(path)

class Memory:   # stored as ( s, a, r, s_ )
    samples = []

    def __init__(self, capacity):
        self.capacity = capacity

    def add(self, sample):
        self.samples.append(sample)

        if len(self.samples) > self.capacity:
            self.samples.pop(0)

    def sample(self, n):
        n = min(n, len(self.samples))
        return random.sample(self.samples, n)

class Agent:
    steps = 0
    epsilon = MAX_EPSILON

    def __init__(self):
        self.brain = Brain()
        self.memory = Memory(MEMORY_CAPACITY)

    def act(self, s):
        if random.random() < self.epsilon:
            return random.randint(0, ACTION_COUNT-1)
        else:
            return np.argmax(self.brain.predict(s))

    def observe(self, sample):  # in (s, a, r, s_) format
        self.memory.add(sample)

        # slowly decrease Epsilon based on our experience
        self.steps += 1
        
        if (self.steps >= OBSERVE):
            self.epsilon -= (MAX_EPSILON - MIN_EPSILON) / (TOTAL_EPISODES - OBSERVE) # MIN_EPSILON + (MAX_EPSILON - MIN_EPSILON) * math.exp(-LAMBDA * self.steps)

    def replay(self):
        batch = self.memory.sample(BATCH_SIZE)
        batchLen = len(batch)

        no_state = np.zeros(STATE_COUNT)


        # CNTK: explicitly setting to float32
        states = np.array([ o[0] for o in batch ], dtype=np.float32)
        states_ = np.array([(no_state if o[3] is None else o[3]) for o in batch ], dtype=np.float32)

        p = agent.brain.predict(states)
        p_ = agent.brain.predict(states_)

        # CNTK: explicitly setting to float32
        x = np.zeros((batchLen, STATE_COUNT)).astype(np.float32)
        y = np.zeros((batchLen, ACTION_COUNT)).astype(np.float32)

        for i in range(batchLen):
            s, a, r, s_ = batch[i]

            # CNTK: [0] because of sequence dimension
            t = p[0][i]
            if s_ is None:
                t[a] = r
            else:
                t[a] = r + GAMMA * np.amax(p_[0][i])

            x[i] = s
            y[i] = t

        self.brain.train(x, y)

    def save(self, path):
        self.brain.save(path)

def run(agent):
    s = env.reset()
    R = 0

    while True:
        # CNTK: explicitly setting to float32
        a = agent.act(s.astype(np.float32))

        s_, r, done, info = env.step(a)

        if done: # terminal state
            s_ = None

        agent.observe((s, a, r, s_))
        agent.replay()

        s = s_
        R += r

        if done:
            if env.debug:
                print("  REWARD: %d" % R)
            return R

startTime = time.time()
agent = Agent()
episode_number = 0
reward_sum = 0
averages = []
while episode_number < TOTAL_EPISODES:
    special = episode_number % BATCH_SIZE_BASELINE == 0
    env.debug = False #special
    reward = run(agent)
    reward_sum += reward
    episode_number += 1
    if special:
        average = reward_sum / BATCH_SIZE_BASELINE
        averages.append(average)
        print('Ep: %d, avg reward: %f' % (episode_number, average))
        reward_sum = 0

#for i in range(len(averages)):
#    print(averages[i])
print("%d" % (time.time() - startTime))

agent.save(os.path.join(os.path.dirname(os.path.abspath(__file__)), "/model.cmf"))

agent.epsilon = 0
env.debug = True
reward = run(agent)
print("Reward: %d" % reward)

distributed.Communicator.finalize()