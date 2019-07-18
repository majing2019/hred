import os

from cachetools import cached

from husky.chat.generated.config import BASE_CORPUS_NAME, PREDICTION_MODES, TRAIN_CORPUS_NAME, \
    USE_PRETRAINED_W2V_EMBEDDINGS_LAYER
from husky.chat.generated.model.inference_model import InferenceCakeChatModel
from husky.chat.generated.utils.data_types import ModelParam
from husky.chat.generated.utils.dataset_loader import get_validation_data_id, get_validation_sets_names
from husky.chat.generated.utils.files_utils import FileNotFoundException
from husky.chat.generated.utils.text_processing import get_index_to_token_path, load_index_to_item, get_index_to_condition_path
from husky.chat.generated.utils.w2v.model import get_w2v_model_id


def _get_index_to_token():
    index_to_token_path = get_index_to_token_path(BASE_CORPUS_NAME)
    file_name = os.path.basename(index_to_token_path)
    if not os.path.exists(index_to_token_path):
        raise FileNotFoundException('No such file: {}'.format(file_name) + ' in: {}'.format(index_to_token_path) +
                                    'Run "python tools/fetch.py" first to get all necessary files.')

    return load_index_to_item(index_to_token_path)


def _get_index_to_condition():
    index_to_condition_path = get_index_to_condition_path(BASE_CORPUS_NAME)
    if not os.path.exists(index_to_condition_path):
        raise FileNotFoundException('Can\'t get index_to_condition because file does not exist. '
                                    'Run tools/fetch.py first to get all required files or construct '
                                    'it yourself.')

    return load_index_to_item(index_to_condition_path)


@cached(cache={})
def get_trained_model(is_reverse_model=False, reverse_model=None):
    """
    Get a trained model, direct or reverse.
    :param is_reverse_model: boolean, if True, a reverse trained model will be returned to be used during inference
    in direct model in *_reranking modes; if False, a direct trained model is returned
    :param reverse_model: object of a reverse model to be used in direct model in *_reranking inference modes
    :return:
    """
    resolver_factory = None

    w2v_model_id = get_w2v_model_id() if USE_PRETRAINED_W2V_EMBEDDINGS_LAYER else None

    model = InferenceCakeChatModel(
        index_to_token=_get_index_to_token(),
        index_to_condition=_get_index_to_condition(),
        training_data_param=ModelParam(value=None, id=TRAIN_CORPUS_NAME),
        validation_data_param=ModelParam(value=None, id=get_validation_data_id(get_validation_sets_names())),
        w2v_model_param=ModelParam(value=None, id=w2v_model_id),
        model_resolver=resolver_factory,
        is_reverse_model=is_reverse_model,
        reverse_model=reverse_model)

    model.init_model()
    model.resolve_model()
    return model


def get_reverse_model(prediction_mode):
    reranking_modes = [PREDICTION_MODES.beamsearch_reranking, PREDICTION_MODES.sampling_reranking]
    return get_trained_model(is_reverse_model=True) if prediction_mode in reranking_modes else None
