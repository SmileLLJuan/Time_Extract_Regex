# -*- coding:utf-8 -*-
# @Time: 2021/5/13 19:04
# @Author: ShaozongLi
# @Email: lishaozong@hikvision.com.cn
# @File: intent_train.py
import json
import threading

import torch
from dataclasses import dataclass, field
import dataclasses
import gc
import logging
import os
from typing import Dict, Optional

import numpy as np

from nlu.intent.convert_intent import convert_nlu_to_bert_text_classification
from nlu.status import NluTrainStatus
from transformers import (
    HfArgumentParser,
    Trainer,
    TrainingArguments,
    glue_compute_metrics,
    glue_output_modes,
    glue_tasks_num_labels,
    set_seed,
)
from transformers import AutoConfig, AutoModelForSequenceClassification, EvalPrediction, GlueDataset, BertTokenizer
from transformers import GlueDataTrainingArguments as DataTrainingArguments
from utils.json_read import JsonRead
from utils.url import get_intent_config_dir, bert_model_name_parse, get_intent_model_dir

logger = logging.getLogger(__name__)


@dataclass
class ModelArguments:
    """
    Arguments pertaining to which model/config/tokenizer we are going to fine-tune from.
    """
    labels: Optional[str] = field(
        metadata={"help": "Path to a file containing all labels. If not specified, CoNLL-2003 labels are used."}
    )

    model_name_or_path: str = field(
        metadata={"help": "Path to pretrained model or model identifier from huggingface.co/models"}
    )
    config_name: Optional[str] = field(
        default=None, metadata={"help": "Pretrained config name or path if not the same as model_name"}
    )
    tokenizer_name: Optional[str] = field(
        default=None, metadata={"help": "Pretrained tokenizer name or path if not the same as model_name"}
    )
    cache_dir: Optional[str] = field(
        default=None, metadata={"help": "Where do you want to store the pretrained models downloaded from s3"}
    )


class BertIntent():

    def __init__(self):
        self.config = get_intent_config_dir()

    def train_main(self, config_dic,train_status):
        # See all possible arguments in src/transformers/training_args.py
        # or by passing the --help flag to this script.
        # We now keep distinct sets of args, for a cleaner separation of concerns.

        parser = HfArgumentParser((ModelArguments, DataTrainingArguments, TrainingArguments))
        model_args, data_args, training_args = parser.parse_map(config_dic)

        if (
                os.path.exists(training_args.output_dir)
                and os.listdir(training_args.output_dir)
                and training_args.do_train
                and not training_args.overwrite_output_dir
        ):
            raise ValueError(
                f"Output directory ({training_args.output_dir}) already exists and is not empty. Use --overwrite_output_dir to overcome."
            )

        # Setup logging
        logging.basicConfig(
            format="%(asctime)s - %(levelname)s - %(name)s -   %(message)s",
            datefmt="%m/%d/%Y %H:%M:%S",
            level=logging.INFO if training_args.local_rank in [-1, 0] else logging.WARN,
        )
        logger.warning(
            "Process rank: %s, device: %s, n_gpu: %s, distributed training: %s, 16-bits training: %s",
            training_args.local_rank,
            training_args.device,
            training_args.n_gpu,
            bool(training_args.local_rank != -1),
            training_args.fp16,
        )
        logger.info("Training/evaluation parameters %s", training_args)

        # Set seed
        set_seed(training_args.seed)

        output_mode = glue_output_modes[data_args.task_name]

        with open(model_args.labels, "r") as f:
            labels = f.read().splitlines()
            glue_tasks_num_labels[data_args.task_name] = len(labels)

        label_map: Dict[int, str] = {i: label for i, label in enumerate(labels)}
        num_labels = len(labels)

        config = AutoConfig.from_pretrained(
            model_args.config_name if model_args.config_name else model_args.model_name_or_path,
            num_labels=num_labels,
            id2label=label_map,
            label2id={label: i for i, label in enumerate(labels)},
            finetuning_task=data_args.task_name,
            cache_dir=model_args.cache_dir,
        )
        tokenizer = BertTokenizer.from_pretrained(
            model_args.tokenizer_name if model_args.tokenizer_name else model_args.model_name_or_path,
            cache_dir=model_args.cache_dir,
        )
        model = AutoModelForSequenceClassification.from_pretrained(
            model_args.model_name_or_path,
            from_tf=bool(".ckpt" in model_args.model_name_or_path),
            config=config,
            cache_dir=model_args.cache_dir,
        )

        # Get datasets
        train_dataset = GlueDataset(data_args, tokenizer=tokenizer, labels=labels) if training_args.do_train else None
        eval_dataset = GlueDataset(data_args, tokenizer=tokenizer, mode="dev",
                                   labels=labels) if training_args.do_eval else None
        test_dataset = GlueDataset(data_args, tokenizer=tokenizer, mode="test",
                                   labels=labels) if training_args.do_predict else None

        def compute_metrics(p: EvalPrediction) -> Dict:
            if output_mode == "classification":
                preds = np.argmax(p.predictions, axis=1)
            elif output_mode == "regression":
                preds = np.squeeze(p.predictions)
            return glue_compute_metrics(data_args.task_name, preds, p.label_ids)

        # Initialize our Trainer
        trainer = Trainer(
            train_status=train_status,
            model=model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            compute_metrics=compute_metrics,
            metric_max_var="eval_acc",
        )

        # Training
        if training_args.do_train:
            train_out = trainer.train(
                model_path=model_args.model_name_or_path if os.path.isdir(model_args.model_name_or_path) else None
            )
            trainer.save_model()
            # For convenience, we also re-save the tokenizer to the same directory,
            # so that you can share your model easily on huggingface.co/models =)
            if trainer.is_world_master():
                tokenizer.save_pretrained(training_args.output_dir)

        # Evaluation
        eval_results = {}
        eval_results["step"] = train_out.global_step
        if training_args.do_eval:
            logger.info("*** Evaluate ***")

            # Loop to handle MNLI double evaluation (matched, mis-matched)
            eval_datasets = [eval_dataset]
            if data_args.task_name == "mnli":
                mnli_mm_data_args = dataclasses.replace(data_args, task_name="mnli-mm")
                eval_datasets.append(GlueDataset(mnli_mm_data_args, tokenizer=tokenizer, mode="dev"))

            for eval_dataset in eval_datasets:
                eval_result = trainer.evaluate(eval_dataset=eval_dataset)

                output_eval_file = os.path.join(
                    training_args.output_dir, f"eval_results_{eval_dataset.args.task_name}.txt"
                )
                if trainer.is_world_master():
                    with open(output_eval_file, "w") as writer:
                        logger.info("***** Eval results {} *****".format(eval_dataset.args.task_name))
                        for key, value in eval_result.items():
                            logger.info("  %s = %s", key, value)
                            writer.write("%s = %s\n" % (key, value))

                eval_results.update(eval_result)

        # 评估后再加入
        eval_results["global_step_max"] = trainer.global_step_max
        if training_args.do_predict:
            logging.info("*** Test ***")
            test_datasets = [test_dataset]
            if data_args.task_name == "mnli":
                mnli_mm_data_args = dataclasses.replace(data_args, task_name="mnli-mm")
                test_datasets.append(GlueDataset(mnli_mm_data_args, tokenizer=tokenizer, mode="test"))

            for test_dataset in test_datasets:
                predictions = trainer.predict(test_dataset=test_dataset).predictions
                if output_mode == "classification":
                    predictions = np.argmax(predictions, axis=1)

                output_test_file = os.path.join(
                    training_args.output_dir, f"test_results_{test_dataset.args.task_name}.txt"
                )
                if trainer.is_world_master():
                    with open(output_test_file, "w") as writer:
                        logger.info("***** Test results {} *****".format(test_dataset.args.task_name))
                        writer.write("index\tprediction\n")
                        for index, item in enumerate(predictions):
                            if output_mode == "regression":
                                writer.write("%d\t%3.3f\n" % (index, item))
                            else:
                                item = test_dataset.get_labels()[item]
                                writer.write("%d\t%s\n" % (index, item))

        try:
            del trainer
            gc.collect()
        except Exception as e:
            logger.error(f"清理掉 trainer 释放资源 error,{e}")
        return eval_results

    def train(self, project, train_data: str,train_status:NluTrainStatus, train_parameter_total):
        '''
        模型训练
        :param project: 项目名称
        :param train_data: 训练数据
        :param train_parameter: 训练参数
        :return:
        '''
        train_parameter = {}
        for train in train_parameter_total:
            if train['model_type'] == 'intent':
                train_parameter = train
                break
        train_status.increase_nlu_train_status()
        jr = JsonRead()
        config_dict = jr.read_dict(self.config)
        bert_model_type=train_parameter["model_name_or_path"] if train_parameter["model_name_or_path"] else 'albert_chinese_base'
        config_dict["model_name_or_path"] = bert_model_name_parse(bert_model_type)
        config_dict["num_train_epochs"] = train_parameter["num_train_epochs"] if train_parameter[
            "num_train_epochs"] else 32
        config_dict["per_gpu_train_batch_size"] = train_parameter["per_gpu_train_batch_size"] if train_parameter[
            "per_gpu_train_batch_size"] else 16

        # 数据处理模块
        try:
            train_status.increase_nlu_train_status()
            convert_nlu_to_bert_text_classification(train_data)
        except FileNotFoundError as e:
            logger.error(f"the train data file is not found.{e}")
            raise
        except Exception as e:
            logger.error(f"process the ner data set occurs error.{e}")
            raise

        if torch.cuda.is_available():
            config_dict["no_cuda"] = False

        config_dict["output_dir"] = get_intent_model_dir(project)
        config_dict["data_dir"] = '/'.join(train_data.split('/')[:-1])
        config_dict["labels"] = os.path.join('/'.join(train_data.split('/')[:-1]), 'labels.txt')
        train_status.increase_nlu_train_status()

        os.makedirs(config_dict["output_dir"]) if not os.path.exists(config_dict["output_dir"]) else logger.debug(
            f"{config_dict['output_dir']} is exists")
        # 写入训练配置文件
        with open(os.path.join(config_dict["output_dir"], 'train_config.json'), 'w', encoding='utf-8') as f:
            json.dump(config_dict, f)
        self.train_main(config_dict,train_status)
        train_status.increase_nlu_train_status()


def thread_intent_train(project, train_data, train_parameter):
    '''
    单线程 意图分类模型训练入口
    :param project:
    :param train_data:
    :param train_parameter:
    :return:
    '''
    intent = BertIntent()
    # 启动一个线程执行
    threading.Thread(target=intent.train,
                     kwargs={'project': project, 'train_data': train_data, 'train_parameter': train_parameter},
                     name='thread_train_intent').start()
    logger.debug("start thread")


if __name__ == "__main__":
    pass
