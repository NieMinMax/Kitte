# -*- coding: utf-8 -*-

from __future__ import division, print_function, absolute_import

import tensorflow as tf
import numpy as np

import logging
from math import sqrt

from sqlalchemy.sql import text

from ..models.base import DBSession
from ..models.base import get_connection
from ..models.ucf_result import Ucf_Result

log = logging.getLogger(__name__)



import tensorflow as tf


def inference_svd(user_batch, item_batch, user_num, item_num, dim=5, device="/cpu:0"):
    with tf.device("/cpu:0"):
        bias_global = tf.get_variable("bias_global", shape=[])
        w_bias_user = tf.get_variable("embd_bias_user", shape=[user_num])
        w_bias_item = tf.get_variable("embd_bias_item", shape=[item_num])
        bias_user = tf.nn.embedding_lookup(w_bias_user, user_batch, name="bias_user")
        bias_item = tf.nn.embedding_lookup(w_bias_item, item_batch, name="bias_item")
        w_user = tf.get_variable("embd_user", shape=[user_num, dim],
                                 initializer=tf.truncated_normal_initializer(stddev=0.02))
        w_item = tf.get_variable("embd_item", shape=[item_num, dim],
                                 initializer=tf.truncated_normal_initializer(stddev=0.02))
        embd_user = tf.nn.embedding_lookup(w_user, user_batch, name="embedding_user")
        embd_item = tf.nn.embedding_lookup(w_item, item_batch, name="embedding_item")
    with tf.device(device):
        infer = tf.reduce_sum(tf.mul(embd_user, embd_item), 1)
        infer = tf.add(infer, bias_global)
        infer = tf.add(infer, bias_user)
        infer = tf.add(infer, bias_item, name="svd_inference")
        regularizer = tf.add(tf.nn.l2_loss(embd_user), tf.nn.l2_loss(embd_item), name="svd_regularizer")
    return infer, regularizer


def optimiaztion(infer, regularizer, rate_batch, learning_rate=0.1, reg=0.1, device="/cpu:0"):
    with tf.device(device):
        cost_l2 = tf.nn.l2_loss(tf.sub(infer, rate_batch))
        panelty = tf.constant(reg, dtype=tf.float32, shape=[], name="l2")
        cost = tf.add(cost_l2, tf.mul(regularizer, panelty))
        train_op = tf.train.FtrlOptimizer(learning_rate).minimize(cost)
    return cost, train_op






from __future__ import absolute_import, division, print_function
import numpy as np
import pandas as pd


def read_process(filname, sep="\t"):
    col_names = ["user", "item", "rate", "st"]
    df = pd.read_csv(filname, sep=sep, header=None, names=col_names)
    df["user"] -= 1
    df["item"] -= 1
    for col in ("user", "item"):
        df[col] = df[col].astype(np.int32)
    df["rate"] = df["rate"].astype(np.float32)
    return df


class ShuffleIterator(object):
    """
    Randomly generate batches
    """
    def __init__(self, inputs, batch_size=10):
        self.inputs = inputs
        self.batch_size = batch_size
        self.num_cols = len(self.inputs)
        self.len = len(self.inputs[0])
        self.inputs = np.transpose(np.vstack([np.array(self.inputs[i]) for i in range(self.num_cols)]))

    def __len__(self):
        return self.len

    def __iter__(self):
        return self

    def __next__(self):
        return self.next()

    def next(self):
        ids = np.random.randint(0, self.len, (self.batch_size,))
        out = self.inputs[ids, :]
        return [out[:, i] for i in range(self.num_cols)]


class OneEpochIterator(ShuffleIterator):
    """
    Sequentially generate one-epoch batches, typically for test data
    """
    def __init__(self, inputs, batch_size=10):
        super(OneEpochIterator, self).__init__(inputs, batch_size=batch_size)
        if batch_size > 0:
            self.idx_group = np.array_split(np.arange(self.len), np.ceil(self.len / batch_size))
        else:
            self.idx_group = [np.arange(self.len)]
        self.group_id = 0

    def next(self):
        if self.group_id >= len(self.idx_group):
            self.group_id = 0
            raise StopIteration
        out = self.inputs[self.idx_group[self.group_id], :]
        self.group_id += 1
        return [out[:, i] for i in range(self.num_cols)]









    



import tensorflow as tf
import dataio
import numpy as np
from collections import deque
from six import next
import time
import ops

np.random.seed(13575)

BATCH_SIZE = 1000
USER_NUM = 6040
ITEM_NUM = 3952
DIM = 15
EPOCH_MAX = 100
DEVICE = "/cpu:0"


def clip(x):
    return np.clip(x, 1.0, 5.0)


def get_data():
    df = dataio.read_process("/tmp/movielens/ml-1m/ratings.dat", sep="::")
    rows = len(df)
    df = df.iloc[np.random.permutation(rows)].reset_index(drop=True)
    split_index = int(rows * 0.9)
    df_train = df[0:split_index]
    df_test = df[split_index:].reset_index(drop=True)
    return df_train, df_test


def svd(train, test):
    samples_per_batch = len(train) // BATCH_SIZE

    iter_train = dataio.ShuffleIterator([train["user"],
                                         train["item"],
                                         train["rate"]],
                                        batch_size=BATCH_SIZE)

    iter_test = dataio.OneEpochIterator([test["user"],
                                         test["item"],
                                         test["rate"]],
                                        batch_size=-1)

    user_batch = tf.placeholder(tf.int32, shape=[None], name="id_user")
    item_batch = tf.placeholder(tf.int32, shape=[None], name="id_item")
    rate_batch = tf.placeholder(tf.float32, shape=[None])

    infer, regularizer = ops.inference_svd(user_batch, item_batch, user_num=USER_NUM, item_num=ITEM_NUM, dim=DIM,
                                           device=DEVICE)
    _, train_op = ops.optimiaztion(infer, regularizer, rate_batch, learning_rate=0.15, reg=0.05, device=DEVICE)

    init_op = tf.initialize_all_variables()
    with tf.Session() as sess:
        sess.run(init_op)
        print("{} {} {} {}".format("epoch", "train_error", "val_error", "elapsed_time"))
        errors = deque(maxlen=samples_per_batch)
        start = time.time()
        for i in range(EPOCH_MAX * samples_per_batch):
            users, items, rates = next(iter_train)
            _, pred_batch = sess.run([train_op, infer], feed_dict={user_batch: users,
                                                                   item_batch: items,
                                                                   rate_batch: rates})
            pred_batch = clip(pred_batch)
            errors.append(np.power(pred_batch - rates, 2))
            if i % samples_per_batch == 0:
                train_err = np.sqrt(np.mean(errors))
                test_err2 = np.array([])
                for users, items, rates in iter_test:
                    pred_batch = sess.run(infer, feed_dict={user_batch: users,
                                                            item_batch: items})
                    pred_batch = clip(pred_batch)
                    test_err2 = np.append(test_err2, np.power(pred_batch - rates, 2))
                end = time.time()
                print("{:3d} {:f} {:f} {:f}(s)".format(i // samples_per_batch, train_err, np.sqrt(np.mean(test_err2)),
                                                       end - start))
                start = end

        output_graph_def = tf.python.client.graph_util.extract_sub_graph(sess.graph.as_graph_def(),
                                                                         ["svd_inference", "svd_regularizer"])
        tf.train.SummaryWriter(logdir="/tmp/svd", graph_def=output_graph_def)


if __name__ == '__main__':
    df_train, df_test = get_data()
    svd(df_train, df_test)







def _get_all_products():
    """
    生成一个巨大的商品数组
    """
    DBConnecion = get_connection()
    sql_str = text("""select distinct product_id from sorder_line""")
    sql_answer = DBConnecion.execute(sql_str).fetchall()
    return sql_answer


def build_ae_model(layer_sizes):
    """
    构建模型
    """
    # Build the encoding layers (0.618黄金比例)
    next_layer_input = layer_sizes*0.618
    encoding_matrices = []
    for dim in layer_sizes:
        input_dim = int(next_layer_input.get_shape()[1])
        # Initialize W using random values in interval [-1/sqrt(n) , 1/sqrt(n)]
        W = tf.Variable(tf.random_uniform([input_dim, dim],
                                          -1.0 / math.sqrt(input_dim),
                                          1.0 / math.sqrt(input_dim)))
        # Initialize b to zero
        b = tf.Variable(tf.zeros([dim]))
        # We are going to use tied-weights so store the W matrix for later reference.
        encoding_matrices.append(W)
        
        output = tf.nn.tanh(tf.matmul(next_layer_input, W) + b)
        
        # the input into the next layer is the output of this layer
        next_layer_input = output

	# The fully encoded x value is now stored in the next_layer_input
	encoded_x = next_layer_input

	# build the reconstruction layers by reversing the reductions
	layer_sizes.reverse()
	encoding_matrices.reverse()

	for i, dim in enumerate(layer_sizes[1:] + [ int(x.get_shape()[1])]) :
		# we are using tied weights, so just lookup the encoding matrix for this step and transpose it
		W = tf.transpose(encoding_matrices[i])
		b = tf.Variable(tf.zeros([dim]))
		output = tf.nn.tanh(tf.matmul(next_layer_input,W) + b)
		next_layer_input = output

	# the fully encoded and reconstructed value of x is here:
	reconstructed_x = next_layer_input

	return {
		'encoded': encoded_x,
		'decoded': reconstructed_x,
		'cost' : tf.sqrt(tf.reduce_mean(tf.square(x-reconstructed_x)))
	}







# Parameters
learning_rate = 0.01
training_epochs = 20
batch_size = 256
display_step = 1
examples_to_show = 10

# Network Parameters
n_hidden_1 = 256 # 1st layer num features
n_hidden_2 = 128 # 2nd layer num features
n_input = 784 # MNIST data input (img shape: 28*28)

# tf Graph input (only pictures)
X = tf.placeholder("float", [None, n_input])

weights = {
    'encoder_h1': tf.Variable(tf.random_normal([n_input, n_hidden_1])),
    'encoder_h2': tf.Variable(tf.random_normal([n_hidden_1, n_hidden_2])),
    'decoder_h1': tf.Variable(tf.random_normal([n_hidden_2, n_hidden_1])),
    'decoder_h2': tf.Variable(tf.random_normal([n_hidden_1, n_input])),
}
biases = {
    'encoder_b1': tf.Variable(tf.random_normal([n_hidden_1])),
    'encoder_b2': tf.Variable(tf.random_normal([n_hidden_2])),
    'decoder_b1': tf.Variable(tf.random_normal([n_hidden_1])),
    'decoder_b2': tf.Variable(tf.random_normal([n_input])),
}


# Building the encoder
def encoder(x):
    # Encoder Hidden layer with sigmoid activation #1
    layer_1 = tf.nn.sigmoid(tf.add(tf.matmul(x, weights['encoder_h1']),
                                   biases['encoder_b1']))
    # Decoder Hidden layer with sigmoid activation #2
    layer_2 = tf.nn.sigmoid(tf.add(tf.matmul(layer_1, weights['encoder_h2']),
                                   biases['encoder_b2']))
    return layer_2


# Building the decoder
def decoder(x):
    # Encoder Hidden layer with sigmoid activation #1
    layer_1 = tf.nn.sigmoid(tf.add(tf.matmul(x, weights['decoder_h1']),
                                   biases['decoder_b1']))
    # Decoder Hidden layer with sigmoid activation #2
    layer_2 = tf.nn.sigmoid(tf.add(tf.matmul(layer_1, weights['decoder_h2']),
                                   biases['decoder_b2']))
    return layer_2

# Construct model
encoder_op = encoder(X)
decoder_op = decoder(encoder_op)

# Prediction
y_pred = decoder_op
# Targets (Labels) are the input data.
y_true = X

# Define loss and optimizer, minimize the squared error
cost = tf.reduce_mean(tf.pow(y_true - y_pred, 2))
optimizer = tf.train.RMSPropOptimizer(learning_rate).minimize(cost)

# Initializing the variables
init = tf.initialize_all_variables()

# Launch the graph
with tf.Session() as sess:
    sess.run(init)
    total_batch = int(mnist.train.num_examples/batch_size)
    # Training cycle
    for epoch in range(training_epochs):
        # Loop over all batches
        for i in range(total_batch):
            batch_xs, batch_ys = mnist.train.next_batch(batch_size)
            # Run optimization op (backprop) and cost op (to get loss value)
            _, c = sess.run([optimizer, cost], feed_dict={X: batch_xs})
        # Display logs per epoch step
        if epoch % display_step == 0:
            print("Epoch:", '%04d' % (epoch+1),
                  "cost=", "{:.9f}".format(c))

    print("Optimization Finished!")

    # Applying encode and decode over test set
    encode_decode = sess.run(
        y_pred, feed_dict={X: mnist.test.images[:examples_to_show]})
    # Compare original images with their reconstructions
    f, a = plt.subplots(2, 10, figsize=(10, 2))
    for i in range(examples_to_show):
        a[0][i].imshow(np.reshape(mnist.test.images[i], (28, 28)))
        a[1][i].imshow(np.reshape(encode_decode[i], (28, 28)))












def _save_score(one_product, rel_product, score):
    if score > 0:
        print one_product, rel_product, score
        one_result = Ucf_Result(
            product_id = one_product,
            rel_product_id = rel_product,
            score = score,
        )
        DBSession.add(one_result)

def do_ae_model():
    ## 获取全部购买商品
    all_products = _get_all_products()
    ## 构建模型
    build_ae_model(len(all_products))

    ## 获取用户及购买的商品tensor
    all_data = get_user_product()

    ## 训练模型
    for i in all_data():
        train(i)
    
    all_items = _get_all_items()
    for one_item_line in all_items:
        for rel_item_line in all_items:
            if one_item_line != rel_item_line:
                score = pearson_correlation(all_data, one_item_line[0], rel_item_line[0])
                _save_score(one_item_line[0], rel_item_line[0], score)
    

def job():
    do_ae_model()
    return




















    

    
# -*- coding: utf-8 -*-

""" Deep Auto-Encoder implementation
	
	An auto-encoder works as follows:
	Data of dimension k is reduced to a lower dimension j using a matrix multiplication:
	softmax(W*x + b)  = x'
	
	where W is matrix from R^k --> R^j
	A reconstruction matrix W' maps back from R^j --> R^k
	so our reconstruction function is softmax'(W' * x' + b') 
	Now the point of the auto-encoder is to create a reduction matrix (values for W, b) 
	that is "good" at reconstructing  the original data. 
	Thus we want to minimize  ||softmax'(W' * (softmax(W *x+ b)) + b')  - x||
	A deep auto-encoder is nothing more than stacking successive layers of these reductions.
"""
import tensorflow as tf
import numpy as np
import math
import random

def create(x, layer_sizes):

	# Build the encoding layers
	next_layer_input = x

	encoding_matrices = []
	for dim in layer_sizes:
		input_dim = int(next_layer_input.get_shape()[1])

		# Initialize W using random values in interval [-1/sqrt(n) , 1/sqrt(n)]
		W = tf.Variable(tf.random_uniform([input_dim, dim], -1.0 / math.sqrt(input_dim), 1.0 / math.sqrt(input_dim)))

		# Initialize b to zero
		b = tf.Variable(tf.zeros([dim]))

		# We are going to use tied-weights so store the W matrix for later reference.
		encoding_matrices.append(W)

		output = tf.nn.tanh(tf.matmul(next_layer_input,W) + b)

		# the input into the next layer is the output of this layer
		next_layer_input = output

	# The fully encoded x value is now stored in the next_layer_input
	encoded_x = next_layer_input

	# build the reconstruction layers by reversing the reductions
	layer_sizes.reverse()
	encoding_matrices.reverse()


	for i, dim in enumerate(layer_sizes[1:] + [ int(x.get_shape()[1])]) :
		# we are using tied weights, so just lookup the encoding matrix for this step and transpose it
		W = tf.transpose(encoding_matrices[i])
		b = tf.Variable(tf.zeros([dim]))
		output = tf.nn.tanh(tf.matmul(next_layer_input,W) + b)
		next_layer_input = output

	# the fully encoded and reconstructed value of x is here:
	reconstructed_x = next_layer_input

	return {
		'encoded': encoded_x,
		'decoded': reconstructed_x,
		'cost' : tf.sqrt(tf.reduce_mean(tf.square(x-reconstructed_x)))
	}

def simple_test():
	sess = tf.Session()
	x = tf.placeholder("float", [None, 4])
	autoencoder = create(x, [2])
	init = tf.initialize_all_variables()
	sess.run(init)
	train_step = tf.train.GradientDescentOptimizer(0.01).minimize(autoencoder['cost'])


	# Our dataset consists of two centers with gaussian noise w/ sigma = 0.1
	c1 = np.array([0,0,0.5,0])
	c2 = np.array([0.5,0,0,0])

	# do 1000 training steps
	for i in range(2000):
		# make a batch of 100:
		batch = []
		for j in range(100):
			# pick a random centroid
			if (random.random() > 0.5):
				vec = c1
			else:
				vec = c2
  			batch.append(np.random.normal(vec, 0.1))
		sess.run(train_step, feed_dict={x: np.array(batch)})
		if i % 100 == 0:
			print i, " cost", sess.run(autoencoder['cost'], feed_dict={x: batch})


def deep_test():
	sess = tf.Session()
	start_dim = 5
	x = tf.placeholder("float", [None, start_dim])
	autoencoder = create(x, [4, 3, 2])
	init = tf.initialize_all_variables()
	sess.run(init)
	train_step = tf.train.GradientDescentOptimizer(0.5).minimize(autoencoder['cost'])


	# Our dataset consists of two centers with gaussian noise w/ sigma = 0.1
	c1 = np.zeros(start_dim)
	c1[0] = 1

	print c1

	c2 = np.zeros(start_dim)
	c2[1] = 1

	# do 1000 training steps
	for i in range(5000):
		# make a batch of 100:
		batch = []
		for j in range(1):
			# pick a random centroid
			if (random.random() > 0.5):
				vec = c1
			else:
				vec = c2
  			batch.append(np.random.normal(vec, 0.1))
		sess.run(train_step, feed_dict={x: np.array(batch)})
		if i % 100 == 0:
			print i, " cost", sess.run(autoencoder['cost'], feed_dict={x: batch})
			print i, " original", batch[0]
			print i, " decoded", sess.run(autoencoder['decoded'], feed_dict={x: batch})
			
if __name__ == '__main__':
	deep_test()








        
        
def weight_variable(shape):
    initial = tf.truncated_normal(shape, stddev=0.1)
    return tf.Variable(initial)

def bias_variable(shape):
    initial = tf.constant(0.1, shape=shape)
    return tf.Variable(initial)

if DEBUG:
    print('creating placeholders for input and output...')


# inputs
x = tf.placeholder('float', shape=[None,input_size])
# outputs = labels
y_ = tf.placeholder('float', shape=[None,input_size])

# To prevent overfitting, we  apply [dropout](https://en.wikipedia.org/wiki/Convolutional_neural_network#Dropout) 
# before the readout layer.
# 
# Dropout removes some nodes from the network at each training stage. Each of the nodes is either kept in the 
# network with probability *keep_prob* or dropped with probability *1 - keep_prob*. After the training stage 
# is over the nodes are returned to the NN with their original weights.
keep_prob = tf.placeholder('float')
if DEBUG:
    print('creating W,b,h variables for various layers...')


W = []
b = []
h = []
h_tmp = []

if DEBUG:
    print('\tnow creating input layer...')
    print('\t\t',input_size,',',NN_HL_ARCH[0])

W.append(weight_variable([input_size,NN_HL_ARCH[0]]))
b.append(bias_variable([NN_HL_ARCH[0]]))
h.append(tf.nn.relu(tf.matmul(x,W[0]) + b[0]))

for i in range(1,len(NN_HL_ARCH)):
    u = NN_HL_ARCH[i-1]
    v = NN_HL_ARCH[i]
    if DEBUG:
        print('\tnow creating layer:', i)
        print('\t\t',u,',',v)

    W.append(weight_variable([u,v]))
    b.append(bias_variable([v]))
    if DEBUG:
        pass
        #print('h', tf.shape(h[i-1]), ', W:', tf.shape(W[i]), ', b:', tf.shape(b[i]))

    h_tmp.append(tf.nn.relu(tf.matmul(h[i-1],W[i]) + b[i]))
    # dropout
    h.append(tf.nn.dropout(h_tmp[-1], keep_prob))

if DEBUG:
    print('\tnow creating output layer...')
    print('\t\t',NN_HL_ARCH[-1],',',input_size)

W.append(weight_variable([NN_HL_ARCH[-1],input_size]))
b.append(bias_variable([input_size]))
if DEBUG:
    print('\tsetting up output vector...')
y = tf.nn.relu(tf.matmul(h[-1],W[-1]) + b[-1])

# 
# ADAM optimiser is a gradient based optimization algorithm, based on adaptive estimates, it's more 
# sophisticated than steepest gradient descent and is well suited for problems with large data or many parameters.
# cost function
cross_entropy = -tf.reduce_sum(y_*tf.log(y))
if DEBUG:
    print('defining objective function...')
# but we shall use rmse
rmse = tf.sqrt(tf.reduce_mean(tf.pow(y-y_, 2)))

if DEBUG:
    print('defining optimization step...')
# optimisation function
train_step = tf.train.AdamOptimizer(LEARNING_RATE).minimize(rmse)

# evaluation
if DEBUG:
    print('defining optimization step...')

# CHECK
error_sq_vector = tf.pow(y - y_,2)

# CHECK
accuracy = tf.sqrt(tf.reduce_mean(error_sq_vector))
predict = tf.identity(y)

# *Finally neural network structure is defined and TensorFlow graph is ready for training.*
# ## Train, validate and predict
# #### Helper functions
# 
# Ideally, we should use all data for every step of the training, but that's expensive. So, instead, 
# we use small "batches" of random data. 
# 
# This method is called [stochastic training](https://en.wikipedia.org/wiki/Stochastic_gradient_descent). 
# It is cheaper, faster and gives much of the same result.
epochs_completed = 0
index_in_epoch = 0
num_examples = train_inputs.shape[0]

# serve data by batches
def next_batch(batch_size):
    
    global train_inputs
    global train_labels
    global index_in_epoch
    global epochs_completed
    
    start = index_in_epoch
    index_in_epoch += batch_size
    
    # when all trainig data have been already used, it is reorder randomly    
    if index_in_epoch > num_examples:
        # finished epoch
        epochs_completed += 1
        # shuffle the data
        perm = np.arange(num_examples)
        np.random.shuffle(perm)
        train_inputs = train_inputs[perm]
        train_labels = train_labels[perm]
        # start next epoch
        start = 0
        index_in_epoch = batch_size
        assert batch_size <= num_examples
    end = index_in_epoch
    return train_inputs[start:end], train_labels[start:end]
# Now when all operations for every variable are defined in TensorFlow graph all computations 
# will be performed outside Python environment.
# start TensorFlow session
init = tf.initialize_all_variables()
sess = tf.InteractiveSession()

sess.run(init)
# Each step of the loop, we get a "batch" of data points from the training set and feed it to 
# the graph to replace the placeholders.  In this case, it's:  *x, y* and *dropout.*
# 
# Also, once in a while, we check training accuracy on an upcoming "batch".
# 
# On the local environment, we recommend [saving training progress]
# (https://www.tensorflow.org/versions/master/api_docs/python/state_ops.html#Saver), 
# so it can be recovered for further training, debugging or evaluation.
# visualisation variables
train_accuracies = []
validation_accuracies = []
x_range = []

display_step=1

for i in range(TRAINING_ITERATIONS):

    #get new batch
    batch_xs, batch_ys = next_batch(BATCH_SIZE)        

    # check progress on every 1st,2nd,...,10th,20th,...,100th... step
    if i%display_step == 0 or (i+1) == TRAINING_ITERATIONS:
        
        train_accuracy = accuracy.eval(feed_dict={x:batch_xs, 
                                                  y_: batch_ys, 
                                                  keep_prob: 1.0})       
        if(VALIDATION_SIZE):
            validation_accuracy = accuracy.eval(feed_dict={ x: validation_inputs[0:BATCH_SIZE], 
                                                            y_: validation_labels[0:BATCH_SIZE], 
                                                            keep_prob: 1.0})                                  
            print('training_accuracy / validation_accuracy => %.2f / %.2f for step %d'%(train_accuracy, validation_accuracy, i))
            
            validation_accuracies.append(validation_accuracy)
            
        else:
             print('training_accuracy => %.4f for step %d'%(train_accuracy, i))
        train_accuracies.append(train_accuracy)
        x_range.append(i)
        
        # increase display_step
        if i%(display_step*10) == 0 and i:
            display_step *= 10
    # train on batch
    sess.run(train_step, feed_dict={x: batch_xs, y_: batch_ys, keep_prob: DROPOUT})
# After training is done, it's good to check accuracy on data that wasn't used in training.
# check final accuracy on validation set  
if(VALIDATION_SIZE):
    validation_accuracy = accuracy.eval(feed_dict={x: validation_inputs, 
                                                   y_: validation_labels, 
                                                   keep_prob: 1.0})
    print('validation_accuracy => %.4f'%validation_accuracy)
    plt.plot(x_range, train_accuracies,'-b', label='Training')
    plt.plot(x_range, validation_accuracies,'-g', label='Validation')
    plt.legend(loc='lower right', frameon=False)
    plt.ylim(ymax = 1.1, ymin = 0.7)
    plt.ylabel('accuracy')
    plt.xlabel('step')
    plt.show()
# When, we're happy with the outcome, we read test data from *test.csv* and predict labels for provided inputs.
# 
# Test data contains only inputs and labels are missing. Otherwise, the structure is similar to training data.
# 
# Predicted labels are stored into CSV file for future submission.
# read test data from CSV file 
test_inputs = pd.read_csv('../input/test.csv').values
test_inputs = test_inputs.astype(np.float)

# convert from [0:255] => [0.0:1.0]
test_inputs = normalize(test_inputs) #np.multiply(test_inputs, 1.0 / 255.0)

# predict test set
output_rows = predict.eval(feed_dict={x: train_inputs, keep_prob: 1.0})
test_rows = predict.eval(feed_dict={x: test_inputs, keep_prob: 1.0})
'''
# using batches is more resource efficient
predicted_lables = np.zeros(test_inputs.shape[0])
for i in range(0,test_inputs.shape[0]//BATCH_SIZE):
    predicted_lables[i*BATCH_SIZE : (i+1)*BATCH_SIZE] = predict.eval(feed_dict={x: test_inputs[i*BATCH_SIZE : (i+1)*BATCH_SIZE], keep_prob: 1.0})
'''

np.savetxt('normalized_input_'+tag+'.csv', 
           train_inputs,
           delimiter=',', 
           header = headertext,
           comments = '', 
           fmt='%f')

np.savetxt('normalized_testset_'+tag+'.csv', 
           test_inputs,
           delimiter=',', 
           header = headertext,
           comments = '', 
           fmt='%f')

# save results
np.savetxt('autoencoded_input_'+tag+'.csv', 
           output_rows, 
           delimiter=',', 
           header = headertext,
           comments = '', 
           fmt='%f')

np.savetxt('testset_autoencoded_'+tag+'.csv', 
           test_rows, 
           delimiter=',', 
           header = headertext,
           comments = '', 
           fmt='%f')


diff = np.array(train_inputs) - np.array(output_rows)

np.savetxt('diff_'+tag+'.csv', 
           diff, 
           delimiter=',', 
           header = headertext,
           comments = '', 
           fmt='%f')



# ## Appendix
# It is good to output some variables for a better understanding of the process. 
# 

saver = tf.train.Saver()
# Save the variables to disk.
save_path = saver.save(sess, "./model_"+tag+".ckpt")
print("Model saved in file: %s" % save_path)


for w_,b_ in zip(W,b):
    print("W:")
    print(w_.eval())
    print("b:")
    print(b_.eval())

sess.close()




class VariationalAutoencoder(object):
    """ Variation Autoencoder (VAE) with an sklearn-like interface implemented using TensorFlow.
    
    This implementation uses probabilistic encoders and decoders using Gaussian 
    distributions and  realized by multi-layer perceptrons. The VAE can be learned
    end-to-end.
    
    See "Auto-Encoding Variational Bayes" by Kingma and Welling for more details.
    """
    def __init__(self, network_architecture, transfer_fct=tf.nn.softplus, 
                 learning_rate=0.001, batch_size=100):
        self.network_architecture = network_architecture
        self.transfer_fct = transfer_fct
        self.learning_rate = learning_rate
        self.batch_size = batch_size
        
        # tf Graph input
        self.x = tf.placeholder(tf.float32, [None, network_architecture["n_input"]])
        
        # Create autoencoder network
        self._create_network()
        # Define loss function based variational upper-bound and 
        # corresponding optimizer
        self._create_loss_optimizer()
        
        # Initializing the tensor flow variables
        init = tf.initialize_all_variables()

        # Launch the session
        self.sess = tf.InteractiveSession()
        self.sess.run(init)
    
    def _create_network(self):
        # Initialize autoencode network weights and biases
        network_weights = self._initialize_weights(**self.network_architecture)

        # Use recognition network to determine mean and 
        # (log) variance of Gaussian distribution in latent
        # space
        self.z_mean, self.z_log_sigma_sq = \
            self._recognition_network(network_weights["weights_recog"], 
                                      network_weights["biases_recog"])

        # Draw one sample z from Gaussian distribution
        n_z = self.network_architecture["n_z"]
        eps = tf.random_normal((self.batch_size, n_z), 0, 1, 
                               dtype=tf.float32)
        # z = mu + sigma*epsilon
        self.z = tf.add(self.z_mean, 
                        tf.mul(tf.sqrt(tf.exp(self.z_log_sigma_sq)), eps))

        # Use generator to determine mean of
        # Bernoulli distribution of reconstructed input
        self.x_reconstr_mean = \
            self._generator_network(network_weights["weights_gener"],
                                    network_weights["biases_gener"])
            
    def _initialize_weights(self, n_hidden_recog_1, n_hidden_recog_2, 
                            n_hidden_gener_1,  n_hidden_gener_2, 
                            n_input, n_z):
        all_weights = dict()
        all_weights['weights_recog'] = {
            'h1': tf.Variable(xavier_init(n_input, n_hidden_recog_1)),
            'h2': tf.Variable(xavier_init(n_hidden_recog_1, n_hidden_recog_2)),
            'out_mean': tf.Variable(xavier_init(n_hidden_recog_2, n_z)),
            'out_log_sigma': tf.Variable(xavier_init(n_hidden_recog_2, n_z))}
        all_weights['biases_recog'] = {
            'b1': tf.Variable(tf.zeros([n_hidden_recog_1], dtype=tf.float32)),
            'b2': tf.Variable(tf.zeros([n_hidden_recog_2], dtype=tf.float32)),
            'out_mean': tf.Variable(tf.zeros([n_z], dtype=tf.float32)),
            'out_log_sigma': tf.Variable(tf.zeros([n_z], dtype=tf.float32))}
        all_weights['weights_gener'] = {
            'h1': tf.Variable(xavier_init(n_z, n_hidden_gener_1)),
            'h2': tf.Variable(xavier_init(n_hidden_gener_1, n_hidden_gener_2)),
            'out_mean': tf.Variable(xavier_init(n_hidden_gener_2, n_input)),
            'out_log_sigma': tf.Variable(xavier_init(n_hidden_gener_2, n_input))}
        all_weights['biases_gener'] = {
            'b1': tf.Variable(tf.zeros([n_hidden_gener_1], dtype=tf.float32)),
            'b2': tf.Variable(tf.zeros([n_hidden_gener_2], dtype=tf.float32)),
            'out_mean': tf.Variable(tf.zeros([n_input], dtype=tf.float32)),
            'out_log_sigma': tf.Variable(tf.zeros([n_input], dtype=tf.float32))}
        return all_weights
            
    def _recognition_network(self, weights, biases):
        # Generate probabilistic encoder (recognition network), which
        # maps inputs onto a normal distribution in latent space.
        # The transformation is parametrized and can be learned.
        layer_1 = self.transfer_fct(tf.add(tf.matmul(self.x, weights['h1']), 
                                           biases['b1'])) 
        layer_2 = self.transfer_fct(tf.add(tf.matmul(layer_1, weights['h2']), 
                                           biases['b2'])) 
        z_mean = tf.add(tf.matmul(layer_2, weights['out_mean']),
                        biases['out_mean'])
        z_log_sigma_sq = \
            tf.add(tf.matmul(layer_2, weights['out_log_sigma']), 
                   biases['out_log_sigma'])
        return (z_mean, z_log_sigma_sq)

    def _generator_network(self, weights, biases):
        # Generate probabilistic decoder (decoder network), which
        # maps points in latent space onto a Bernoulli distribution in data space.
        # The transformation is parametrized and can be learned.
        layer_1 = self.transfer_fct(tf.add(tf.matmul(self.z, weights['h1']), 
                                           biases['b1'])) 
        layer_2 = self.transfer_fct(tf.add(tf.matmul(layer_1, weights['h2']), 
                                           biases['b2'])) 
        x_reconstr_mean = \
            tf.nn.sigmoid(tf.add(tf.matmul(layer_2, weights['out_mean']), 
                                 biases['out_mean']))
        return x_reconstr_mean
            
    def _create_loss_optimizer(self):
        # The loss is composed of two terms:
        # 1.) The reconstruction loss (the negative log probability
        #     of the input under the reconstructed Bernoulli distribution 
        #     induced by the decoder in the data space).
        #     This can be interpreted as the number of "nats" required
        #     for reconstructing the input when the activation in latent
        #     is given.
        # Adding 1e-10 to avoid evaluatio of log(0.0)
        reconstr_loss = \
            -tf.reduce_sum(self.x * tf.log(1e-10 + self.x_reconstr_mean)
                           + (1-self.x) * tf.log(1e-10 + 1 - self.x_reconstr_mean),
                           1)
        # 2.) The latent loss, which is defined as the Kullback Leibler divergence 
        ##    between the distribution in latent space induced by the encoder on 
        #     the data and some prior. This acts as a kind of regularizer.
        #     This can be interpreted as the number of "nats" required
        #     for transmitting the the latent space distribution given
        #     the prior.
        latent_loss = -0.5 * tf.reduce_sum(1 + self.z_log_sigma_sq 
                                           - tf.square(self.z_mean) 
                                           - tf.exp(self.z_log_sigma_sq), 1)
        self.cost = tf.reduce_mean(reconstr_loss + latent_loss)   # average over batch
        # Use ADAM optimizer
        self.optimizer = \
            tf.train.AdamOptimizer(learning_rate=self.learning_rate).minimize(self.cost)
        
    def partial_fit(self, X):
        """Train model based on mini-batch of input data.
        
        Return cost of mini-batch.
        """
        opt, cost = self.sess.run((self.optimizer, self.cost), 
                                  feed_dict={self.x: X})
        return cost
    
    def transform(self, X):
        """Transform data by mapping it into the latent space."""
        # Note: This maps to mean of distribution, we could alternatively
        # sample from Gaussian distribution
        return self.sess.run(self.z_mean, feed_dict={self.x: X})
    
    def generate(self, z_mu=None):
        """ Generate data by sampling from latent space.
        
        If z_mu is not None, data for this point in latent space is
        generated. Otherwise, z_mu is drawn from prior in latent 
        space.        
        """
        if z_mu is None:
            z_mu = np.random.normal(size=self.network_architecture["n_z"])
        # Note: This maps to mean of distribution, we could alternatively
        # sample from Gaussian distribution
        return self.sess.run(self.x_reconstr_mean, 
                             feed_dict={self.z: z_mu})
    
    def reconstruct(self, X):
        """ Use VAE to reconstruct given data. """
        return self.sess.run(self.x_reconstr_mean, 
                             feed_dict={self.x: X})


def train(network_architecture, learning_rate=0.001,
          batch_size=100, training_epochs=10, display_step=5):
    vae = VariationalAutoencoder(network_architecture, 
                                 learning_rate=learning_rate, 
                                 batch_size=batch_size)
    # Training cycle
    for epoch in range(training_epochs):
        avg_cost = 0.
        total_batch = int(n_samples / batch_size)
        # Loop over all batches
        for i in range(total_batch):
            batch_xs, _ = mnist.train.next_batch(batch_size)

            # Fit training using batch data
            cost = vae.partial_fit(batch_xs)
            # Compute average loss
            avg_cost += cost / n_samples * batch_size

        # Display logs per epoch step
        if epoch % display_step == 0:
            print "Epoch:", '%04d' % (epoch+1), \
                  "cost=", "{:.9f}".format(avg_cost)
    return vae




network_architecture = \
    dict(n_hidden_recog_1=500, # 1st layer encoder neurons
         n_hidden_recog_2=500, # 2nd layer encoder neurons
         n_hidden_gener_1=500, # 1st layer decoder neurons
         n_hidden_gener_2=500, # 2nd layer decoder neurons
         n_input=784, # MNIST data input (img shape: 28*28)
         n_z=20)  # dimensionality of latent space

vae = train(network_architecture, training_epochs=75)


x_sample = mnist.test.next_batch(100)[0]
x_reconstruct = vae.reconstruct(x_sample)

plt.figure(figsize=(8, 12))
for i in range(5):

    plt.subplot(5, 2, 2*i + 1)
    plt.imshow(x_sample[i].reshape(28, 28), vmin=0, vmax=1)
    plt.title("Test input")
    plt.colorbar()
    plt.subplot(5, 2, 2*i + 2)
    plt.imshow(x_reconstruct[i].reshape(28, 28), vmin=0, vmax=1)
    plt.title("Reconstruction")
    plt.colorbar()
plt.tight_layout()


# -*- coding: utf-8 -*-

""" Auto Encoder Example.
Using an auto encoder on MNIST handwritten digits.
References:
    Y. LeCun, L. Bottou, Y. Bengio, and P. Haffner. "Gradient-based
    learning applied to document recognition." Proceedings of the IEEE,
    86(11):2278-2324, November 1998.
Links:
    [MNIST Dataset] http://yann.lecun.com/exdb/mnist/
"""
from __future__ import division, print_function, absolute_import

import tensorflow as tf
import numpy as np
import matplotlib.pyplot as plt

# Import MINST data
from tensorflow.examples.tutorials.mnist import input_data
mnist = input_data.read_data_sets("/tmp/data/", one_hot=True)

# Parameters
learning_rate = 0.01
training_epochs = 20
batch_size = 256
display_step = 1
examples_to_show = 10

# Network Parameters
n_hidden_1 = 256 # 1st layer num features
n_hidden_2 = 128 # 2nd layer num features
n_input = 784 # MNIST data input (img shape: 28*28)

# tf Graph input (only pictures)
X = tf.placeholder("float", [None, n_input])

weights = {
    'encoder_h1': tf.Variable(tf.random_normal([n_input, n_hidden_1])),
    'encoder_h2': tf.Variable(tf.random_normal([n_hidden_1, n_hidden_2])),
    'decoder_h1': tf.Variable(tf.random_normal([n_hidden_2, n_hidden_1])),
    'decoder_h2': tf.Variable(tf.random_normal([n_hidden_1, n_input])),
}
biases = {
    'encoder_b1': tf.Variable(tf.random_normal([n_hidden_1])),
    'encoder_b2': tf.Variable(tf.random_normal([n_hidden_2])),
    'decoder_b1': tf.Variable(tf.random_normal([n_hidden_1])),
    'decoder_b2': tf.Variable(tf.random_normal([n_input])),
}


# Building the encoder
def encoder(x):
    # Encoder Hidden layer with sigmoid activation #1
    layer_1 = tf.nn.sigmoid(tf.add(tf.matmul(x, weights['encoder_h1']),
                                   biases['encoder_b1']))
    # Decoder Hidden layer with sigmoid activation #2
    layer_2 = tf.nn.sigmoid(tf.add(tf.matmul(layer_1, weights['encoder_h2']),
                                   biases['encoder_b2']))
    return layer_2


# Building the decoder
def decoder(x):
    # Encoder Hidden layer with sigmoid activation #1
    layer_1 = tf.nn.sigmoid(tf.add(tf.matmul(x, weights['decoder_h1']),
                                   biases['decoder_b1']))
    # Decoder Hidden layer with sigmoid activation #2
    layer_2 = tf.nn.sigmoid(tf.add(tf.matmul(layer_1, weights['decoder_h2']),
                                   biases['decoder_b2']))
    return layer_2

# Construct model
encoder_op = encoder(X)
decoder_op = decoder(encoder_op)

# Prediction
y_pred = decoder_op
# Targets (Labels) are the input data.
y_true = X

# Define loss and optimizer, minimize the squared error
cost = tf.reduce_mean(tf.pow(y_true - y_pred, 2))
optimizer = tf.train.RMSPropOptimizer(learning_rate).minimize(cost)

# Initializing the variables
init = tf.initialize_all_variables()

# Launch the graph
with tf.Session() as sess:
    sess.run(init)
    total_batch = int(mnist.train.num_examples/batch_size)
    # Training cycle
    for epoch in range(training_epochs):
        # Loop over all batches
        for i in range(total_batch):
            batch_xs, batch_ys = mnist.train.next_batch(batch_size)
            # Run optimization op (backprop) and cost op (to get loss value)
            _, c = sess.run([optimizer, cost], feed_dict={X: batch_xs})
        # Display logs per epoch step
        if epoch % display_step == 0:
            print("Epoch:", '%04d' % (epoch+1),
                  "cost=", "{:.9f}".format(c))

    print("Optimization Finished!")

    # Applying encode and decode over test set
    encode_decode = sess.run(
        y_pred, feed_dict={X: mnist.test.images[:examples_to_show]})
    # Compare original images with their reconstructions
    f, a = plt.subplots(2, 10, figsize=(10, 2))
    for i in range(examples_to_show):
        a[0][i].imshow(np.reshape(mnist.test.images[i], (28, 28)))
        a[1][i].imshow(np.reshape(encode_decode[i], (28, 28)))
    f.show()
    plt.draw()
    plt.waitforbuttonpress()


    
