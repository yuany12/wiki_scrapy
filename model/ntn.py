import math
import numpy as np
from numpy import dot
import copy
import scipy.optimize as opt
import cPickle
import logging

class my_neural_tensor_network():
    def __init__(self, params, init_evs = None):
        if type(params) is str:
            self.load(params)
            return
        self.embedding_size = params['embedding_size']
        self.num_entities = params['num_entities']
        self.slice_size = params['slice_size']
        self.lamda = params['lamda']
        self.batch_size = params['batch_size']
        self.cor_size = params['corrupt_size']
        self.num_iterations = params['num_iterations']
        self.batch_iterations = params['batch_iterations']
        self.ev_fixed = params['ev_fixed']
        self.threshold = params['threshold']
        self.save_file = params['save_file']
        self.save_period = params['save_period']
        
        r = 1e-1
        entity_vectors = init_evs.copy() if init_evs is not None else np.random.random((self.embedding_size, self.num_entities)) * 2 * r - r 
        r = 1 / math.sqrt(2 * self.embedding_size)
        W = np.random.random((self.embedding_size, self.embedding_size, self.slice_size)) * 2 * r - r
        v = np.zeros((self.slice_size, 2 * self.embedding_size))
        b, u = np.zeros((self.slice_size)), np.zeros((self.slice_size))
        if not self.ev_fixed:
            self.theta, self.decode = self.stackToParams(W, v, b, u, entity_vectors)
        else:
            self.theta, self.decode = self.stackToParams(W, v, b, u)
            self.entity_vectors = entity_vectors

    def stackToParams(self, *args):
        theta, decode = [], []
        for arg in args:
            decode.append(arg.shape)
            theta = np.concatenate((theta, arg.flatten()))
        return theta, decode

    def paramsToStack(self, theta):
        stack, index = [], 0
        for i in range(len(self.decode)):
            stack.append(theta[index: index + np.prod(self.decode[i])].reshape(self.decode[i]))
            index += np.prod(self.decode[i])
        return stack

    def act(self, x):
        return np.tanh(x)

    def act_der(self, x):
        return 1 - np.power(x, 2)

    def predict(self, data, score = False):
        if not self.ev_fixed:
            W, v, b, u, entity_vectors = self.paramsToStack(self.theta)
        else:
            W, v, b, u = self.paramsToStack(self.theta)
            entity_vectors = self.entity_vectors
        ev1, ev2 = entity_vectors[:, data[:, 0]], entity_vectors[:, data[:, 1]]
        predict_size = ev1.shape[1]
        pre = np.zeros((self.slice_size, predict_size))
        for i in range(predict_size):
            for slice in range(self.slice_size):
                pre[slice, i] += dot(dot(ev1[:, i], W[:, :, slice]), ev2[:, i])
            pre[:, i] += b + dot(v, np.concatenate((ev1[:, i], ev2[:, i])))
        if score: return dot(u, self.act(pre))
        return (dot(u, self.act(pre)) > self.threshold)

    def cost(self, theta, indices, flip):
        if not self.ev_fixed:
            W, v, b, u, entity_vectors = self.paramsToStack(theta)
        else:
            W, v, b, u = self.paramsToStack(theta)
            entity_vectors = self.entity_vectors
        e1, e2, e3 = indices['e1'], indices['e2'], indices['e3']
        ev1, ev2, ev3 = entity_vectors[:, e1], entity_vectors[:, e2], entity_vectors[:, e3]
        if not flip:
            ev1_neg, ev2_neg = ev1, ev3
            e1_neg, e2_neg = e1, e3
        else:
            ev1_neg, ev2_neg = ev3, ev2
            e1_neg, e2_neg = e3, e2
        cur_batch_size = e1.shape[0]
        pre_pos, pre_neg = np.zeros((self.slice_size, cur_batch_size)), np.zeros((self.slice_size, cur_batch_size))
        for i in range(cur_batch_size):
            for slice in range(self.slice_size):
                pre_pos[slice, i] += dot(dot(ev1[:, i], W[:, :, slice]), ev2[:, i])
                pre_neg[slice, i] += dot(dot(ev1_neg[:, i], W[:, :, slice]), ev2_neg[:, i])
            pre_pos[:, i] += b + dot(v, np.concatenate((ev1[:, i], ev2[:, i])))
            pre_neg[:, i] += b + dot(v, np.concatenate((ev1_neg[:, i], ev2_neg[:, i])))
        act_pos, act_neg = self.act(pre_pos), self.act(pre_neg)
        score_pos, score_neg = dot(u, act_pos), dot(u, act_neg)
        wrong_filter = (score_neg + 1 > score_pos)
        cost = np.sum((score_neg + 1 - score_pos)[wrong_filter])
        
        wrong_size = np.sum(wrong_filter)
        act_pos, act_neg = act_pos[:, wrong_filter], act_neg[:, wrong_filter]
        ev1, ev2, ev1_neg, ev2_neg = ev1[:, wrong_filter], ev2[:, wrong_filter], ev1_neg[:, wrong_filter], ev2_neg[:, wrong_filter]
        e1, e2, e1_neg, e2_neg = e1[wrong_filter], e2[wrong_filter], e1_neg[wrong_filter], e2_neg[wrong_filter]

        W_grad, v_grad = np.zeros(W.shape), np.zeros(v.shape)
        u_grad = np.sum(act_neg - act_pos, axis = 1)
        fder_pos, fder_neg = self.act_der(act_pos), self.act_der(act_neg)
        u_fder_pos, u_fder_neg = u.reshape((self.slice_size, 1)) * fder_pos, u.reshape((self.slice_size, 1)) * fder_neg
        b_grad = np.sum(u_fder_neg - u_fder_pos, axis = 1)
        for i in range(wrong_size):
            v_grad += np.outer(u_fder_neg[:, i], np.concatenate((ev1_neg[:, i], ev2_neg[:, i]))) - np.outer(u_fder_pos[:, i], np.concatenate((ev1[:, i], ev2[:, i])))
            W_grad += np.outer(ev1_neg[:, i], ev2_neg[:, i]).reshape((self.embedding_size, self.embedding_size, 1)) * u_fder_neg[:, i].reshape((1, 1, self.slice_size)) - \
                np.outer(ev1[:, i], ev2[:, i]).reshape((self.embedding_size, self.embedding_size, 1)) * u_fder_pos[:, i].reshape((1, 1, self.slice_size))
        if not self.ev_fixed:
            ev_grad = np.zeros(entity_vectors.shape)
            for i in range(wrong_size):
                for slice in range(self.slice_size):
                    ev_grad[:, e1_neg[i]] += dot(W[:, :, slice], ev2_neg[:, i]) * u_fder_neg[slice, i]
                    ev_grad[:, e2_neg[i]] += dot(ev1_neg[:, i], W[:, :, slice]) * u_fder_neg[slice, i]
                    ev_grad[:, e1[i]] -= dot(W[:, :, slice], ev2[:, i]) * u_fder_pos[slice, i]
                    ev_grad[:, e2[i]] -= dot(ev1[:, i], W[:, :, slice]) * u_fder_pos[slice, i]
            ev_grad /= cur_batch_size

        for grad in [W_grad, v_grad, b_grad, u_grad]:
            grad /= cur_batch_size
        cost = cost / cur_batch_size + 0.5 * self.lamda * np.sum(theta * theta)
        if not self.ev_fixed:
            return cost, self.stackToParams(W_grad, v_grad, b_grad, u_grad, ev_grad)[0]
        return cost, self.stackToParams(W_grad, v_grad, b_grad, u_grad)[0]

    def train(self, data):
        for i in range(self.num_iterations):
            logging.info('iteration #%d' % i)
            batch, indices = np.random.randint(data.shape[0], size = self.batch_size), {}
            indices['e1'], indices['e2'] = np.tile(data[batch, 0], self.cor_size), np.tile(data[batch, 1], self.cor_size)
            indices['e3'] = np.random.randint(self.num_entities, size = self.batch_size * self.cor_size)
            flip = np.random.random() < 0.5
            self.theta = opt.minimize(self.cost, self.theta, args = (indices, flip), method = 'L-BFGS-B', jac = True, options = {'maxiter': self.batch_iterations, 'disp': True}).x
            if (i + 1) % self.save_period == 0: self.save()

    def save(self):
        cPickle.dump(self.__dict__, open(self.save_file, 'w'))

    def load(self, filename):
        self.__dict__ = cPickle.load(open(filename))
