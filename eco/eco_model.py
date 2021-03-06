import logging
import math
from typing import Dict

import pandas
from sklearn.linear_model import HuberRegressor
from sklearn.linear_model.base import LinearModel
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split

from eco import config
from eco.data_utils import (dump_models, load_training_data,
                            prepare_training_data)

logger = logging.getLogger(__name__)


def train_regression(trees_df: pandas.DataFrame, factor: str) -> LinearModel:
    x_train, x_validation, y_train, y_validation = train_test_split(
        trees_df[['OBWOD', 'OBWOD_SQ']],
        trees_df[factor],
        test_size=0.2,
        random_state=52,
    )

    reg = HuberRegressor()
    reg.fit(x_train, y_train)
    mean_abs_err_val = mean_absolute_error(y_validation, reg.predict(x_validation))
    mean_abs_err_train = mean_absolute_error(y_train, reg.predict(x_train))
    r2_val = r2_score(y_validation, reg.predict(x_validation))
    r2_train = r2_score(y_train, reg.predict(x_train))
    logger.info(f'Trained {factor}. Mean_abs_err: {mean_abs_err_val}, R2: {r2_val}')
    logger.debug(f'(training set) Mean_abs_err: {mean_abs_err_train}, R2: {r2_train}')

    return reg


def predict_benefit(reg_model: LinearModel, trunk_diam: float) -> float:
    trunk_diam_sqrt = math.sqrt(trunk_diam)
    return reg_model.predict([[trunk_diam, trunk_diam_sqrt]])[0]


def predict_tree_benefits(models: dict, trunk_diam: float) -> Dict[str, float]:
    benefits = {}
    for factor in config.FACTORS:
        reg_model = models[factor]
        benefits[factor] = predict_benefit(reg_model, trunk_diam)
    return benefits


def train() -> None:
    tr_data = prepare_training_data(
        load_training_data(config.TRAINING_DATA_PATH))
    models = {}

    for factor in config.FACTORS:
        reg = train_regression(tr_data, factor)
        models[factor] = reg

    dump_models(models)
