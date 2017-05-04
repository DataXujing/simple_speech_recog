"""
1. ckpt/1-bi-rnn-gru-tanh/
2. ckpt/1-bi-rnn-gru-tanh-l2norm/
3. ckpt/1-bi-rnn-lstm-tanh-l2norm/
4. ckpt/2-bi-rnn-lstm-tanh-l2norm/
"""
import tensorflow as tf
from models import *
from utils import *

FLAG = False
COUNTER = 0

LOG_DIR = 'ckpt/3-bi-rnn-lstm-tanh-l2norm/'


def one_iteration(model, batch_data, step, writer, sess=None):
    features = batch_data['features']
    labels = batch_data['labels']
    seq_length = batch_data['seq_length']
    if sess is None:
        sess = tf.get_default_session()
    if sess is None:
        raise ValueError("you must pass a session or using with tf.Session() as sess")
    sparse_labels = sparse_tuple_from(labels)

    feed_dict = {model.inputs: features,
                 model.labels: labels,
                 model.sparse_labels: sparse_labels,
                 model.seq_lengths: seq_length}
    fetch_list = [model.optimizer, model.merge_summary, model.edit_distance]
    _, summary, edit_distance = sess.run(fetch_list, feed_dict)
    writer.add_summary(summary=summary, global_step=step)
    if edit_distance <= 0.01:
        global COUNTER
        global FLAG
        FLAG = True
        COUNTER += 1
        print("COUNTER->", COUNTER)
        if COUNTER >= 10:
            exit()
    else:
        global COUNTER
        global FLAG
        if FLAG:
            COUNTER -= 1
            FLAG = False
            print("COUNTER->", COUNTER)


def main(_):
    tf.set_random_seed(2017)
    config = ConfigDelta()
    # prepare data
    root_dir = "data"
    train_files,_ = split_file_names(root_dir)
    id2cls, cls2id = generating_cls()
    bg = BatchGenerator(config, train_files, cls2id=cls2id)
    iter_bg = iter(bg)

    # build model

    model = BiRnnModel(config, rnn_type='lstm')
    model.inference()
    model.train_op()
    saver = tf.train.Saver()
    with tf.Session() as sess:
        # train model
        tf.global_variables_initializer().run()
        #8180
        saver.restore(sess, save_path=LOG_DIR+'rnn-model.ckpt')

        writer = tf.summary.FileWriter(logdir=LOG_DIR, graph=sess.graph)
        for i in range(config.num_iterations):
            features, labels,  seq_length = next(iter_bg)
            batch_data={}
            batch_data['features'] = features
            batch_data['labels'] = labels
            batch_data['seq_length'] = seq_length
            one_iteration(model, batch_data=batch_data, step=i, writer=writer)
            if i % 10 == 0:
                print("iteration count: ", i)
                saver.save(sess, save_path=LOG_DIR+'rnn-model.ckpt')
if __name__ == '__main__':
    tf.app.run()