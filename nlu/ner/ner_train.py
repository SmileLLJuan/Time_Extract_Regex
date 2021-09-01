# -*- coding:utf-8 -*-
# @Time: 2021/5/13 16:26
# @Author: ShaozongLi
# @Email: lishaozong@hikvision.com.cn
# @File: ner_train.py
import gc
import json
import logging
import os
import threading
from typing import Optional, Tuple, List, Dict

import torch
from dataclasses import dataclass, field
import numpy as np

from torch import nn
from seqeval.metrics import f1_score, precision_score, recall_score

from nlu.ner.convert_token import convert_nlu_to_bert_token_classification
from nlu.ner.ner_dataset import NerDataset, Split
from nlu.status import NluTrainStatus
from transformers import HfArgumentParser, TrainingArguments, set_seed, AutoConfig, BertTokenizer, \
    AutoModelForTokenClassification, Trainer, EvalPrediction
from utils.json_read import JsonRead
from utils.url import get_ner_config_dir, bert_model_name_parse, get_ner_model_dir

logger = logging.getLogger(__name__)


@dataclass
class ModelArguments:
    """
    Arguments pertaining to which model/config/tokenizer we are going to fine-tune from.
    """

    model_name_or_path: str = field(
        metadata={"help": "Path to pretrained model or model identifier from huggingface.co/models"}
    )
    config_name: Optional[str] = field(
        default=None, metadata={"help": "Pretrained config name or path if not the same as model_name"}
    )
    tokenizer_name: Optional[str] = field(
        default=None, metadata={"help": "Pretrained tokenizer name or path if not the same as model_name"}
    )
    use_fast: bool = field(default=False, metadata={"help": "Set this flag to use fast tokenization."})
    # If you want to tweak more attributes on your tokenizer, you should do it in a distinct script,
    # or just modify its tokenizer_config.json.
    cache_dir: Optional[str] = field(
        default=None, metadata={"help": "Where do you want to store the pretrained models downloaded from s3"}
    )


@dataclass
class DataTrainingArguments:
    """
    Arguments pertaining to what data we are going to input our model for training and eval.
    """

    data_dir: str = field(
        metadata={"help": "The input data dir. Should contain the .txt files for a CoNLL-2003-formatted task."}
    )
    labels: Optional[str] = field(
        metadata={"help": "Path to a file containing all labels. If not specified, CoNLL-2003 labels are used."}
    )
    max_seq_length: int = field(
        default=128,
        metadata={
            "help": "The maximum total input sequence length after tokenization. Sequences longer "
                    "than this will be truncated, sequences shorter will be padded."
        },
    )
    overwrite_cache: bool = field(
        default=True, metadata={"help": "Overwrite the cached training and evaluation sets"}
    )


class BertNer():
    def __init__(self):
        self.config = get_ner_config_dir()

    def train_main(self, config_dic, train_status):
        # See all possible arguments in src/transformers/training_args.py
        # or by passing the --help flag to this script.
        # We now keep distinct sets of args, for a cleaner separation of concerns.

        parser = HfArgumentParser((ModelArguments, DataTrainingArguments, TrainingArguments))
        '''
        if len(sys.argv) == 2 and sys.argv[1].endswith(".json"):
            # If we pass only one argument to the script and it's the path to a json file,
            # let's parse it to get our arguments.
            model_args, data_args, training_args = parser.parse_json_file(json_file=os.path.abspath(sys.argv[1]))
        else:
            model_args, data_args, training_args = parser.parse_args_into_dataclasses()
        '''
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

        # Prepare CONLL-2003 task
        with open(data_args.labels, "r") as f:
            labels = f.read().splitlines()
        # labels = get_labels(data_args.labels)
        label_map: Dict[int, str] = {i: label for i, label in enumerate(labels)}
        num_labels = len(labels)

        # Load pretrained model and tokenizer
        #
        # Distributed training:
        # The .from_pretrained methods guarantee that only one local process can concurrently
        # download model & vocab.

        config = AutoConfig.from_pretrained(
            model_args.config_name if model_args.config_name else model_args.model_name_or_path,
            num_labels=num_labels,
            id2label=label_map,
            label2id={label: i for i, label in enumerate(labels)},
            cache_dir=model_args.cache_dir,
        )
        tokenizer = BertTokenizer.from_pretrained(
            model_args.tokenizer_name if model_args.tokenizer_name else model_args.model_name_or_path,
            cache_dir=model_args.cache_dir,
            use_fast=model_args.use_fast,
        )
        model = AutoModelForTokenClassification.from_pretrained(
            model_args.model_name_or_path,
            from_tf=bool(".ckpt" in model_args.model_name_or_path),
            config=config,
            cache_dir=model_args.cache_dir,
        )

        # Get datasets
        train_dataset = (
            NerDataset(
                data_dir=data_args.data_dir,
                tokenizer=tokenizer,
                labels=labels,
                model_type=config.model_type,
                max_seq_length=data_args.max_seq_length,
                overwrite_cache=data_args.overwrite_cache,
                mode=Split.train,
            )
            if training_args.do_train
            else None
        )
        eval_dataset = (
            NerDataset(
                data_dir=data_args.data_dir,
                tokenizer=tokenizer,
                labels=labels,
                model_type=config.model_type,
                max_seq_length=data_args.max_seq_length,
                overwrite_cache=data_args.overwrite_cache,
                mode=Split.dev,
            )
            if training_args.do_eval
            else None
        )

        def align_predictions(predictions: np.ndarray, label_ids: np.ndarray) -> Tuple[List[int], List[int]]:
            preds = np.argmax(predictions, axis=2)

            batch_size, seq_len = preds.shape

            out_label_list = [[] for _ in range(batch_size)]
            preds_list = [[] for _ in range(batch_size)]

            for i in range(batch_size):
                for j in range(seq_len):
                    if label_ids[i, j] != nn.CrossEntropyLoss().ignore_index:
                        out_label_list[i].append(label_map[label_ids[i][j]])
                        preds_list[i].append(label_map[preds[i][j]])

            return preds_list, out_label_list

        def compute_metrics(p: EvalPrediction) -> Dict:
            preds_list, out_label_list = align_predictions(p.predictions, p.label_ids)
            return {
                "precision": precision_score(out_label_list, preds_list),
                "recall": recall_score(out_label_list, preds_list),
                "f1": f1_score(out_label_list, preds_list),
            }

        # Initialize our Trainer
        trainer = Trainer(
            train_status=train_status,
            model=model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            compute_metrics=compute_metrics,
            metric_max_var="eval_f1"
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
        results = {}
        results["step"] = train_out.global_step
        if training_args.do_eval:
            logger.info("*** Evaluate ***")

            result = trainer.evaluate()

            output_eval_file = os.path.join(training_args.output_dir, "eval_results.txt")
            if trainer.is_world_master():
                with open(output_eval_file, "w") as writer:
                    logger.info("***** Eval results *****")
                    for key, value in result.items():
                        logger.info("  %s = %s", key, value)
                        writer.write("%s = %s\n" % (key, value))

                results.update(result)
        # 评估后再加入
        results["global_step_max"] = trainer.global_step_max
        # Predict
        if training_args.do_predict:
            test_dataset = NerDataset(
                data_dir=data_args.data_dir,
                tokenizer=tokenizer,
                labels=labels,
                model_type=config.model_type,
                max_seq_length=data_args.max_seq_length,
                overwrite_cache=data_args.overwrite_cache,
                mode=Split.test,
            )

            predictions, label_ids, metrics = trainer.predict(test_dataset)
            preds_list, _ = align_predictions(predictions, label_ids)

            output_test_results_file = os.path.join(training_args.output_dir, "test_results.txt")
            if trainer.is_world_master():
                with open(output_test_results_file, "w") as writer:
                    for key, value in metrics.items():
                        logger.info("  %s = %s", key, value)
                        writer.write("%s = %s\n" % (key, value))

            # Save predictions
            output_test_predictions_file = os.path.join(training_args.output_dir, "test_predictions.txt")
            if trainer.is_world_master():
                with open(output_test_predictions_file, "w") as writer:
                    with open(os.path.join(data_args.data_dir, "test.txt"), "r") as f:
                        example_id = 0
                        for line in f:
                            if line.startswith("-DOCSTART-") or line == "" or line == "\n":
                                writer.write(line)
                                if not preds_list[example_id]:
                                    example_id += 1
                            elif preds_list[example_id]:
                                output_line = line.split()[0] + " " + preds_list[example_id].pop(0) + "\n"
                                writer.write(output_line)
                            else:
                                logger.warning(
                                    "Maximum sequence length exceeded: No prediction for '%s'.", line.split()[0]
                                )
        try:
            del trainer
            gc.collect()
        except Exception as e:
            logger.error(f"清理掉 trainer 释放资源 error,{e}")
        return results

    def train(self, project, train_data: str, train_status: NluTrainStatus, train_parameter_total):
        '''
        模型训练
        :param project: 项目名称
        :param train_data: 训练数据
        :param train_parameter: 训练参数
        :return:
        '''
        train_parameter = {}
        for train in train_parameter_total:
            if train['model_type'] == 'ner':
                train_parameter = train
                break

        train_status.increase_nlu_train_status()
        jr = JsonRead()
        config_dict = jr.read_dict(self.config)
        bert_model_type = train_parameter["model_name_or_path"] if train_parameter[
            "model_name_or_path"] else 'albert_chinese_base'
        config_dict["model_name_or_path"] = bert_model_name_parse(bert_model_type)
        config_dict["num_train_epochs"] = train_parameter["num_train_epochs"] if train_parameter[
            "num_train_epochs"] else 32
        config_dict["per_gpu_train_batch_size"] = train_parameter["per_gpu_train_batch_size"] if train_parameter[
            "per_gpu_train_batch_size"] else 16

        # 数据处理模块
        try:
            max_length = config_dict["max_seq_length"] if config_dict["max_seq_length"] else 64
            train_status.increase_nlu_train_status()
            convert_nlu_to_bert_token_classification(train_data, config_dict["model_name_or_path"], max_len=max_length)
        except FileNotFoundError as e:
            logger.error(f"the train data file is not found.{e}")
            raise
        except Exception as e:
            logger.error(f"process the ner data set occurs error.{e}")
            raise

        if torch.cuda.is_available():
            config_dict["no_cuda"] = False

        config_dict["output_dir"] = get_ner_model_dir(project)
        config_dict["data_dir"] = '/'.join(train_data.split('/')[:-1])
        config_dict["labels"] = os.path.join('/'.join(train_data.split('/')[:-1]), 'labels.txt')
        train_status.increase_nlu_train_status()
        # 写入训练配置文件
        os.makedirs(config_dict["output_dir"]) if not os.path.exists(config_dict["output_dir"]) else logger.debug(
            f"{config_dict['output_dir']} is exists")
        with open(os.path.join(config_dict["output_dir"], 'train_config.json'), 'w', encoding='utf-8') as f:
            json.dump(config_dict, f)
        self.train_main(config_dict, train_status)
        train_status.increase_nlu_train_status()

if __name__ == "__main__":
    pass
