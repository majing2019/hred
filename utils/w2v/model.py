import multiprocessing
import os
from gensim.models import Word2Vec

from husky.chat.generated.config import TRAIN_CORPUS_NAME, VOCABULARY_MAX_SIZE, WORD_EMBEDDING_DIMENSION, \
    USE_SKIP_GRAM, MIN_WORD_FREQ, TOKEN_REPRESENTATION_SIZE, W2V_WINDOW_SIZE
from husky.chat.generated.model.model_utils import ModelLoaderException
from husky.chat.generated.utils.files_utils import DummyFileResolver, ensure_dir
from husky.chat.generated.utils.logger import get_logger
from husky.chat.generated.utils.tee_file import file_buffered_tee
from husky.chat.generated.utils.w2v import get_w2v_model_name, get_w2v_params_str, get_w2v_model_path

_WORKERS_NUM = multiprocessing.cpu_count()

_logger = get_logger(__name__)


def _train_model(tokenized_lines, voc_size, vec_size, window_size, skip_gram):
    _logger.info('Word2Vec model will be trained now. It can take long, so relax and have fun.')

    params_str = get_w2v_params_str(voc_size, vec_size, window_size, skip_gram)
    _logger.info('Parameters for training: {}'.format(params_str))

    model = Word2Vec(
        window=window_size,
        size=vec_size,
        max_vocab_size=voc_size,
        min_count=MIN_WORD_FREQ,
        workers=_WORKERS_NUM,
        sg=skip_gram)

    tokenized_lines_for_voc, tokenized_lines_for_train = file_buffered_tee(tokenized_lines)

    model.build_vocab(tokenized_lines_for_voc)
    model.train(tokenized_lines_for_train, total_words=50000, epochs=10)

    # forget the original vectors and only keep the normalized ones = saves lots of memory
    # https://radimrehurek.com/gensim/models/word2vec.html#gensim.models.word2vec.Word2Vec.init_sims
    model.init_sims(replace=True)

    return model


def _save_model(model, model_path):
    _logger.info('Saving model to {}'.format(model_path))
    ensure_dir(os.path.dirname(model_path))
    model.save(model_path, separately=[])
    _logger.info('Model has been saved')

def _load_model(model_path):
    _logger.info('Loading model from {}'.format(model_path))
    model = Word2Vec.load(model_path, mmap='r')
    _logger.info('Model "{}" has been loaded.'.format(os.path.basename(model_path)))
    return model


def _get_w2v_model(corpus_name,
                   voc_size,
                   tokenized_lines=None,
                   vec_size=TOKEN_REPRESENTATION_SIZE,
                   window_size=W2V_WINDOW_SIZE,
                   skip_gram=USE_SKIP_GRAM):
    _logger.info('Getting w2v model')

    model_path = get_w2v_model_path(corpus_name, voc_size, vec_size, window_size, skip_gram)
    
    if not os.path.exists(model_path):
        if not tokenized_lines:
            raise ModelLoaderException(
                'Tokenized corpus "{}" was not provided, so w2v model can\'t be trained.'.format(corpus_name))

        # bin model is not present on the disk, so get it
        model = _train_model(tokenized_lines, voc_size, vec_size, window_size, skip_gram)
        _save_model(model, model_path)
    else:
        # bin model is on the disk, load it
        model = _load_model(model_path)

    _logger.info('Successfully got w2v model\n')

    return model

def get_w2v_model(corpus_name=TRAIN_CORPUS_NAME,
                  voc_size=VOCABULARY_MAX_SIZE,
                  vec_size=WORD_EMBEDDING_DIMENSION,
                  window_size=W2V_WINDOW_SIZE,
                  skip_gram=USE_SKIP_GRAM):

    w2v_model = _get_w2v_model(
        corpus_name=corpus_name,
        voc_size=voc_size,
        vec_size=vec_size,
        window_size=window_size,
        skip_gram=skip_gram)

    return w2v_model


def get_w2v_model_id(corpus_name=TRAIN_CORPUS_NAME,
                     voc_size=VOCABULARY_MAX_SIZE,
                     vec_size=WORD_EMBEDDING_DIMENSION,
                     window_size=W2V_WINDOW_SIZE,
                     skip_gram=USE_SKIP_GRAM):

    return get_w2v_model_name(
        corpus_name, voc_size=voc_size, vec_size=vec_size, window_size=window_size, skip_gram=skip_gram)
