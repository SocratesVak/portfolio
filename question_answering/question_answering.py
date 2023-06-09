# -*- coding: utf-8 -*-
"""Question_Answering.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/146F3MnCxYM-2QmevpEAAhsCMNSnH8E1Y
"""

!pip install huggingface_hub
from huggingface_hub import notebook_login
notebook_login()

!pip install datasets
from datasets import load_dataset
squad = load_dataset("squad", split="train")
squad = squad.train_test_split(test_size=0.2)

squad["train"][0]

!pip install transformers
from transformers import AutoTokenizer
tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")

def preprocess_function(examples):
    questions = [q.strip() for q in examples["question"]]
    
    inputs = tokenizer(
        questions,
        examples["context"],
        max_length=384,
        truncation="only_second",
        return_offsets_mapping=True,
        padding="max_length",
    )

    offset_mapping = inputs.pop("offset_mapping")
    answers = examples["answers"]
    start_positions = []
    end_positions = []

    for i, offset in enumerate(offset_mapping):
        answer = answers[i]
        start_char = answer["answer_start"][0]
        end_char = answer["answer_start"][0] + len(answer["text"][0])
        sequence_ids = inputs.sequence_ids(i)

        # Find the start and end of the context
        idx = 0
        while sequence_ids[idx] != 1:
            idx += 1
        context_start = idx
        while sequence_ids[idx] == 1:
            idx += 1
        context_end = idx - 1

        # If the answer is not fully inside the context, label it (0, 0)
        if offset[context_start][0] > end_char or offset[context_end][1] < start_char:
            start_positions.append(0)
            end_positions.append(0)
        else:
            # Otherwise it's the start and end token positions
            idx = context_start
            while idx <= context_end and offset[idx][0] <= start_char:
                idx += 1
            start_positions.append(idx - 1)

            idx = context_end
            while idx >= context_start and offset[idx][1] >= end_char:
                idx -= 1
            end_positions.append(idx + 1)

    inputs["start_positions"] = start_positions
    inputs["end_positions"] = end_positions
    return inputs

tokenized_squad = squad.map(preprocess_function, batched=True, remove_columns=squad["train"].column_names)

tokenized_squad

from transformers import DefaultDataCollator, AutoModelForQuestionAnswering, TrainingArguments, Trainer
data_collator = DefaultDataCollator()
model = AutoModelForQuestionAnswering.from_pretrained("distilbert-base-uncased")

from torch import cuda
device = 'cuda' if cuda.is_available() else 'cpu'

training_args = TrainingArguments(
    output_dir="my_qa_model",
    evaluation_strategy="epoch",
    learning_rate=2e-5,
    per_device_train_batch_size=32,
    per_device_eval_batch_size=32,
    num_train_epochs=5,
    weight_decay=0.01,
    push_to_hub=False,
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_squad["train"],
    eval_dataset=tokenized_squad["test"],
    tokenizer=tokenizer,
    data_collator=data_collator,
)

trainer.train()

question = "How many programming languages does BLOOM support?"
context = "BLOOM has 176 billion parameters and can generate text in 46 languages natural languages and 13 programming languages."

tokenizer = AutoTokenizer.from_pretrained("/content/my_qa_model/checkpoint-10500")
model = AutoModelForQuestionAnswering.from_pretrained("/content/my_qa_model/checkpoint-10500")
inputs = tokenizer(question, context, return_tensors="pt")

import torch

with torch.no_grad():
    outputs = model(**inputs)

answer_start_index = outputs.start_logits.argmax()
answer_end_index = outputs.end_logits.argmax()

predict_answer_tokens = inputs.input_ids[0, answer_start_index : answer_end_index + 1]
print(question)
tokenizer.decode(predict_answer_tokens)

import pandas as pd
eval = pd.DataFrame(squad['train'])

evaluation_data = eval.sample(n=200)

evaluation_data

questions = list(evaluation_data['question'])
contexts = list(evaluation_data['context'])
answers= list(evaluation_data['answers'])

answers = [x['text'][0] for x in answers]

import re
import string
import collections

def normalize_answer(s):
  """Lower text and remove punctuation, articles and extra whitespace."""
  def remove_articles(text):
    regex = re.compile(r'\b(a|an|the)\b', re.UNICODE)
    return re.sub(regex, ' ', text)
  def white_space_fix(text):
    return ' '.join(text.split())
  def remove_punc(text):
    exclude = set(string.punctuation)
    return ''.join(ch for ch in text if ch not in exclude)
  def lower(text):
    return text.lower()
  return white_space_fix(remove_articles(remove_punc(lower(s))))

def get_tokens(s):
  if not s: return []
  return normalize_answer(s).split()

def compute_exact(a_gold, a_pred):
  return int(normalize_answer(a_gold) == normalize_answer(a_pred))

def compute_f1(a_gold, a_pred):
  gold_toks = get_tokens(a_gold)
  pred_toks = get_tokens(a_pred)
  common = collections.Counter(gold_toks) & collections.Counter(pred_toks)
  num_same = sum(common.values())
  if len(gold_toks) == 0 or len(pred_toks) == 0:
    # If either is no-answer, then F1 is 1 if they agree, 0 otherwise
    return int(gold_toks == pred_toks)
  if num_same == 0:
    return 0
  precision = 1.0 * num_same / len(pred_toks)
  recall = 1.0 * num_same / len(gold_toks)
  f1 = (2 * precision * recall) / (precision + recall)
  return f1

f1=[]
exact=[]

for i in range(len(questions)):
  inputs = tokenizer(questions[i], contexts[i], return_tensors="pt")
  with torch.no_grad():
    outputs = model(**inputs)
  answer_start_index = outputs.start_logits.argmax()
  answer_end_index = outputs.end_logits.argmax()
  predict_answer_tokens = inputs.input_ids[0, answer_start_index : answer_end_index + 1]
  predict_answer = tokenizer.decode(predict_answer_tokens)
  print(i,' ', questions[i],'\n','prediction: ', predict_answer,'\n',"ground truth: ", answers[i],'\n','-----------------------------')
  exact.append(compute_exact(answers[i],predict_answer))
  f1.append(compute_f1(answers[i],predict_answer))

from statistics import mean

f1_final=mean(f1)
exact_final=mean(exact)

print("F1 score is: ",f1_final)
print("Exact matches score is: ",exact_final)